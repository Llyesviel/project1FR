from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, UserProfile, UserSession


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля пользователя"""
    
    class Meta:
        model = UserProfile
        fields = [
            'bio', 'birth_date', 'location', 'website',
            'theme', 'language', 'timezone'
        ]
        extra_kwargs = {
            'birth_date': {'required': False},
            'bio': {'required': False},
            'location': {'required': False},
            'website': {'required': False},
        }


class UserSerializer(serializers.ModelSerializer):
    """Основной сериализатор пользователя"""
    
    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    avatar_url = serializers.CharField(source='get_avatar_url', read_only=True)
    
    # Права доступа (только для чтения)
    is_admin = serializers.BooleanField(read_only=True)
    is_manager = serializers.BooleanField(read_only=True)
    is_executor = serializers.BooleanField(read_only=True)
    can_create_defects = serializers.BooleanField(read_only=True)
    can_assign_defects = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'role', 'phone', 'avatar', 'avatar_url',
            'position', 'department', 'is_active', 'created_at',
            'updated_at', 'last_activity', 'email_notifications',
            'push_notifications', 'profile', 'is_admin', 'is_manager',
            'is_executor', 'can_create_defects', 'can_assign_defects'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'last_activity',
            'is_admin', 'is_manager', 'is_executor',
            'can_create_defects', 'can_assign_defects'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
        }
    
    def validate_email(self, value):
        """Валидация email"""
        user = self.instance
        if User.objects.exclude(pk=user.pk if user else None).filter(email=value).exists():
            raise serializers.ValidationError('Пользователь с таким email уже существует.')
        return value
    
    def validate_phone(self, value):
        """Валидация телефона"""
        if value and len(value.replace('+', '').replace(' ', '').replace('-', '')) < 10:
            raise serializers.ValidationError('Номер телефона слишком короткий.')
        return value


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователя"""
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'role', 'phone',
            'position', 'department'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, attrs):
        """Валидация данных"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Пароли не совпадают.'
            })
        return attrs
    
    def validate_email(self, value):
        """Валидация email"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Пользователь с таким email уже существует.')
        return value
    
    def validate_username(self, value):
        """Валидация username"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Пользователь с таким именем уже существует.')
        return value
    
    def create(self, validated_data):
        """Создание пользователя"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        # Создаем профиль пользователя
        UserProfile.objects.create(user=user)
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления пользователя"""
    
    profile = UserProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'avatar',
            'position', 'department', 'email_notifications',
            'push_notifications', 'profile'
        ]
    
    def update(self, instance, validated_data):
        """Обновление пользователя и профиля"""
        profile_data = validated_data.pop('profile', None)
        
        # Обновляем основные данные пользователя
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Обновляем профиль
        if profile_data:
            profile, created = UserProfile.objects.get_or_create(user=instance)
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """Сериализатор для смены пароля"""
    
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate_old_password(self, value):
        """Валидация старого пароля"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Неверный текущий пароль.')
        return value
    
    def validate(self, attrs):
        """Валидация данных"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Пароли не совпадают.'
            })
        return attrs
    
    def save(self):
        """Сохранение нового пароля"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Сериализатор для входа в систему"""
    
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        """Валидация данных для входа"""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            # Пытаемся найти пользователя по email
            try:
                user = User.objects.get(email=email)
                username = user.username
            except User.DoesNotExist:
                raise serializers.ValidationError('Неверные учетные данные.')
            
            # Аутентификация
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError('Неверные учетные данные.')
            
            if not user.is_active:
                raise serializers.ValidationError('Учетная запись отключена.')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Необходимо указать email и пароль.')


class UserSessionSerializer(serializers.ModelSerializer):
    """Сериализатор для сессий пользователя"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = UserSession
        fields = [
            'id', 'user', 'user_name', 'session_key',
            'ip_address', 'user_agent', 'created_at',
            'last_activity', 'is_active'
        ]
        read_only_fields = [
            'id', 'session_key', 'created_at', 'last_activity'
        ]


class UserListSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для списка пользователей"""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    avatar_url = serializers.CharField(source='get_avatar_url', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name',
            'role', 'position', 'department', 'avatar_url',
            'is_active', 'last_activity'
        ]


class UserDetailSerializer(UserSerializer):
    """Детальный сериализатор пользователя"""
    
    sessions = UserSessionSerializer(many=True, read_only=True)
    
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['sessions']


class ResetPasswordSerializer(serializers.Serializer):
    """Сериализатор для сброса пароля"""
    
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Валидация email"""
        try:
            User.objects.get(email=value, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError('Пользователь с таким email не найден.')
        return value


class ResetPasswordConfirmSerializer(serializers.Serializer):
    """Сериализатор для подтверждения сброса пароля"""
    
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        """Валидация данных"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Пароли не совпадают.'
            })
        return attrs