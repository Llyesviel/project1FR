from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Создаем роутер для ViewSet
router = DefaultRouter()
router.register(r'projects', views.ProjectViewSet, basename='project')
router.register(r'facilities', views.FacilityViewSet, basename='facility')
router.register(r'documents', views.FacilityDocumentViewSet, basename='document')
router.register(r'tasks', views.TaskViewSet, basename='task')

# URL паттерны
urlpatterns = [
    # API роуты через роутер
    path('', include(router.urls)),
    
    # Дополнительные маршруты для проектов
    path('api/projects/<int:project_id>/members/', 
         views.ProjectViewSet.as_view({'get': 'members', 'post': 'add_member'}), 
         name='project-members'),
    
    path('api/projects/<int:project_id>/members/<int:user_id>/', 
         views.ProjectViewSet.as_view({'delete': 'remove_member', 'patch': 'update_member_role'}), 
         name='project-member-detail'),
    
    path('api/projects/<int:project_id>/statistics/', 
         views.ProjectViewSet.as_view({'get': 'statistics'}), 
         name='project-statistics'),
    
    path('api/projects/<int:project_id>/facilities/', 
         views.ProjectViewSet.as_view({'get': 'facilities'}), 
         name='project-facilities'),
    
    path('api/projects/<int:project_id>/export/', 
         views.ProjectViewSet.as_view({'get': 'export_data'}), 
         name='project-export'),
    
    # Дополнительные маршруты для объектов
    path('api/facilities/<int:facility_id>/documents/', 
         views.FacilityViewSet.as_view({'get': 'documents', 'post': 'upload_document'}), 
         name='facility-documents'),
    
    path('api/facilities/<int:facility_id>/history/', 
         views.FacilityViewSet.as_view({'get': 'history'}), 
         name='facility-history'),
    
    path('api/facilities/<int:facility_id>/update-status/', 
         views.FacilityViewSet.as_view({'patch': 'update_status'}), 
         name='facility-update-status'),
    
    path('api/facilities/by-project/<int:project_id>/', 
         views.FacilityViewSet.as_view({'get': 'by_project'}), 
         name='facilities-by-project'),
    
    # Маршруты для документов
    path('api/documents/<int:document_id>/download/', 
         views.FacilityDocumentViewSet.as_view({'get': 'download'}), 
         name='document-download'),
    
    path('api/documents/<int:document_id>/preview/', 
         views.FacilityDocumentViewSet.as_view({'get': 'preview'}), 
         name='document-preview'),
    
    # Статистика и отчеты
    path('api/statistics/projects/', 
         views.ProjectStatisticsView.as_view({'get': 'list'}), 
         name='projects-statistics'),
    
    path('api/statistics/facilities/', 
         views.FacilityStatisticsView.as_view({'get': 'list'}), 
         name='facilities-statistics'),
    
    path('api/reports/project-progress/', 
         views.ProjectProgressReportView.as_view({'get': 'list'}), 
         name='project-progress-report'),
    
    # Поиск
    path('api/search/projects/', 
         views.ProjectSearchView.as_view({'get': 'list'}), 
         name='search-projects'),
    
    path('api/search/facilities/', 
         views.FacilitySearchView.as_view({'get': 'list'}), 
         name='search-facilities'),
    
    # Массовые операции
    path('api/bulk/facilities/update-status/', 
         views.BulkFacilityStatusUpdateView.as_view({'post': 'create'}), 
         name='bulk-facility-status-update'),
    
    path('api/bulk/facilities/assign-responsible/', 
         views.BulkFacilityAssignView.as_view({'post': 'create'}), 
         name='bulk-facility-assign'),
    
    # Шаблоны и импорт/экспорт
    path('api/templates/project/', 
         views.ProjectTemplateView.as_view({'get': 'list'}), 
         name='project-template'),
    
    path('api/import/facilities/', 
         views.FacilityImportView.as_view({'post': 'create'}), 
         name='facility-import'),
    
    path('api/export/facilities/', 
         views.FacilityExportView.as_view({'get': 'list'}), 
         name='facility-export'),
]

# Добавляем имя приложения для namespace
app_name = 'projects'