from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Defect(models.Model):
    """Модель дефекта"""
    
    class Status(models.TextChoices):
        NEW = 'new', _('Новый')
        IN_PROGRESS = 'in_progress', _('В работе')
        TESTING = 'testing', _('На проверке')
        RESOLVED = 'resolved', _('Решен')
        CLOSED = 'closed', _('Закрыт')
        REJECTED = 'rejected', _('Отклонен')
    
    class Severity(models.TextChoices):
        LOW = 'low', _('Низкая')
        MEDIUM = 'medium', _('Средняя')
        HIGH = 'high', _('Высокая')
        CRITICAL = 'critical', _('Критическая')
    
    class Priority(models.TextChoices):
        LOW = 'low', _('Низкий')
        MEDIUM = 'medium', _('Средний')
        HIGH = 'high', _('Высокий')
        URGENT = 'urgent', _('Срочный')
    
    # Основная информация
    title = models.CharField(
        max_length=200,
        verbose_name=_('Заголовок')
    )
    description = models.TextField(
        verbose_name=_('Описание')
    )
    
    # Связи
    facility = models.ForeignKey(
        'facilities.Facility',
        on_delete=models.CASCADE,
        related_name='defects',
        verbose_name=_('Объект')
    )
    
    # Статусы и приоритеты
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        verbose_name=_('Статус')
    )
    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.MEDIUM,
        verbose_name=_('Серьезность')
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        verbose_name=_('Приоритет')
    )
    
    # Пользователи
    reported_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='reported_defects',
        verbose_name=_('Сообщил')
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_defects',
        verbose_name=_('Назначен')
    )
    
    # Временные метки
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Создан')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Обновлен')
    )
    due_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Срок выполнения')
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Решен')
    )
    
    # Дополнительные поля
    location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Местоположение')
    )
    estimated_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Оценочная стоимость')
    )
    actual_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Фактическая стоимость')
    )
    
    class Meta:
        verbose_name = _('Дефект')
        verbose_name_plural = _('Дефекты')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['facility', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['severity', 'priority']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    @property
    def is_overdue(self):
        """Проверяет, просрочен ли дефект"""
        if self.due_date and self.status not in [self.Status.RESOLVED, self.Status.CLOSED]:
            from django.utils import timezone
            return timezone.now() > self.due_date
        return False