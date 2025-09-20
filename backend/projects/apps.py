from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    """Конфигурация приложения управления проектами"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'projects'
    verbose_name = 'Управление проектами'
    
    def ready(self):
        """Инициализация приложения"""
        # Импорт сигналов
        try:
            import projects.signals
        except ImportError:
            pass