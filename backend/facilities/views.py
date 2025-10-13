from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Prefetch
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from django.http import Http404

from .models import (
    FacilityType,
    Facility,
    FacilityDocument,
    FacilityImage,
    MaintenanceSchedule
)
from .serializers import (
    FacilityTypeSerializer,
    FacilityListSerializer,
    FacilityDetailSerializer,
    FacilityCreateUpdateSerializer,
    FacilityDocumentSerializer,
    FacilityImageSerializer,
    MaintenanceScheduleSerializer
)
from .filters import FacilityFilter, MaintenanceScheduleFilter
from .permissions import FacilityPermission


class FacilityTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для типов объектов недвижимости"""
    
    queryset = FacilityType.objects.filter(is_active=True).annotate(
        facilities_count=Count('facilities')
    )
    serializer_class = FacilityTypeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'facilities_count']
    ordering = ['name']


class FacilityViewSet(viewsets.ModelViewSet):
    """ViewSet для объектов недвижимости"""
    
    permission_classes = [IsAuthenticated, FacilityPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = FacilityFilter
    search_fields = [
        'name',
        'description',
        'address',
        'city',
        'region'
    ]
    ordering_fields = [
        'name',
        'created_at',
        'updated_at',
        'status',
        'condition',
        'city'
    ]
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Получение queryset с оптимизацией запросов"""
        queryset = Facility.objects.select_related(
            'facility_type',
            'project',
            'manager',
            'created_by'
        ).prefetch_related(
            Prefetch(
                'images',
                queryset=FacilityImage.objects.order_by('-is_primary', 'order')
            ),
            'documents',
            'maintenance_schedules'
        )
        
        # Фильтрация по проекту пользователя (если не суперпользователь)
        if not self.request.user.is_superuser:
            from projects.models import ProjectMembership
            user_projects = ProjectMembership.objects.filter(
                user=self.request.user,
                is_active=True
            ).values_list('project_id', flat=True)
            queryset = queryset.filter(project_id__in=user_projects)
        
        return queryset
    
    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        if self.action == 'list':
            return FacilityListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return FacilityCreateUpdateSerializer
        return FacilityDetailSerializer
    
    @action(detail=True, methods=['get'])
    def images(self, request, pk=None):
        """Получение изображений объекта"""
        facility = self.get_object()
        images = facility.images.order_by('-is_primary', 'order')
        serializer = FacilityImageSerializer(images, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def upload_image(self, request, pk=None):
        """Загрузка изображения для объекта"""
        facility = self.get_object()
        serializer = FacilityImageSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save(facility=facility)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Получение документов объекта"""
        facility = self.get_object()
        documents = facility.documents.filter(is_active=True).order_by('-uploaded_at')
        serializer = FacilityDocumentSerializer(
            documents,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def upload_document(self, request, pk=None):
        """Загрузка документа для объекта"""
        facility = self.get_object()
        serializer = FacilityDocumentSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save(facility=facility)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def maintenance_schedules(self, request, pk=None):
        """Получение графиков обслуживания объекта"""
        facility = self.get_object()
        schedules = facility.maintenance_schedules.select_related(
            'responsible_person',
            'created_by'
        ).order_by('next_maintenance_date')
        
        serializer = MaintenanceScheduleSerializer(
            schedules,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def create_maintenance_schedule(self, request, pk=None):
        """Создание графика обслуживания для объекта"""
        facility = self.get_object()
        serializer = MaintenanceScheduleSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save(facility=facility)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def defects(self, request, pk=None):
        """Получение дефектов объекта"""
        facility = self.get_object()
        
        # Импортируем сериализатор дефектов (будет создан позже)
        try:
            from defects.serializers import DefectListSerializer
            defects = facility.defects.select_related(
                'reported_by',
                'assigned_to',
                'facility'
            ).order_by('-created_at')
            
            serializer = DefectListSerializer(
                defects,
                many=True,
                context={'request': request}
            )
            return Response(serializer.data)
        except ImportError:
            return Response({
                'message': _('Модуль дефектов не найден')
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Статистика по объектам"""
        queryset = self.get_queryset()
        
        stats = {
            'total_facilities': queryset.count(),
            'by_status': {},
            'by_condition': {},
            'by_type': {},
            'by_city': {}
        }
        
        # Статистика по статусам
        for choice in Facility.STATUS_CHOICES:
            status_code = choice[0]
            count = queryset.filter(status=status_code).count()
            stats['by_status'][status_code] = {
                'count': count,
                'label': choice[1]
            }
        
        # Статистика по состоянию
        for choice in Facility.CONDITION_CHOICES:
            condition_code = choice[0]
            count = queryset.filter(condition=condition_code).count()
            stats['by_condition'][condition_code] = {
                'count': count,
                'label': choice[1]
            }
        
        # Статистика по типам
        type_stats = queryset.values(
            'facility_type__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        for item in type_stats:
            stats['by_type'][item['facility_type__name']] = item['count']
        
        # Статистика по городам
        city_stats = queryset.values(
            'city'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        for item in city_stats:
            stats['by_city'][item['city']] = item['count']
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def map_data(self, request):
        """Данные для отображения на карте"""
        queryset = self.get_queryset().filter(
            latitude__isnull=False,
            longitude__isnull=False
        )
        
        # Применяем фильтры
        filterset = self.filterset_class(request.GET, queryset=queryset)
        if filterset.is_valid():
            queryset = filterset.qs
        
        map_data = []
        for facility in queryset:
            map_data.append({
                'id': facility.id,
                'name': facility.name,
                'address': facility.address,
                'coordinates': facility.coordinates,
                'status': facility.status,
                'condition': facility.condition,
                'facility_type': facility.facility_type.name,
                'defects_count': facility.get_defects_count(),
                'critical_defects_count': facility.get_critical_defects_count()
            })
        
        return Response(map_data)


class FacilityImageViewSet(viewsets.ModelViewSet):
    """ViewSet для изображений объектов"""
    
    serializer_class = FacilityImageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['facility', 'image_type', 'is_primary']
    ordering_fields = ['order', 'uploaded_at']
    ordering = ['order', '-uploaded_at']
    
    def get_queryset(self):
        """Получение queryset с учетом прав доступа"""
        queryset = FacilityImage.objects.select_related(
            'facility',
            'uploaded_by'
        )
        
        # Фильтрация по проектам пользователя
        if not self.request.user.is_superuser:
            user_projects = self.request.user.project_members.values_list('project_id', flat=True)
            queryset = queryset.filter(facility__project_id__in=user_projects)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def set_primary(self, request, pk=None):
        """Установка изображения как основного"""
        image = self.get_object()
        
        # Убираем флаг основного у других изображений этого объекта
        FacilityImage.objects.filter(
            facility=image.facility,
            is_primary=True
        ).update(is_primary=False)
        
        # Устанавливаем текущее изображение как основное
        image.is_primary = True
        image.save()
        
        serializer = self.get_serializer(image)
        return Response(serializer.data)


class FacilityDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet для документов объектов"""
    
    serializer_class = FacilityDocumentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['facility', 'document_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'document_date', 'expiry_date', 'uploaded_at']
    ordering = ['-uploaded_at']
    
    def get_queryset(self):
        """Получение queryset с учетом прав доступа"""
        queryset = FacilityDocument.objects.select_related(
            'facility',
            'uploaded_by'
        )
        
        # Фильтрация по проектам пользователя
        if not self.request.user.is_superuser:
            user_projects = self.request.user.project_members.values_list('project_id', flat=True)
            queryset = queryset.filter(facility__project_id__in=user_projects)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Документы, срок действия которых истекает в ближайшее время"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Документы, которые истекают в течение 30 дней
        expiry_threshold = timezone.now().date() + timedelta(days=30)
        
        queryset = self.get_queryset().filter(
            expiry_date__isnull=False,
            expiry_date__lte=expiry_threshold,
            is_active=True
        ).order_by('expiry_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expired(self, request):
        """Просроченные документы"""
        from django.utils import timezone
        
        queryset = self.get_queryset().filter(
            expiry_date__isnull=False,
            expiry_date__lt=timezone.now().date(),
            is_active=True
        ).order_by('expiry_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class MaintenanceScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet для графиков обслуживания"""
    
    serializer_class = MaintenanceScheduleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = MaintenanceScheduleFilter
    search_fields = ['name', 'description', 'facility__name']
    ordering_fields = [
        'name',
        'next_maintenance_date',
        'created_at',
        'status'
    ]
    ordering = ['next_maintenance_date']
    
    def get_queryset(self):
        """Получение queryset с учетом прав доступа"""
        queryset = MaintenanceSchedule.objects.select_related(
            'facility',
            'responsible_person',
            'created_by'
        )
        
        # Фильтрация по проектам пользователя
        if not self.request.user.is_superuser:
            user_projects = self.request.user.project_members.values_list('project_id', flat=True)
            queryset = queryset.filter(facility__project_id__in=user_projects)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Просроченные обслуживания"""
        from django.utils import timezone
        
        queryset = self.get_queryset().filter(
            next_maintenance_date__lt=timezone.now().date(),
            status='active'
        ).order_by('next_maintenance_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Предстоящие обслуживания"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Обслуживания в течение следующих 30 дней
        upcoming_threshold = timezone.now().date() + timedelta(days=30)
        
        queryset = self.get_queryset().filter(
            next_maintenance_date__gte=timezone.now().date(),
            next_maintenance_date__lte=upcoming_threshold,
            status='active'
        ).order_by('next_maintenance_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete_maintenance(self, request, pk=None):
        """Отметка о выполнении обслуживания"""
        schedule = self.get_object()
        
        if schedule.status != 'active':
            return Response({
                'error': _('Можно отметить выполнение только для активных графиков')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Обновляем дату следующего обслуживания
        schedule.next_maintenance_date = schedule.calculate_next_maintenance_date()
        schedule.save()
        
        # Здесь можно создать запись о выполненном обслуживании
        # (будет реализовано в модуле maintenance)
        
        serializer = self.get_serializer(schedule)
        return Response({
            'message': _('Обслуживание отмечено как выполненное'),
            'schedule': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def calendar(self, request):
        """Календарь обслуживаний"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Получаем параметры даты из запроса
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            # По умолчанию показываем текущий месяц
            today = timezone.now().date()
            start_date = today.replace(day=1)
            if today.month == 12:
                end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        else:
            from datetime import datetime
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        queryset = self.get_queryset().filter(
            next_maintenance_date__gte=start_date,
            next_maintenance_date__lte=end_date,
            status='active'
        ).order_by('next_maintenance_date')
        
        # Группируем по датам
        calendar_data = {}
        for schedule in queryset:
            date_str = schedule.next_maintenance_date.isoformat()
            if date_str not in calendar_data:
                calendar_data[date_str] = []
            
            calendar_data[date_str].append({
                'id': schedule.id,
                'name': schedule.name,
                'facility': schedule.facility.name,
                'responsible_person': schedule.responsible_person.get_full_name() if schedule.responsible_person else None,
                'estimated_duration_hours': schedule.estimated_duration_hours,
                'is_overdue': schedule.is_overdue
            })
        
        return Response({
            'start_date': start_date,
            'end_date': end_date,
            'calendar': calendar_data
        })


# Дополнительные View классы для статистики и отчетов
class FacilityStatisticsView(viewsets.ViewSet):
    """Статистика по объектам"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Получить статистику по объектам"""
        from django.db.models import Count, Q
        
        total_facilities = Facility.objects.count()
        active_facilities = Facility.objects.filter(status='active').count()
        
        stats = {
            'total_facilities': total_facilities,
            'active_facilities': active_facilities,
            'inactive_facilities': total_facilities - active_facilities,
            'by_status': dict(Facility.objects.values('status').annotate(count=Count('id')).values_list('status', 'count')),
            'by_condition': dict(Facility.objects.values('condition').annotate(count=Count('id')).values_list('condition', 'count')),
            'by_type': dict(Facility.objects.values('facility_type__name').annotate(count=Count('id')).values_list('facility_type__name', 'count'))
        }
        
        return Response(stats)


class FacilityDashboardView(viewsets.ViewSet):
    """Данные для дашборда объектов"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Получить данные для дашборда"""
        return Response({'message': 'Dashboard data'})


class FacilityExportView(viewsets.ViewSet):
    """Экспорт данных объектов"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Экспорт списка объектов"""
        return Response({'message': 'Export facilities'})


class MaintenanceExportView(viewsets.ViewSet):
    """Экспорт данных обслуживания"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Экспорт графиков обслуживания"""
        return Response({'message': 'Export maintenance schedules'})


class FacilityImportView(viewsets.ViewSet):
    """Импорт данных объектов"""
    permission_classes = [IsAuthenticated]
    
    def create(self, request):
        """Импорт объектов из файла"""
        return Response({'message': 'Import facilities'})


class FacilityMapDataView(viewsets.ViewSet):
    """Данные для карты объектов"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Получить данные объектов для отображения на карте"""
        return Response({'message': 'Map data'})


class FacilityReportView(viewsets.ViewSet):
    """Отчеты по объектам"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Генерация отчета по объектам"""
        return Response({'message': 'Facility report'})


class MaintenanceReportView(viewsets.ViewSet):
    """Отчеты по обслуживанию"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Генерация отчета по обслуживанию"""
        return Response({'message': 'Maintenance report'})


class UpcomingMaintenanceView(viewsets.ViewSet):
    """Предстоящее обслуживание"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Получить список предстоящего обслуживания"""
        return Response({'message': 'Upcoming maintenance'})


class OverdueMaintenanceView(viewsets.ViewSet):
    """Просроченное обслуживание"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Получить список просроченного обслуживания"""
        return Response({'message': 'Overdue maintenance'})