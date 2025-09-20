from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_migrate


class NotificationsConfig(AppConfig):
    """Конфигурация приложения уведомлений"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'
    verbose_name = _('Уведомления')
    
    def ready(self):
        """Инициализация приложения"""
        # Импортируем сигналы
        try:
            from . import signals
        except ImportError:
            pass
        
        # Регистрируем задачи для очистки уведомлений
        try:
            from . import tasks
        except ImportError:
            pass
        
        # Подключаем обработчик для создания начальных данных
        post_migrate.connect(self.create_initial_data, sender=self)
    
    def create_initial_data(self, sender, **kwargs):
        """Создание начальных данных после миграций."""
        from .models import NotificationTemplate
        
        # Создаем базовые шаблоны уведомлений
        default_templates = [
            {
                'name': 'Добро пожаловать',
                'code': 'welcome',
                'description': 'Приветственное уведомление для новых пользователей',
                'title_template': 'Добро пожаловать в систему управления объектами!',
                'message_template': 'Здравствуйте, {{ user.first_name }}! Добро пожаловать в нашу систему.',
                'email_subject_template': 'Добро пожаловать в систему управления объектами',
                'email_body_template': 'Здравствуйте, {{ user.first_name }}!\n\nДобро пожаловать в нашу систему управления объектами.',
                'notification_type': 'info',
                'category': 'user',
                'priority': 'medium',
                'required_context_vars': ['user']
            },
            {
                'name': 'Новый проект создан',
                'code': 'project_created',
                'description': 'Уведомление о создании нового проекта',
                'title_template': 'Создан новый проект: {{ project.name }}',
                'message_template': 'Проект "{{ project.name }}" был успешно создан.',
                'email_subject_template': 'Новый проект: {{ project.name }}',
                'email_body_template': 'Ваш проект "{{ project.name }}" был успешно создан.',
                'notification_type': 'success',
                'category': 'project',
                'priority': 'medium',
                'required_context_vars': ['project']
            },
            {
                'name': 'Системная ошибка',
                'code': 'system_error',
                'description': 'Уведомление о системной ошибке',
                'title_template': 'Системная ошибка',
                'message_template': 'Произошла системная ошибка. Администраторы уведомлены.',
                'email_subject_template': 'Системная ошибка в приложении',
                'email_body_template': 'В системе произошла ошибка.',
                'notification_type': 'error',
                'category': 'system',
                'priority': 'critical',
                'required_context_vars': ['error']
            }
        ]
        
        for template_data in default_templates:
            NotificationTemplate.objects.get_or_create(
                code=template_data['code'],
                defaults=template_data
            )