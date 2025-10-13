from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DefectViewSet

app_name = 'defects'

router = DefaultRouter()
router.register(r'', DefectViewSet)

urlpatterns = [
    path('', include(router.urls)),
]