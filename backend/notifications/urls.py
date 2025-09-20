from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from . import views

# Основной роутер
router = DefaultRouter()
router.register(r'notifications', views.NotificationViewSet, basename='notification')
router.register(r'templates', views.NotificationTemplateViewSet, basename='notificationtemplate')
router.register(r'settings', views.NotificationSettingsViewSet, basename='notificationsettings')
router.register(r'batches', views.NotificationBatchViewSet, basename='notificationbatch')

# Вложенные роутеры для связанных ресурсов
notifications_router = routers.NestedDefaultRouter(
    router, r'notifications', lookup='notification'
)

app_name = 'notifications'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    path('api/', include(notifications_router.urls)),
    
    # Дополнительные endpoints
    # Stats endpoint is available through NotificationViewSet.stats action
    # path('api/stats/user/<int:user_id>/', views.UserNotificationStatsView.as_view(), name='user-notification-stats'),
    # path('api/export/', views.NotificationExportView.as_view(), name='notification-export'),
    # path('api/import/', views.NotificationImportView.as_view(), name='notification-import'),
    
    # Webhook endpoints
    # path('api/webhooks/delivery/', views.NotificationWebhookView.as_view(), name='notification-webhook'),
    
    # Unsubscribe endpoints
    # path('unsubscribe/<int:user_id>/', views.UnsubscribeView.as_view(), name='unsubscribe'),
    # path('unsubscribe/<int:user_id>/<str:token>/', views.UnsubscribeConfirmView.as_view(), name='unsubscribe-confirm'),
    
    # Real-time endpoints
    # path('api/realtime/connect/', views.RealtimeConnectView.as_view(), name='realtime-connect'),
    # path('api/realtime/disconnect/', views.RealtimeDisconnectView.as_view(), name='realtime-disconnect'),
    
    # Health check
    # path('api/health/', views.NotificationHealthView.as_view(), name='notification-health'),
]

# WebSocket URLs (если используется Django Channels)
websocket_urlpatterns = [
    # path('ws/notifications/', views.NotificationConsumer.as_asgi()),
    # path('ws/notifications/<int:user_id>/', views.UserNotificationConsumer.as_asgi()),
]