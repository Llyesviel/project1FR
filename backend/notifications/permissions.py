from rest_framework import permissions
from django.contrib.auth import get_user_model
from .models import Notification, NotificationSettings

User = get_user_model()


class IsOwnerOrAdmin(permissions.BasePermission):
    """Разрешение для владельца объекта или администратора"""
    
    def has_object_permission(self, request, view, obj):
        # Администраторы имеют полный доступ
        if request.user.is_staff:
            return True
        
        # Проверяем владельца в зависимости от типа объекта
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'recipient'):
            return obj.recipient == request.user
        
        return False


class IsNotificationRecipientOrAdmin(permissions.BasePermission):
    """Разрешение для получателя уведомления или администратора"""
    
    def has_object_permission(self, request, view, obj):
        # Администраторы имеют полный доступ
        if request.user.is_staff:
            return True
        
        # Проверяем, что пользователь является получателем уведомления
        if isinstance(obj, Notification):
            return obj.recipient == request.user
        
        return False


class CanManageNotifications(permissions.BasePermission):
    """Разрешение на управление уведомлениями"""
    
    def has_permission(self, request, view):
        # Пользователь должен быть аутентифицирован
        if not request.user.is_authenticated:
            return False
        
        # Администраторы могут управлять всеми уведомлениями
        if request.user.is_staff:
            return True
        
        # Менеджеры проектов могут создавать уведомления
        if hasattr(request.user, 'groups'):
            manager_groups = ['project_managers', 'facility_managers', 'administrators']
            user_groups = request.user.groups.values_list('name', flat=True)
            if any(group in user_groups for group in manager_groups):
                return True
        
        # Пользователи с соответствующими разрешениями
        required_permissions = [
            'notifications.add_notification',
            'notifications.change_notification',
            'notifications.delete_notification'
        ]
        
        return any(request.user.has_perm(perm) for perm in required_permissions)


class CanManageNotificationTemplates(permissions.BasePermission):
    """Разрешение на управление шаблонами уведомлений"""
    
    def has_permission(self, request, view):
        # Пользователь должен быть аутентифицирован
        if not request.user.is_authenticated:
            return False
        
        # Администраторы имеют полный доступ
        if request.user.is_staff:
            return True
        
        # Только администраторы и менеджеры могут управлять шаблонами
        if hasattr(request.user, 'groups'):
            allowed_groups = ['administrators', 'system_managers']
            user_groups = request.user.groups.values_list('name', flat=True)
            return any(group in user_groups for group in allowed_groups)
        
        # Пользователи с соответствующими разрешениями
        required_permissions = [
            'notifications.add_notificationtemplate',
            'notifications.change_notificationtemplate',
            'notifications.delete_notificationtemplate'
        ]
        
        return any(request.user.has_perm(perm) for perm in required_permissions)


class CanManageNotificationBatches(permissions.BasePermission):
    """Разрешение на управление пакетами уведомлений"""
    
    def has_permission(self, request, view):
        # Пользователь должен быть аутентифицирован
        if not request.user.is_authenticated:
            return False
        
        # Администраторы имеют полный доступ
        if request.user.is_staff:
            return True
        
        # Менеджеры могут создавать и управлять пакетами
        if hasattr(request.user, 'groups'):
            allowed_groups = ['administrators', 'project_managers', 'system_managers']
            user_groups = request.user.groups.values_list('name', flat=True)
            return any(group in user_groups for group in allowed_groups)
        
        # Пользователи с соответствующими разрешениями
        required_permissions = [
            'notifications.add_notificationbatch',
            'notifications.change_notificationbatch',
            'notifications.delete_notificationbatch'
        ]
        
        return any(request.user.has_perm(perm) for perm in required_permissions)
    
    def has_object_permission(self, request, view, obj):
        # Администраторы имеют полный доступ
        if request.user.is_staff:
            return True
        
        # Создатель пакета может им управлять
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
        
        return False


class CanViewNotificationStats(permissions.BasePermission):
    """Разрешение на просмотр статистики уведомлений"""
    
    def has_permission(self, request, view):
        # Пользователь должен быть аутентифицирован
        if not request.user.is_authenticated:
            return False
        
        # Администраторы могут видеть всю статистику
        if request.user.is_staff:
            return True
        
        # Менеджеры могут видеть статистику
        if hasattr(request.user, 'groups'):
            allowed_groups = ['administrators', 'project_managers', 'facility_managers', 'system_managers']
            user_groups = request.user.groups.values_list('name', flat=True)
            return any(group in user_groups for group in allowed_groups)
        
        # Обычные пользователи могут видеть только свою статистику
        return True


class CanSendNotifications(permissions.BasePermission):
    """Разрешение на отправку уведомлений"""
    
    def has_permission(self, request, view):
        # Пользователь должен быть аутентифицирован
        if not request.user.is_authenticated:
            return False
        
        # Администраторы могут отправлять любые уведомления
        if request.user.is_staff:
            return True
        
        # Менеджеры могут отправлять уведомления
        if hasattr(request.user, 'groups'):
            allowed_groups = ['administrators', 'project_managers', 'facility_managers']
            user_groups = request.user.groups.values_list('name', flat=True)
            return any(group in user_groups for group in allowed_groups)
        
        # Пользователи с соответствующими разрешениями
        return request.user.has_perm('notifications.add_notification')


class CanBulkManageNotifications(permissions.BasePermission):
    """Разрешение на массовые операции с уведомлениями"""
    
    def has_permission(self, request, view):
        # Пользователь должен быть аутентифицирован
        if not request.user.is_authenticated:
            return False
        
        # Администраторы могут выполнять массовые операции
        if request.user.is_staff:
            return True
        
        # Пользователи могут выполнять массовые операции только со своими уведомлениями
        return True


class IsNotificationSettingsOwner(permissions.BasePermission):
    """Разрешение для владельца настроек уведомлений"""
    
    def has_permission(self, request, view):
        # Пользователь должен быть аутентифицирован
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Администраторы имеют полный доступ
        if request.user.is_staff:
            return True
        
        # Пользователь может управлять только своими настройками
        if isinstance(obj, NotificationSettings):
            return obj.user == request.user
        
        return False


class CanAccessNotificationAPI(permissions.BasePermission):
    """Базовое разрешение для доступа к API уведомлений"""
    
    def has_permission(self, request, view):
        # Пользователь должен быть аутентифицирован
        if not request.user.is_authenticated:
            return False
        
        # Проверяем, что пользователь активен
        if not request.user.is_active:
            return False
        
        # Проверяем настройки уведомлений пользователя
        try:
            settings = NotificationSettings.objects.get(user=request.user)
            # Если пользователь отключил все уведомления, ограничиваем доступ к некоторым операциям
            if (not settings.email_notifications and 
                not settings.push_notifications and 
                view.action in ['create', 'bulk_action']):
                return False
        except NotificationSettings.DoesNotExist:
            # Если настроек нет, создаем их с настройками по умолчанию
            NotificationSettings.objects.create(user=request.user)
        
        return True


class CanManageSystemNotifications(permissions.BasePermission):
    """Разрешение на управление системными уведомлениями"""
    
    def has_permission(self, request, view):
        # Пользователь должен быть аутентифицирован
        if not request.user.is_authenticated:
            return False
        
        # Только администраторы и системные менеджеры
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Пользователи с соответствующими разрешениями
        system_permissions = [
            'notifications.can_send_system_notifications',
            'notifications.can_manage_notification_templates',
            'notifications.can_view_all_notifications'
        ]
        
        return any(request.user.has_perm(perm) for perm in system_permissions)


class NotificationPermissionMixin:
    """Миксин для проверки разрешений уведомлений"""
    
    def check_notification_permission(self, user, notification, action='view'):
        """Проверить разрешение на действие с уведомлением"""
        
        # Администраторы имеют полный доступ
        if user.is_staff:
            return True
        
        # Получатель может просматривать и изменять свои уведомления
        if notification.recipient == user:
            return action in ['view', 'update', 'delete']
        
        # Отправитель может просматривать отправленные уведомления
        if notification.sender == user:
            return action == 'view'
        
        return False
    
    def check_template_permission(self, user, template, action='view'):
        """Проверить разрешение на действие с шаблоном"""
        
        # Администраторы имеют полный доступ
        if user.is_staff:
            return True
        
        # Менеджеры могут управлять шаблонами
        if hasattr(user, 'groups'):
            allowed_groups = ['administrators', 'system_managers']
            user_groups = user.groups.values_list('name', flat=True)
            if any(group in user_groups for group in allowed_groups):
                return True
        
        # Для просмотра достаточно разрешения на создание уведомлений
        if action == 'view':
            return user.has_perm('notifications.add_notification')
        
        return False
    
    def check_batch_permission(self, user, batch, action='view'):
        """Проверить разрешение на действие с пакетом"""
        
        # Администраторы имеют полный доступ
        if user.is_staff:
            return True
        
        # Создатель может управлять своими пакетами
        if hasattr(batch, 'created_by') and batch.created_by == user:
            return True
        
        # Менеджеры могут просматривать пакеты
        if action == 'view' and hasattr(user, 'groups'):
            allowed_groups = ['administrators', 'project_managers', 'system_managers']
            user_groups = user.groups.values_list('name', flat=True)
            return any(group in user_groups for group in allowed_groups)
        
        return False