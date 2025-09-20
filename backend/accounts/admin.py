from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import User, UserProfile, UserSession


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Админка для управления пользователями"""
    
    list_display = (
        'email', 'get_full_name', 'role', 'position', 'department',
        'is_active', 'is_staff', 'last_login', 'created_at'
    )
    
    list_filter = (
        'role', 'is_active', 'is_staff', 'is_superuser',
        'created_at', 'last_login', 'department'
    )
    
    search_fields = (
        'email', 'username', 'first_name', 'last_name',
        'position', 'department', 'phone'
    )
    
    ordering = ('-created_at',)
    
    readonly_fields = (
        'created_at', 'updated_at', 'last_login',
        'date_joined', 'get_avatar_preview'
    )
    
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'username', 'email', 'password',
                'first_name', 'last_name'
            )
        }),
        ('Роль и права доступа', {
            'fields': (
                'role', 'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            )
        }),
        ('Профессиональная информация', {
            'fields': (
                'position', 'department', 'phone'
            )
        }),
        ('Профиль', {
            'fields': (
                'avatar', 'get_avatar_preview'
            )
        }),
        ('Настройки уведомлений', {
            'fields': (
                'email_notifications', 'push_notifications'
            )
        }),
        ('Системная информация', {
            'fields': (
                'last_login', 'date_joined', 'created_at',
                'updated_at', 'last_activity'
            ),
            'classes': ('collapse',)
        })
    )
    
    add_fieldsets = (
        ('Создание пользователя', {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'password1', 'password2',
                'first_name', 'last_name', 'role'
            )
        }),
    )
    
    actions = [
        'activate_users', 'deactivate_users',
        'make_managers', 'make_executors'
    ]
    
    def get_full_name(self, obj):
        """Отображение полного имени"""
        return obj.get_full_name()
    get_full_name.short_description = 'Полное имя'
    get_full_name.admin_order_field = 'first_name'
    
    def get_avatar_preview(self, obj):
        """Превью аватара в админке"""
        if obj.avatar:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%; object-fit: cover;" />',
                obj.avatar.url
            )
        return 'Нет изображения'
    get_avatar_preview.short_description = 'Превью аватара'
    
    def activate_users(self, request, queryset):
        """Активировать выбранных пользователей"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'Активировано пользователей: {updated}'
        )
    activate_users.short_description = 'Активировать выбранных пользователей'
    
    def deactivate_users(self, request, queryset):
        """Деактивировать выбранных пользователей"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'Деактивировано пользователей: {updated}'
        )
    deactivate_users.short_description = 'Деактивировать выбранных пользователей'
    
    def make_managers(self, request, queryset):
        """Назначить менеджерами"""
        updated = queryset.update(role=User.Role.MANAGER)
        self.message_user(
            request,
            f'Назначено менеджерами: {updated}'
        )
    make_managers.short_description = 'Назначить менеджерами'
    
    def make_executors(self, request, queryset):
        """Назначить исполнителями"""
        updated = queryset.update(role=User.Role.EXECUTOR)
        self.message_user(
            request,
            f'Назначено исполнителями: {updated}'
        )
    make_executors.short_description = 'Назначить исполнителями'


class UserProfileInline(admin.StackedInline):
    """Инлайн для профиля пользователя"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Профиль'
    
    fieldsets = (
        ('Личная информация', {
            'fields': ('bio', 'birth_date', 'location', 'website')
        }),
        ('Настройки интерфейса', {
            'fields': ('theme', 'language', 'timezone')
        })
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Админка для профилей пользователей"""
    
    list_display = (
        'user', 'location', 'theme', 'language',
        'created_at', 'updated_at'
    )
    
    list_filter = ('theme', 'language', 'created_at')
    
    search_fields = (
        'user__email', 'user__first_name', 'user__last_name',
        'location', 'bio'
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Пользователь', {
            'fields': ('user',)
        }),
        ('Личная информация', {
            'fields': ('bio', 'birth_date', 'location', 'website')
        }),
        ('Настройки интерфейса', {
            'fields': ('theme', 'language', 'timezone')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """Админка для сессий пользователей"""
    
    list_display = (
        'user', 'ip_address', 'get_user_agent_short',
        'created_at', 'last_activity', 'is_active'
    )
    
    list_filter = (
        'is_active', 'created_at', 'last_activity'
    )
    
    search_fields = (
        'user__email', 'user__first_name', 'user__last_name',
        'ip_address', 'session_key'
    )
    
    readonly_fields = (
        'session_key', 'created_at', 'last_activity',
        'get_user_agent_full'
    )
    
    ordering = ('-last_activity',)
    
    actions = ['deactivate_sessions']
    
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'user', 'session_key', 'is_active'
            )
        }),
        ('Техническая информация', {
            'fields': (
                'ip_address', 'get_user_agent_full'
            )
        }),
        ('Временные метки', {
            'fields': (
                'created_at', 'last_activity'
            )
        })
    )
    
    def get_user_agent_short(self, obj):
        """Краткая версия User Agent"""
        if obj.user_agent:
            return obj.user_agent[:50] + '...' if len(obj.user_agent) > 50 else obj.user_agent
        return 'Не определен'
    get_user_agent_short.short_description = 'Браузер'
    
    def get_user_agent_full(self, obj):
        """Полная версия User Agent"""
        return obj.user_agent or 'Не определен'
    get_user_agent_full.short_description = 'Полная информация о браузере'
    
    def deactivate_sessions(self, request, queryset):
        """Деактивировать выбранные сессии"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'Деактивировано сессий: {updated}'
        )
    deactivate_sessions.short_description = 'Деактивировать выбранные сессии'
    
    def has_add_permission(self, request):
        """Запретить создание сессий через админку"""
        return False


# Настройка заголовков админки
admin.site.site_header = 'Система управления объектами'
admin.site.site_title = 'Админ-панель'
admin.site.index_title = 'Добро пожаловать в систему управления'