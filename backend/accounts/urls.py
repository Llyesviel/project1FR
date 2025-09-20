from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

from .views import (
    CustomTokenObtainPairView,
    LoginView,
    LogoutView,
    UserViewSet,
    ResetPasswordView,
    ResetPasswordConfirmView,
    user_stats,
)

# Создаем роутер для ViewSet
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

app_name = 'accounts'

urlpatterns = [
    # JWT токены
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Аутентификация
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    
    # Сброс пароля
    path('auth/reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('auth/reset-password/<str:uid>/<str:token>/', 
         ResetPasswordConfirmView.as_view(), name='reset_password_confirm'),
    
    # Статистика
    path('stats/', user_stats, name='user_stats'),
    
    # ViewSet маршруты
    path('', include(router.urls)),
]

# Дополнительные маршруты для удобства
urlpatterns += [
    # Профиль текущего пользователя
    path('profile/', UserViewSet.as_view({'get': 'me', 'put': 'me', 'patch': 'me'}), name='profile'),
    
    # Смена пароля
    path('change-password/', UserViewSet.as_view({'post': 'change_password'}), name='change_password'),
]