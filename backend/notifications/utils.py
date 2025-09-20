from django.template import Template, Context
from django.template.loader import render_to_string
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Q
from typing import Dict, List, Any, Optional, Union
import logging
import json
from datetime import datetime, timedelta

from .models import (
    Notification, 
    NotificationTemplate, 
    NotificationSettings,
    NotificationBatch
)

User = get_user_model()
logger = logging.getLogger(__name__)


class NotificationRenderer:
    """Класс для рендеринга уведомлений из шаблонов"""
    
    @staticmethod
    def render_template(template_content: str, context: Dict[str, Any]) -> str:
        """Рендерит шаблон с контекстом"""
        try:
            template = Template(template_content)
            django_context = Context(context)
            return template.render(django_context)
        except Exception as e:
            logger.error(f'Ошибка рендеринга шаблона: {str(e)}')
            return template_content  # Возвращаем исходный текст при ошибке
    
    @classmethod
    def render_notification_template(
        cls, 
        template: NotificationTemplate, 
        context: Dict[str, Any]
    ) -> Dict[str, str]:
        """Рендерит шаблон уведомления"""
        # Добавляем стандартные переменные в контекст
        standard_context = {
            'site_name': getattr(settings, 'SITE_NAME', 'Система управления объектами'),
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:3000'),
            'current_date': timezone.now().date(),
            'current_datetime': timezone.now(),
        }
        
        full_context = {**standard_context, **context}
        
        return {
            'title': cls.render_template(template.title_template, full_context),
            'message': cls.render_template(template.message_template, full_context),
            'email_subject': cls.render_template(
                template.email_subject_template or template.title_template, 
                full_context
            ),
            'email_body': cls.render_template(
                template.email_body_template or template.message_template, 
                full_context
            )
        }


class NotificationSender:
    """Класс для отправки уведомлений"""
    
    def __init__(self):
        self.renderer = NotificationRenderer()
    
    def send_notification(
        self,
        recipient: User,
        template: Union[NotificationTemplate, str],
        context: Dict[str, Any] = None,
        sender: User = None,
        priority: str = 'medium',
        action_url: str = None,
        expires_at: datetime = None,
        extra_data: Dict[str, Any] = None,
        send_email: bool = True,
        send_push: bool = True
    ) -> Notification:
        """Отправляет уведомление пользователю"""
        
        context = context or {}
        extra_data = extra_data or {}
        
        # Если передан код шаблона, получаем объект шаблона
        if isinstance(template, str):
            try:
                template = NotificationTemplate.objects.get(code=template)
            except NotificationTemplate.DoesNotExist:
                raise ValueError(f'Шаблон с кодом "{template}" не найден')
        
        # Добавляем получателя в контекст
        context.update({
            'user': recipient,
            'recipient': recipient,
        })
        
        # Рендерим шаблон
        rendered = self.renderer.render_notification_template(template, context)
        
        # Создаем уведомление
        notification = Notification.objects.create(
            recipient=recipient,
            sender=sender,
            title=rendered['title'],
            message=rendered['message'],
            notification_type=template.notification_type,
            category=template.category,
            priority=priority,
            action_url=action_url,
            expires_at=expires_at,
            extra_data={
                'template_code': template.code,
                'rendered_context': context,
                **extra_data
            }
        )
        
        # Проверяем настройки пользователя
        settings_obj, _ = NotificationSettings.objects.get_or_create(user=recipient)
        
        # Отправляем email асинхронно
        if send_email and settings_obj.email_notifications:
            from .tasks import send_notification_email
            send_notification_email.delay(notification.id)
        
        # Отправляем push уведомление асинхронно
        if send_push and settings_obj.push_notifications:
            from .tasks import send_push_notification
            send_push_notification.delay(notification.id)
        
        logger.info(f'Уведомление создано: {notification.id} для пользователя {recipient.username}')
        
        return notification
    
    def send_bulk_notification(
        self,
        recipients: List[User],
        template: Union[NotificationTemplate, str],
        context: Dict[str, Any] = None,
        sender: User = None,
        priority: str = 'medium',
        **kwargs
    ) -> List[Notification]:
        """Отправляет уведомления нескольким пользователям"""
        
        notifications = []
        
        for recipient in recipients:
            try:
                notification = self.send_notification(
                    recipient=recipient,
                    template=template,
                    context=context,
                    sender=sender,
                    priority=priority,
                    **kwargs
                )
                notifications.append(notification)
            except Exception as e:
                logger.error(f'Ошибка отправки уведомления пользователю {recipient.id}: {str(e)}')
        
        return notifications
    
    def send_notification_batch(
        self,
        template: NotificationTemplate,
        recipients: List[User],
        context_data: Dict[str, Any] = None,
        created_by: User = None,
        scheduled_at: datetime = None
    ) -> NotificationBatch:
        """Создает и отправляет пакет уведомлений"""
        
        # Создаем пакет
        batch = NotificationBatch.objects.create(
            template=template,
            context_data=context_data or {},
            created_by=created_by,
            scheduled_at=scheduled_at or timezone.now()
        )
        
        # Добавляем получателей
        batch.recipients.set(recipients)
        
        # Отправляем пакет асинхронно
        from .tasks import send_notification_batch
        
        if scheduled_at and scheduled_at > timezone.now():
            # Планируем отправку на указанное время
            send_notification_batch.apply_async(
                args=[batch.id],
                eta=scheduled_at
            )
        else:
            # Отправляем немедленно
            send_notification_batch.delay(batch.id)
        
        return batch


class NotificationFilter:
    """Класс для фильтрации уведомлений"""
    
    @staticmethod
    def get_user_notifications(
        user: User,
        is_read: bool = None,
        category: str = None,
        priority: str = None,
        notification_type: str = None,
        date_from: datetime = None,
        date_to: datetime = None,
        search: str = None,
        limit: int = None
    ) -> 'QuerySet[Notification]':
        """Получает отфильтрованные уведомления пользователя"""
        
        queryset = Notification.objects.filter(recipient=user)
        
        # Фильтры
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read)
        
        if category:
            queryset = queryset.filter(category=category)
        
        if priority:
            queryset = queryset.filter(priority=priority)
        
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(message__icontains=search)
            )
        
        # Сортировка
        queryset = queryset.order_by('-priority_order', '-created_at')
        
        # Лимит
        if limit:
            queryset = queryset[:limit]
        
        return queryset
    
    @staticmethod
    def get_unread_count(user: User, category: str = None) -> int:
        """Получает количество непрочитанных уведомлений"""
        queryset = Notification.objects.filter(recipient=user, is_read=False)
        
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset.count()
    
    @staticmethod
    def get_recent_notifications(user: User, hours: int = 24, limit: int = 10) -> 'QuerySet[Notification]':
        """Получает недавние уведомления"""
        since = timezone.now() - timedelta(hours=hours)
        
        return Notification.objects.filter(
            recipient=user,
            created_at__gte=since
        ).order_by('-created_at')[:limit]


class NotificationStats:
    """Класс для получения статистики уведомлений"""
    
    @staticmethod
    def get_user_stats(user: User, period_days: int = 30) -> Dict[str, Any]:
        """Получает статистику уведомлений пользователя"""
        since = timezone.now() - timedelta(days=period_days)
        
        notifications = Notification.objects.filter(
            recipient=user,
            created_at__gte=since
        )
        
        total = notifications.count()
        read = notifications.filter(is_read=True).count()
        unread = notifications.filter(is_read=False).count()
        
        # Статистика по категориям
        category_stats = {}
        for category_code, category_name in Notification.CATEGORIES:
            count = notifications.filter(category=category_code).count()
            if count > 0:
                category_stats[category_code] = {
                    'name': category_name,
                    'count': count,
                    'percentage': round((count / total) * 100, 1) if total > 0 else 0
                }
        
        # Статистика по приоритету
        priority_stats = {}
        for priority_code, priority_name in Notification.PRIORITIES:
            count = notifications.filter(priority=priority_code).count()
            if count > 0:
                priority_stats[priority_code] = {
                    'name': priority_name,
                    'count': count,
                    'percentage': round((count / total) * 100, 1) if total > 0 else 0
                }
        
        # Среднее время прочтения
        read_notifications = notifications.filter(is_read=True, read_at__isnull=False)
        avg_read_time = None
        
        if read_notifications.exists():
            total_read_time = sum([
                (n.read_at - n.created_at).total_seconds() 
                for n in read_notifications 
                if n.read_at
            ])
            avg_read_time = total_read_time / read_notifications.count()
        
        return {
            'period_days': period_days,
            'total_notifications': total,
            'read_notifications': read,
            'unread_notifications': unread,
            'read_percentage': round((read / total) * 100, 1) if total > 0 else 0,
            'category_stats': category_stats,
            'priority_stats': priority_stats,
            'avg_read_time_seconds': avg_read_time,
            'avg_read_time_formatted': NotificationStats._format_duration(avg_read_time) if avg_read_time else None
        }
    
    @staticmethod
    def get_global_stats(period_days: int = 30) -> Dict[str, Any]:
        """Получает глобальную статистику уведомлений"""
        since = timezone.now() - timedelta(days=period_days)
        
        notifications = Notification.objects.filter(created_at__gte=since)
        
        total = notifications.count()
        read = notifications.filter(is_read=True).count()
        unread = notifications.filter(is_read=False).count()
        
        # Активные пользователи
        active_users = notifications.values('recipient').distinct().count()
        
        # Статистика по дням
        daily_stats = []
        for i in range(period_days):
            date = (timezone.now() - timedelta(days=i)).date()
            day_notifications = notifications.filter(created_at__date=date)
            
            daily_stats.append({
                'date': date.isoformat(),
                'total': day_notifications.count(),
                'read': day_notifications.filter(is_read=True).count(),
                'unread': day_notifications.filter(is_read=False).count()
            })
        
        daily_stats.reverse()  # От старых к новым
        
        return {
            'period_days': period_days,
            'total_notifications': total,
            'read_notifications': read,
            'unread_notifications': unread,
            'active_users': active_users,
            'daily_stats': daily_stats,
            'avg_notifications_per_user': round(total / active_users, 1) if active_users > 0 else 0
        }
    
    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Форматирует продолжительность в читаемый вид"""
        if seconds < 60:
            return f'{int(seconds)} сек'
        elif seconds < 3600:
            return f'{int(seconds // 60)} мин {int(seconds % 60)} сек'
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f'{hours} ч {minutes} мин'


class NotificationValidator:
    """Класс для валидации уведомлений"""
    
    @staticmethod
    def validate_template_context(template: NotificationTemplate, context: Dict[str, Any]) -> Dict[str, List[str]]:
        """Валидирует контекст для шаблона"""
        errors = {}
        
        # Проверяем обязательные переменные
        if template.required_context_vars:
            required_vars = template.required_context_vars
            missing_vars = []
            
            for var in required_vars:
                if var not in context:
                    missing_vars.append(var)
            
            if missing_vars:
                errors['missing_variables'] = missing_vars
        
        # Проверяем рендеринг шаблонов
        try:
            NotificationRenderer.render_notification_template(template, context)
        except Exception as e:
            errors['template_render_error'] = [str(e)]
        
        return errors
    
    @staticmethod
    def validate_notification_data(
        recipient: User,
        title: str,
        message: str,
        notification_type: str = None,
        category: str = None,
        priority: str = None
    ) -> Dict[str, List[str]]:
        """Валидирует данные уведомления"""
        errors = {}
        
        # Проверяем обязательные поля
        if not title or not title.strip():
            errors.setdefault('title', []).append('Заголовок обязателен')
        
        if not message or not message.strip():
            errors.setdefault('message', []).append('Сообщение обязательно')
        
        # Проверяем длину
        if title and len(title) > 200:
            errors.setdefault('title', []).append('Заголовок не может быть длиннее 200 символов')
        
        if message and len(message) > 1000:
            errors.setdefault('message', []).append('Сообщение не может быть длиннее 1000 символов')
        
        # Проверяем валидность выборов
        if notification_type and notification_type not in dict(Notification.NOTIFICATION_TYPES):
            errors.setdefault('notification_type', []).append('Недопустимый тип уведомления')
        
        if category and category not in dict(Notification.CATEGORIES):
            errors.setdefault('category', []).append('Недопустимая категория')
        
        if priority and priority not in dict(Notification.PRIORITIES):
            errors.setdefault('priority', []).append('Недопустимый приоритет')
        
        return errors


class NotificationExporter:
    """Класс для экспорта уведомлений"""
    
    @staticmethod
    def export_user_notifications(
        user: User,
        format: str = 'json',
        date_from: datetime = None,
        date_to: datetime = None
    ) -> Union[str, bytes]:
        """Экспортирует уведомления пользователя"""
        
        queryset = Notification.objects.filter(recipient=user)
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        notifications_data = []
        
        for notification in queryset.order_by('-created_at'):
            notifications_data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'notification_type': notification.get_notification_type_display(),
                'category': notification.get_category_display(),
                'priority': notification.get_priority_display(),
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'read_at': notification.read_at.isoformat() if notification.read_at else None,
                'action_url': notification.action_url,
                'sender': notification.sender.username if notification.sender else None
            })
        
        if format == 'json':
            return json.dumps({
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                },
                'export_date': timezone.now().isoformat(),
                'total_notifications': len(notifications_data),
                'notifications': notifications_data
            }, ensure_ascii=False, indent=2)
        
        elif format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                'id', 'title', 'message', 'notification_type', 'category', 
                'priority', 'is_read', 'created_at', 'read_at', 'action_url', 'sender'
            ])
            
            writer.writeheader()
            writer.writerows(notifications_data)
            
            return output.getvalue()
        
        else:
            raise ValueError(f'Неподдерживаемый формат экспорта: {format}')


# Вспомогательные функции
def send_notification(
    recipient: User,
    template_code: str,
    context: Dict[str, Any] = None,
    **kwargs
) -> Notification:
    """Быстрая отправка уведомления по коду шаблона"""
    sender = NotificationSender()
    return sender.send_notification(
        recipient=recipient,
        template=template_code,
        context=context,
        **kwargs
    )


def send_bulk_notification(
    recipients: List[User],
    template_code: str,
    context: Dict[str, Any] = None,
    **kwargs
) -> List[Notification]:
    """Быстрая массовая отправка уведомлений"""
    sender = NotificationSender()
    return sender.send_bulk_notification(
        recipients=recipients,
        template=template_code,
        context=context,
        **kwargs
    )


def get_unread_count(user: User, category: str = None) -> int:
    """Быстрое получение количества непрочитанных уведомлений"""
    return NotificationFilter.get_unread_count(user, category)


def mark_notifications_as_read(
    user: User,
    notification_ids: List[int] = None,
    category: str = None
) -> int:
    """Отмечает уведомления как прочитанные"""
    queryset = Notification.objects.filter(recipient=user, is_read=False)
    
    if notification_ids:
        queryset = queryset.filter(id__in=notification_ids)
    
    if category:
        queryset = queryset.filter(category=category)
    
    return queryset.update(is_read=True, read_at=timezone.now())


def delete_old_notifications(days: int = 30) -> int:
    """Удаляет старые уведомления"""
    cutoff_date = timezone.now() - timedelta(days=days)
    
    deleted_count = Notification.objects.filter(
        created_at__lt=cutoff_date,
        is_read=True
    ).delete()[0]
    
    return deleted_count