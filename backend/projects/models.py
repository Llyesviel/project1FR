from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()


class Project(models.Model):
    """Модель проекта"""
    
    class Status(models.TextChoices):
        PLANNING = 'planning', 'Планирование'
        ACTIVE = 'active', 'Активный'
        ON_HOLD = 'on_hold', 'Приостановлен'
        COMPLETED = 'completed', 'Завершен'
        CANCELLED = 'cancelled', 'Отменен'
    
    class Priority(models.TextChoices):
        LOW = 'low', 'Низкий'
        MEDIUM = 'medium', 'Средний'
        HIGH = 'high', 'Высокий'
        CRITICAL = 'critical', 'Критический'
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    name = models.CharField(
        'Название проекта',
        max_length=200,
        help_text='Название проекта'
    )
    
    description = models.TextField(
        'Описание',
        blank=True,
        help_text='Подробное описание проекта'
    )
    
    code = models.CharField(
        'Код проекта',
        max_length=20,
        unique=True,
        help_text='Уникальный код проекта'
    )
    
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNING,
        help_text='Текущий статус проекта'
    )
    
    priority = models.CharField(
        'Приоритет',
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        help_text='Приоритет проекта'
    )
    
    manager = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='managed_projects',
        verbose_name='Менеджер проекта',
        help_text='Ответственный менеджер проекта'
    )
    
    team_members = models.ManyToManyField(
        User,
        through='ProjectMembership',
        related_name='projects',
        verbose_name='Участники команды',
        blank=True
    )
    
    client = models.CharField(
        'Клиент',
        max_length=200,
        blank=True,
        help_text='Название клиента или заказчика'
    )
    
    budget = models.DecimalField(
        'Бюджет',
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0'))],
        help_text='Бюджет проекта в рублях'
    )
    
    start_date = models.DateField(
        'Дата начала',
        blank=True,
        null=True,
        help_text='Планируемая дата начала проекта'
    )
    
    end_date = models.DateField(
        'Дата окончания',
        blank=True,
        null=True,
        help_text='Планируемая дата окончания проекта'
    )
    
    actual_start_date = models.DateField(
        'Фактическая дата начала',
        blank=True,
        null=True,
        help_text='Фактическая дата начала работ'
    )
    
    actual_end_date = models.DateField(
        'Фактическая дата окончания',
        blank=True,
        null=True,
        help_text='Фактическая дата завершения проекта'
    )
    
    progress = models.PositiveIntegerField(
        'Прогресс (%)',
        default=0,
        validators=[MaxValueValidator(100)],
        help_text='Процент выполнения проекта'
    )
    
    location = models.CharField(
        'Местоположение',
        max_length=200,
        blank=True,
        help_text='Адрес или местоположение проекта'
    )
    
    coordinates_lat = models.DecimalField(
        'Широта',
        max_digits=10,
        decimal_places=8,
        blank=True,
        null=True,
        help_text='Географическая широта'
    )
    
    coordinates_lng = models.DecimalField(
        'Долгота',
        max_digits=11,
        decimal_places=8,
        blank=True,
        null=True,
        help_text='Географическая долгота'
    )
    
    is_active = models.BooleanField(
        'Активный',
        default=True,
        help_text='Активен ли проект'
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_projects',
        verbose_name='Создан пользователем'
    )
    
    created_at = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        'Дата обновления',
        auto_now=True
    )
    
    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['manager']),
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def is_overdue(self):
        """Проверяет, просрочен ли проект"""
        if self.end_date and self.status not in [self.Status.COMPLETED, self.Status.CANCELLED]:
            return timezone.now().date() > self.end_date
        return False
    
    @property
    def duration_planned(self):
        """Планируемая продолжительность проекта в днях"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return None
    
    @property
    def duration_actual(self):
        """Фактическая продолжительность проекта в днях"""
        if self.actual_start_date:
            end_date = self.actual_end_date or timezone.now().date()
            return (end_date - self.actual_start_date).days
        return None
    
    def get_team_count(self):
        """Возвращает количество участников команды"""
        return self.team_members.count()
    
    def get_facilities_count(self):
        """Возвращает количество объектов в проекте"""
        return self.facilities.count()
    
    def get_defects_count(self):
        """Возвращает количество дефектов в проекте"""
        return sum(facility.defects.count() for facility in self.facilities.all())


class ProjectMembership(models.Model):
    """Модель участия в проекте"""
    
    class Role(models.TextChoices):
        MANAGER = 'manager', 'Менеджер'
        ARCHITECT = 'architect', 'Архитектор'
        ENGINEER = 'engineer', 'Инженер'
        SUPERVISOR = 'supervisor', 'Супервайзер'
        WORKER = 'worker', 'Рабочий'
        INSPECTOR = 'inspector', 'Инспектор'
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        verbose_name='Проект'
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    
    role = models.CharField(
        'Роль в проекте',
        max_length=20,
        choices=Role.choices,
        default=Role.WORKER,
        help_text='Роль участника в проекте'
    )
    
    joined_at = models.DateTimeField(
        'Дата присоединения',
        auto_now_add=True
    )
    
    left_at = models.DateTimeField(
        'Дата выхода',
        blank=True,
        null=True
    )
    
    is_active = models.BooleanField(
        'Активный участник',
        default=True
    )
    
    class Meta:
        verbose_name = 'Участие в проекте'
        verbose_name_plural = 'Участие в проектах'
        unique_together = ['project', 'user']
        indexes = [
            models.Index(fields=['project', 'is_active']),
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.project.name} ({self.get_role_display()})"


class Facility(models.Model):
    """Модель объекта (здания, сооружения)"""
    
    class Type(models.TextChoices):
        BUILDING = 'building', 'Здание'
        STRUCTURE = 'structure', 'Сооружение'
        INFRASTRUCTURE = 'infrastructure', 'Инфраструктура'
        EQUIPMENT = 'equipment', 'Оборудование'
        LANDSCAPE = 'landscape', 'Благоустройство'
    
    class Status(models.TextChoices):
        PLANNING = 'planning', 'Планирование'
        CONSTRUCTION = 'construction', 'Строительство'
        TESTING = 'testing', 'Тестирование'
        COMPLETED = 'completed', 'Завершен'
        MAINTENANCE = 'maintenance', 'Обслуживание'
        DECOMMISSIONED = 'decommissioned', 'Выведен из эксплуатации'
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='project_facilities',
        verbose_name='Проект',
        help_text='Проект, к которому относится объект'
    )
    
    name = models.CharField(
        'Название объекта',
        max_length=200,
        help_text='Название объекта'
    )
    
    description = models.TextField(
        'Описание',
        blank=True,
        help_text='Подробное описание объекта'
    )
    
    code = models.CharField(
        'Код объекта',
        max_length=50,
        help_text='Уникальный код объекта в рамках проекта'
    )
    
    type = models.CharField(
        'Тип объекта',
        max_length=20,
        choices=Type.choices,
        default=Type.BUILDING,
        help_text='Тип объекта'
    )
    
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNING,
        help_text='Текущий статус объекта'
    )
    
    floor_count = models.PositiveIntegerField(
        'Количество этажей',
        blank=True,
        null=True,
        help_text='Количество этажей (для зданий)'
    )
    
    area = models.DecimalField(
        'Площадь (м²)',
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0'))],
        help_text='Общая площадь объекта в квадратных метрах'
    )
    
    volume = models.DecimalField(
        'Объем (м³)',
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0'))],
        help_text='Объем объекта в кубических метрах'
    )
    
    location = models.CharField(
        'Местоположение',
        max_length=200,
        blank=True,
        help_text='Конкретное местоположение объекта'
    )
    
    coordinates_lat = models.DecimalField(
        'Широта',
        max_digits=10,
        decimal_places=8,
        blank=True,
        null=True,
        help_text='Географическая широта'
    )
    
    coordinates_lng = models.DecimalField(
        'Долгота',
        max_digits=11,
        decimal_places=8,
        blank=True,
        null=True,
        help_text='Географическая долгота'
    )
    
    responsible_person = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='responsible_facilities',
        verbose_name='Ответственный',
        blank=True,
        null=True,
        help_text='Ответственный за объект'
    )
    
    construction_start = models.DateField(
        'Начало строительства',
        blank=True,
        null=True,
        help_text='Дата начала строительства'
    )
    
    construction_end = models.DateField(
        'Окончание строительства',
        blank=True,
        null=True,
        help_text='Планируемая дата окончания строительства'
    )
    
    actual_completion = models.DateField(
        'Фактическое завершение',
        blank=True,
        null=True,
        help_text='Фактическая дата завершения строительства'
    )
    
    progress = models.PositiveIntegerField(
        'Прогресс (%)',
        default=0,
        validators=[MaxValueValidator(100)],
        help_text='Процент готовности объекта'
    )
    
    is_active = models.BooleanField(
        'Активный',
        default=True,
        help_text='Активен ли объект'
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_project_facilities',
        verbose_name='Создан пользователем'
    )
    
    created_at = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        'Дата обновления',
        auto_now=True
    )
    
    class Meta:
        verbose_name = 'Объект'
        verbose_name_plural = 'Объекты'
        ordering = ['project', 'code']
        unique_together = ['project', 'code']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['type']),
            models.Index(fields=['responsible_person']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.project.code}-{self.code}: {self.name}"
    
    @property
    def is_overdue(self):
        """Проверяет, просрочен ли объект"""
        if self.construction_end and self.status not in [self.Status.COMPLETED, self.Status.DECOMMISSIONED]:
            return timezone.now().date() > self.construction_end
        return False
    
    @property
    def construction_duration_planned(self):
        """Планируемая продолжительность строительства в днях"""
        if self.construction_start and self.construction_end:
            return (self.construction_end - self.construction_start).days
        return None
    
    @property
    def construction_duration_actual(self):
        """Фактическая продолжительность строительства в днях"""
        if self.construction_start:
            end_date = self.actual_completion or timezone.now().date()
            return (end_date - self.construction_start).days
        return None
    
    def get_defects_count(self):
        """Возвращает количество дефектов объекта"""
        return self.defects.count()
    
    def get_open_defects_count(self):
        """Возвращает количество открытых дефектов"""
        return self.defects.filter(status__in=['new', 'in_progress', 'testing']).count()


class FacilityDocument(models.Model):
    """Модель документов объекта"""
    
    class Type(models.TextChoices):
        BLUEPRINT = 'blueprint', 'Чертеж'
        SPECIFICATION = 'specification', 'Спецификация'
        CERTIFICATE = 'certificate', 'Сертификат'
        REPORT = 'report', 'Отчет'
        PHOTO = 'photo', 'Фотография'
        OTHER = 'other', 'Другое'
    
    facility = models.ForeignKey(
        Facility,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='Объект'
    )
    
    name = models.CharField(
        'Название документа',
        max_length=200,
        help_text='Название документа'
    )
    
    description = models.TextField(
        'Описание',
        blank=True,
        help_text='Описание документа'
    )
    
    type = models.CharField(
        'Тип документа',
        max_length=20,
        choices=Type.choices,
        default=Type.OTHER,
        help_text='Тип документа'
    )
    
    file = models.FileField(
        'Файл',
        upload_to='facility_documents/',
        help_text='Файл документа'
    )
    
    version = models.CharField(
        'Версия',
        max_length=20,
        default='1.0',
        help_text='Версия документа'
    )
    
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='uploaded_project_facility_documents',
        verbose_name='Загружен пользователем'
    )
    
    uploaded_at = models.DateTimeField(
        'Дата загрузки',
        auto_now_add=True
    )
    
    is_active = models.BooleanField(
        'Активный',
        default=True,
        help_text='Активен ли документ'
    )
    
    class Meta:
        verbose_name = 'Документ объекта'
        verbose_name_plural = 'Документы объектов'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['facility', 'type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.facility.name} - {self.name}"
    
    def get_file_size(self):
        """Возвращает размер файла в байтах"""
        if self.file:
            return self.file.size
        return 0
    
    def get_file_extension(self):
        """Возвращает расширение файла"""
        if self.file:
            return self.file.name.split('.')[-1].lower()
        return ''


class Task(models.Model):
    """Модель задачи"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает'
        IN_PROGRESS = 'in_progress', 'В работе'
        COMPLETED = 'completed', 'Завершена'
        OVERDUE = 'overdue', 'Просрочена'
        CANCELLED = 'cancelled', 'Отменена'
    
    class Priority(models.TextChoices):
        LOW = 'low', 'Низкий'
        MEDIUM = 'medium', 'Средний'
        HIGH = 'high', 'Высокий'
        URGENT = 'urgent', 'Срочный'
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    title = models.CharField(
        'Заголовок',
        max_length=200,
        help_text='Название задачи'
    )
    
    description = models.TextField(
        'Описание',
        blank=True,
        help_text='Подробное описание задачи'
    )
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Проект',
        help_text='Проект, к которому относится задача'
    )
    
    facility = models.ForeignKey(
        'Facility',
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Объект',
        blank=True,
        null=True,
        help_text='Объект, к которому относится задача'
    )
    
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text='Текущий статус задачи'
    )
    
    priority = models.CharField(
        'Приоритет',
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        help_text='Приоритет задачи'
    )
    
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        verbose_name='Назначена'
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_tasks',
        verbose_name='Создана пользователем'
    )
    
    due_date = models.DateTimeField(
        'Срок выполнения',
        blank=True,
        null=True,
        help_text='Крайний срок выполнения задачи'
    )
    
    completed_at = models.DateTimeField(
        'Дата завершения',
        blank=True,
        null=True,
        help_text='Дата фактического завершения задачи'
    )
    
    estimated_hours = models.PositiveIntegerField(
        'Оценочное время (часы)',
        blank=True,
        null=True,
        help_text='Оценочное время выполнения в часах'
    )
    
    actual_hours = models.PositiveIntegerField(
        'Фактическое время (часы)',
        blank=True,
        null=True,
        help_text='Фактическое время выполнения в часах'
    )
    
    created_at = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        'Дата обновления',
        auto_now=True
    )
    
    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['project']),
            models.Index(fields=['facility']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    @property
    def is_overdue(self):
        """Проверяет, просрочена ли задача"""
        if self.due_date and self.status not in [self.Status.COMPLETED, self.Status.CANCELLED]:
            return timezone.now() > self.due_date
        return False
    
    @property
    def progress_percentage(self):
        """Возвращает процент выполнения на основе статуса"""
        status_progress = {
            self.Status.PENDING: 0,
            self.Status.IN_PROGRESS: 50,
            self.Status.COMPLETED: 100,
            self.Status.OVERDUE: 25,
            self.Status.CANCELLED: 0,
        }
        return status_progress.get(self.status, 0)