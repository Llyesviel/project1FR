from rest_framework import permissions
from django.db.models import Q
from .models import Project, Facility, ProjectMembership


class IsProjectManagerOrAdmin(permissions.BasePermission):
    """Разрешение для менеджеров проекта и администраторов"""
    
    def has_permission(self, request, view):
        """Проверка базового разрешения"""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Проверка разрешения на объект"""
        user = request.user
        
        # Администраторы имеют полный доступ
        if user.groups.filter(name='Admins').exists():
            return True
        
        # Если объект - проект
        if isinstance(obj, Project):
            # Менеджер проекта имеет полный доступ
            if obj.manager == user:
                return True
            
            # Участники команды с ролью менеджера имеют доступ
            if ProjectMembership.objects.filter(
                project=obj,
                user=user,
                role=ProjectMembership.Role.MANAGER,
                is_active=True
            ).exists():
                return True
        
        return False


class IsFacilityResponsibleOrAdmin(permissions.BasePermission):
    """Разрешение для ответственных за объект и администраторов"""
    
    def has_permission(self, request, view):
        """Проверка базового разрешения"""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Проверка разрешения на объект"""
        user = request.user
        
        # Администраторы имеют полный доступ
        if user.groups.filter(name='Admins').exists():
            return True
        
        # Если объект - объект (Facility)
        if isinstance(obj, Facility):
            # Ответственный за объект имеет полный доступ
            if obj.responsible_person == user:
                return True
            
            # Менеджер проекта имеет доступ к объектам проекта
            if obj.project.manager == user:
                return True
            
            # Участники команды проекта с ролью менеджера имеют доступ
            if ProjectMembership.objects.filter(
                project=obj.project,
                user=user,
                role=ProjectMembership.Role.MANAGER,
                is_active=True
            ).exists():
                return True
        
        return False


class IsProjectMemberOrAdmin(permissions.BasePermission):
    """Разрешение для участников проекта и администраторов"""
    
    def has_permission(self, request, view):
        """Проверка базового разрешения"""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Проверка разрешения на объект"""
        user = request.user
        
        # Администраторы имеют полный доступ
        if user.groups.filter(name='Admins').exists():
            return True
        
        # Определяем проект в зависимости от типа объекта
        project = None
        if isinstance(obj, Project):
            project = obj
        elif isinstance(obj, Facility):
            project = obj.project
        elif hasattr(obj, 'facility'):
            project = obj.facility.project
        
        if project:
            # Менеджер проекта имеет доступ
            if project.manager == user:
                return True
            
            # Участники команды имеют доступ
            if ProjectMembership.objects.filter(
                project=project,
                user=user,
                is_active=True
            ).exists():
                return True
        
        return False


class IsOwnerOrProjectMemberOrAdmin(permissions.BasePermission):
    """Разрешение для владельца объекта, участников проекта и администраторов"""
    
    def has_permission(self, request, view):
        """Проверка базового разрешения"""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Проверка разрешения на объект"""
        user = request.user
        
        # Администраторы имеют полный доступ
        if user.groups.filter(name='Admins').exists():
            return True
        
        # Владелец объекта имеет доступ
        if hasattr(obj, 'created_by') and obj.created_by == user:
            return True
        
        if hasattr(obj, 'uploaded_by') and obj.uploaded_by == user:
            return True
        
        # Проверяем доступ через участие в проекте
        project = None
        if isinstance(obj, Project):
            project = obj
        elif isinstance(obj, Facility):
            project = obj.project
        elif hasattr(obj, 'facility'):
            project = obj.facility.project
        
        if project:
            # Менеджер проекта имеет доступ
            if project.manager == user:
                return True
            
            # Участники команды имеют доступ
            if ProjectMembership.objects.filter(
                project=project,
                user=user,
                is_active=True
            ).exists():
                return True
        
        return False


class IsManagerOrAdmin(permissions.BasePermission):
    """Разрешение только для менеджеров и администраторов"""
    
    def has_permission(self, request, view):
        """Проверка базового разрешения"""
        user = request.user
        
        if not user or not user.is_authenticated:
            return False
        
        # Администраторы имеют доступ
        if user.groups.filter(name='Admins').exists():
            return True
        
        # Менеджеры имеют доступ
        if user.groups.filter(name='Managers').exists():
            return True
        
        return False


class IsAdminOnly(permissions.BasePermission):
    """Разрешение только для администраторов"""
    
    def has_permission(self, request, view):
        """Проверка базового разрешения"""
        user = request.user
        
        if not user or not user.is_authenticated:
            return False
        
        return user.groups.filter(name='Admins').exists()


class CanViewProject(permissions.BasePermission):
    """Разрешение на просмотр проекта"""
    
    def has_permission(self, request, view):
        """Проверка базового разрешения"""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Проверка разрешения на просмотр объекта"""
        user = request.user
        
        # Администраторы видят все
        if user.groups.filter(name='Admins').exists():
            return True
        
        # Определяем проект
        project = obj if isinstance(obj, Project) else getattr(obj, 'project', None)
        
        if project:
            # Менеджер проекта видит проект
            if project.manager == user:
                return True
            
            # Участники команды видят проект
            if ProjectMembership.objects.filter(
                project=project,
                user=user,
                is_active=True
            ).exists():
                return True
        
        return False


class CanEditProject(permissions.BasePermission):
    """Разрешение на редактирование проекта"""
    
    def has_permission(self, request, view):
        """Проверка базового разрешения"""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Проверка разрешения на редактирование объекта"""
        user = request.user
        
        # Администраторы могут редактировать все
        if user.groups.filter(name='Admins').exists():
            return True
        
        # Определяем проект
        project = obj if isinstance(obj, Project) else getattr(obj, 'project', None)
        
        if project:
            # Менеджер проекта может редактировать
            if project.manager == user:
                return True
            
            # Участники команды с ролью менеджера могут редактировать
            if ProjectMembership.objects.filter(
                project=project,
                user=user,
                role__in=[ProjectMembership.Role.MANAGER, ProjectMembership.Role.ARCHITECT],
                is_active=True
            ).exists():
                return True
        
        return False


class CanManageTeam(permissions.BasePermission):
    """Разрешение на управление командой проекта"""
    
    def has_permission(self, request, view):
        """Проверка базового разрешения"""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Проверка разрешения на управление командой"""
        user = request.user
        
        # Администраторы могут управлять всеми командами
        if user.groups.filter(name='Admins').exists():
            return True
        
        # Определяем проект
        project = obj if isinstance(obj, Project) else getattr(obj, 'project', None)
        
        if project:
            # Менеджер проекта может управлять командой
            if project.manager == user:
                return True
            
            # Участники с ролью менеджера могут управлять командой
            if ProjectMembership.objects.filter(
                project=project,
                user=user,
                role=ProjectMembership.Role.MANAGER,
                is_active=True
            ).exists():
                return True
        
        return False


class ReadOnlyOrManagerPermission(permissions.BasePermission):
    """Разрешение на чтение для всех, на запись только для менеджеров"""
    
    def has_permission(self, request, view):
        """Проверка базового разрешения"""
        user = request.user
        
        if not user or not user.is_authenticated:
            return False
        
        # Чтение разрешено всем аутентифицированным пользователям
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Запись только для менеджеров и администраторов
        return user.groups.filter(name__in=['Managers', 'Admins']).exists()
    
    def has_object_permission(self, request, view, obj):
        """Проверка разрешения на объект"""
        user = request.user
        
        # Чтение разрешено участникам проекта
        if request.method in permissions.SAFE_METHODS:
            return CanViewProject().has_object_permission(request, view, obj)
        
        # Запись только для менеджеров проекта и администраторов
        return CanEditProject().has_object_permission(request, view, obj)