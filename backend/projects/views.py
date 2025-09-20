from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Count, Q, Avg
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import Project, ProjectMembership, Facility, FacilityDocument
from .serializers import (
    ProjectListSerializer, ProjectDetailSerializer, ProjectCreateUpdateSerializer,
    FacilityListSerializer, FacilityDetailSerializer, FacilityCreateUpdateSerializer,
    FacilityDocumentSerializer, ProjectMembershipSerializer, ProjectStatisticsSerializer
)
from .permissions import IsProjectManagerOrAdmin, IsFacilityResponsibleOrAdmin
from .filters import ProjectFilter, FacilityFilter


class ProjectViewSet(viewsets.ModelViewSet):
    """ViewSet для управления проектами"""
    
    queryset = Project.objects.select_related(
        'manager', 'created_by'
    ).prefetch_related(
        'team_members', 'facilities'
    ).filter(is_active=True)
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProjectFilter
    search_fields = ['name', 'code', 'description', 'client']
    ordering_fields = ['name', 'code', 'status', 'priority', 'start_date', 'end_date', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        if self.action == 'list':
            return ProjectListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProjectCreateUpdateSerializer
        return ProjectDetailSerializer
    
    def get_permissions(self):
        """Настройка разрешений"""
        if self.action in ['create']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsProjectManagerOrAdmin]
        elif self.action in ['add_member', 'remove_member', 'update_member']:
            permission_classes = [IsProjectManagerOrAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Фильтрация проектов по правам доступа"""
        user = self.request.user
        queryset = super().get_queryset()
        
        # Администраторы видят все проекты
        if user.groups.filter(name='Admins').exists():
            return queryset
        
        # Менеджеры видят свои проекты и проекты своих команд
        if user.groups.filter(name='Managers').exists():
            return queryset.filter(
                Q(manager=user) | Q(team_members=user)
            ).distinct()
        
        # Обычные пользователи видят только проекты, где они участники
        return queryset.filter(team_members=user).distinct()
    
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Добавить участника в проект"""
        project = self.get_object()
        serializer = ProjectMembershipSerializer(data=request.data)
        
        if serializer.is_valid():
            # Проверяем, не является ли пользователь уже участником
            user_id = serializer.validated_data['user_id']
            if ProjectMembership.objects.filter(project=project, user_id=user_id, is_active=True).exists():
                return Response(
                    {'error': 'Пользователь уже является участником проекта'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer.save(project=project)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'])
    def remove_member(self, request, pk=None):
        """Удалить участника из проекта"""
        project = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'Требуется указать user_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            membership = ProjectMembership.objects.get(
                project=project, user_id=user_id, is_active=True
            )
            membership.is_active = False
            membership.left_at = timezone.now()
            membership.save()
            
            return Response({'message': 'Участник удален из проекта'})
        except ProjectMembership.DoesNotExist:
            return Response(
                {'error': 'Участник не найден в проекте'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['patch'])
    def update_member(self, request, pk=None):
        """Обновить роль участника проекта"""
        project = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'Требуется указать user_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            membership = ProjectMembership.objects.get(
                project=project, user_id=user_id, is_active=True
            )
            serializer = ProjectMembershipSerializer(
                membership, data=request.data, partial=True
            )
            
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ProjectMembership.DoesNotExist:
            return Response(
                {'error': 'Участник не найден в проекте'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def facilities(self, request, pk=None):
        """Получить объекты проекта"""
        project = self.get_object()
        facilities = project.facilities.filter(is_active=True)
        
        # Применяем фильтры
        facility_filter = FacilityFilter(request.GET, queryset=facilities)
        facilities = facility_filter.qs
        
        serializer = FacilityListSerializer(facilities, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Статистика по проекту"""
        project = self.get_object()
        
        facilities = project.facilities.filter(is_active=True)
        
        stats = {
            'facilities_count': facilities.count(),
            'facilities_by_type': dict(
                facilities.values('type').annotate(
                    count=Count('id')
                ).values_list('type', 'count')
            ),
            'facilities_by_status': dict(
                facilities.values('status').annotate(
                    count=Count('id')
                ).values_list('status', 'count')
            ),
            'average_progress': facilities.aggregate(
                avg_progress=Avg('progress')
            )['avg_progress'] or 0,
            'team_members_count': project.get_team_count(),
            'total_defects': project.get_defects_count(),
            'overdue_facilities': facilities.filter(
                construction_end__lt=timezone.now().date(),
                status__in=['planning', 'construction', 'testing']
            ).count()
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Дашборд проектов"""
        user = request.user
        queryset = self.get_queryset()
        
        # Общая статистика
        total_projects = queryset.count()
        active_projects = queryset.filter(status='active').count()
        completed_projects = queryset.filter(status='completed').count()
        overdue_projects = queryset.filter(
            end_date__lt=timezone.now().date(),
            status__in=['planning', 'active', 'on_hold']
        ).count()
        
        # Статистика по статусам
        projects_by_status = dict(
            queryset.values('status').annotate(
                count=Count('id')
            ).values_list('status', 'count')
        )
        
        # Статистика по приоритетам
        projects_by_priority = dict(
            queryset.values('priority').annotate(
                count=Count('id')
            ).values_list('priority', 'count')
        )
        
        # Статистика по объектам
        facilities = Facility.objects.filter(
            project__in=queryset, is_active=True
        )
        
        facilities_by_type = dict(
            facilities.values('type').annotate(
                count=Count('id')
            ).values_list('type', 'count')
        )
        
        facilities_by_status = dict(
            facilities.values('status').annotate(
                count=Count('id')
            ).values_list('status', 'count')
        )
        
        stats = {
            'total_projects': total_projects,
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'overdue_projects': overdue_projects,
            'total_facilities': facilities.count(),
            'total_defects': sum(f.get_defects_count() for f in facilities),
            'projects_by_status': projects_by_status,
            'projects_by_priority': projects_by_priority,
            'facilities_by_type': facilities_by_type,
            'facilities_by_status': facilities_by_status
        }
        
        serializer = ProjectStatisticsSerializer(stats)
        return Response(serializer.data)


class FacilityViewSet(viewsets.ModelViewSet):
    """ViewSet для управления объектами"""
    
    queryset = Facility.objects.select_related(
        'project', 'responsible_person', 'created_by'
    ).prefetch_related(
        'documents'
    ).filter(is_active=True)
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = FacilityFilter
    search_fields = ['name', 'code', 'description', 'location']
    ordering_fields = [
        'name', 'code', 'type', 'status', 'progress',
        'construction_start', 'construction_end', 'created_at'
    ]
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        if self.action == 'list':
            return FacilityListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return FacilityCreateUpdateSerializer
        return FacilityDetailSerializer
    
    def get_permissions(self):
        """Настройка разрешений"""
        if self.action in ['create']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsFacilityResponsibleOrAdmin]
        elif self.action in ['upload_document', 'delete_document']:
            permission_classes = [IsFacilityResponsibleOrAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Фильтрация объектов по правам доступа"""
        user = self.request.user
        queryset = super().get_queryset()
        
        # Администраторы видят все объекты
        if user.groups.filter(name='Admins').exists():
            return queryset
        
        # Менеджеры видят объекты своих проектов
        if user.groups.filter(name='Managers').exists():
            return queryset.filter(
                Q(project__manager=user) | 
                Q(project__team_members=user) |
                Q(responsible_person=user)
            ).distinct()
        
        # Обычные пользователи видят объекты проектов, где они участники
        return queryset.filter(
            Q(project__team_members=user) |
            Q(responsible_person=user)
        ).distinct()
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_document(self, request, pk=None):
        """Загрузить документ для объекта"""
        facility = self.get_object()
        
        serializer = FacilityDocumentSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save(facility=facility)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'])
    def delete_document(self, request, pk=None):
        """Удалить документ объекта"""
        facility = self.get_object()
        document_id = request.data.get('document_id')
        
        if not document_id:
            return Response(
                {'error': 'Требуется указать document_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            document = FacilityDocument.objects.get(
                id=document_id, facility=facility
            )
            document.delete()
            return Response({'message': 'Документ удален'})
        except FacilityDocument.DoesNotExist:
            return Response(
                {'error': 'Документ не найден'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Получить документы объекта"""
        facility = self.get_object()
        documents = facility.documents.filter(is_active=True)
        
        # Фильтрация по типу документа
        doc_type = request.query_params.get('type')
        if doc_type:
            documents = documents.filter(type=doc_type)
        
        serializer = FacilityDocumentSerializer(documents, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def update_progress(self, request, pk=None):
        """Обновить прогресс объекта"""
        facility = self.get_object()
        progress = request.data.get('progress')
        
        if progress is None:
            return Response(
                {'error': 'Требуется указать progress'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            progress = int(progress)
            if not 0 <= progress <= 100:
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {'error': 'Прогресс должен быть числом от 0 до 100'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        facility.progress = progress
        
        # Автоматически обновляем статус при 100% прогрессе
        if progress == 100 and facility.status != Facility.Status.COMPLETED:
            facility.status = Facility.Status.COMPLETED
            facility.actual_completion = timezone.now().date()
        
        facility.save()
        
        serializer = self.get_serializer(facility)
        return Response(serializer.data)


class FacilityDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet для управления документами объектов"""
    
    queryset = FacilityDocument.objects.select_related(
        'facility', 'uploaded_by'
    ).filter(is_active=True)
    
    serializer_class = FacilityDocumentSerializer
    parser_classes = [MultiPartParser, FormParser]
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description', 'facility__name']
    filterset_fields = ['type', 'facility', 'facility__project']
    ordering_fields = ['name', 'type', 'uploaded_at']
    ordering = ['-uploaded_at']
    
    def get_permissions(self):
        """Настройка разрешений"""
        if self.action in ['create']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsFacilityResponsibleOrAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Фильтрация документов по правам доступа"""
        user = self.request.user
        queryset = super().get_queryset()
        
        # Администраторы видят все документы
        if user.groups.filter(name='Admins').exists():
            return queryset
        
        # Менеджеры видят документы объектов своих проектов
        if user.groups.filter(name='Managers').exists():
            return queryset.filter(
                Q(facility__project__manager=user) |
                Q(facility__project__team_members=user) |
                Q(facility__responsible_person=user)
            ).distinct()
        
        # Обычные пользователи видят документы объектов проектов, где они участники
        return queryset.filter(
            Q(facility__project__team_members=user) |
            Q(facility__responsible_person=user)
        ).distinct()
    
    def perform_create(self, serializer):
        """Создание документа с указанием загрузившего пользователя"""
        facility_id = self.request.data.get('facility_id')
        if facility_id:
            facility = get_object_or_404(Facility, id=facility_id)
            serializer.save(facility=facility, uploaded_by=self.request.user)
        else:
            serializer.save(uploaded_by=self.request.user)


class ProjectStatisticsView(viewsets.GenericViewSet):
    """Статистика по проектам"""
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """Получить общую статистику по проектам"""
        stats = {
            'total_projects': Project.objects.count(),
            'active_projects': Project.objects.filter(status='active').count(),
            'completed_projects': Project.objects.filter(status='completed').count(),
        }
        return Response(stats)


class FacilityStatisticsView(viewsets.GenericViewSet):
    """Статистика по объектам"""
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """Получить общую статистику по объектам"""
        stats = {
            'total_facilities': Facility.objects.count(),
            'active_facilities': Facility.objects.filter(status='active').count(),
            'completed_facilities': Facility.objects.filter(status='completed').count(),
        }
        return Response(stats)


class ProjectProgressReportView(viewsets.GenericViewSet):
    """Отчет по прогрессу проектов"""
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """Получить отчет по прогрессу проектов"""
        return Response({'message': 'Project progress report'})


class ProjectSearchView(viewsets.GenericViewSet):
    """Поиск проектов"""
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """Поиск проектов"""
        return Response({'message': 'Project search'})


class FacilitySearchView(viewsets.GenericViewSet):
    """Поиск объектов"""
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """Поиск объектов"""
        return Response({'message': 'Facility search'})


class BulkFacilityStatusUpdateView(viewsets.GenericViewSet):
    """Массовое обновление статуса объектов"""
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request):
        """Массовое обновление статуса"""
        return Response({'message': 'Bulk status update'})


class BulkFacilityAssignView(viewsets.GenericViewSet):
    """Массовое назначение ответственных"""
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request):
        """Массовое назначение"""
        return Response({'message': 'Bulk assign'})


class ProjectTemplateView(viewsets.GenericViewSet):
    """Шаблоны проектов"""
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """Получить шаблоны проектов"""
        return Response({'message': 'Project templates'})


class FacilityImportView(viewsets.GenericViewSet):
    """Импорт объектов"""
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request):
        """Импорт объектов"""
        return Response({'message': 'Facility import'})


class FacilityExportView(viewsets.GenericViewSet):
    """Экспорт объектов"""
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """Экспорт объектов"""
        return Response({'message': 'Facility export'})