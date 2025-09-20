from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class NotificationType(models.TextChoices):
    """Типы уведомлений"""
    INFO = 'info', _('Информация')
    SUCCESS = 'success', _('Успех')
    WARNING = 'warning', _('Предупреждение')
    ERROR = 'error', _('Ошибка')
    SYSTEM = 'system', _('Системное')


class NotificationCategory(models.TextChoices):
    """Категории уведомлений"""
    PROJECT = 'project', _('Проект')
    FACILITY = 'facility', _('Объект')
    DOCUMENT = 'document', _('Документ')
    USER = 'user', _('Пользователь')
    SYSTEM = 'system', _('Система')
    SECURITY = 'security', _('Безопасность')


class NotificationPriority(models.TextChoices):
    """Приоритет уведомлений"""
    LOW = 'low', _('Низкий')
    NORMAL = 'normal', _('Обычный')
    HIGH = 'high', _('Высокий')
    URGENT = 'urgent', _('Срочный')


class Notification(models.Model):
    """Модель уведомления"""
    
    # Получатель уведомления
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('Получатель')
    )
    
    # Отправитель уведомления (может быть None для системных уведомлений)
    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_notifications',
        verbose_name=_('Отправитель')
    )
    
    # Основная информация
    title = models.CharField(
        max_length=200,
        verbose_name=_('Заголовок')
    )
    
    message = models.TextField(
        verbose_name=_('Сообщение')
    )
    
    # Классификация
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
        verbose_name=_('Тип уведомления')
    )
    
    category = models.CharField(
        max_length=20,
        choices=NotificationCategory.choices,
        default=NotificationCategory.SYSTEM,
        verbose_name=_('Категория')
    )
    
    priority = models.CharField(
        max_length=20,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL,
        verbose_name=_('Приоритет')
    )
    
    # Связь с объектом (Generic Foreign Key)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Тип объекта')
    )
    
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('ID объекта')
    )
    
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Статус и временные метки
    is_read = models.BooleanField(
        default=False,
        verbose_name=_('Прочитано')
    )
    
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Время прочтения')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Создано')
    )
    
    # Дополнительные данные в JSON формате
    extra_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Дополнительные данные')
    )
    
    # URL для перехода (опционально)
    action_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name=_('URL действия')
    )
    
    # Срок действия уведомления
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Истекает')
    )
    
    class Meta:
        verbose_name = _('Уведомление')
        verbose_name_plural = _('Уведомления')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['priority', '-created_at']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f'{self.title} -> {self.recipient.username}'
    
    def mark_as_read(self):
        """Отметить уведомление как прочитанное"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def is_expired(self):
        """Проверить, истекло ли уведомление"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def get_age_in_days(self):
        """Получить возраст уведомления в днях"""
        return (timezone.now() - self.created_at).days
    
    def clean(self):
        """Валидация модели"""
        super().clean()
        
        # Проверяем, что expires_at больше created_at
        if self.expires_at and self.created_at and self.expires_at <= self.created_at:
            raise ValidationError({
                'expires_at': _('Срок действия должен быть больше времени создания')
            })


class NotificationTemplate(models.Model):
    """Шаблон уведомления для автоматической генерации"""
    
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Код шаблона'),
        help_text=_('Уникальный код для программного доступа')
    )
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Название шаблона')
    )
    
    title_template = models.CharField(
        max_length=200,
        verbose_name=_('Шаблон заголовка'),
        help_text=_('Используйте {переменная} для подстановки значений')
    )
    
    message_template = models.TextField(
        verbose_name=_('Шаблон сообщения'),
        help_text=_('Используйте {переменная} для подстановки значений')
    )
    
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
        verbose_name=_('Тип уведомления')
    )
    
    category = models.CharField(
        max_length=20,
        choices=NotificationCategory.choices,
        verbose_name=_('Категория')
    )
    
    priority = models.CharField(
        max_length=20,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL,
        verbose_name=_('Приоритет')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('Описание'),
        help_text=_('Описание назначения шаблона')
    )
    
    email_subject_template = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Шаблон темы email'),
        help_text=_('Используйте {{ переменная }} для подстановки значений')
    )
    
    email_body_template = models.TextField(
        blank=True,
        verbose_name=_('Шаблон тела email'),
        help_text=_('Используйте {{ переменная }} для подстановки значений')
    )
    
    required_context_vars = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Обязательные переменные контекста'),
        help_text=_('Список переменных, которые должны быть переданы в контексте')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активен')
    )
    
    # Срок действия по умолчанию (в днях)
    default_expires_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Срок действия (дни)'),
        help_text=_('Количество дней, после которых уведомление истекает')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Создан')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Обновлен')
    )
    
    class Meta:
        verbose_name = _('Шаблон уведомления')
        verbose_name_plural = _('Шаблоны уведомлений')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def create_notification(self, recipient, context=None, sender=None, content_object=None):
        """Создать уведомление на основе шаблона"""
        if not self.is_active:
            return None
        
        context = context or {}
        
        # Форматируем заголовок и сообщение
        try:
            title = self.title_template.format(**context)
            message = self.message_template.format(**context)
        except KeyError as e:
            raise ValueError(f'Отсутствует переменная в контексте: {e}')
        
        # Вычисляем срок действия
        expires_at = None
        if self.default_expires_days:
            expires_at = timezone.now() + timezone.timedelta(days=self.default_expires_days)
        
        # Создаем уведомление
        notification = Notification.objects.create(
            recipient=recipient,
            sender=sender,
            title=title,
            message=message,
            notification_type=self.notification_type,
            category=self.category,
            priority=self.priority,
            content_object=content_object,
            expires_at=expires_at,
            extra_data=context
        )
        
        return notification


class NotificationSettings(models.Model):
    """Настройки уведомлений пользователя"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_settings',
        verbose_name=_('Пользователь')
    )
    
    # Общие настройки
    email_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Email уведомления')
    )
    
    push_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Push уведомления')
    )
    
    # Настройки по категориям
    project_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Уведомления о проектах')
    )
    
    facility_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Уведомления об объектах')
    )
    
    document_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Уведомления о документах')
    )
    
    security_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Уведомления безопасности')
    )
    
    # Настройки по приоритету
    low_priority_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Низкий приоритет')
    )
    
    normal_priority_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Обычный приоритет')
    )
    
    high_priority_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Высокий приоритет')
    )
    
    urgent_priority_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Срочные уведомления')
    )
    
    # Время тишины (не отправлять уведомления)
    quiet_hours_start = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_('Начало тихих часов')
    )
    
    quiet_hours_end = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_('Конец тихих часов')
    )
    
    # Автоматическое удаление прочитанных уведомлений
    auto_delete_read_after_days = models.PositiveIntegerField(
        default=30,
        verbose_name=_('Удалять прочитанные через (дней)')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Создано')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Обновлено')
    )
    
    class Meta:
        verbose_name = _('Настройки уведомлений')
        verbose_name_plural = _('Настройки уведомлений')
    
    def __str__(self):
        return f'Настройки уведомлений: {self.user.username}'
    
    def should_receive_notification(self, notification):
        """Проверить, должен ли пользователь получить уведомление"""
        # Проверяем общие настройки
        if not self.email_notifications and not self.push_notifications:
            return False
        
        # Проверяем настройки по категориям
        category_settings = {
            NotificationCategory.PROJECT: self.project_notifications,
            NotificationCategory.FACILITY: self.facility_notifications,
            NotificationCategory.DOCUMENT: self.document_notifications,
            NotificationCategory.SECURITY: self.security_notifications,
        }
        
        if notification.category in category_settings:
            if not category_settings[notification.category]:
                return False
        
        # Проверяем настройки по приоритету
        priority_settings = {
            NotificationPriority.LOW: self.low_priority_notifications,
            NotificationPriority.NORMAL: self.normal_priority_notifications,
            NotificationPriority.HIGH: self.high_priority_notifications,
            NotificationPriority.URGENT: self.urgent_priority_notifications,
        }
        
        if notification.priority in priority_settings:
            if not priority_settings[notification.priority]:
                return False
        
        # Проверяем тихие часы
        if self.quiet_hours_start and self.quiet_hours_end:
            current_time = timezone.now().time()
            if self.quiet_hours_start <= current_time <= self.quiet_hours_end:
                # Срочные уведомления отправляем даже в тихие часы
                if notification.priority != NotificationPriority.URGENT:
                    return False
        
        return True


class NotificationBatch(models.Model):
    """Пакетная отправка уведомлений"""
    
    name = models.CharField(
        max_length=200,
        default='Пакет уведомлений',
        verbose_name=_('Название пакета')
    )
    
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.CASCADE,
        verbose_name=_('Шаблон')
    )
    
    recipients = models.ManyToManyField(
        User,
        verbose_name=_('Получатели')
    )
    
    context_data = models.JSONField(
        default=dict,
        verbose_name=_('Данные контекста')
    )
    
    # Статус отправки
    is_sent = models.BooleanField(
        default=False,
        verbose_name=_('Отправлено')
    )
    
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Время отправки')
    )
    
    # Статистика
    total_recipients = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Всего получателей')
    )
    
    successful_sends = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Успешных отправок')
    )
    
    failed_sends = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Неудачных отправок')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Создан')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_notification_batches',
        verbose_name=_('Создал')
    )
    
    class Meta:
        verbose_name = _('Пакет уведомлений')
        verbose_name_plural = _('Пакеты уведомлений')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def send_notifications(self):
        """Отправить уведомления всем получателям"""
        if self.is_sent:
            return False
        
        successful = 0
        failed = 0
        
        for recipient in self.recipients.all():
            try:
                notification = self.template.create_notification(
                    recipient=recipient,
                    context=self.context_data,
                    sender=self.created_by
                )
                if notification:
                    successful += 1
                else:
                    failed += 1
            except Exception:
                failed += 1
        
        # Обновляем статистику
        self.total_recipients = self.recipients.count()
        self.successful_sends = successful
        self.failed_sends = failed
        self.is_sent = True
        self.sent_at = timezone.now()
        self.save()
        
        return True