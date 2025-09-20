from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FacilitiesConfig(AppConfig):
    """Конфигурация приложения facilities"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'facilities'
    verbose_name = _('Управление объектами недвижимости')
    
    def ready(self):
        """Инициализация приложения"""
        # Импортируем сигналы
        try:
            from . import signals
        except ImportError:
            pass
        
        # Регистрируем задачи Celery (если используется)
        try:
            from . import tasks
        except ImportError:
            pass