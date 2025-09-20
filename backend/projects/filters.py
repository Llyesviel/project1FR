import django_filters
from django_filters import rest_framework as filters
from .models import Project
from facilities.models import Facility


class ProjectFilter(filters.FilterSet):
    """Фильтр для проектов"""
    name = filters.CharFilter(lookup_expr='icontains')
    status = filters.ChoiceFilter(choices=[])
    created_at = filters.DateFromToRangeFilter()
    
    class Meta:
        model = Project
        fields = ['name', 'status', 'created_at']


class FacilityFilter(filters.FilterSet):
    """Фильтр для объектов"""
    name = filters.CharFilter(lookup_expr='icontains')
    facility_type = filters.ChoiceFilter(choices=[])
    address = filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = Facility
        fields = ['name', 'facility_type', 'address']