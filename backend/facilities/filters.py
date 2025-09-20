import django_filters
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from .models import Facility, MaintenanceSchedule


class FacilityFilter(django_filters.FilterSet):
    """Фильтр для объектов недвижимости"""
    
    # Текстовый поиск
    search = django_filters.CharFilter(
        method='filter_search',
        label=_('Поиск')
    )
    
    # Фильтры по основным полям
    facility_type = django_filters.NumberFilter(
        field_name='facility_type',
        label=_('Тип объекта')
    )
    
    project = django_filters.NumberFilter(
        field_name='project',
        label=_('Проект')
    )
    
    status = django_filters.MultipleChoiceFilter(
        choices=Facility.STATUS_CHOICES,
        label=_('Статус')
    )
    
    condition = django_filters.MultipleChoiceFilter(
        choices=Facility.CONDITION_CHOICES,
        label=_('Состояние')
    )
    
    city = django_filters.CharFilter(
        field_name='city',
        lookup_expr='icontains',
        label=_('Город')
    )
    
    region = django_filters.CharFilter(
        field_name='region',
        lookup_expr='icontains',
        label=_('Регион')
    )
    
    manager = django_filters.NumberFilter(
        field_name='manager',
        label=_('Управляющий')
    )
    
    # Фильтры по площади
    total_area_min = django_filters.NumberFilter(
        field_name='total_area',
        lookup_expr='gte',
        label=_('Минимальная общая площадь')
    )
    
    total_area_max = django_filters.NumberFilter(
        field_name='total_area',
        lookup_expr='lte',
        label=_('Максимальная общая площадь')
    )
    
    usable_area_min = django_filters.NumberFilter(
        field_name='usable_area',
        lookup_expr='gte',
        label=_('Минимальная полезная площадь')
    )
    
    usable_area_max = django_filters.NumberFilter(
        field_name='usable_area',
        lookup_expr='lte',
        label=_('Максимальная полезная площадь')
    )
    
    # Фильтры по годам
    construction_year_min = django_filters.NumberFilter(
        field_name='construction_year',
        lookup_expr='gte',
        label=_('Год постройки от')
    )
    
    construction_year_max = django_filters.NumberFilter(
        field_name='construction_year',
        lookup_expr='lte',
        label=_('Год постройки до')
    )
    
    # Фильтры по стоимости
    current_value_min = django_filters.NumberFilter(
        field_name='current_value',
        lookup_expr='gte',
        label=_('Минимальная стоимость')
    )
    
    current_value_max = django_filters.NumberFilter(
        field_name='current_value',
        lookup_expr='lte',
        label=_('Максимальная стоимость')
    )
    
    # Фильтры по датам
    created_after = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='gte',
        label=_('Создан после')
    )
    
    created_before = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='lte',
        label=_('Создан до')
    )
    
    # Специальные фильтры
    has_coordinates = django_filters.BooleanFilter(
        method='filter_has_coordinates',
        label=_('Имеет координаты')
    )
    
    has_defects = django_filters.BooleanFilter(
        method='filter_has_defects',
        label=_('Имеет дефекты')
    )
    
    needs_attention = django_filters.BooleanFilter(
        method='filter_needs_attention',
        label=_('Требует внимания')
    )
    
    has_maintenance = django_filters.BooleanFilter(
        method='filter_has_maintenance',
        label=_('Имеет график обслуживания')
    )
    
    class Meta:
        model = Facility
        fields = {
            'floors_count': ['exact', 'gte', 'lte'],
        }
    
    def filter_search(self, queryset, name, value):
        """Поиск по нескольким полям"""
        if not value:
            return queryset
        
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(address__icontains=value) |
            Q(city__icontains=value) |
            Q(region__icontains=value)
        )
    
    def filter_has_coordinates(self, queryset, name, value):
        """Фильтр по наличию координат"""
        if value is True:
            return queryset.filter(
                latitude__isnull=False,
                longitude__isnull=False
            )
        elif value is False:
            return queryset.filter(
                Q(latitude__isnull=True) |
                Q(longitude__isnull=True)
            )
        return queryset
    
    def filter_has_defects(self, queryset, name, value):
        """Фильтр по наличию дефектов"""
        if value is True:
            return queryset.filter(defects__isnull=False).distinct()
        elif value is False:
            return queryset.filter(defects__isnull=True)
        return queryset
    
    def filter_needs_attention(self, queryset, name, value):
        """Фильтр по необходимости внимания"""
        if value is True:
            return queryset.filter(condition__in=['poor', 'critical'])
        elif value is False:
            return queryset.exclude(condition__in=['poor', 'critical'])
        return queryset
    
    def filter_has_maintenance(self, queryset, name, value):
        """Фильтр по наличию графика обслуживания"""
        if value is True:
            return queryset.filter(maintenance_schedules__isnull=False).distinct()
        elif value is False:
            return queryset.filter(maintenance_schedules__isnull=True)
        return queryset


class MaintenanceScheduleFilter(django_filters.FilterSet):
    """Фильтр для графиков обслуживания"""
    
    # Текстовый поиск
    search = django_filters.CharFilter(
        method='filter_search',
        label=_('Поиск')
    )
    
    # Основные фильтры
    facility = django_filters.NumberFilter(
        field_name='facility',
        label=_('Объект')
    )
    
    facility_type = django_filters.NumberFilter(
        field_name='facility__facility_type',
        label=_('Тип объекта')
    )
    
    project = django_filters.NumberFilter(
        field_name='facility__project',
        label=_('Проект')
    )
    
    frequency = django_filters.MultipleChoiceFilter(
        choices=MaintenanceSchedule.FREQUENCY_CHOICES,
        label=_('Периодичность')
    )
    
    status = django_filters.MultipleChoiceFilter(
        choices=MaintenanceSchedule.STATUS_CHOICES,
        label=_('Статус')
    )
    
    responsible_person = django_filters.NumberFilter(
        field_name='responsible_person',
        label=_('Ответственный')
    )
    
    # Фильтры по датам
    next_maintenance_after = django_filters.DateFilter(
        field_name='next_maintenance_date',
        lookup_expr='gte',
        label=_('Следующее обслуживание после')
    )
    
    next_maintenance_before = django_filters.DateFilter(
        field_name='next_maintenance_date',
        lookup_expr='lte',
        label=_('Следующее обслуживание до')
    )
    
    start_date_after = django_filters.DateFilter(
        field_name='start_date',
        lookup_expr='gte',
        label=_('Дата начала после')
    )
    
    start_date_before = django_filters.DateFilter(
        field_name='start_date',
        lookup_expr='lte',
        label=_('Дата начала до')
    )
    
    # Фильтры по стоимости и времени
    estimated_cost_min = django_filters.NumberFilter(
        field_name='estimated_cost',
        lookup_expr='gte',
        label=_('Минимальная стоимость')
    )
    
    estimated_cost_max = django_filters.NumberFilter(
        field_name='estimated_cost',
        lookup_expr='lte',
        label=_('Максимальная стоимость')
    )
    
    estimated_duration_min = django_filters.NumberFilter(
        field_name='estimated_duration_hours',
        lookup_expr='gte',
        label=_('Минимальная продолжительность (часы)')
    )
    
    estimated_duration_max = django_filters.NumberFilter(
        field_name='estimated_duration_hours',
        lookup_expr='lte',
        label=_('Максимальная продолжительность (часы)')
    )
    
    # Специальные фильтры
    is_overdue = django_filters.BooleanFilter(
        method='filter_is_overdue',
        label=_('Просрочено')
    )
    
    upcoming_days = django_filters.NumberFilter(
        method='filter_upcoming_days',
        label=_('Предстоящие в течение N дней')
    )
    
    city = django_filters.CharFilter(
        field_name='facility__city',
        lookup_expr='icontains',
        label=_('Город объекта')
    )
    
    class Meta:
        model = MaintenanceSchedule
        fields = []
    
    def filter_search(self, queryset, name, value):
        """Поиск по нескольким полям"""
        if not value:
            return queryset
        
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(facility__name__icontains=value) |
            Q(notes__icontains=value)
        )
    
    def filter_is_overdue(self, queryset, name, value):
        """Фильтр по просрочке"""
        from django.utils import timezone
        
        if value is True:
            return queryset.filter(
                next_maintenance_date__lt=timezone.now().date(),
                status='active'
            )
        elif value is False:
            return queryset.filter(
                Q(next_maintenance_date__gte=timezone.now().date()) |
                Q(status__ne='active')
            )
        return queryset
    
    def filter_upcoming_days(self, queryset, name, value):
        """Фильтр по предстоящим обслуживаниям в течение N дней"""
        if not value:
            return queryset
        
        from django.utils import timezone
        from datetime import timedelta
        
        end_date = timezone.now().date() + timedelta(days=int(value))
        
        return queryset.filter(
            next_maintenance_date__gte=timezone.now().date(),
            next_maintenance_date__lte=end_date,
            status='active'
        )