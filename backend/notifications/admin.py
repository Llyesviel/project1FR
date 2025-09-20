from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Q
from .models import (
    Notification, 
    NotificationTemplate, 
    NotificationSettings, 
    NotificationBatch
)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Админка для уведомлений"""
    
    list_display = [
        'title', 
        'recipient_link', 
        'sender_link', 
        'notification_type', 
        'category', 
        'priority', 
        'is_read_badge', 
        'created_at',
        'expires_at'
    ]
    
    list_filter = [
        'notification_type',
        'category', 
        'priority',
        'is_read',
        'created_at',
        'expires_at'
    ]
    
    search_fields = [
        'title', 
        'message', 
        'recipient__username', 
        'recipient__email',
        'sender__username'
    ]
    
    readonly_fields = [
        'created_at', 
        'read_at', 
        'content_type', 
        'object_id',
        'content_object_link'
    ]
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('title', 'message', 'recipient', 'sender')
        }),
        (_('Классификация'), {
            'fields': ('notification_type', 'category', 'priority')
        }),
        (_('Связанный объект'), {
            'fields': ('content_type', 'object_id', 'content_object_link'),
            'classes': ('collapse',)
        }),
        (_('Статус'), {
            'fields': ('is_read', 'read_at', 'expires_at')
        }),
        (_('Дополнительно'), {
            'fields': ('action_url', 'extra_data'),
            'classes': ('collapse',)
        }),
        (_('Временные метки'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    actions = [
        'mark_as_read', 
        'mark_as_unread', 
        'delete_expired',
        'send_email_notification'
    ]
    
    date_hierarchy = 'created_at'
    
    def recipient_link(self, obj):
        """Ссылка на получателя"""
        if obj.recipient:
            url = reverse('admin:accounts_user_change', args=[obj.recipient.pk])
            return format_html('<a href="{}">{}</a>', url, obj.recipient.username)
        return '-'
    recipient_link.short_description = _('Получатель')
    
    def sender_link(self, obj):
        """Ссылка на отправителя"""
        if obj.sender:
            url = reverse('admin:accounts_user_change', args=[obj.sender.pk])
            return format_html('<a href="{}">{}</a>', url, obj.sender.username)
        return _('Система')
    sender_link.short_description = _('Отправитель')
    
    def is_read_badge(self, obj):
        """Бейдж статуса прочтения"""
        if obj.is_read:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ {}</span>',
                _('Прочитано')
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ {}</span>',
                _('Не прочитано')
            )
    is_read_badge.short_description = _('Статус')
    
    def content_object_link(self, obj):
        """Ссылка на связанный объект"""
        if obj.content_object:
            try:
                # Пытаемся получить админскую ссылку
                model_name = obj.content_type.model
                app_label = obj.content_type.app_label
                url = reverse(f'admin:{app_label}_{model_name}_change', args=[obj.object_id])
                return format_html('<a href="{}">{}</a>', url, str(obj.content_object))
            except:
                return str(obj.content_object)
        return '-'
    content_object_link.short_description = _('Связанный объект')
    
    def mark_as_read(self, request, queryset):
        """Отметить как прочитанное"""
        updated = 0
        for notification in queryset.filter(is_read=False):
            notification.mark_as_read()
            updated += 1
        
        self.message_user(
            request, 
            _(f'Отмечено как прочитанное: {updated} уведомлений')
        )
    mark_as_read.short_description = _('Отметить как прочитанное')
    
    def mark_as_unread(self, request, queryset):
        """Отметить как непрочитанное"""
        updated = queryset.filter(is_read=True).update(
            is_read=False, 
            read_at=None
        )
        
        self.message_user(
            request, 
            _(f'Отмечено как непрочитанное: {updated} уведомлений')
        )
    mark_as_unread.short_description = _('Отметить как непрочитанное')
    
    def delete_expired(self, request, queryset):
        """Удалить истекшие уведомления"""
        now = timezone.now()
        expired_count = queryset.filter(
            expires_at__lt=now
        ).count()
        
        queryset.filter(expires_at__lt=now).delete()
        
        self.message_user(
            request, 
            _(f'Удалено истекших уведомлений: {expired_count}')
        )
    delete_expired.short_description = _('Удалить истекшие')
    
    def send_email_notification(self, request, queryset):
        """Отправить email уведомления"""
        # Здесь можно добавить логику отправки email
        count = queryset.count()
        self.message_user(
            request, 
            _(f'Email уведомления отправлены: {count}')
        )
    send_email_notification.short_description = _('Отправить email')
    
    def get_queryset(self, request):
        """Оптимизированный queryset"""
        return super().get_queryset(request).select_related(
            'recipient', 'sender', 'content_type'
        )


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """Админка для шаблонов уведомлений"""
    
    list_display = [
        'name', 
        'notification_type', 
        'category', 
        'priority', 
        'is_active',
        'usage_count',
        'created_at'
    ]
    
    list_filter = [
        'notification_type', 
        'category', 
        'priority', 
        'is_active',
        'created_at'
    ]
    
    search_fields = ['name', 'title_template', 'message_template']
    
    readonly_fields = ['created_at', 'updated_at', 'usage_count']
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'is_active')
        }),
        (_('Шаблоны'), {
            'fields': ('title_template', 'message_template'),
            'description': _('Используйте {переменная} для подстановки значений')
        }),
        (_('Классификация'), {
            'fields': ('notification_type', 'category', 'priority')
        }),
        (_('Настройки'), {
            'fields': ('default_expires_days',)
        }),
        (_('Информация'), {
            'fields': ('usage_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['activate_templates', 'deactivate_templates', 'test_template']
    
    def usage_count(self, obj):
        """Количество использований шаблона"""
        # Подсчитываем через связанные NotificationBatch
        return obj.notificationbatch_set.count()
    usage_count.short_description = _('Использований')
    
    def activate_templates(self, request, queryset):
        """Активировать шаблоны"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request, 
            _(f'Активировано шаблонов: {updated}')
        )
    activate_templates.short_description = _('Активировать')
    
    def deactivate_templates(self, request, queryset):
        """Деактивировать шаблоны"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request, 
            _(f'Деактивировано шаблонов: {updated}')
        )
    deactivate_templates.short_description = _('Деактивировать')
    
    def test_template(self, request, queryset):
        """Тестировать шаблон"""
        # Здесь можно добавить логику тестирования шаблона
        count = queryset.count()
        self.message_user(
            request, 
            _(f'Протестировано шаблонов: {count}')
        )
    test_template.short_description = _('Тестировать')


class NotificationInline(admin.TabularInline):
    """Инлайн для уведомлений пользователя"""
    model = Notification
    fk_name = 'recipient'
    extra = 0
    readonly_fields = ['title', 'notification_type', 'is_read', 'created_at']
    fields = ['title', 'notification_type', 'is_read', 'created_at']
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    """Админка для настроек уведомлений"""
    
    list_display = [
        'user_link', 
        'email_notifications', 
        'push_notifications',
        'project_notifications',
        'security_notifications',
        'updated_at'
    ]
    
    list_filter = [
        'email_notifications', 
        'push_notifications',
        'project_notifications',
        'facility_notifications',
        'document_notifications',
        'security_notifications'
    ]
    
    search_fields = ['user__username', 'user__email']
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('Пользователь'), {
            'fields': ('user',)
        }),
        (_('Общие настройки'), {
            'fields': ('email_notifications', 'push_notifications')
        }),
        (_('Категории уведомлений'), {
            'fields': (
                'project_notifications',
                'facility_notifications', 
                'document_notifications',
                'security_notifications'
            )
        }),
        (_('Приоритет уведомлений'), {
            'fields': (
                'low_priority_notifications',
                'normal_priority_notifications',
                'high_priority_notifications',
                'urgent_priority_notifications'
            )
        }),
        (_('Расписание'), {
            'fields': ('quiet_hours_start', 'quiet_hours_end')
        }),
        (_('Автоматическая очистка'), {
            'fields': ('auto_delete_read_after_days',)
        }),
        (_('Временные метки'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_link(self, obj):
        """Ссылка на пользователя"""
        url = reverse('admin:accounts_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = _('Пользователь')


@admin.register(NotificationBatch)
class NotificationBatchAdmin(admin.ModelAdmin):
    """Админка для пакетных уведомлений"""
    
    list_display = [
        'name', 
        'template', 
        'total_recipients', 
        'successful_sends',
        'failed_sends',
        'is_sent',
        'created_at'
    ]
    
    list_filter = [
        'is_sent', 
        'template__category',
        'template__priority',
        'created_at'
    ]
    
    search_fields = ['name', 'template__name']
    
    readonly_fields = [
        'is_sent', 
        'sent_at', 
        'total_recipients',
        'successful_sends', 
        'failed_sends',
        'created_at'
    ]
    
    filter_horizontal = ['recipients']
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'template', 'created_by')
        }),
        (_('Получатели'), {
            'fields': ('recipients',)
        }),
        (_('Данные'), {
            'fields': ('context_data',)
        }),
        (_('Статус отправки'), {
            'fields': (
                'is_sent', 
                'sent_at', 
                'total_recipients',
                'successful_sends', 
                'failed_sends'
            ),
            'classes': ('collapse',)
        }),
        (_('Временные метки'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    actions = ['send_batch_notifications']
    
    def send_batch_notifications(self, request, queryset):
        """Отправить пакетные уведомления"""
        sent_count = 0
        for batch in queryset.filter(is_sent=False):
            if batch.send_notifications():
                sent_count += 1
        
        self.message_user(
            request, 
            _(f'Отправлено пакетов: {sent_count}')
        )
    send_batch_notifications.short_description = _('Отправить уведомления')
    
    def get_queryset(self, request):
        """Оптимизированный queryset"""
        return super().get_queryset(request).select_related(
            'template', 'created_by'
        ).prefetch_related('recipients')


# Настройка заголовков админки
admin.site.site_header = _('Система управления объектами - Администрирование')
admin.site.site_title = _('Админ-панель')
admin.site.index_title = _('Добро пожаловать в админ-панель')