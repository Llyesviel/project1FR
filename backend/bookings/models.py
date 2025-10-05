from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from facilities.models import Facility

User = get_user_model()


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('approved', 'Подтверждено'),
        ('rejected', 'Отклонено'),
        ('cancelled', 'Отменено'),
    ]

    facility = models.ForeignKey(
        'projects.Facility',
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='Объект'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='Пользователь'
    )
    start_time = models.DateTimeField(verbose_name='Время начала')
    end_time = models.DateTimeField(verbose_name='Время окончания')
    purpose = models.TextField(verbose_name='Цель бронирования')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    
    # Поля для одобрения/отклонения
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_bookings',
        verbose_name='Одобрено пользователем'
    )
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='Время одобрения')
    rejection_reason = models.TextField(blank=True, verbose_name='Причина отклонения')

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.facility.name} - {self.user.username} ({self.start_time.strftime("%d.%m.%Y %H:%M")})'

    def clean(self):
        """Валидация модели"""
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError('Время окончания должно быть позже времени начала')
            
            if self.start_time < timezone.now():
                raise ValidationError('Нельзя создать бронирование на прошедшее время')

        # Проверка на пересечение бронирований
        if self.facility_id:
            overlapping_bookings = Booking.objects.filter(
                facility=self.facility,
                status__in=['pending', 'approved'],
                start_time__lt=self.end_time,
                end_time__gt=self.start_time
            )
            
            if self.pk:
                overlapping_bookings = overlapping_bookings.exclude(pk=self.pk)
            
            if overlapping_bookings.exists():
                raise ValidationError('На это время уже есть бронирование для данного объекта')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def duration(self):
        """Продолжительность бронирования"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

    @property
    def is_active(self):
        """Активно ли бронирование сейчас"""
        now = timezone.now()
        return (
            self.status == 'approved' and
            self.start_time <= now <= self.end_time
        )

    @property
    def is_upcoming(self):
        """Предстоящее ли бронирование"""
        return (
            self.status == 'approved' and
            self.start_time > timezone.now()
        )

    def approve(self, approved_by_user):
        """Одобрить бронирование"""
        self.status = 'approved'
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.save()

    def reject(self, reason=''):
        """Отклонить бронирование"""
        self.status = 'rejected'
        self.rejection_reason = reason
        self.save()

    def cancel(self):
        """Отменить бронирование"""
        self.status = 'cancelled'
        self.save()
