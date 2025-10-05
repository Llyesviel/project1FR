from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.shortcuts import render
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

def home_view(request):
    """Главная страница системы управления объектами"""
    return JsonResponse({
        'message': 'Добро пожаловать в систему управления объектами!',
        'version': '1.0.0',
        'endpoints': {
            'admin': '/admin/',
            'api_docs': '/api/docs/',
            'api_redoc': '/api/redoc/',
            'api_schema': '/api/schema/',
            'auth': '/api/auth/',
            'projects': '/api/projects/',
            'facilities': '/api/facilities/',
            'defects': '/api/defects/',
            'notifications': '/api/notifications/',
            'reports': '/api/reports/',
            'bookings': '/api/bookings/',
        }
    })

urlpatterns = [
    # Home page
    path('', home_view, name='home'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API Endpoints
    path('api/auth/', include('accounts.urls')),
    path('api/projects/', include('projects.urls')),
    path('api/facilities/', include('facilities.urls')),
    path('api/defects/', include('defects.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/bookings/', include('bookings.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = "Система управления дефектами"
admin.site.site_title = "Facilities Management"
admin.site.index_title = "Панель администрирования"