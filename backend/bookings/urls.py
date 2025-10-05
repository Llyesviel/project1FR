from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookingViewSet

# Создаем роутер для API
router = DefaultRouter()
router.register(r'bookings', BookingViewSet, basename='booking')

urlpatterns = [
    path('', include(router.urls)),
]

# Дополнительные URL паттерны для специальных эндпоинтов
app_name = 'bookings'