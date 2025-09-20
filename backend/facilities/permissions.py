from rest_framework import permissions
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class IsFacilityManager(permissions.BasePermission):
    """Разрешение для управляющих объектами недвижимости"""
    
    message = _('Только управляющие объектами могут выполнять это действие.')
    
    def has_permission(self, request, view):
        """Проверка общего разрешения"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Суперпользователи имеют все права
        if request.user.is_superuser:
            return True
        
        # Проверяем роль пользователя
        return hasattr(request.user, 'role') and request.user.role in ['facility_manager', 'admin']
    
    def has_object_permission(self, request, view, obj):
        """Проверка разрешения на конкретный объект"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Суперпользователи имеют все права
        if request.user.is_superuser:
            return True
        
        # Администраторы имеют все права
        if hasattr(request.user, 'role') and request.user.role == 'admin':
            return True
        
        # Управляющие могут работать только со своими объектами
        if hasattr(obj, 'manager'):
            return obj.manager == request.user
        
        # Для связанных объектов проверяем через facility
        if hasattr(obj, 'facility') and hasattr(obj.facility, 'manager'):
            return obj.facility.manager == request.user
        
        return False


class IsFacilityOwnerOrManager(permissions.BasePermission):
    """Разрешение для владельцев или управляющих объектами"""
    
    message = _('Только владельцы или управляющие объектами могут выполнять это действие.')
    
    def has_permission(self, request, view):
        """Проверка общего разрешения"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Суперпользователи имеют все права
        if request.user.is_superuser:
            return True
        
        # Проверяем роль пользователя
        return hasattr(request.user, 'role') and request.user.role in [
            'facility_manager', 'property_owner', 'admin'
        ]
    
    def has_object_permission(self, request, view, obj):
        """Проверка разрешения на конкретный объект"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Суперпользователи имеют все права
        if request.user.is_superuser:
            return True
        
        # Администраторы имеют все права
        if hasattr(request.user, 'role') and request.user.role == 'admin':
            return True
        
        # Проверяем владельца или управляющего
        if hasattr(obj, 'manager') and obj.manager == request.user:
            return True
        
        if hasattr(obj, 'owner') and obj.owner == request.user:
            return True
        
        # Для связанных объектов проверяем через facility
        if hasattr(obj, 'facility'):
            facility = obj.facility
            if hasattr(facility, 'manager') and facility.manager == request.user:
                return True
            if hasattr(facility, 'owner') and facility.owner == request.user:
                return True
        
        return False


class IsMaintenanceResponsible(permissions.BasePermission):
    """Разрешение для ответственных за обслуживание"""
    
    message = _('Только ответственные за обслуживание могут выполнять это действие.')
    
    def has_permission(self, request, view):
        """Проверка общего разрешения"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Суперпользователи имеют все права
        if request.user.is_superuser:
            return True
        
        # Проверяем роль пользователя
        return hasattr(request.user, 'role') and request.user.role in [
            'facility_manager', 'maintenance_worker', 'admin'
        ]
    
    def has_object_permission(self, request, view, obj):
        """Проверка разрешения на конкретный объект"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Суперпользователи имеют все права
        if request.user.is_superuser:
            return True
        
        # Администраторы имеют все права
        if hasattr(request.user, 'role') and request.user.role == 'admin':
            return True
        
        # Проверяем ответственного за обслуживание
        if hasattr(obj, 'responsible_person') and obj.responsible_person == request.user:
            return True
        
        # Управляющий объектом также может управлять обслуживанием
        if hasattr(obj, 'facility') and hasattr(obj.facility, 'manager'):
            return obj.facility.manager == request.user
        
        return False


class FacilityPermission(permissions.BasePermission):
    """Комплексное разрешение для объектов недвижимости"""
    
    def has_permission(self, request, view):
        """Проверка общего разрешения"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Суперпользователи имеют все права
        if request.user.is_superuser:
            return True
        
        # Для безопасных методов (GET, HEAD, OPTIONS) разрешаем всем аутентифицированным
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Для небезопасных методов проверяем роль
        return hasattr(request.user, 'role') and request.user.role in [
            'facility_manager', 'property_owner', 'admin'
        ]
    
    def has_object_permission(self, request, view, obj):
        """Проверка разрешения на конкретный объект"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Суперпользователи имеют все права
        if request.user.is_superuser:
            return True
        
        # Администраторы имеют все права
        if hasattr(request.user, 'role') and request.user.role == 'admin':
            return True
        
        # Для безопасных методов проверяем доступ к просмотру
        if request.method in permissions.SAFE_METHODS:
            # Управляющие и владельцы могут просматривать свои объекты
            if hasattr(obj, 'manager') and obj.manager == request.user:
                return True
            if hasattr(obj, 'owner') and obj.owner == request.user:
                return True
            
            # Работники обслуживания могут просматривать объекты, за которые отвечают
            if hasattr(request.user, 'role') and request.user.role == 'maintenance_worker':
                # Проверяем, есть ли у пользователя задачи по этому объекту
                return obj.maintenance_schedules.filter(
                    responsible_person=request.user
                ).exists()
            
            return False
        
        # Для небезопасных методов только владельцы и управляющие
        if hasattr(obj, 'manager') and obj.manager == request.user:
            return True
        if hasattr(obj, 'owner') and obj.owner == request.user:
            return True
        
        return False


class ReadOnlyOrOwner(permissions.BasePermission):
    """Разрешение только для чтения или для владельца"""
    
    def has_permission(self, request, view):
        """Проверка общего разрешения"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Для безопасных методов разрешаем всем аутентифицированным
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Для небезопасных методов требуем специальные роли
        return hasattr(request.user, 'role') and request.user.role in [
            'facility_manager', 'property_owner', 'admin'
        ]
    
    def has_object_permission(self, request, view, obj):
        """Проверка разрешения на конкретный объект"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Суперпользователи имеют все права
        if request.user.is_superuser:
            return True
        
        # Для безопасных методов разрешаем всем аутентифицированным
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Для небезопасных методов проверяем владельца
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
        
        if hasattr(obj, 'manager') and obj.manager == request.user:
            return True
        
        if hasattr(obj, 'owner') and obj.owner == request.user:
            return True
        
        # Администраторы имеют все права
        if hasattr(request.user, 'role') and request.user.role == 'admin':
            return True
        
        return False


class ProjectMemberPermission(permissions.BasePermission):
    """Разрешение для участников проекта"""
    
    def has_permission(self, request, view):
        """Проверка общего разрешения"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        """Проверка разрешения на конкретный объект"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Суперпользователи имеют все права
        if request.user.is_superuser:
            return True
        
        # Администраторы имеют все права
        if hasattr(request.user, 'role') and request.user.role == 'admin':
            return True
        
        # Проверяем участие в проекте
        if hasattr(obj, 'project'):
            project = obj.project
            # Здесь должна быть логика проверки участия в проекте
            # Пока упрощенная версия
            return True
        
        return False