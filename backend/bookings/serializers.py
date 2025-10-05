from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Booking
from projects.models import Facility


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя в бронированиях"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name', 'email']
        
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class FacilitySerializer(serializers.ModelSerializer):
    """Сериализатор для объекта в бронированиях"""
    
    class Meta:
        model = Facility
        fields = ['id', 'name', 'location', 'capacity', 'status']


class BookingSerializer(serializers.ModelSerializer):
    """Основной сериализатор для бронирований"""
    user_details = UserSerializer(source='user', read_only=True)
    facility_details = FacilitySerializer(source='facility', read_only=True)
    approved_by_details = UserSerializer(source='approved_by', read_only=True)
    duration = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    is_upcoming = serializers.ReadOnlyField()
    
    class Meta:
        model = Booking
        fields = [
            'id', 'facility', 'user', 'start_time', 'end_time', 'purpose', 
            'status', 'created_at', 'updated_at', 'approved_by', 'approved_at',
            'rejection_reason', 'user_details', 'facility_details', 
            'approved_by_details', 'duration', 'is_active', 'is_upcoming'
        ]
        read_only_fields = ['user', 'approved_by', 'approved_at', 'created_at', 'updated_at']

    def validate(self, data):
        """Валидация данных бронирования"""
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        facility = data.get('facility')
        
        # Проверка времени
        if start_time and end_time:
            if start_time >= end_time:
                raise serializers.ValidationError(
                    "Время окончания должно быть позже времени начала"
                )
            
            if start_time < timezone.now():
                raise serializers.ValidationError(
                    "Нельзя создать бронирование на прошедшее время"
                )
        
        # Проверка на пересечение бронирований
        if facility and start_time and end_time:
            overlapping_bookings = Booking.objects.filter(
                facility=facility,
                status__in=['pending', 'approved'],
                start_time__lt=end_time,
                end_time__gt=start_time
            )
            
            # Исключаем текущее бронирование при обновлении
            if self.instance:
                overlapping_bookings = overlapping_bookings.exclude(pk=self.instance.pk)
            
            if overlapping_bookings.exists():
                raise serializers.ValidationError(
                    "На это время уже есть бронирование для данного объекта"
                )
        
        return data

    def create(self, validated_data):
        """Создание бронирования"""
        # Устанавливаем текущего пользователя
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class BookingCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания бронирования"""
    
    class Meta:
        model = Booking
        fields = ['facility', 'start_time', 'end_time', 'purpose']

    def validate(self, data):
        """Валидация данных при создании"""
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        facility = data.get('facility')
        
        # Проверка времени
        if start_time and end_time:
            if start_time >= end_time:
                raise serializers.ValidationError(
                    "Время окончания должно быть позже времени начала"
                )
            
            if start_time < timezone.now():
                raise serializers.ValidationError(
                    "Нельзя создать бронирование на прошедшее время"
                )
        
        # Проверка на пересечение бронирований
        if facility and start_time and end_time:
            overlapping_bookings = Booking.objects.filter(
                facility=facility,
                status__in=['pending', 'approved'],
                start_time__lt=end_time,
                end_time__gt=start_time
            )
            
            if overlapping_bookings.exists():
                raise serializers.ValidationError(
                    "На это время уже есть бронирование для данного объекта"
                )
        
        return data

    def create(self, validated_data):
        """Создание бронирования с текущим пользователем"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class BookingUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления бронирования"""
    
    class Meta:
        model = Booking
        fields = ['start_time', 'end_time', 'purpose']

    def validate(self, data):
        """Валидация при обновлении"""
        start_time = data.get('start_time', self.instance.start_time)
        end_time = data.get('end_time', self.instance.end_time)
        
        # Проверка времени
        if start_time >= end_time:
            raise serializers.ValidationError(
                "Время окончания должно быть позже времени начала"
            )
        
        if start_time < timezone.now():
            raise serializers.ValidationError(
                "Нельзя изменить бронирование на прошедшее время"
            )
        
        # Проверка на пересечение бронирований
        overlapping_bookings = Booking.objects.filter(
            facility=self.instance.facility,
            status__in=['pending', 'approved'],
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exclude(pk=self.instance.pk)
        
        if overlapping_bookings.exists():
            raise serializers.ValidationError(
                "На это время уже есть бронирование для данного объекта"
            )
        
        return data


class BookingApprovalSerializer(serializers.Serializer):
    """Сериализатор для одобрения/отклонения бронирования"""
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data['action'] == 'reject' and not data.get('reason'):
            raise serializers.ValidationError(
                "При отклонении бронирования необходимо указать причину"
            )
        return data


class BookingStatsSerializer(serializers.Serializer):
    """Сериализатор для статистики бронирований"""
    total = serializers.IntegerField()
    pending = serializers.IntegerField()
    approved = serializers.IntegerField()
    rejected = serializers.IntegerField()
    cancelled = serializers.IntegerField()
    active_now = serializers.IntegerField()
    upcoming = serializers.IntegerField()