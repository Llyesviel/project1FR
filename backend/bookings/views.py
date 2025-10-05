from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Booking
from .serializers import (
    BookingSerializer, BookingCreateSerializer, BookingUpdateSerializer,
    BookingApprovalSerializer, BookingStatsSerializer
)
from projects.models import Facility


class BookingViewSet(viewsets.ModelViewSet):
    """ViewSet для управления бронированиями"""
    queryset = Booking.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'facility', 'user']
    search_fields = ['purpose', 'facility__name', 'user__username', 'user__first_name', 'user__last_name']
    ordering_fields = ['created_at', 'start_time', 'end_time']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        if self.action == 'create':
            return BookingCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return BookingUpdateSerializer
        elif self.action in ['approve', 'reject']:
            return BookingApprovalSerializer
        return BookingSerializer

    def get_queryset(self):
        """Фильтрация queryset в зависимости от роли пользователя"""
        user = self.request.user
        queryset = Booking.objects.select_related('user', 'facility', 'approved_by')
        
        # Администраторы видят все бронирования
        if user.is_staff or user.is_superuser:
            return queryset
        
        # Обычные пользователи видят только свои бронирования
        return queryset.filter(user=user)

    def perform_create(self, serializer):
        """Создание бронирования с текущим пользователем"""
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """Обновление бронирования с проверкой прав"""
        booking = self.get_object()
        user = self.request.user
        
        # Проверяем права на редактирование
        if not (user.is_staff or user == booking.user):
            return Response(
                {'error': 'У вас нет прав для редактирования этого бронирования'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Нельзя редактировать одобренные или отклоненные бронирования
        if booking.status in ['approved', 'rejected']:
            return Response(
                {'error': 'Нельзя редактировать одобренные или отклоненные бронирования'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save()

    def perform_destroy(self, instance):
        """Удаление бронирования с проверкой прав"""
        user = self.request.user
        
        # Проверяем права на удаление
        if not (user.is_staff or user == instance.user):
            return Response(
                {'error': 'У вас нет прав для удаления этого бронирования'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Нельзя удалять активные бронирования
        if instance.is_active:
            return Response(
                {'error': 'Нельзя удалить активное бронирование'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        instance.delete()

    @action(detail=False, methods=['get'])
    def my(self, request):
        """Получить бронирования текущего пользователя"""
        bookings = self.get_queryset().filter(user=request.user)
        
        # Применяем фильтры
        status_filter = request.query_params.get('status')
        if status_filter:
            bookings = bookings.filter(status=status_filter)
        
        facility_filter = request.query_params.get('facility')
        if facility_filter:
            bookings = bookings.filter(facility_id=facility_filter)
        
        # Пагинация
        page = self.paginate_queryset(bookings)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Получить предстоящие бронирования пользователя"""
        now = timezone.now()
        bookings = self.get_queryset().filter(
            user=request.user,
            status='approved',
            start_time__gt=now
        ).order_by('start_time')[:5]
        
        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Получить активные бронирования пользователя"""
        now = timezone.now()
        bookings = self.get_queryset().filter(
            user=request.user,
            status='approved',
            start_time__lte=now,
            end_time__gte=now
        )
        
        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        """Одобрить бронирование (только для администраторов)"""
        booking = self.get_object()
        
        if booking.status != 'pending':
            return Response(
                {'error': 'Можно одобрить только ожидающие бронирования'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем на пересечение с другими одобренными бронированиями
        overlapping = Booking.objects.filter(
            facility=booking.facility,
            status='approved',
            start_time__lt=booking.end_time,
            end_time__gt=booking.start_time
        ).exclude(pk=booking.pk)
        
        if overlapping.exists():
            return Response(
                {'error': 'На это время уже есть одобренное бронирование'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.approve(request.user)
        serializer = self.get_serializer(booking)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def reject(self, request, pk=None):
        """Отклонить бронирование (только для администраторов)"""
        booking = self.get_object()
        serializer = BookingApprovalSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        if booking.status != 'pending':
            return Response(
                {'error': 'Можно отклонить только ожидающие бронирования'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = serializer.validated_data.get('reason', '')
        booking.reject(reason)
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Отменить бронирование"""
        booking = self.get_object()
        user = request.user
        
        # Проверяем права на отмену
        if not (user.is_staff or user == booking.user):
            return Response(
                {'error': 'У вас нет прав для отмены этого бронирования'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status in ['rejected', 'cancelled']:
            return Response(
                {'error': 'Бронирование уже отклонено или отменено'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Нельзя отменять активные бронирования
        if booking.is_active:
            return Response(
                {'error': 'Нельзя отменить активное бронирование'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.cancel()
        serializer = self.get_serializer(booking)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Статистика бронирований"""
        user = request.user
        queryset = self.get_queryset()
        
        # Если не администратор, показываем только статистику пользователя
        if not (user.is_staff or user.is_superuser):
            queryset = queryset.filter(user=user)
        
        now = timezone.now()
        
        stats = {
            'total': queryset.count(),
            'pending': queryset.filter(status='pending').count(),
            'approved': queryset.filter(status='approved').count(),
            'rejected': queryset.filter(status='rejected').count(),
            'cancelled': queryset.filter(status='cancelled').count(),
            'active_now': queryset.filter(
                status='approved',
                start_time__lte=now,
                end_time__gte=now
            ).count(),
            'upcoming': queryset.filter(
                status='approved',
                start_time__gt=now
            ).count(),
        }
        
        serializer = BookingStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def calendar(self, request):
        """Календарь бронирований для объекта"""
        facility_id = request.query_params.get('facility')
        if not facility_id:
            return Response(
                {'error': 'Необходимо указать ID объекта'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            facility = Facility.objects.get(id=facility_id)
        except Facility.DoesNotExist:
            return Response(
                {'error': 'Объект не найден'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Получаем бронирования для объекта
        bookings = Booking.objects.filter(
            facility=facility,
            status__in=['pending', 'approved']
        ).select_related('user')
        
        # Фильтр по дате
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if date_from:
            bookings = bookings.filter(start_time__gte=date_from)
        if date_to:
            bookings = bookings.filter(end_time__lte=date_to)
        
        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)
