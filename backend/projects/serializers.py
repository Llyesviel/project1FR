from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import Project, ProjectMembership, Facility, FacilityDocument

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Базовый сериализатор пользователя для вложенных объектов"""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name']
        read_only_fields = ['id', 'username', 'email', 'full_name']


class ProjectMembershipSerializer(serializers.ModelSerializer):
    """Сериализатор для участия в проекте"""
    
    user = UserBasicSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = ProjectMembership
        fields = [
            'id', 'user', 'user_id', 'role', 'role_display',
            'joined_at', 'left_at', 'is_active'
        ]
        read_only_fields = ['id', 'joined_at']
    
    def validate_user_id(self, value):
        """Валидация пользователя"""
        try:
            user = User.objects.get(id=value)
            if not user.is_active:
                raise serializers.ValidationError('Пользователь неактивен')
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError('Пользователь не найден')


class FacilityBasicSerializer(serializers.ModelSerializer):
    """Базовый сериализатор объекта для списков"""
    
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    responsible_person = UserBasicSerializer(read_only=True)
    defects_count = serializers.IntegerField(source='get_defects_count', read_only=True)
    open_defects_count = serializers.IntegerField(source='get_open_defects_count', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Facility
        fields = [
            'id', 'code', 'name', 'type', 'type_display',
            'status', 'status_display', 'progress',
            'responsible_person', 'defects_count', 'open_defects_count',
            'construction_end', 'is_overdue'
        ]


class ProjectListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка проектов"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    manager = UserBasicSerializer(read_only=True)
    team_count = serializers.IntegerField(source='get_team_count', read_only=True)
    facilities_count = serializers.IntegerField(source='get_facilities_count', read_only=True)
    defects_count = serializers.IntegerField(source='get_defects_count', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    duration_planned = serializers.IntegerField(read_only=True)
    duration_actual = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'id', 'code', 'name', 'status', 'status_display',
            'priority', 'priority_display', 'progress',
            'manager', 'team_count', 'facilities_count', 'defects_count',
            'start_date', 'end_date', 'is_overdue',
            'duration_planned', 'duration_actual', 'created_at'
        ]


class ProjectDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор проекта"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    manager = UserBasicSerializer(read_only=True)
    created_by = UserBasicSerializer(read_only=True)
    team_members = ProjectMembershipSerializer(source='projectmembership_set', many=True, read_only=True)
    facilities = FacilityBasicSerializer(many=True, read_only=True)
    
    # Статистика
    team_count = serializers.IntegerField(source='get_team_count', read_only=True)
    facilities_count = serializers.IntegerField(source='get_facilities_count', read_only=True)
    defects_count = serializers.IntegerField(source='get_defects_count', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    duration_planned = serializers.IntegerField(read_only=True)
    duration_actual = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'id', 'code', 'name', 'description', 'client',
            'status', 'status_display', 'priority', 'priority_display',
            'progress', 'budget', 'location',
            'coordinates_lat', 'coordinates_lng',
            'start_date', 'end_date', 'actual_start_date', 'actual_end_date',
            'manager', 'created_by', 'team_members', 'facilities',
            'team_count', 'facilities_count', 'defects_count',
            'is_overdue', 'duration_planned', 'duration_actual',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_by', 'created_at', 'updated_at',
            'team_count', 'facilities_count', 'defects_count',
            'is_overdue', 'duration_planned', 'duration_actual'
        ]


class ProjectCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления проекта"""
    
    manager_id = serializers.UUIDField(write_only=True, required=False)
    team_members_data = ProjectMembershipSerializer(many=True, write_only=True, required=False)
    
    class Meta:
        model = Project
        fields = [
            'code', 'name', 'description', 'client',
            'status', 'priority', 'progress', 'budget',
            'location', 'coordinates_lat', 'coordinates_lng',
            'start_date', 'end_date', 'actual_start_date', 'actual_end_date',
            'manager_id', 'team_members_data', 'is_active'
        ]
    
    def validate_code(self, value):
        """Валидация уникальности кода проекта"""
        if self.instance:
            # При обновлении исключаем текущий объект
            if Project.objects.exclude(id=self.instance.id).filter(code=value).exists():
                raise serializers.ValidationError('Проект с таким кодом уже существует')
        else:
            # При создании
            if Project.objects.filter(code=value).exists():
                raise serializers.ValidationError('Проект с таким кодом уже существует')
        return value
    
    def validate_manager_id(self, value):
        """Валидация менеджера проекта"""
        if value:
            try:
                user = User.objects.get(id=value)
                if not user.is_active:
                    raise serializers.ValidationError('Пользователь неактивен')
                # Проверяем роль пользователя
                if not user.groups.filter(name__in=['Managers', 'Admins']).exists():
                    raise serializers.ValidationError('Пользователь не может быть менеджером проекта')
                return value
            except User.DoesNotExist:
                raise serializers.ValidationError('Пользователь не найден')
        return value
    
    def validate(self, attrs):
        """Общая валидация"""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                'end_date': 'Дата окончания не может быть раньше даты начала'
            })
        
        actual_start = attrs.get('actual_start_date')
        actual_end = attrs.get('actual_end_date')
        
        if actual_start and actual_end and actual_start > actual_end:
            raise serializers.ValidationError({
                'actual_end_date': 'Фактическая дата окончания не может быть раньше фактической даты начала'
            })
        
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        """Создание проекта с участниками команды"""
        team_members_data = validated_data.pop('team_members_data', [])
        manager_id = validated_data.pop('manager_id', None)
        
        if manager_id:
            validated_data['manager_id'] = manager_id
        
        # Устанавливаем создателя
        validated_data['created_by'] = self.context['request'].user
        
        project = Project.objects.create(**validated_data)
        
        # Добавляем участников команды
        for member_data in team_members_data:
            user_id = member_data.pop('user_id')
            ProjectMembership.objects.create(
                project=project,
                user_id=user_id,
                **member_data
            )
        
        return project
    
    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновление проекта"""
        team_members_data = validated_data.pop('team_members_data', None)
        manager_id = validated_data.pop('manager_id', None)
        
        if manager_id:
            validated_data['manager_id'] = manager_id
        
        # Обновляем основные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Обновляем участников команды, если данные переданы
        if team_members_data is not None:
            # Удаляем существующих участников
            instance.projectmembership_set.all().delete()
            
            # Добавляем новых участников
            for member_data in team_members_data:
                user_id = member_data.pop('user_id')
                ProjectMembership.objects.create(
                    project=instance,
                    user_id=user_id,
                    **member_data
                )
        
        return instance


class FacilityDocumentSerializer(serializers.ModelSerializer):
    """Сериализатор для документов объекта"""
    
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    uploaded_by = UserBasicSerializer(read_only=True)
    file_size = serializers.IntegerField(source='get_file_size', read_only=True)
    file_extension = serializers.CharField(source='get_file_extension', read_only=True)
    
    class Meta:
        model = FacilityDocument
        fields = [
            'id', 'name', 'description', 'type', 'type_display',
            'file', 'version', 'uploaded_by', 'uploaded_at',
            'file_size', 'file_extension', 'is_active'
        ]
        read_only_fields = ['id', 'uploaded_by', 'uploaded_at', 'file_size', 'file_extension']
    
    def create(self, validated_data):
        """Создание документа"""
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)


class FacilityListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка объектов"""
    
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    project = ProjectListSerializer(read_only=True)
    responsible_person = UserBasicSerializer(read_only=True)
    defects_count = serializers.IntegerField(source='get_defects_count', read_only=True)
    open_defects_count = serializers.IntegerField(source='get_open_defects_count', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    construction_duration_planned = serializers.IntegerField(read_only=True)
    construction_duration_actual = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Facility
        fields = [
            'id', 'code', 'name', 'type', 'type_display',
            'status', 'status_display', 'progress',
            'project', 'responsible_person',
            'defects_count', 'open_defects_count',
            'construction_start', 'construction_end', 'actual_completion',
            'is_overdue', 'construction_duration_planned', 'construction_duration_actual',
            'created_at'
        ]


class FacilityDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор объекта"""
    
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    project = ProjectListSerializer(read_only=True)
    responsible_person = UserBasicSerializer(read_only=True)
    created_by = UserBasicSerializer(read_only=True)
    documents = FacilityDocumentSerializer(many=True, read_only=True)
    
    # Статистика
    defects_count = serializers.IntegerField(source='get_defects_count', read_only=True)
    open_defects_count = serializers.IntegerField(source='get_open_defects_count', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    construction_duration_planned = serializers.IntegerField(read_only=True)
    construction_duration_actual = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Facility
        fields = [
            'id', 'code', 'name', 'description', 'type', 'type_display',
            'status', 'status_display', 'progress',
            'floor_count', 'area', 'volume', 'location',
            'coordinates_lat', 'coordinates_lng',
            'project', 'responsible_person', 'created_by',
            'construction_start', 'construction_end', 'actual_completion',
            'documents', 'defects_count', 'open_defects_count',
            'is_overdue', 'construction_duration_planned', 'construction_duration_actual',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_by', 'created_at', 'updated_at',
            'defects_count', 'open_defects_count', 'is_overdue',
            'construction_duration_planned', 'construction_duration_actual'
        ]


class FacilityCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления объекта"""
    
    project_id = serializers.UUIDField(write_only=True)
    responsible_person_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = Facility
        fields = [
            'code', 'name', 'description', 'type', 'status', 'progress',
            'floor_count', 'area', 'volume', 'location',
            'coordinates_lat', 'coordinates_lng',
            'project_id', 'responsible_person_id',
            'construction_start', 'construction_end', 'actual_completion',
            'is_active'
        ]
    
    def validate_project_id(self, value):
        """Валидация проекта"""
        try:
            project = Project.objects.get(id=value)
            if not project.is_active:
                raise serializers.ValidationError('Проект неактивен')
            return value
        except Project.DoesNotExist:
            raise serializers.ValidationError('Проект не найден')
    
    def validate_responsible_person_id(self, value):
        """Валидация ответственного лица"""
        if value:
            try:
                user = User.objects.get(id=value)
                if not user.is_active:
                    raise serializers.ValidationError('Пользователь неактивен')
                return value
            except User.DoesNotExist:
                raise serializers.ValidationError('Пользователь не найден')
        return value
    
    def validate(self, attrs):
        """Общая валидация"""
        project_id = attrs.get('project_id')
        code = attrs.get('code')
        
        # Проверяем уникальность кода в рамках проекта
        if self.instance:
            # При обновлении
            if Facility.objects.exclude(id=self.instance.id).filter(
                project_id=project_id, code=code
            ).exists():
                raise serializers.ValidationError({
                    'code': 'Объект с таким кодом уже существует в данном проекте'
                })
        else:
            # При создании
            if Facility.objects.filter(project_id=project_id, code=code).exists():
                raise serializers.ValidationError({
                    'code': 'Объект с таким кодом уже существует в данном проекте'
                })
        
        # Валидация дат
        start_date = attrs.get('construction_start')
        end_date = attrs.get('construction_end')
        actual_date = attrs.get('actual_completion')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                'construction_end': 'Дата окончания не может быть раньше даты начала'
            })
        
        if start_date and actual_date and start_date > actual_date:
            raise serializers.ValidationError({
                'actual_completion': 'Фактическая дата завершения не может быть раньше даты начала'
            })
        
        return attrs
    
    def create(self, validated_data):
        """Создание объекта"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ProjectStatisticsSerializer(serializers.Serializer):
    """Сериализатор для статистики проектов"""
    
    total_projects = serializers.IntegerField()
    active_projects = serializers.IntegerField()
    completed_projects = serializers.IntegerField()
    overdue_projects = serializers.IntegerField()
    total_facilities = serializers.IntegerField()
    total_defects = serializers.IntegerField()
    projects_by_status = serializers.DictField()
    projects_by_priority = serializers.DictField()
    facilities_by_type = serializers.DictField()
    facilities_by_status = serializers.DictField()