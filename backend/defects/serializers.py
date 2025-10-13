from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Defect
from projects.models import Task, Facility

User = get_user_model()


class DefectSerializer(serializers.ModelSerializer):
    """Сериализатор для дефектов"""
    
    reported_by_name = serializers.CharField(source='reported_by.get_full_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    facility_name = serializers.CharField(source='facility.name', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Defect
        fields = [
            'id', 'title', 'description', 'facility', 'facility_name',
            'status', 'severity', 'priority', 'reported_by', 'reported_by_name',
            'assigned_to', 'assigned_to_name', 'created_at', 'updated_at',
            'due_date', 'resolved_at', 'location', 'estimated_cost',
            'actual_cost', 'is_overdue'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'reported_by']
    
    def create(self, validated_data):
        """Создание дефекта с автоматическим назначением создателя"""
        validated_data['reported_by'] = self.context['request'].user
        return super().create(validated_data)


class DefectListSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для списка дефектов"""
    
    reported_by_name = serializers.CharField(source='reported_by.get_full_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    facility_name = serializers.CharField(source='facility.name', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Defect
        fields = [
            'id', 'title', 'facility_name', 'status', 'severity', 'priority',
            'reported_by_name', 'assigned_to_name', 'created_at', 'due_date',
            'is_overdue'
        ]


class TaskSerializer(serializers.ModelSerializer):
    """Сериализатор для задач"""
    
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    facility_name = serializers.CharField(source='facility.name', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    progress_percentage = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'project', 'project_name',
            'facility', 'facility_name', 'status', 'priority',
            'assigned_to', 'assigned_to_name', 'created_by', 'created_by_name',
            'due_date', 'completed_at', 'estimated_hours', 'actual_hours',
            'created_at', 'updated_at', 'is_overdue', 'progress_percentage'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def create(self, validated_data):
        """Создание задачи с автоматическим назначением создателя"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class TaskListSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для списка задач"""
    
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    facility_name = serializers.CharField(source='facility.name', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    progress_percentage = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'project_name', 'facility_name', 'status', 'priority',
            'assigned_to_name', 'created_by_name', 'due_date', 'created_at',
            'is_overdue', 'progress_percentage'
        ]


class DefectStatusUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления статуса дефекта"""
    
    class Meta:
        model = Defect
        fields = ['status', 'resolved_at']
        
    def update(self, instance, validated_data):
        """Автоматически устанавливает дату решения при изменении статуса"""
        if validated_data.get('status') == Defect.Status.RESOLVED:
            validated_data['resolved_at'] = timezone.now()
        elif validated_data.get('status') != Defect.Status.RESOLVED:
            validated_data['resolved_at'] = None
        return super().update(instance, validated_data)


class TaskStatusUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления статуса задачи"""
    
    class Meta:
        model = Task
        fields = ['status', 'completed_at']
        
    def update(self, instance, validated_data):
        """Автоматически устанавливает дату завершения при изменении статуса"""
        if validated_data.get('status') == Task.Status.COMPLETED:
            validated_data['completed_at'] = timezone.now()
        elif validated_data.get('status') != Task.Status.COMPLETED:
            validated_data['completed_at'] = None
        return super().update(instance, validated_data)