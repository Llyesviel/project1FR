from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType

from .models import (
    Notification, 
    NotificationTemplate, 
    NotificationSettings, 
    NotificationBatch
)
from .serializers import (
    NotificationSerializer,
    NotificationCreateSerializer,
    NotificationUpdateSerializer,
    NotificationTemplateSerializer,
    NotificationSettingsSerializer,
    NotificationBatchSerializer,
    NotificationStatsSerializer,
    BulkNotificationActionSerializer,
    NotificationPreferencesSerializer
)
from .permissions import (
    IsOwnerOrAdmin,
    IsNotificationRecipientOrAdmin,
    CanManageNotifications
)
from .filters import NotificationFilter, NotificationTemplateFilter
from .tasks import send_notification_batch

User = get_user_model()


class NotificationPagination(PageNumberPagination):
    """Пагинация для уведомлений"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet для управления уведомлениями"""
    
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = NotificationPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = NotificationFilter
    search_fields = ['title', 'message']
    ordering_fields = ['created_at', 'priority', 'is_read']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Получить queryset уведомлений"""
        user = self.request.user
        
        if user.is_staff and self.action in ['list', 'retrieve']:
            # Администраторы могут видеть все уведомления
            queryset = Notification.objects.all()
        else:
            # Обычные пользователи видят только свои уведомления
            queryset = Notification.objects.filter(recipient=user)
        
        return queryset.select_related(
            'recipient', 'sender', 'content_type'
        ).prefetch_related('content_object')
    
    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        if self.action == 'create':
            return NotificationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return NotificationUpdateSerializer
        return NotificationSerializer
    
    def get_permissions(self):
        """Получить разрешения в зависимости от действия"""
        if self.action == 'create':
            permission_classes = [CanManageNotifications]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsNotificationRecipientOrAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Создание уведомления"""
        serializer.save(sender=self.request.user)
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Получить непрочитанные уведомления"""
        queryset = self.get_queryset().filter(is_read=False)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Получить статистику уведомлений"""
        user = request.user
        queryset = self.get_queryset()
        
        # Базовая статистика
        total = queryset.count()
        unread = queryset.filter(is_read=False).count()
        read = queryset.filter(is_read=True).count()
        expired = queryset.filter(
            expires_at__lt=timezone.now(),
            expires_at__isnull=False
        ).count()
        
        # Статистика по типам
        by_type = dict(queryset.values('notification_type').annotate(
            count=Count('id')
        ).values_list('notification_type', 'count'))
        
        # Статистика по категориям
        by_category = dict(queryset.values('category').annotate(
            count=Count('id')
        ).values_list('category', 'count'))
        
        # Статистика по приоритету
        by_priority = dict(queryset.values('priority').annotate(
            count=Count('id')
        ).values_list('priority', 'count'))
        
        # Статистика по времени
        now = timezone.now()
        today = queryset.filter(created_at__date=now.date()).count()
        week = queryset.filter(created_at__gte=now - timedelta(days=7)).count()
        month = queryset.filter(created_at__gte=now - timedelta(days=30)).count()
        
        # Процентные показатели
        read_rate = (read / total * 100) if total > 0 else 0
        
        # Среднее время ответа (в часах)
        read_notifications = queryset.filter(is_read=True, read_at__isnull=False)
        response_times = []
        for notification in read_notifications:
            if notification.read_at and notification.created_at:
                delta = notification.read_at - notification.created_at
                response_times.append(delta.total_seconds() / 3600)  # в часах
        
        response_time_avg = sum(response_times) / len(response_times) if response_times else 0
        
        stats_data = {
            'total_notifications': total,
            'unread_notifications': unread,
            'read_notifications': read,
            'expired_notifications': expired,
            'by_type': by_type,
            'by_category': by_category,
            'by_priority': by_priority,
            'today_notifications': today,
            'week_notifications': week,
            'month_notifications': month,
            'read_rate': round(read_rate, 2),
            'response_time_avg': round(response_time_avg, 2)
        }
        
        serializer = NotificationStatsSerializer(stats_data)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Отметить уведомление как прочитанное"""
        notification = self.get_object()
        
        if not notification.is_read:
            notification.mark_as_read()
            return Response({'status': 'marked as read'})
        
        return Response(
            {'error': 'Уведомление уже прочитано'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def mark_unread(self, request, pk=None):
        """Отметить уведомление как непрочитанное"""
        notification = self.get_object()
        
        if notification.is_read:
            notification.is_read = False
            notification.read_at = None
            notification.save(update_fields=['is_read', 'read_at'])
            return Response({'status': 'marked as unread'})
        
        return Response(
            {'error': 'Уведомление уже непрочитано'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Отметить все уведомления как прочитанные"""
        queryset = self.get_queryset().filter(is_read=False)
        count = queryset.update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'status': 'success',
            'marked_count': count
        })
    
    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Массовые действия с уведомлениями"""
        serializer = BulkNotificationActionSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        notification_ids = serializer.validated_data['notification_ids']
        action_type = serializer.validated_data['action']
        
        queryset = self.get_queryset().filter(id__in=notification_ids)
        
        if action_type == 'mark_read':
            count = queryset.filter(is_read=False).update(
                is_read=True,
                read_at=timezone.now()
            )
            message = f'Отмечено как прочитанные: {count}'
        
        elif action_type == 'mark_unread':
            count = queryset.filter(is_read=True).update(
                is_read=False,
                read_at=None
            )
            message = f'Отмечено как непрочитанные: {count}'
        
        elif action_type == 'delete':
            count = queryset.count()
            queryset.delete()
            message = f'Удалено уведомлений: {count}'
        
        return Response({
            'status': 'success',
            'message': message,
            'affected_count': count
        })
    
    @action(detail=False, methods=['delete'])
    def clear_read(self, request):
        """Очистить все прочитанные уведомления"""
        queryset = self.get_queryset().filter(is_read=True)
        count = queryset.count()
        queryset.delete()
        
        return Response({
            'status': 'success',
            'deleted_count': count
        })
    
    @action(detail=False, methods=['delete'])
    def clear_expired(self, request):
        """Очистить просроченные уведомления"""
        queryset = self.get_queryset().filter(
            expires_at__lt=timezone.now(),
            expires_at__isnull=False
        )
        count = queryset.count()
        queryset.delete()
        
        return Response({
            'status': 'success',
            'deleted_count': count
        })


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet для управления шаблонами уведомлений"""
    
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [CanManageNotifications]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = NotificationTemplateFilter
    search_fields = ['name', 'title_template', 'message_template']
    ordering_fields = ['name', 'created_at', 'notification_type']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Дублировать шаблон"""
        template = self.get_object()
        
        # Создаем копию
        new_template = NotificationTemplate.objects.create(
            name=f"{template.name} (копия)",
            title_template=template.title_template,
            message_template=template.message_template,
            notification_type=template.notification_type,
            category=template.category,
            priority=template.priority,
            default_expires_days=template.default_expires_days,
            is_active=False  # Копия неактивна по умолчанию
        )
        
        serializer = self.get_serializer(new_template)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def test_render(self, request, pk=None):
        """Тестировать рендеринг шаблона"""
        template = self.get_object()
        context = request.data.get('context', {})
        
        try:
            rendered_title = template.render_title(context)
            rendered_message = template.render_message(context)
            
            return Response({
                'title': rendered_title,
                'message': rendered_message,
                'context_used': context
            })
        except Exception as e:
            return Response(
                {'error': f'Ошибка рендеринга: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class NotificationSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet для управления настройками уведомлений"""
    
    serializer_class = NotificationSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Получить настройки пользователя"""
        return NotificationSettings.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Получить или создать настройки пользователя"""
        settings, created = NotificationSettings.objects.get_or_create(
            user=self.request.user
        )
        return settings
    
    def list(self, request):
        """Получить настройки пользователя"""
        settings = self.get_object()
        serializer = self.get_serializer(settings)
        return Response(serializer.data)
    
    def create(self, request):
        """Создание настроек не разрешено через API"""
        return Response(
            {'error': 'Настройки создаются автоматически'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    def update(self, request, pk=None):
        """Обновить настройки"""
        settings = self.get_object()
        serializer = self.get_serializer(settings, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    def partial_update(self, request, pk=None):
        """Частично обновить настройки"""
        settings = self.get_object()
        serializer = self.get_serializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def quick_setup(self, request):
        """Быстрая настройка предпочтений"""
        serializer = NotificationPreferencesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        settings = self.get_object()
        data = serializer.validated_data
        
        # Применяем быстрые настройки
        if data.get('enable_all'):
            settings.email_notifications = True
            settings.push_notifications = True
            settings.project_notifications = True
            settings.facility_notifications = True
            settings.document_notifications = True
            settings.security_notifications = True
            settings.low_priority_notifications = True
            settings.normal_priority_notifications = True
            settings.high_priority_notifications = True
            settings.urgent_priority_notifications = True
        
        elif data.get('disable_all'):
            settings.email_notifications = False
            settings.push_notifications = False
            settings.project_notifications = False
            settings.facility_notifications = False
            settings.document_notifications = False
            settings.security_notifications = False
            settings.low_priority_notifications = False
            settings.normal_priority_notifications = False
            settings.high_priority_notifications = False
            settings.urgent_priority_notifications = False
        
        # Настройки по категориям
        categories = data.get('categories', [])
        if categories:
            settings.project_notifications = 'project' in categories
            settings.facility_notifications = 'facility' in categories
            settings.document_notifications = 'document' in categories
            settings.security_notifications = 'security' in categories
        
        # Настройки по приоритету
        priorities = data.get('priorities', [])
        if priorities:
            settings.low_priority_notifications = 'low' in priorities
            settings.normal_priority_notifications = 'normal' in priorities
            settings.high_priority_notifications = 'high' in priorities
            settings.urgent_priority_notifications = 'urgent' in priorities
        
        settings.save()
        
        response_serializer = self.get_serializer(settings)
        return Response(response_serializer.data)


class NotificationBatchViewSet(viewsets.ModelViewSet):
    """ViewSet для управления пакетами уведомлений"""
    
    queryset = NotificationBatch.objects.all()
    serializer_class = NotificationBatchSerializer
    permission_classes = [CanManageNotifications]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['created_at', 'sent_at', 'total_recipients']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Получить queryset пакетов"""
        return self.queryset.select_related(
            'template', 'created_by'
        ).prefetch_related('recipients')
    
    def perform_create(self, serializer):
        """Создание пакета уведомлений"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """Отправить пакет уведомлений"""
        batch = self.get_object()
        
        if batch.is_sent:
            return Response(
                {'error': 'Пакет уже отправлен'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Запускаем асинхронную задачу отправки
        try:
            send_notification_batch.delay(batch.id)
            return Response({
                'status': 'success',
                'message': 'Пакет поставлен в очередь на отправку'
            })
        except Exception as e:
            return Response(
                {'error': f'Ошибка при постановке в очередь: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """Предварительный просмотр пакета"""
        batch = self.get_object()
        
        # Берем первого получателя для примера
        recipient = batch.recipients.first()
        if not recipient:
            return Response(
                {'error': 'Нет получателей в пакете'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Создаем контекст для рендеринга
            context = batch.context_data.copy() if batch.context_data else {}
            context.update({
                'user': recipient,
                'recipient': recipient,
                'batch': batch
            })
            
            # Рендерим шаблон
            title = batch.template.render_title(context)
            message = batch.template.render_message(context)
            
            return Response({
                'title': title,
                'message': message,
                'recipient_example': {
                    'id': recipient.id,
                    'username': recipient.username,
                    'email': recipient.email,
                    'full_name': recipient.get_full_name()
                },
                'context_used': context
            })
        except Exception as e:
            return Response(
                {'error': f'Ошибка рендеринга: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Статистика пакетов уведомлений"""
        queryset = self.get_queryset()
        
        total_batches = queryset.count()
        sent_batches = queryset.filter(is_sent=True).count()
        pending_batches = queryset.filter(is_sent=False).count()
        
        # Статистика по отправкам
        total_recipients = queryset.aggregate(
            total=Count('recipients')
        )['total'] or 0
        
        successful_sends = queryset.aggregate(
            total=Count('successful_sends')
        )['total'] or 0
        
        failed_sends = queryset.aggregate(
            total=Count('failed_sends')
        )['total'] or 0
        
        success_rate = (successful_sends / total_recipients * 100) if total_recipients > 0 else 0
        
        return Response({
            'total_batches': total_batches,
            'sent_batches': sent_batches,
            'pending_batches': pending_batches,
            'total_recipients': total_recipients,
            'successful_sends': successful_sends,
            'failed_sends': failed_sends,
            'success_rate': round(success_rate, 2)
        })