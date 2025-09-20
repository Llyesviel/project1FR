from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import login, logout
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from datetime import datetime
import logging

from .models import User, UserProfile, UserSession
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    UserListSerializer, UserDetailSerializer, LoginSerializer,
    ChangePasswordSerializer, ResetPasswordSerializer,
    ResetPasswordConfirmSerializer, UserSessionSerializer
)
from .permissions import IsOwnerOrAdmin, IsAdminOrManager

logger = logging.getLogger(__name__)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Кастомное представление для получения JWT токенов"""
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Обновляем время последней активности
            serializer = LoginSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                user = serializer.validated_data['user']
                user.last_activity = datetime.now()
                user.save(update_fields=['last_activity'])
                
                # Создаем или обновляем сессию
                session_key = request.session.session_key
                if session_key:
                    UserSession.objects.update_or_create(
                        session_key=session_key,
                        defaults={
                            'user': user,
                            'ip_address': self.get_client_ip(request),
                            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                            'is_active': True
                        }
                    )
                
                logger.info(f'Пользователь {user.email} успешно вошел в систему')
        
        return response
    
    def get_client_ip(self, request):
        """Получение IP адреса клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LoginView(APIView):
    """Представление для входа в систему"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Создаем JWT токены
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            # Обновляем время последней активности
            user.last_activity = datetime.now()
            user.save(update_fields=['last_activity'])
            
            # Логируем вход
            logger.info(f'Пользователь {user.email} успешно вошел в систему')
            
            return Response({
                'access': str(access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """Представление для выхода из системы"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            # Деактивируем сессию
            session_key = request.session.session_key
            if session_key:
                UserSession.objects.filter(
                    session_key=session_key,
                    user=request.user
                ).update(is_active=False)
            
            # Добавляем refresh токен в черный список
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            logger.info(f'Пользователь {request.user.email} вышел из системы')
            
            return Response({
                'message': 'Вы успешно вышли из системы'
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f'Ошибка при выходе из системы: {str(e)}')
            return Response({
                'error': 'Ошибка при выходе из системы'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(ModelViewSet):
    """ViewSet для управления пользователями"""
    
    queryset = User.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'is_active', 'department']
    search_fields = ['email', 'first_name', 'last_name', 'username', 'position']
    ordering_fields = ['created_at', 'last_activity', 'email']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'list':
            return UserListSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer
    
    def get_permissions(self):
        """Настройка прав доступа"""
        if self.action == 'create':
            permission_classes = [IsAdminOrManager]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsOwnerOrAdmin]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Фильтрация queryset в зависимости от роли пользователя"""
        user = self.request.user
        
        if user.is_admin:
            return User.objects.all()
        elif user.is_manager:
            return User.objects.filter(role__in=[User.Role.EXECUTOR, User.Role.VIEWER])
        else:
            return User.objects.filter(id=user.id)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """Получение и обновление профиля текущего пользователя"""
        if request.method == 'GET':
            serializer = UserDetailSerializer(request.user)
            return Response(serializer.data)
        
        elif request.method in ['PUT', 'PATCH']:
            serializer = UserUpdateSerializer(
                request.user,
                data=request.data,
                partial=request.method == 'PATCH'
            )
            
            if serializer.is_valid():
                serializer.save()
                return Response(UserDetailSerializer(request.user).data)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Смена пароля текущего пользователя"""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            logger.info(f'Пользователь {request.user.email} сменил пароль')
            return Response({
                'message': 'Пароль успешно изменен'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def activate(self, request, pk=None):
        """Активация пользователя"""
        user = self.get_object()
        user.is_active = True
        user.save()
        
        logger.info(f'Пользователь {user.email} активирован администратором {request.user.email}')
        
        return Response({
            'message': f'Пользователь {user.get_full_name()} активирован'
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def deactivate(self, request, pk=None):
        """Деактивация пользователя"""
        user = self.get_object()
        
        if user == request.user:
            return Response({
                'error': 'Нельзя деактивировать самого себя'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.is_active = False
        user.save()
        
        # Деактивируем все сессии пользователя
        UserSession.objects.filter(user=user).update(is_active=False)
        
        logger.info(f'Пользователь {user.email} деактивирован администратором {request.user.email}')
        
        return Response({
            'message': f'Пользователь {user.get_full_name()} деактивирован'
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def sessions(self, request, pk=None):
        """Получение сессий пользователя"""
        user = self.get_object()
        
        # Проверяем права доступа
        if not (request.user == user or request.user.is_admin):
            return Response({
                'error': 'Недостаточно прав доступа'
            }, status=status.HTTP_403_FORBIDDEN)
        
        sessions = UserSession.objects.filter(user=user).order_by('-last_activity')
        serializer = UserSessionSerializer(sessions, many=True)
        
        return Response(serializer.data)


class ResetPasswordView(APIView):
    """Представление для сброса пароля"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email, is_active=True)
            
            # Генерируем токен для сброса пароля
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Формируем ссылку для сброса
            reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
            
            # Отправляем email
            subject = 'Сброс пароля в системе управления объектами'
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'reset_url': reset_url,
                'site_name': 'Система управления объектами'
            })
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    html_message=message
                )
                
                logger.info(f'Отправлена ссылка для сброса пароля на {email}')
                
                return Response({
                    'message': 'Ссылка для сброса пароля отправлена на ваш email'
                }, status=status.HTTP_200_OK)
            
            except Exception as e:
                logger.error(f'Ошибка отправки email: {str(e)}')
                return Response({
                    'error': 'Ошибка отправки email'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordConfirmView(APIView):
    """Представление для подтверждения сброса пароля"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, uid, token):
        try:
            # Декодируем uid
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
            
            # Проверяем токен
            if not default_token_generator.check_token(user, token):
                return Response({
                    'error': 'Недействительная ссылка для сброса пароля'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = ResetPasswordConfirmSerializer(data=request.data)
            
            if serializer.is_valid():
                # Устанавливаем новый пароль
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                
                # Деактивируем все сессии пользователя
                UserSession.objects.filter(user=user).update(is_active=False)
                
                logger.info(f'Пользователь {user.email} сбросил пароль')
                
                return Response({
                    'message': 'Пароль успешно изменен'
                }, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({
                'error': 'Недействительная ссылка для сброса пароля'
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats(request):
    """Статистика пользователей (только для администраторов)"""
    if not request.user.is_admin:
        return Response({
            'error': 'Недостаточно прав доступа'
        }, status=status.HTTP_403_FORBIDDEN)
    
    stats = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'inactive_users': User.objects.filter(is_active=False).count(),
        'users_by_role': {
            'admins': User.objects.filter(role=User.Role.ADMIN).count(),
            'managers': User.objects.filter(role=User.Role.MANAGER).count(),
            'executors': User.objects.filter(role=User.Role.EXECUTOR).count(),
            'viewers': User.objects.filter(role=User.Role.VIEWER).count(),
        },
        'active_sessions': UserSession.objects.filter(is_active=True).count(),
    }
    
    return Response(stats)