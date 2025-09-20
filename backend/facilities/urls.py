from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Создаем роутер для API
router = DefaultRouter()

# Регистрируем ViewSet'ы
router.register(r'facility-types', views.FacilityTypeViewSet, basename='facilitytype')
router.register(r'facilities', views.FacilityViewSet, basename='facility')
router.register(r'facility-images', views.FacilityImageViewSet, basename='facilityimage')
router.register(r'facility-documents', views.FacilityDocumentViewSet, basename='facilitydocument')
router.register(r'maintenance-schedules', views.MaintenanceScheduleViewSet, basename='maintenanceschedule')

# URL patterns
urlpatterns = [
    # API endpoints через роутер
    path('api/', include(router.urls)),
    
    # Дополнительные endpoints для статистики и отчетов
    path('api/statistics/', views.FacilityStatisticsView.as_view({'get': 'list'}), name='facility-statistics'),
    path('api/dashboard/', views.FacilityDashboardView.as_view({'get': 'list'}), name='facility-dashboard'),
    
    # Endpoints для экспорта данных
    path('api/facilities/export/', views.FacilityExportView.as_view({'get': 'list'}), name='facility-export'),
    path('api/maintenance-schedules/export/', views.MaintenanceExportView.as_view({'get': 'list'}), name='maintenance-export'),
    
    # Endpoints для импорта данных
    path('api/facilities/import/', views.FacilityImportView.as_view({'post': 'create'}), name='facility-import'),
    
    # Endpoints для карты
    path('api/facilities/map-data/', views.FacilityMapDataView.as_view({'get': 'list'}), name='facility-map-data'),
    
    # Endpoints для отчетов
    path('api/reports/facilities/', views.FacilityReportView.as_view({'get': 'list'}), name='facility-report'),
    path('api/reports/maintenance/', views.MaintenanceReportView.as_view({'get': 'list'}), name='maintenance-report'),
    
    # Endpoints для обслуживания
    path('api/maintenance/upcoming/', views.UpcomingMaintenanceView.as_view({'get': 'list'}), name='upcoming-maintenance'),
    path('api/maintenance/overdue/', views.OverdueMaintenanceView.as_view({'get': 'list'}), name='overdue-maintenance'),
]

# Добавляем имя приложения для namespace
app_name = 'facilities'