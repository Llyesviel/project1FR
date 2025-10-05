from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Создаем роутер для ViewSet
router = DefaultRouter()
router.register(r'stats', views.DashboardStatsViewSet, basename='stats')

app_name = 'reports'

urlpatterns = [
    # API роуты через роутер
    path('api/', include(router.urls)),
    
    # Дополнительные endpoints
    path('api/stats/dashboard/', views.dashboard_stats, name='dashboard-stats'),
]