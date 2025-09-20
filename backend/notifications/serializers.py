from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .models import (
    Notification, 
    NotificationTemplate, 
    NotificationSettings, 
    NotificationBatch
)

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Базовый сериализатор пользователя для уведомлений"""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'avatar_url']
        read_only_fields = ['id', 'username', 'email']
    
    def get_avatar_url(self, obj):
        """Получить URL аватара пользователя"""
        if hasattr(obj, 'profile') and obj.profile.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile.avatar.url)
        return None


class ContentObjectSerializer(serializers.Serializer):
    """Сериализатор для связанного объекта"""
    
    id = serializers.IntegerField()
    model = serializers.CharField()
    app_label = serializers.CharField()
    name = serializers.CharField()
    url = serializers.CharField(required=False)
    
    def to_representation(self, instance):
        """Преобразование объекта в представление"""
        if not instance:
            return None
        
        data = {
            'id': instance.pk,
            'model': instance._meta.model_name,
            'app_label': instance._meta.app_label,
            'name': str(instance)
        }
        
        # Добавляем URL если возможно
        try:
            if hasattr(instance, 'get_absolute_url'):
                data['url'] = instance.get_absolute_url()
        except:
            pass
        
        return data


class NotificationSerializer(serializers.ModelSerializer):
    """Сериализатор уведомления"""
    
    recipient = UserBasicSerializer(read_only=True)
    sender = UserBasicSerializer(read_only=True)
    content_object = ContentObjectSerializer(read_only=True)
    
    # Дополнительные поля
    age_in_days = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'sender', 'title', 'message',
            'notification_type', 'notification_type_display',
            'category', 'category_display',
            'priority', 'priority_display',
            'content_object', 'is_read', 'read_at',
            'created_at', 'expires_at', 'action_url',
            'extra_data', 'age_in_days', 'is_expired'
        ]
        read_only_fields = [
            'id', 'recipient', 'sender', 'created_at', 'read_at',
            'age_in_days', 'is_expired'
        ]
    
    def get_age_in_days(self, obj):
        """Возраст уведомления в днях"""
        return obj.get_age_in_days()
    
    def get_is_expired(self, obj):
        """Проверка истечения срока"""
        return obj.is_expired()


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания уведомления"""
    
    recipient_id = serializers.IntegerField(write_only=True)
    content_type_id = serializers.IntegerField(write_only=True, required=False)
    object_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Notification
        fields = [
            'recipient_id', 'title', 'message',
            'notification_type', 'category', 'priority',
            'content_type_id', 'object_id',
            'action_url', 'expires_at', 'extra_data'
        ]
    
    def validate_recipient_id(self, value):
        """Валидация получателя"""
        try:
            User.objects.get(id=value)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError('Пользователь не найден')
    
    def validate(self, attrs):
        """Общая валидация"""
        # Проверяем связанный объект
        content_type_id = attrs.get('content_type_id')
        object_id = attrs.get('object_id')
        
        if content_type_id and not object_id:
            raise serializers.ValidationError(
                'Необходимо указать object_id при указании content_type_id'
            )
        
        if object_id and not content_type_id:
            raise serializers.ValidationError(
                'Необходимо указать content_type_id при указании object_id'
            )
        
        # Проверяем срок действия
        expires_at = attrs.get('expires_at')
        if expires_at and expires_at <= timezone.now():
            raise serializers.ValidationError(
                'Срок действия должен быть в будущем'
            )
        
        return attrs
    
    def create(self, validated_data):
        """Создание уведомления"""
        recipient_id = validated_data.pop('recipient_id')
        content_type_id = validated_data.pop('content_type_id', None)
        object_id = validated_data.pop('object_id', None)
        
        # Получаем пользователя
        recipient = User.objects.get(id=recipient_id)
        
        # Устанавливаем связанный объект
        if content_type_id and object_id:
            content_type = ContentType.objects.get(id=content_type_id)
            validated_data['content_type'] = content_type
            validated_data['object_id'] = object_id
        
        # Устанавливаем отправителя из контекста
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['sender'] = request.user
        
        validated_data['recipient'] = recipient
        
        return super().create(validated_data)


class NotificationUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления уведомления"""
    
    class Meta:
        model = Notification
        fields = ['is_read']
    
    def update(self, instance, validated_data):
        """Обновление уведомления"""
        is_read = validated_data.get('is_read')
        
        if is_read and not instance.is_read:
            instance.mark_as_read()
        elif not is_read and instance.is_read:
            instance.is_read = False
            instance.read_at = None
            instance.save(update_fields=['is_read', 'read_at'])
        
        return instance


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Сериализатор шаблона уведомления"""
    
    usage_count = serializers.SerializerMethodField()
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'title_template', 'message_template',
            'notification_type', 'notification_type_display',
            'category', 'category_display',
            'priority', 'priority_display',
            'is_active', 'default_expires_days',
            'usage_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']
    
    def get_usage_count(self, obj):
        """Количество использований шаблона"""
        return obj.notificationbatch_set.count()


class NotificationSettingsSerializer(serializers.ModelSerializer):
    """Сериализатор настроек уведомлений"""
    
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = NotificationSettings
        fields = [
            'id', 'user', 'email_notifications', 'push_notifications',
            'project_notifications', 'facility_notifications',
            'document_notifications', 'security_notifications',
            'low_priority_notifications', 'normal_priority_notifications',
            'high_priority_notifications', 'urgent_priority_notifications',
            'quiet_hours_start', 'quiet_hours_end',
            'auto_delete_read_after_days', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        """Валидация настроек"""
        quiet_start = attrs.get('quiet_hours_start')
        quiet_end = attrs.get('quiet_hours_end')
        
        # Проверяем тихие часы
        if quiet_start and quiet_end:
            if quiet_start >= quiet_end:
                raise serializers.ValidationError(
                    'Время начала тихих часов должно быть меньше времени окончания'
                )
        
        # Проверяем период автоудаления
        auto_delete_days = attrs.get('auto_delete_read_after_days')
        if auto_delete_days and auto_delete_days < 1:
            raise serializers.ValidationError(
                'Период автоудаления должен быть больше 0 дней'
            )
        
        return attrs


class NotificationBatchSerializer(serializers.ModelSerializer):
    """Сериализатор пакета уведомлений"""
    
    template = NotificationTemplateSerializer(read_only=True)
    template_id = serializers.IntegerField(write_only=True)
    recipients = UserBasicSerializer(many=True, read_only=True)
    recipient_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )
    created_by = UserBasicSerializer(read_only=True)
    
    # Статистика
    success_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = NotificationBatch
        fields = [
            'id', 'name', 'template', 'template_id',
            'recipients', 'recipient_ids', 'context_data',
            'is_sent', 'sent_at', 'total_recipients',
            'successful_sends', 'failed_sends', 'success_rate',
            'created_at', 'created_by'
        ]
        read_only_fields = [
            'id', 'is_sent', 'sent_at', 'total_recipients',
            'successful_sends', 'failed_sends', 'success_rate',
            'created_at', 'created_by'
        ]
    
    def get_success_rate(self, obj):
        """Процент успешных отправок"""
        if obj.total_recipients > 0:
            return round((obj.successful_sends / obj.total_recipients) * 100, 2)
        return 0
    
    def validate_template_id(self, value):
        """Валидация шаблона"""
        try:
            template = NotificationTemplate.objects.get(id=value)
            if not template.is_active:
                raise serializers.ValidationError('Шаблон неактивен')
            return value
        except NotificationTemplate.DoesNotExist:
            raise serializers.ValidationError('Шаблон не найден')
    
    def validate_recipient_ids(self, value):
        """Валидация получателей"""
        if not value:
            raise serializers.ValidationError('Необходимо указать получателей')
        
        # Проверяем существование пользователей
        existing_users = User.objects.filter(id__in=value).values_list('id', flat=True)
        missing_users = set(value) - set(existing_users)
        
        if missing_users:
            raise serializers.ValidationError(
                f'Пользователи не найдены: {list(missing_users)}'
            )
        
        return value
    
    def create(self, validated_data):
        """Создание пакета уведомлений"""
        template_id = validated_data.pop('template_id')
        recipient_ids = validated_data.pop('recipient_ids')
        
        # Получаем шаблон
        template = NotificationTemplate.objects.get(id=template_id)
        
        # Устанавливаем создателя
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        
        validated_data['template'] = template
        
        # Создаем пакет
        batch = super().create(validated_data)
        
        # Добавляем получателей
        recipients = User.objects.filter(id__in=recipient_ids)
        batch.recipients.set(recipients)
        
        return batch


class NotificationStatsSerializer(serializers.Serializer):
    """Сериализатор статистики уведомлений"""
    
    total_notifications = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()
    read_notifications = serializers.IntegerField()
    expired_notifications = serializers.IntegerField()
    
    # Статистика по типам
    by_type = serializers.DictField()
    by_category = serializers.DictField()
    by_priority = serializers.DictField()
    
    # Статистика по времени
    today_notifications = serializers.IntegerField()
    week_notifications = serializers.IntegerField()
    month_notifications = serializers.IntegerField()
    
    # Процентные показатели
    read_rate = serializers.FloatField()
    response_time_avg = serializers.FloatField()  # Среднее время ответа в часах


class BulkNotificationActionSerializer(serializers.Serializer):
    """Сериализатор для массовых действий с уведомлениями"""
    
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    action = serializers.ChoiceField(
        choices=['mark_read', 'mark_unread', 'delete']
    )
    
    def validate_notification_ids(self, value):
        """Валидация ID уведомлений"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError('Пользователь не аутентифицирован')
        
        # Проверяем, что все уведомления принадлежат пользователю
        user_notifications = Notification.objects.filter(
            id__in=value,
            recipient=request.user
        ).values_list('id', flat=True)
        
        missing_notifications = set(value) - set(user_notifications)
        if missing_notifications:
            raise serializers.ValidationError(
                f'Уведомления не найдены или не принадлежат пользователю: {list(missing_notifications)}'
            )
        
        return value


class NotificationPreferencesSerializer(serializers.Serializer):
    """Сериализатор для быстрой настройки предпочтений"""
    
    enable_all = serializers.BooleanField(required=False)
    disable_all = serializers.BooleanField(required=False)
    categories = serializers.ListField(
        child=serializers.ChoiceField(choices=[
            'project', 'facility', 'document', 'security'
        ]),
        required=False
    )
    priorities = serializers.ListField(
        child=serializers.ChoiceField(choices=[
            'low', 'normal', 'high', 'urgent'
        ]),
        required=False
    )
    
    def validate(self, attrs):
        """Валидация предпочтений"""
        enable_all = attrs.get('enable_all')
        disable_all = attrs.get('disable_all')
        
        if enable_all and disable_all:
            raise serializers.ValidationError(
                'Нельзя одновременно включить и отключить все уведомления'
            )
        
        return attrs