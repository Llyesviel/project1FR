from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from decimal import Decimal

User = get_user_model()


class FacilityType(models.Model):
    """Тип объекта недвижимости"""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Название')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Описание')
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text=_('CSS класс иконки'),
        verbose_name=_('Иконка')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активен')
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
        verbose_name = _('Тип объекта')
        verbose_name_plural = _('Типы объектов')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Facility(models.Model):
    """Объект недвижимости"""
    
    STATUS_CHOICES = [
        ('active', _('Активный')),
        ('inactive', _('Неактивный')),
        ('maintenance', _('На обслуживании')),
        ('renovation', _('На реконструкции')),
        ('demolished', _('Снесен')),
    ]
    
    CONDITION_CHOICES = [
        ('excellent', _('Отличное')),
        ('good', _('Хорошее')),
        ('satisfactory', _('Удовлетворительное')),
        ('poor', _('Плохое')),
        ('critical', _('Критическое')),
    ]
    
    # Основная информация
    name = models.CharField(
        max_length=200,
        verbose_name=_('Название')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Описание')
    )
    facility_type = models.ForeignKey(
        FacilityType,
        on_delete=models.PROTECT,
        related_name='facilities',
        verbose_name=_('Тип объекта')
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='facilities',
        verbose_name=_('Проект')
    )
    
    # Адрес и местоположение
    address = models.TextField(
        verbose_name=_('Адрес')
    )
    city = models.CharField(
        max_length=100,
        verbose_name=_('Город')
    )
    region = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Регион')
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Почтовый индекс')
    )
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal('-90.0')),
            MaxValueValidator(Decimal('90.0'))
        ],
        verbose_name=_('Широта')
    )
    longitude = models.DecimalField(
        max_digits=11,
        decimal_places=8,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal('-180.0')),
            MaxValueValidator(Decimal('180.0'))
        ],
        verbose_name=_('Долгота')
    )
    
    # Технические характеристики
    total_area = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('Общая площадь (м²)')
    )
    usable_area = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('Полезная площадь (м²)')
    )
    floors_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Количество этажей')
    )
    construction_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1800),
            MaxValueValidator(2100)
        ],
        verbose_name=_('Год постройки')
    )
    renovation_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1800),
            MaxValueValidator(2100)
        ],
        verbose_name=_('Год последней реконструкции')
    )
    
    # Статус и состояние
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name=_('Статус')
    )
    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        default='good',
        verbose_name=_('Состояние')
    )
    condition_notes = models.TextField(
        blank=True,
        verbose_name=_('Примечания к состоянию')
    )
    
    # Финансовая информация
    purchase_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('Стоимость покупки')
    )
    current_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('Текущая стоимость')
    )
    insurance_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('Страховая стоимость')
    )
    
    # Ответственные лица
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_facilities',
        verbose_name=_('Управляющий')
    )
    
    # Дополнительные данные
    extra_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Дополнительные данные')
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
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_facilities',
        verbose_name=_('Создал')
    )
    
    class Meta:
        verbose_name = _('Объект недвижимости')
        verbose_name_plural = _('Объекты недвижимости')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['facility_type', 'condition']),
            models.Index(fields=['city', 'region']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.address})"
    
    def get_absolute_url(self):
        return reverse('facility-detail', kwargs={'pk': self.pk})
    
    @property
    def is_active(self):
        """Проверка активности объекта"""
        return self.status == 'active'
    
    @property
    def needs_attention(self):
        """Требует внимания (плохое или критическое состояние)"""
        return self.condition in ['poor', 'critical']
    
    @property
    def coordinates(self):
        """Координаты объекта"""
        if self.latitude and self.longitude:
            return {
                'lat': float(self.latitude),
                'lng': float(self.longitude)
            }
        return None
    
    def get_defects_count(self):
        """Количество дефектов объекта"""
        return self.defects.count()
    
    def get_open_defects_count(self):
        """Количество открытых дефектов"""
        return self.defects.filter(status__in=['new', 'in_progress']).count()
    
    def get_critical_defects_count(self):
        """Количество критических дефектов"""
        return self.defects.filter(severity='critical').count()


class FacilityDocument(models.Model):
    """Документы объекта недвижимости"""
    
    DOCUMENT_TYPES = [
        ('technical_passport', _('Технический паспорт')),
        ('ownership_certificate', _('Свидетельство о собственности')),
        ('construction_permit', _('Разрешение на строительство')),
        ('commissioning_act', _('Акт ввода в эксплуатацию')),
        ('floor_plan', _('Поэтажный план')),
        ('technical_plan', _('Технический план')),
        ('inspection_report', _('Отчет об обследовании')),
        ('insurance_policy', _('Страховой полис')),
        ('maintenance_contract', _('Договор обслуживания')),
        ('other', _('Другое')),
    ]
    
    facility = models.ForeignKey(
        Facility,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name=_('Объект')
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_('Название документа')
    )
    document_type = models.CharField(
        max_length=30,
        choices=DOCUMENT_TYPES,
        verbose_name=_('Тип документа')
    )
    file = models.FileField(
        upload_to='facilities/documents/%Y/%m/',
        verbose_name=_('Файл')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Описание')
    )
    document_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Дата документа')
    )
    expiry_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Дата истечения')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активен')
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Загружен')
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_facility_documents',
        verbose_name=_('Загрузил')
    )
    
    class Meta:
        verbose_name = _('Документ объекта')
        verbose_name_plural = _('Документы объектов')
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['facility', 'document_type']),
            models.Index(fields=['expiry_date']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.facility.name})"
    
    @property
    def is_expired(self):
        """Проверка истечения срока действия документа"""
        if self.expiry_date:
            from django.utils import timezone
            return timezone.now().date() > self.expiry_date
        return False
    
    @property
    def file_size(self):
        """Размер файла в байтах"""
        try:
            return self.file.size
        except (ValueError, OSError):
            return 0
    
    @property
    def file_extension(self):
        """Расширение файла"""
        import os
        return os.path.splitext(self.file.name)[1].lower()


class FacilityImage(models.Model):
    """Изображения объекта недвижимости"""
    
    IMAGE_TYPES = [
        ('exterior', _('Внешний вид')),
        ('interior', _('Интерьер')),
        ('floor_plan', _('План этажа')),
        ('technical', _('Техническое фото')),
        ('defect', _('Фото дефекта')),
        ('progress', _('Ход работ')),
        ('other', _('Другое')),
    ]
    
    facility = models.ForeignKey(
        Facility,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('Объект')
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Заголовок')
    )
    image = models.ImageField(
        upload_to='facilities/images/%Y/%m/',
        verbose_name=_('Изображение')
    )
    image_type = models.CharField(
        max_length=20,
        choices=IMAGE_TYPES,
        default='other',
        verbose_name=_('Тип изображения')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Описание')
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name=_('Основное изображение')
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Порядок')
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Загружено')
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_facility_images',
        verbose_name=_('Загрузил')
    )
    
    class Meta:
        verbose_name = _('Изображение объекта')
        verbose_name_plural = _('Изображения объектов')
        ordering = ['order', '-uploaded_at']
        indexes = [
            models.Index(fields=['facility', 'image_type']),
            models.Index(fields=['is_primary']),
        ]
    
    def __str__(self):
        return f"{self.title or 'Изображение'} ({self.facility.name})"
    
    def save(self, *args, **kwargs):
        # Если это основное изображение, убираем флаг у других
        if self.is_primary:
            FacilityImage.objects.filter(
                facility=self.facility,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class MaintenanceSchedule(models.Model):
    """График обслуживания объекта"""
    
    FREQUENCY_CHOICES = [
        ('daily', _('Ежедневно')),
        ('weekly', _('Еженедельно')),
        ('monthly', _('Ежемесячно')),
        ('quarterly', _('Ежеквартально')),
        ('semi_annually', _('Раз в полгода')),
        ('annually', _('Ежегодно')),
        ('custom', _('Пользовательский')),
    ]
    
    STATUS_CHOICES = [
        ('active', _('Активен')),
        ('paused', _('Приостановлен')),
        ('completed', _('Завершен')),
        ('cancelled', _('Отменен')),
    ]
    
    facility = models.ForeignKey(
        Facility,
        on_delete=models.CASCADE,
        related_name='maintenance_schedules',
        verbose_name=_('Объект')
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_('Название')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Описание')
    )
    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        verbose_name=_('Периодичность')
    )
    custom_frequency_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Пользовательская периодичность (дни)')
    )
    start_date = models.DateField(
        verbose_name=_('Дата начала')
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Дата окончания')
    )
    next_maintenance_date = models.DateField(
        verbose_name=_('Следующее обслуживание')
    )
    responsible_person = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenance_schedules',
        verbose_name=_('Ответственный')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name=_('Статус')
    )
    estimated_duration_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.1'))],
        verbose_name=_('Ожидаемая продолжительность (часы)')
    )
    estimated_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('Ожидаемая стоимость')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Примечания')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Создан')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Обновлен')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_maintenance_schedules',
        verbose_name=_('Создал')
    )
    
    class Meta:
        verbose_name = _('График обслуживания')
        verbose_name_plural = _('Графики обслуживания')
        ordering = ['next_maintenance_date']
        indexes = [
            models.Index(fields=['facility', 'status']),
            models.Index(fields=['next_maintenance_date']),
            models.Index(fields=['responsible_person']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.facility.name})"
    
    @property
    def is_overdue(self):
        """Проверка просрочки обслуживания"""
        from django.utils import timezone
        return timezone.now().date() > self.next_maintenance_date
    
    def calculate_next_maintenance_date(self):
        """Расчет следующей даты обслуживания"""
        from datetime import timedelta
        
        if self.frequency == 'daily':
            return self.next_maintenance_date + timedelta(days=1)
        elif self.frequency == 'weekly':
            return self.next_maintenance_date + timedelta(weeks=1)
        elif self.frequency == 'monthly':
            return self.next_maintenance_date + timedelta(days=30)
        elif self.frequency == 'quarterly':
            return self.next_maintenance_date + timedelta(days=90)
        elif self.frequency == 'semi_annually':
            return self.next_maintenance_date + timedelta(days=180)
        elif self.frequency == 'annually':
            return self.next_maintenance_date + timedelta(days=365)
        elif self.frequency == 'custom' and self.custom_frequency_days:
            return self.next_maintenance_date + timedelta(days=self.custom_frequency_days)
        
        return self.next_maintenance_date