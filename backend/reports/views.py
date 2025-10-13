from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta

from projects.models import Project, Facility, Task
from accounts.models import User
from defects.models import Defect


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_stats(request):
    """Общая статистика для дашборда"""
    user = request.user
    
    # Фильтруем проекты в зависимости от роли пользователя
    if user.role == User.Role.ADMIN:
        projects = Project.objects.all()
        facilities = Facility.objects.all()
    elif user.role == User.Role.MANAGER:
        projects = Project.objects.filter(
            Q(manager=user) | Q(team_members=user)
        ).distinct()
        facilities = Facility.objects.filter(project__in=projects)
    else:
        projects = Project.objects.filter(team_members=user)
        facilities = Facility.objects.filter(project__in=projects)
    
    # Основная статистика
    total_projects = projects.count()
    active_projects = projects.filter(status='active').count()
    completed_projects = projects.filter(status='completed').count()
    overdue_projects = projects.filter(
        end_date__lt=timezone.now().date(),
        status__in=['planning', 'active', 'on_hold']
    ).count()
    
    # Статистика по объектам
    total_facilities = facilities.count()
    active_facilities = facilities.filter(status='active').count()
    completed_facilities = facilities.filter(status='completed').count()
    
    # Статистика по дефектам
    if user.role == User.Role.ADMIN:
        defects = Defect.objects.all()
    else:
        # Получаем дефекты для объектов, связанных с проектами пользователя
        defects = Defect.objects.filter(facility__project__in=projects)
    
    total_defects = defects.count()
    open_defects = defects.filter(status__in=['open', 'in_progress']).count()
    critical_defects = defects.filter(severity='critical').count()
    
    # Статистика по задачам
    if user.role == User.Role.ADMIN:
        tasks = Task.objects.all()
    else:
        tasks = Task.objects.filter(project__in=projects)
    
    active_tasks = tasks.filter(status__in=['pending', 'in_progress']).count()
    overdue_tasks = tasks.filter(
        due_date__lt=timezone.now().date(),
        status__in=['pending', 'in_progress']
    ).count()
    
    # Статистика по бронированиям (заглушка, так как модель бронирований не определена)
    active_bookings = 0  # Заглушка
    
    # Статистика по статусам проектов
    projects_by_status = dict(
        projects.values('status').annotate(
            count=Count('id')
        ).values_list('status', 'count')
    )
    
    # Статистика по приоритетам проектов
    projects_by_priority = dict(
        projects.values('priority').annotate(
            count=Count('id')
        ).values_list('priority', 'count')
    )
    
    # Статистика по типам объектов
    facilities_by_type = dict(
        facilities.values('type').annotate(
            count=Count('id')
        ).values_list('type', 'count')
    )
    
    # Статистика по статусам объектов
    facilities_by_status = dict(
        facilities.values('status').annotate(
            count=Count('id')
        ).values_list('status', 'count')
    )
    
    # Средний прогресс проектов
    avg_progress = projects.aggregate(
        avg_progress=Avg('progress')
    )['avg_progress'] or 0
    
    # Статистика за последние 30 дней
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_projects = projects.filter(created_at__gte=thirty_days_ago).count()
    recent_facilities = facilities.filter(created_at__gte=thirty_days_ago).count()
    recent_defects = defects.filter(created_at__gte=thirty_days_ago).count()
    
    stats = {
        # Основные показатели
        'total_projects': total_projects,
        'active_projects': active_projects,
        'completed_projects': completed_projects,
        'overdue_projects': overdue_projects,
        'total_facilities': total_facilities,
        'active_facilities': active_facilities,
        'completed_facilities': completed_facilities,
        'total_defects': total_defects,
        'open_defects': open_defects,
        'critical_defects': critical_defects,
        'active_bookings': active_bookings,
        
        # Средние показатели
        'avg_progress': round(avg_progress, 2),
        
        # Статистика по категориям
        'projects_by_status': projects_by_status,
        'projects_by_priority': projects_by_priority,
        'facilities_by_type': facilities_by_type,
        'facilities_by_status': facilities_by_status,
        
        # Статистика за период
        'recent_projects': recent_projects,
        'recent_facilities': recent_facilities,
        'recent_defects': recent_defects,
        
        # Дополнительная информация
        'user_role': user.role,
        'last_updated': timezone.now().isoformat(),
    }
    
    return Response(stats)


class DashboardStatsViewSet(viewsets.ViewSet):
    """ViewSet для статистики дашборда"""
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """Получить статистику дашборда"""
        return dashboard_stats(request)