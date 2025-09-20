from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from .models import (
    FacilityType,
    Facility,
    FacilityDocument,
    FacilityImage,
    MaintenanceSchedule
)

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Базовый сериализатор пользователя"""
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name', 'email']
        read_only_fields = ['id', 'username', 'email']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class FacilityTypeSerializer(serializers.ModelSerializer):
    """Сериализатор типа объекта недвижимости"""
    
    facilities_count = serializers.SerializerMethodField()
    
    class Meta:
        model = FacilityType
        fields = [
            'id',
            'name',
            'description',
            'icon',
            'is_active',
            'facilities_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'facilities_count']
    
    def get_facilities_count(self, obj):
        """Количество объектов данного типа"""
        return getattr(obj, 'facilities_count', obj.facilities.count())


class FacilityImageSerializer(serializers.ModelSerializer):
    """Сериализатор изображений объекта"""
    
    uploaded_by = UserBasicSerializer(read_only=True)
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = FacilityImage
        fields = [
            'id',
            'title',
            'image',
            'image_url',
            'image_type',
            'description',
            'is_primary',
            'order',
            'uploaded_at',
            'uploaded_by'
        ]
        read_only_fields = ['id', 'uploaded_at', 'uploaded_by', 'image_url']
    
    def get_image_url(self, obj):
        """Полный URL изображения"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def create(self, validated_data):
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)


class FacilityDocumentSerializer(serializers.ModelSerializer):
    """Сериализатор документов объекта"""
    
    uploaded_by = UserBasicSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()
    file_extension = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = FacilityDocument
        fields = [
            'id',
            'name',
            'document_type',
            'file',
            'file_url',
            'file_size_mb',
            'file_extension',
            'description',
            'document_date',
            'expiry_date',
            'is_expired',
            'is_active',
            'uploaded_at',
            'uploaded_by'
        ]
        read_only_fields = [
            'id',
            'uploaded_at',
            'uploaded_by',
            'file_url',
            'file_size_mb',
            'file_extension',
            'is_expired'
        ]
    
    def get_file_url(self, obj):
        """Полный URL файла"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_file_size_mb(self, obj):
        """Размер файла в мегабайтах"""
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return 0
    
    def get_file_extension(self, obj):
        """Расширение файла"""
        return obj.file_extension
    
    def get_is_expired(self, obj):
        """Проверка истечения срока действия"""
        return obj.is_expired
    
    def create(self, validated_data):
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)


class MaintenanceScheduleSerializer(serializers.ModelSerializer):
    """Сериализатор графика обслуживания"""
    
    responsible_person = UserBasicSerializer(read_only=True)
    responsible_person_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    created_by = UserBasicSerializer(read_only=True)
    is_overdue = serializers.SerializerMethodField()
    days_until_maintenance = serializers.SerializerMethodField()
    
    class Meta:
        model = MaintenanceSchedule
        fields = [
            'id',
            'name',
            'description',
            'frequency',
            'custom_frequency_days',
            'start_date',
            'end_date',
            'next_maintenance_date',
            'responsible_person',
            'responsible_person_id',
            'status',
            'estimated_duration_hours',
            'estimated_cost',
            'notes',
            'is_overdue',
            'days_until_maintenance',
            'created_at',
            'updated_at',
            'created_by'
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'created_by',
            'is_overdue',
            'days_until_maintenance'
        ]
    
    def get_is_overdue(self, obj):
        """Проверка просрочки"""
        return obj.is_overdue
    
    def get_days_until_maintenance(self, obj):
        """Дни до следующего обслуживания"""
        from django.utils import timezone
        if obj.next_maintenance_date:
            delta = obj.next_maintenance_date - timezone.now().date()
            return delta.days
        return None
    
    def validate(self, data):
        """Валидация данных"""
        # Проверка пользовательской периодичности
        if data.get('frequency') == 'custom' and not data.get('custom_frequency_days'):
            raise serializers.ValidationError({
                'custom_frequency_days': _('Обязательно для пользовательской периодичности')
            })
        
        # Проверка дат
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError({
                'end_date': _('Дата окончания должна быть позже даты начала')
            })
        
        return data
    
    def create(self, validated_data):
        responsible_person_id = validated_data.pop('responsible_person_id', None)
        if responsible_person_id:
            validated_data['responsible_person_id'] = responsible_person_id
        
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        responsible_person_id = validated_data.pop('responsible_person_id', None)
        if responsible_person_id is not None:
            validated_data['responsible_person_id'] = responsible_person_id
        
        return super().update(instance, validated_data)


class FacilityListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка объектов (краткая информация)"""
    
    facility_type = FacilityTypeSerializer(read_only=True)
    manager = UserBasicSerializer(read_only=True)
    primary_image = serializers.SerializerMethodField()
    defects_count = serializers.SerializerMethodField()
    open_defects_count = serializers.SerializerMethodField()
    critical_defects_count = serializers.SerializerMethodField()
    coordinates = serializers.SerializerMethodField()
    
    class Meta:
        model = Facility
        fields = [
            'id',
            'name',
            'facility_type',
            'address',
            'city',
            'status',
            'condition',
            'manager',
            'primary_image',
            'defects_count',
            'open_defects_count',
            'critical_defects_count',
            'coordinates',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_primary_image(self, obj):
        """Основное изображение объекта"""
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return FacilityImageSerializer(primary_image, context=self.context).data
        
        # Если нет основного, берем первое доступное
        first_image = obj.images.first()
        if first_image:
            return FacilityImageSerializer(first_image, context=self.context).data
        
        return None
    
    def get_defects_count(self, obj):
        """Общее количество дефектов"""
        return getattr(obj, 'defects_count', obj.get_defects_count())
    
    def get_open_defects_count(self, obj):
        """Количество открытых дефектов"""
        return getattr(obj, 'open_defects_count', obj.get_open_defects_count())
    
    def get_critical_defects_count(self, obj):
        """Количество критических дефектов"""
        return getattr(obj, 'critical_defects_count', obj.get_critical_defects_count())
    
    def get_coordinates(self, obj):
        """Координаты объекта"""
        return obj.coordinates


class FacilityDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор объекта недвижимости"""
    
    facility_type = FacilityTypeSerializer(read_only=True)
    facility_type_id = serializers.IntegerField(write_only=True)
    manager = UserBasicSerializer(read_only=True)
    manager_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    created_by = UserBasicSerializer(read_only=True)
    
    # Связанные объекты
    images = FacilityImageSerializer(many=True, read_only=True)
    documents = FacilityDocumentSerializer(many=True, read_only=True)
    maintenance_schedules = MaintenanceScheduleSerializer(many=True, read_only=True)
    
    # Вычисляемые поля
    defects_count = serializers.SerializerMethodField()
    open_defects_count = serializers.SerializerMethodField()
    critical_defects_count = serializers.SerializerMethodField()
    coordinates = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    needs_attention = serializers.SerializerMethodField()
    
    class Meta:
        model = Facility
        fields = [
            'id',
            'name',
            'description',
            'facility_type',
            'facility_type_id',
            'address',
            'city',
            'region',
            'postal_code',
            'latitude',
            'longitude',
            'coordinates',
            'total_area',
            'usable_area',
            'floors_count',
            'construction_year',
            'renovation_year',
            'status',
            'condition',
            'condition_notes',
            'purchase_price',
            'current_value',
            'insurance_value',
            'manager',
            'manager_id',
            'extra_data',
            'is_active',
            'needs_attention',
            'defects_count',
            'open_defects_count',
            'critical_defects_count',
            'images',
            'documents',
            'maintenance_schedules',
            'created_at',
            'updated_at',
            'created_by'
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'created_by',
            'is_active',
            'needs_attention',
            'coordinates'
        ]
    
    def get_defects_count(self, obj):
        """Общее количество дефектов"""
        return obj.get_defects_count()
    
    def get_open_defects_count(self, obj):
        """Количество открытых дефектов"""
        return obj.get_open_defects_count()
    
    def get_critical_defects_count(self, obj):
        """Количество критических дефектов"""
        return obj.get_critical_defects_count()
    
    def get_coordinates(self, obj):
        """Координаты объекта"""
        return obj.coordinates
    
    def get_is_active(self, obj):
        """Проверка активности объекта"""
        return obj.is_active
    
    def get_needs_attention(self, obj):
        """Требует внимания"""
        return obj.needs_attention
    
    def validate(self, data):
        """Валидация данных"""
        # Проверка координат
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if (latitude is not None and longitude is None) or (latitude is None and longitude is not None):
            raise serializers.ValidationError({
                'coordinates': _('Необходимо указать и широту, и долготу')
            })
        
        # Проверка площадей
        total_area = data.get('total_area')
        usable_area = data.get('usable_area')
        
        if total_area and usable_area and usable_area > total_area:
            raise serializers.ValidationError({
                'usable_area': _('Полезная площадь не может быть больше общей площади')
            })
        
        # Проверка годов
        construction_year = data.get('construction_year')
        renovation_year = data.get('renovation_year')
        
        if construction_year and renovation_year and renovation_year < construction_year:
            raise serializers.ValidationError({
                'renovation_year': _('Год реконструкции не может быть раньше года постройки')
            })
        
        return data
    
    def create(self, validated_data):
        manager_id = validated_data.pop('manager_id', None)
        if manager_id:
            validated_data['manager_id'] = manager_id
        
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        manager_id = validated_data.pop('manager_id', None)
        if manager_id is not None:
            validated_data['manager_id'] = manager_id
        
        return super().update(instance, validated_data)


class FacilityCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления объекта"""
    
    class Meta:
        model = Facility
        fields = [
            'name',
            'description',
            'facility_type',
            'project',
            'address',
            'city',
            'region',
            'postal_code',
            'latitude',
            'longitude',
            'total_area',
            'usable_area',
            'floors_count',
            'construction_year',
            'renovation_year',
            'status',
            'condition',
            'condition_notes',
            'purchase_price',
            'current_value',
            'insurance_value',
            'manager',
            'extra_data'
        ]
    
    def validate(self, data):
        """Валидация данных"""
        # Проверка координат
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if (latitude is not None and longitude is None) or (latitude is None and longitude is not None):
            raise serializers.ValidationError({
                'coordinates': _('Необходимо указать и широту, и долготу')
            })
        
        # Проверка площадей
        total_area = data.get('total_area')
        usable_area = data.get('usable_area')
        
        if total_area and usable_area and usable_area > total_area:
            raise serializers.ValidationError({
                'usable_area': _('Полезная площадь не может быть больше общей площади')
            })
        
        return data
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)