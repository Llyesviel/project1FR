from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from PIL import Image
import os


class User(AbstractUser):
    """Расширенная модель пользователя"""
    
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Администратор'
        MANAGER = 'MANAGER', 'Менеджер'
        ENGINEER = 'ENGINEER', 'Инженер'
        EXECUTIVE = 'EXECUTIVE', 'Руководитель'
        CUSTOMER = 'CUSTOMER', 'Заказчик'
    
    email = models.EmailField(
        'Email адрес',
        unique=True,
        help_text='Обязательное поле. Введите действующий email адрес.'
    )
    
    role = models.CharField(
        'Роль',
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        help_text='Роль пользователя в системе'
    )
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Номер телефона должен быть в формате: '+999999999'. До 15 цифр."
    )
    
    phone = models.CharField(
        'Телефон',
        validators=[phone_regex],
        max_length=17,
        blank=True,
        help_text='Контактный номер телефона'
    )
    
    avatar = models.ImageField(
        'Аватар',
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text='Фотография профиля пользователя'
    )
    
    position = models.CharField(
        'Должность',
        max_length=100,
        blank=True,
        help_text='Должность в организации'
    )
    
    department = models.CharField(
        'Отдел',
        max_length=100,
        blank=True,
        help_text='Отдел или подразделение'
    )
    
    is_active = models.BooleanField(
        'Активный',
        default=True,
        help_text='Отметьте, если пользователь должен считаться активным. '
                  'Уберите эту отметку вместо удаления учетной записи.'
    )
    
    created_at = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        'Дата обновления',
        auto_now=True
    )
    
    last_activity = models.DateTimeField(
        'Последняя активность',
        blank=True,
        null=True,
        help_text='Время последней активности пользователя'
    )
    
    # Настройки уведомлений
    email_notifications = models.BooleanField(
        'Email уведомления',
        default=True,
        help_text='Получать уведомления по email'
    )
    
    push_notifications = models.BooleanField(
        'Push уведомления',
        default=True,
        help_text='Получать push уведомления'
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        """Возвращает полное имя пользователя"""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.username
    
    def get_short_name(self):
        """Возвращает краткое имя пользователя"""
        return self.first_name or self.username
    
    def save(self, *args, **kwargs):
        """Переопределенный метод сохранения"""
        # Обработка аватара
        if self.avatar:
            # Ограничиваем размер изображения
            super().save(*args, **kwargs)
            
            img = Image.open(self.avatar.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.avatar.path)
        else:
            super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Переопределенный метод удаления"""
        # Удаляем файл аватара при удалении пользователя
        if self.avatar:
            if os.path.isfile(self.avatar.path):
                os.remove(self.avatar.path)
        super().delete(*args, **kwargs)
    
    @property
    def is_admin(self):
        """Проверяет, является ли пользователь администратором"""
        return self.role == self.Role.ADMIN or self.is_superuser
    
    @property
    def is_manager(self):
        """Проверяет, является ли пользователь менеджером"""
        return self.role in [self.Role.ADMIN, self.Role.MANAGER] or self.is_superuser
    
    @property
    def is_engineer(self):
        """Проверяет, является ли пользователь инженером"""
        return self.role in [self.Role.ADMIN, self.Role.ENGINEER] or self.is_superuser
    
    @property
    def is_executive(self):
        """Проверяет, является ли пользователь руководителем"""
        return self.role in [self.Role.ADMIN, self.Role.EXECUTIVE] or self.is_superuser
    
    @property
    def is_customer(self):
        """Проверяет, является ли пользователь заказчиком"""
        return self.role in [self.Role.ADMIN, self.Role.CUSTOMER] or self.is_superuser
    
    @property
    def can_create_defects(self):
        """Проверяет, может ли пользователь создавать дефекты"""
        return self.role in [self.Role.ADMIN, self.Role.ENGINEER] or self.is_superuser
    
    @property
    def can_assign_defects(self):
        """Проверяет, может ли пользователь назначать дефекты"""
        return self.role in [self.Role.ADMIN, self.Role.MANAGER] or self.is_superuser
    
    @property
    def can_assign_tasks(self):
        """Проверяет, может ли пользователь назначать задачи"""
        return self.role in [self.Role.ADMIN, self.Role.MANAGER] or self.is_superuser
    
    @property
    def can_control_deadlines(self):
        """Проверяет, может ли пользователь контролировать сроки"""
        return self.role in [self.Role.ADMIN, self.Role.MANAGER] or self.is_superuser
    
    @property
    def can_generate_reports(self):
        """Проверяет, может ли пользователь формировать отчеты"""
        return self.role in [self.Role.ADMIN, self.Role.MANAGER] or self.is_superuser
    
    @property
    def can_update_info(self):
        """Проверяет, может ли пользователь обновлять информацию"""
        return self.role in [self.Role.ADMIN, self.Role.ENGINEER] or self.is_superuser
    
    @property
    def can_view_progress(self):
        """Проверяет, может ли пользователь просматривать прогресс"""
        return self.role in [self.Role.ADMIN, self.Role.EXECUTIVE, self.Role.CUSTOMER] or self.is_superuser
    
    @property
    def can_view_reports(self):
        """Проверяет, может ли пользователь просматривать отчеты"""
        return self.role in [self.Role.ADMIN, self.Role.EXECUTIVE, self.Role.CUSTOMER, self.Role.MANAGER] or self.is_superuser
    
    def get_avatar_url(self):
        """Возвращает URL аватара или дефолтный"""
        if self.avatar:
            return self.avatar.url
        return '/static/images/default-avatar.png'


class UserProfile(models.Model):
    """Дополнительная информация профиля пользователя"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь'
    )
    
    bio = models.TextField(
        'О себе',
        max_length=500,
        blank=True,
        help_text='Краткая информация о пользователе'
    )
    
    birth_date = models.DateField(
        'Дата рождения',
        blank=True,
        null=True
    )
    
    location = models.CharField(
        'Местоположение',
        max_length=100,
        blank=True,
        help_text='Город или регион'
    )
    
    website = models.URLField(
        'Веб-сайт',
        blank=True,
        help_text='Личный веб-сайт или профиль в соцсети'
    )
    
    # Настройки интерфейса
    theme = models.CharField(
        'Тема интерфейса',
        max_length=20,
        choices=[
            ('light', 'Светлая'),
            ('dark', 'Темная'),
            ('auto', 'Автоматически'),
        ],
        default='light'
    )
    
    language = models.CharField(
        'Язык интерфейса',
        max_length=10,
        choices=[
            ('ru', 'Русский'),
            ('en', 'English'),
        ],
        default='ru'
    )
    
    timezone = models.CharField(
        'Часовой пояс',
        max_length=50,
        default='Europe/Moscow',
        help_text='Часовой пояс пользователя'
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
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'
    
    def __str__(self):
        return f"Профиль {self.user.get_full_name()}"


class UserSession(models.Model):
    """Модель для отслеживания сессий пользователей"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name='Пользователь'
    )
    
    session_key = models.CharField(
        'Ключ сессии',
        max_length=40,
        unique=True
    )
    
    ip_address = models.GenericIPAddressField(
        'IP адрес',
        blank=True,
        null=True
    )
    
    user_agent = models.TextField(
        'User Agent',
        blank=True,
        help_text='Информация о браузере и устройстве'
    )
    
    created_at = models.DateTimeField(
        'Время входа',
        auto_now_add=True
    )
    
    last_activity = models.DateTimeField(
        'Последняя активность',
        auto_now=True
    )
    
    is_active = models.BooleanField(
        'Активная сессия',
        default=True
    )
    
    class Meta:
        verbose_name = 'Сессия пользователя'
        verbose_name_plural = 'Сессии пользователей'
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_key']),
        ]
    
    def __str__(self):
        return f"Сессия {self.user.get_full_name()} - {self.created_at}"