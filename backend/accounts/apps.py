from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Конфигурация приложения accounts"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'Управление пользователями'
    
    def ready(self):
        """Инициализация приложения"""
        # Импортируем сигналы
        try:
            import accounts.signals
        except ImportError:
            pass