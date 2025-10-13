from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone

from .models import Defect
from .serializers import (
    DefectSerializer, 
    DefectListSerializer, 
    DefectStatusUpdateSerializer
)
from accounts.permissions import IsAdminOrManager, IsExecutorOrHigher


class DefectViewSet(viewsets.ModelViewSet):
    """ViewSet для управления дефектами"""
    
    queryset = Defect.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'severity', 'priority', 'facility', 'assigned_to']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['created_at', 'updated_at', 'due_date', 'priority']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        if self.action == 'list':
            return DefectListSerializer
        elif self.action == 'update_status':
            return DefectStatusUpdateSerializer
        return DefectSerializer
    
    def get_permissions(self):
        """Настройка разрешений в зависимости от действия"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsExecutorOrHigher]
        elif self.action in ['assign', 'update_status']:
            permission_classes = [IsAuthenticated, IsAdminOrManager]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Фильтрация дефектов в зависимости от роли пользователя"""
        user = self.request.user
        queryset = Defect.objects.select_related(
            'facility', 'reported_by', 'assigned_to'
        )
        
        # Администраторы и менеджеры видят все дефекты
        if user.is_admin or user.is_manager:
            return queryset
        
        # Инженеры видят дефекты, которые они создали или которые им назначены
        elif user.is_engineer:
            return queryset.filter(
                Q(reported_by=user) | Q(assigned_to=user)
            )
        
        # Остальные пользователи видят только свои дефекты
        return queryset.filter(reported_by=user)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsExecutorOrHigher])
    def update_status(self, request, pk=None):
        """Обновление статуса дефекта"""
        defect = self.get_object()
        serializer = self.get_serializer(defect, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAdminOrManager])
    def assign(self, request, pk=None):
        """Назначение дефекта пользователю"""
        defect = self.get_object()
        assigned_to_id = request.data.get('assigned_to')
        
        if assigned_to_id:
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                assigned_user = User.objects.get(id=assigned_to_id)
                defect.assigned_to = assigned_user
                defect.save()
                
                serializer = self.get_serializer(defect)
                return Response(serializer.data)
            except User.DoesNotExist:
                return Response(
                    {'error': 'Пользователь не найден'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(
            {'error': 'Не указан пользователь для назначения'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def my_defects(self, request):
        """Получение дефектов текущего пользователя"""
        user = request.user
        defects = self.get_queryset().filter(
            Q(reported_by=user) | Q(assigned_to=user)
        )
        
        page = self.paginate_queryset(defects)
        if page is not None:
            serializer = DefectListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = DefectListSerializer(defects, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Получение просроченных дефектов"""
        overdue_defects = self.get_queryset().filter(
            due_date__lt=timezone.now(),
            status__in=[Defect.Status.NEW, Defect.Status.IN_PROGRESS]
        )
        
        page = self.paginate_queryset(overdue_defects)
        if page is not None:
            serializer = DefectListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = DefectListSerializer(overdue_defects, many=True)
        return Response(serializer.data)