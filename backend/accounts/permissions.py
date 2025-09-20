from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """Разрешение для владельца объекта или администратора"""
    
    def has_object_permission(self, request, view, obj):
        # Администраторы имеют полный доступ
        if request.user.is_admin:
            return True
        
        # Пользователь может редактировать только свой профиль
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Для модели User
        return obj == request.user


class IsAdminOrManager(permissions.BasePermission):
    """Разрешение только для администраторов и менеджеров"""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_manager
        )


class IsAdminOnly(permissions.BasePermission):
    """Разрешение только для администраторов"""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_admin
        )


class IsExecutorOrHigher(permissions.BasePermission):
    """Разрешение для исполнителей и выше"""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_executor
        )


class CanCreateDefects(permissions.BasePermission):
    """Разрешение на создание дефектов"""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.can_create_defects
        )


class CanAssignDefects(permissions.BasePermission):
    """Разрешение на назначение дефектов"""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.can_assign_defects
        )


class IsOwnerOrManagerOrAdmin(permissions.BasePermission):
    """Разрешение для владельца, менеджера или администратора"""
    
    def has_object_permission(self, request, view, obj):
        # Администраторы и менеджеры имеют доступ
        if request.user.is_manager:
            return True
        
        # Владелец объекта имеет доступ
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        if hasattr(obj, 'assigned_to'):
            return obj.assigned_to == request.user
        
        return obj == request.user


class ReadOnlyOrOwnerOrAdmin(permissions.BasePermission):
    """Чтение для всех, изменение только для владельца или администратора"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Чтение разрешено всем аутентифицированным пользователям
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Изменение только для владельца или администратора
        if request.user.is_admin:
            return True
        
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return obj == request.user


class DepartmentPermission(permissions.BasePermission):
    """Разрешение на основе отдела"""
    
    def has_object_permission(self, request, view, obj):
        # Администраторы имеют полный доступ
        if request.user.is_admin:
            return True
        
        # Менеджеры могут работать с объектами своего отдела
        if request.user.is_manager:
            if hasattr(obj, 'department'):
                return obj.department == request.user.department
            
            if hasattr(obj, 'user') and hasattr(obj.user, 'department'):
                return obj.user.department == request.user.department
        
        # Владелец объекта имеет доступ
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False