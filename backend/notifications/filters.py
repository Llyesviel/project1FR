import django_filters
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from .models import (
    Notification, 
    NotificationTemplate, 
    NotificationBatch,
    NotificationSettings,
    NotificationType,
    NotificationCategory,
    NotificationPriority
)

User = get_user_model()


class NotificationFilter(django_filters.FilterSet):
    """Фильтр для уведомлений"""
    
    # Фильтры по статусу
    is_read = django_filters.BooleanFilter()
    is_expired = django_filters.BooleanFilter(method='filter_is_expired')
    
    # Фильтры по типу и категории
    notification_type = django_filters.ChoiceFilter(
        choices=NotificationType.choices
    )
    category = django_filters.ChoiceFilter(
        choices=NotificationCategory.choices
    )
    priority = django_filters.ChoiceFilter(
        choices=NotificationPriority.choices
    )
    
    # Фильтры по пользователям
    recipient = django_filters.ModelChoiceFilter(
        queryset=User.objects.all(),
        field_name='recipient'
    )
    sender = django_filters.ModelChoiceFilter(
        queryset=User.objects.all(),
        field_name='sender'
    )
    
    # Фильтры по времени
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte'
    )
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte'
    )
    created_date = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='date'
    )
    
    read_after = django_filters.DateTimeFilter(
        field_name='read_at',
        lookup_expr='gte'
    )
    read_before = django_filters.DateTimeFilter(
        field_name='read_at',
        lookup_expr='lte'
    )
    
    expires_after = django_filters.DateTimeFilter(
        field_name='expires_at',
        lookup_expr='gte'
    )
    expires_before = django_filters.DateTimeFilter(
        field_name='expires_at',
        lookup_expr='lte'
    )
    
    # Фильтры по периодам
    period = django_filters.ChoiceFilter(
        choices=[
            ('today', 'Сегодня'),
            ('yesterday', 'Вчера'),
            ('week', 'Эта неделя'),
            ('month', 'Этот месяц'),
            ('quarter', 'Этот квартал'),
            ('year', 'Этот год')
        ],
        method='filter_by_period'
    )
    
    # Фильтр по возрасту уведомления
    age_days = django_filters.NumberFilter(method='filter_by_age_days')
    age_days_gte = django_filters.NumberFilter(method='filter_by_age_days_gte')
    age_days_lte = django_filters.NumberFilter(method='filter_by_age_days_lte')
    
    # Фильтр по связанному объекту
    content_type = django_filters.ModelChoiceFilter(
        queryset=ContentType.objects.all()
    )
    object_id = django_filters.NumberFilter()
    
    # Фильтр по наличию действия
    has_action_url = django_filters.BooleanFilter(method='filter_has_action_url')
    
    # Комбинированные фильтры
    unread_urgent = django_filters.BooleanFilter(method='filter_unread_urgent')
    unread_high_priority = django_filters.BooleanFilter(method='filter_unread_high_priority')
    
    class Meta:
        model = Notification
        fields = {
            'title': ['icontains', 'exact'],
            'message': ['icontains'],
        }
    
    def filter_is_expired(self, queryset, name, value):
        """Фильтр по истечению срока"""
        now = timezone.now()
        if value:
            return queryset.filter(
                expires_at__lt=now,
                expires_at__isnull=False
            )
        else:
            return queryset.filter(
                Q(expires_at__gte=now) | Q(expires_at__isnull=True)
            )
    
    def filter_by_period(self, queryset, name, value):
        """Фильтр по периоду"""
        now = timezone.now()
        
        if value == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return queryset.filter(created_at__gte=start_date)
        
        elif value == 'yesterday':
            yesterday = now - timedelta(days=1)
            start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
            return queryset.filter(
                created_at__gte=start_date,
                created_at__lt=end_date
            )
        
        elif value == 'week':
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            return queryset.filter(created_at__gte=start_date)
        
        elif value == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return queryset.filter(created_at__gte=start_date)
        
        elif value == 'quarter':
            quarter_start_month = ((now.month - 1) // 3) * 3 + 1
            start_date = now.replace(
                month=quarter_start_month, 
                day=1, 
                hour=0, 
                minute=0, 
                second=0, 
                microsecond=0
            )
            return queryset.filter(created_at__gte=start_date)
        
        elif value == 'year':
            start_date = now.replace(
                month=1, 
                day=1, 
                hour=0, 
                minute=0, 
                second=0, 
                microsecond=0
            )
            return queryset.filter(created_at__gte=start_date)
        
        return queryset
    
    def filter_by_age_days(self, queryset, name, value):
        """Фильтр по точному возрасту в днях"""
        target_date = timezone.now() - timedelta(days=value)
        start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        return queryset.filter(
            created_at__gte=start_date,
            created_at__lt=end_date
        )
    
    def filter_by_age_days_gte(self, queryset, name, value):
        """Фильтр по минимальному возрасту в днях"""
        target_date = timezone.now() - timedelta(days=value)
        return queryset.filter(created_at__lte=target_date)
    
    def filter_by_age_days_lte(self, queryset, name, value):
        """Фильтр по максимальному возрасту в днях"""
        target_date = timezone.now() - timedelta(days=value)
        return queryset.filter(created_at__gte=target_date)
    
    def filter_has_action_url(self, queryset, name, value):
        """Фильтр по наличию URL действия"""
        if value:
            return queryset.exclude(Q(action_url='') | Q(action_url__isnull=True))
        else:
            return queryset.filter(Q(action_url='') | Q(action_url__isnull=True))
    
    def filter_unread_urgent(self, queryset, name, value):
        """Фильтр непрочитанных срочных уведомлений"""
        if value:
            return queryset.filter(
                is_read=False,
                priority='urgent'
            )
        return queryset
    
    def filter_unread_high_priority(self, queryset, name, value):
        """Фильтр непрочитанных высокоприоритетных уведомлений"""
        if value:
            return queryset.filter(
                is_read=False,
                priority__in=['high', 'urgent']
            )
        return queryset


class NotificationTemplateFilter(django_filters.FilterSet):
    """Фильтр для шаблонов уведомлений"""
    
    # Фильтры по статусу
    is_active = django_filters.BooleanFilter()
    
    # Фильтры по типу и категории
    notification_type = django_filters.ChoiceFilter(
        choices=NotificationType.choices
    )
    category = django_filters.ChoiceFilter(
        choices=NotificationCategory.choices
    )
    priority = django_filters.ChoiceFilter(
        choices=NotificationPriority.choices
    )
    
    # Фильтры по времени
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte'
    )
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte'
    )
    
    updated_after = django_filters.DateTimeFilter(
        field_name='updated_at',
        lookup_expr='gte'
    )
    updated_before = django_filters.DateTimeFilter(
        field_name='updated_at',
        lookup_expr='lte'
    )
    
    # Фильтр по сроку действия по умолчанию
    default_expires_days = django_filters.NumberFilter()
    default_expires_days_gte = django_filters.NumberFilter(
        field_name='default_expires_days',
        lookup_expr='gte'
    )
    default_expires_days_lte = django_filters.NumberFilter(
        field_name='default_expires_days',
        lookup_expr='lte'
    )
    
    # Фильтр по использованию
    has_usage = django_filters.BooleanFilter(method='filter_has_usage')
    
    class Meta:
        model = NotificationTemplate
        fields = {
            'name': ['icontains', 'exact'],
            'title_template': ['icontains'],
            'message_template': ['icontains'],
        }
    
    def filter_has_usage(self, queryset, name, value):
        """Фильтр по наличию использования шаблона"""
        if value:
            return queryset.filter(notificationbatch__isnull=False).distinct()
        else:
            return queryset.filter(notificationbatch__isnull=True)


class NotificationBatchFilter(django_filters.FilterSet):
    """Фильтр для пакетов уведомлений"""
    
    # Фильтры по статусу
    is_sent = django_filters.BooleanFilter()
    
    # Фильтры по шаблону
    template = django_filters.ModelChoiceFilter(
        queryset=NotificationTemplate.objects.all()
    )
    template_name = django_filters.CharFilter(
        field_name='template__name',
        lookup_expr='icontains'
    )
    
    # Фильтры по создателю
    created_by = django_filters.ModelChoiceFilter(
        queryset=User.objects.all()
    )
    
    # Фильтры по времени
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte'
    )
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte'
    )
    
    sent_after = django_filters.DateTimeFilter(
        field_name='sent_at',
        lookup_expr='gte'
    )
    sent_before = django_filters.DateTimeFilter(
        field_name='sent_at',
        lookup_expr='lte'
    )
    
    # Фильтры по количеству получателей
    total_recipients = django_filters.NumberFilter()
    total_recipients_gte = django_filters.NumberFilter(
        field_name='total_recipients',
        lookup_expr='gte'
    )
    total_recipients_lte = django_filters.NumberFilter(
        field_name='total_recipients',
        lookup_expr='lte'
    )
    
    # Фильтры по успешности
    successful_sends_gte = django_filters.NumberFilter(
        field_name='successful_sends',
        lookup_expr='gte'
    )
    failed_sends_gte = django_filters.NumberFilter(
        field_name='failed_sends',
        lookup_expr='gte'
    )
    
    # Фильтр по проценту успешности
    success_rate_gte = django_filters.NumberFilter(method='filter_success_rate_gte')
    success_rate_lte = django_filters.NumberFilter(method='filter_success_rate_lte')
    
    # Фильтр по получателям
    recipient = django_filters.ModelChoiceFilter(
        queryset=User.objects.all(),
        field_name='recipients'
    )
    
    class Meta:
        model = NotificationBatch
        fields = {
            'name': ['icontains', 'exact'],
        }
    
    def filter_success_rate_gte(self, queryset, name, value):
        """Фильтр по минимальному проценту успешности"""
        filtered_ids = []
        for batch in queryset:
            if batch.total_recipients > 0:
                success_rate = (batch.successful_sends / batch.total_recipients) * 100
                if success_rate >= value:
                    filtered_ids.append(batch.id)
        
        return queryset.filter(id__in=filtered_ids)
    
    def filter_success_rate_lte(self, queryset, name, value):
        """Фильтр по максимальному проценту успешности"""
        filtered_ids = []
        for batch in queryset:
            if batch.total_recipients > 0:
                success_rate = (batch.successful_sends / batch.total_recipients) * 100
                if success_rate <= value:
                    filtered_ids.append(batch.id)
            elif value >= 0:  # Если нет получателей, считаем успешность 0%
                filtered_ids.append(batch.id)
        
        return queryset.filter(id__in=filtered_ids)


class NotificationSettingsFilter(django_filters.FilterSet):
    """Фильтр для настроек уведомлений"""
    
    # Фильтры по типам уведомлений
    email_notifications = django_filters.BooleanFilter()
    push_notifications = django_filters.BooleanFilter()
    
    # Фильтры по категориям
    project_notifications = django_filters.BooleanFilter()
    facility_notifications = django_filters.BooleanFilter()
    document_notifications = django_filters.BooleanFilter()
    security_notifications = django_filters.BooleanFilter()
    
    # Фильтры по приоритету
    low_priority_notifications = django_filters.BooleanFilter()
    normal_priority_notifications = django_filters.BooleanFilter()
    high_priority_notifications = django_filters.BooleanFilter()
    urgent_priority_notifications = django_filters.BooleanFilter()
    
    # Фильтры по времени
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte'
    )
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte'
    )
    
    updated_after = django_filters.DateTimeFilter(
        field_name='updated_at',
        lookup_expr='gte'
    )
    updated_before = django_filters.DateTimeFilter(
        field_name='updated_at',
        lookup_expr='lte'
    )
    
    # Фильтр по автоудалению
    auto_delete_read_after_days = django_filters.NumberFilter()
    auto_delete_enabled = django_filters.BooleanFilter(method='filter_auto_delete_enabled')
    
    # Фильтр по тихим часам
    has_quiet_hours = django_filters.BooleanFilter(method='filter_has_quiet_hours')
    
    class Meta:
        model = NotificationSettings
        fields = ['user']
    
    def filter_auto_delete_enabled(self, queryset, name, value):
        """Фильтр по включенному автоудалению"""
        if value:
            return queryset.filter(auto_delete_read_after_days__gt=0)
        else:
            return queryset.filter(
                Q(auto_delete_read_after_days=0) | 
                Q(auto_delete_read_after_days__isnull=True)
            )
    
    def filter_has_quiet_hours(self, queryset, name, value):
        """Фильтр по наличию тихих часов"""
        if value:
            return queryset.filter(
                quiet_hours_start__isnull=False,
                quiet_hours_end__isnull=False
            )
        else:
            return queryset.filter(
                Q(quiet_hours_start__isnull=True) | 
                Q(quiet_hours_end__isnull=True)
            )


class NotificationSearchFilter:
    """Класс для расширенного поиска уведомлений"""
    
    @staticmethod
    def search_notifications(queryset, search_query):
        """Поиск уведомлений по различным полям"""
        if not search_query:
            return queryset
        
        # Разбиваем запрос на слова
        search_terms = search_query.split()
        
        # Создаем Q-объект для поиска
        search_q = Q()
        
        for term in search_terms:
            term_q = (
                Q(title__icontains=term) |
                Q(message__icontains=term) |
                Q(recipient__username__icontains=term) |
                Q(recipient__first_name__icontains=term) |
                Q(recipient__last_name__icontains=term) |
                Q(recipient__email__icontains=term) |
                Q(sender__username__icontains=term) |
                Q(sender__first_name__icontains=term) |
                Q(sender__last_name__icontains=term) |
                Q(extra_data__icontains=term)
            )
            
            search_q &= term_q
        
        return queryset.filter(search_q)
    
    @staticmethod
    def search_templates(queryset, search_query):
        """Поиск шаблонов уведомлений"""
        if not search_query:
            return queryset
        
        search_terms = search_query.split()
        search_q = Q()
        
        for term in search_terms:
            term_q = (
                Q(name__icontains=term) |
                Q(title_template__icontains=term) |
                Q(message_template__icontains=term)
            )
            
            search_q &= term_q
        
        return queryset.filter(search_q)
    
    @staticmethod
    def search_batches(queryset, search_query):
        """Поиск пакетов уведомлений"""
        if not search_query:
            return queryset
        
        search_terms = search_query.split()
        search_q = Q()
        
        for term in search_terms:
            term_q = (
                Q(name__icontains=term) |
                Q(template__name__icontains=term) |
                Q(created_by__username__icontains=term) |
                Q(created_by__first_name__icontains=term) |
                Q(created_by__last_name__icontains=term)
            )
            
            search_q &= term_q
        
        return queryset.filter(search_q)


class NotificationDateRangeFilter:
    """Класс для фильтрации по диапазонам дат"""
    
    @staticmethod
    def filter_by_date_range(queryset, field_name, start_date, end_date):
        """Фильтрация по диапазону дат"""
        filters = {}
        
        if start_date:
            filters[f'{field_name}__gte'] = start_date
        
        if end_date:
            filters[f'{field_name}__lte'] = end_date
        
        return queryset.filter(**filters)
    
    @staticmethod
    def get_predefined_ranges():
        """Получить предопределенные диапазоны дат"""
        now = timezone.now()
        
        return {
            'today': {
                'start': now.replace(hour=0, minute=0, second=0, microsecond=0),
                'end': now.replace(hour=23, minute=59, second=59, microsecond=999999)
            },
            'yesterday': {
                'start': (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
                'end': (now - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
            },
            'this_week': {
                'start': (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0),
                'end': now
            },
            'last_week': {
                'start': (now - timedelta(days=now.weekday() + 7)).replace(hour=0, minute=0, second=0, microsecond=0),
                'end': (now - timedelta(days=now.weekday() + 1)).replace(hour=23, minute=59, second=59, microsecond=999999)
            },
            'this_month': {
                'start': now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
                'end': now
            },
            'last_month': {
                'start': (now.replace(day=1) - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0),
                'end': (now.replace(day=1) - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
            }
        }