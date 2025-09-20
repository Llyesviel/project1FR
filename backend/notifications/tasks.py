from celery import shared_task
from django.core.mail import send_mail, send_mass_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
from datetime import timedelta
import logging
import json
from typing import List, Dict, Any

from .models import (
    Notification, 
    NotificationTemplate, 
    NotificationBatch, 
    NotificationSettings
)
from .utils import NotificationSender, NotificationRenderer

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_notification_email(self, notification_id: int):
    """Отправить email уведомление"""
    try:
        notification = Notification.objects.get(id=notification_id)
        
        # Проверяем настройки пользователя
        settings_obj, _ = NotificationSettings.objects.get_or_create(
            user=notification.recipient
        )
        
        if not settings_obj.email_notifications:
            logger.info(f'Email уведомления отключены для пользователя {notification.recipient.username}')
            return {'status': 'skipped', 'reason': 'email_disabled'}
        
        # Проверяем тихие часы
        if settings_obj.is_quiet_time():
            # Откладываем отправку до окончания тихих часов
            eta = settings_obj.get_next_active_time()
            self.retry(eta=eta)
            return
        
        # Проверяем категорию уведомления
        if not settings_obj.should_send_notification(notification):
            logger.info(f'Уведомление категории {notification.category} отключено для пользователя {notification.recipient.username}')
            return {'status': 'skipped', 'reason': 'category_disabled'}
        
        # Формируем email
        subject = f'[{settings.PROJECT_NAME}] {notification.title}'
        
        # HTML версия
        html_message = render_to_string('notifications/email/notification.html', {
            'notification': notification,
            'user': notification.recipient,
            'site_url': settings.SITE_URL,
            'unsubscribe_url': f"{settings.SITE_URL}/notifications/unsubscribe/{notification.recipient.id}/"
        })
        
        # Текстовая версия
        plain_message = strip_tags(html_message)
        
        # Отправляем email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.recipient.email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f'Email уведомление отправлено пользователю {notification.recipient.email}')
        return {'status': 'sent', 'recipient': notification.recipient.email}
        
    except Notification.DoesNotExist:
        logger.error(f'Уведомление с ID {notification_id} не найдено')
        return {'status': 'error', 'reason': 'notification_not_found'}
    
    except Exception as exc:
        logger.error(f'Ошибка отправки email уведомления {notification_id}: {str(exc)}')
        
        # Повторяем попытку с экспоненциальной задержкой
        countdown = 2 ** self.request.retries * 60  # 1, 2, 4 минуты
        self.retry(exc=exc, countdown=countdown)


@shared_task(bind=True, max_retries=3)
def send_push_notification(self, notification_id: int):
    """Отправить push уведомление"""
    try:
        notification = Notification.objects.get(id=notification_id)
        
        # Проверяем настройки пользователя
        settings_obj, _ = NotificationSettings.objects.get_or_create(
            user=notification.recipient
        )
        
        if not settings_obj.push_notifications:
            logger.info(f'Push уведомления отключены для пользователя {notification.recipient.username}')
            return {'status': 'skipped', 'reason': 'push_disabled'}
        
        # Проверяем тихие часы
        if settings_obj.is_quiet_time():
            eta = settings_obj.get_next_active_time()
            self.retry(eta=eta)
            return
        
        # Проверяем категорию уведомления
        if not settings_obj.should_send_notification(notification):
            logger.info(f'Уведомление категории {notification.category} отключено для пользователя {notification.recipient.username}')
            return {'status': 'skipped', 'reason': 'category_disabled'}
        
        # Здесь должна быть интеграция с сервисом push уведомлений
        # Например, Firebase Cloud Messaging, Apple Push Notification Service и т.д.
        
        # Пример для Firebase FCM (требует установки firebase-admin)
        # from firebase_admin import messaging
        # 
        # message = messaging.Message(
        #     notification=messaging.Notification(
        #         title=notification.title,
        #         body=notification.message[:100] + '...' if len(notification.message) > 100 else notification.message
        #     ),
        #     data={
        #         'notification_id': str(notification.id),
        #         'action_url': notification.action_url or '',
        #         'category': notification.category,
        #         'priority': notification.priority
        #     },
        #     token=user_device_token  # Токен устройства пользователя
        # )
        # 
        # response = messaging.send(message)
        
        logger.info(f'Push уведомление отправлено пользователю {notification.recipient.username}')
        return {'status': 'sent', 'recipient': notification.recipient.username}
        
    except Notification.DoesNotExist:
        logger.error(f'Уведомление с ID {notification_id} не найдено')
        return {'status': 'error', 'reason': 'notification_not_found'}
    
    except Exception as exc:
        logger.error(f'Ошибка отправки push уведомления {notification_id}: {str(exc)}')
        
        countdown = 2 ** self.request.retries * 60
        self.retry(exc=exc, countdown=countdown)


@shared_task(bind=True, max_retries=3)
def send_notification_batch(self, batch_id: int):
    """Отправить пакет уведомлений"""
    try:
        with transaction.atomic():
            batch = NotificationBatch.objects.select_for_update().get(id=batch_id)
            
            if batch.is_sent:
                logger.warning(f'Пакет {batch_id} уже отправлен')
                return {'status': 'already_sent'}
            
            # Получаем получателей
            recipients = batch.recipients.all()
            batch.total_recipients = recipients.count()
            batch.save(update_fields=['total_recipients'])
        
        successful_sends = 0
        failed_sends = 0
        
        # Создаем уведомления для каждого получателя
        for recipient in recipients:
            try:
                # Проверяем настройки получателя
                settings_obj, _ = NotificationSettings.objects.get_or_create(user=recipient)
                
                # Создаем контекст для рендеринга
                context = batch.context_data.copy() if batch.context_data else {}
                context.update({
                    'user': recipient,
                    'recipient': recipient,
                    'batch': batch
                })
                
                # Рендерим шаблон
                title = batch.template.render_title(context)
                message = batch.template.render_message(context)
                
                # Вычисляем срок действия
                expires_at = None
                if batch.template.default_expires_days:
                    expires_at = timezone.now() + timedelta(days=batch.template.default_expires_days)
                
                # Создаем уведомление
                notification = Notification.objects.create(
                    recipient=recipient,
                    sender=batch.created_by,
                    title=title,
                    message=message,
                    notification_type=batch.template.notification_type,
                    category=batch.template.category,
                    priority=batch.template.priority,
                    expires_at=expires_at,
                    extra_data={
                        'batch_id': batch.id,
                        'template_id': batch.template.id,
                        **context
                    }
                )
                
                # Отправляем email и push уведомления асинхронно
                if settings_obj.email_notifications:
                    send_notification_email.delay(notification.id)
                
                if settings_obj.push_notifications:
                    send_push_notification.delay(notification.id)
                
                successful_sends += 1
                
            except Exception as e:
                logger.error(f'Ошибка создания уведомления для пользователя {recipient.id}: {str(e)}')
                failed_sends += 1
        
        # Обновляем статистику пакета
        with transaction.atomic():
            batch.refresh_from_db()
            batch.successful_sends = successful_sends
            batch.failed_sends = failed_sends
            batch.is_sent = True
            batch.sent_at = timezone.now()
            batch.save(update_fields=['successful_sends', 'failed_sends', 'is_sent', 'sent_at'])
        
        logger.info(f'Пакет {batch_id} отправлен: {successful_sends} успешно, {failed_sends} с ошибками')
        
        return {
            'status': 'completed',
            'successful_sends': successful_sends,
            'failed_sends': failed_sends,
            'total_recipients': batch.total_recipients
        }
        
    except NotificationBatch.DoesNotExist:
        logger.error(f'Пакет уведомлений с ID {batch_id} не найден')
        return {'status': 'error', 'reason': 'batch_not_found'}
    
    except Exception as exc:
        logger.error(f'Ошибка отправки пакета уведомлений {batch_id}: {str(exc)}')
        
        countdown = 2 ** self.request.retries * 300  # 5, 10, 20 минут
        self.retry(exc=exc, countdown=countdown)


@shared_task
def cleanup_old_notifications():
    """Очистка старых уведомлений"""
    try:
        # Удаляем просроченные уведомления
        expired_count = Notification.objects.filter(
            expires_at__lt=timezone.now(),
            expires_at__isnull=False
        ).delete()[0]
        
        # Удаляем прочитанные уведомления согласно настройкам пользователей
        auto_deleted_count = 0
        
        for settings_obj in NotificationSettings.objects.filter(
            auto_delete_read_after_days__gt=0
        ):
            cutoff_date = timezone.now() - timedelta(days=settings_obj.auto_delete_read_after_days)
            
            deleted_count = Notification.objects.filter(
                recipient=settings_obj.user,
                is_read=True,
                read_at__lt=cutoff_date
            ).delete()[0]
            
            auto_deleted_count += deleted_count
        
        logger.info(f'Очистка уведомлений завершена: {expired_count} просроченных, {auto_deleted_count} автоудаленных')
        
        return {
            'status': 'completed',
            'expired_deleted': expired_count,
            'auto_deleted': auto_deleted_count
        }
        
    except Exception as e:
        logger.error(f'Ошибка очистки уведомлений: {str(e)}')
        return {'status': 'error', 'message': str(e)}


@shared_task
def send_digest_notifications():
    """Отправка дайджеста уведомлений"""
    try:
        # Находим пользователей с непрочитанными уведомлениями
        users_with_unread = User.objects.filter(
            received_notifications__is_read=False
        ).distinct()
        
        digest_sent_count = 0
        
        for user in users_with_unread:
            try:
                # Проверяем настройки пользователя
                settings_obj, _ = NotificationSettings.objects.get_or_create(user=user)
                
                if not settings_obj.email_notifications:
                    continue
                
                # Получаем непрочитанные уведомления за последние 24 часа
                yesterday = timezone.now() - timedelta(days=1)
                unread_notifications = Notification.objects.filter(
                    recipient=user,
                    is_read=False,
                    created_at__gte=yesterday
                ).order_by('-priority', '-created_at')[:10]  # Максимум 10 уведомлений
                
                if not unread_notifications.exists():
                    continue
                
                # Формируем дайджест
                subject = f'[{settings.PROJECT_NAME}] Дайджест уведомлений ({unread_notifications.count()})'
                
                html_message = render_to_string('notifications/email/digest.html', {
                    'user': user,
                    'notifications': unread_notifications,
                    'total_unread': Notification.objects.filter(recipient=user, is_read=False).count(),
                    'site_url': settings.SITE_URL,
                    'unsubscribe_url': f"{settings.SITE_URL}/notifications/unsubscribe/{user.id}/"
                })
                
                plain_message = strip_tags(html_message)
                
                # Отправляем дайджест
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False
                )
                
                digest_sent_count += 1
                
            except Exception as e:
                logger.error(f'Ошибка отправки дайджеста пользователю {user.id}: {str(e)}')
        
        logger.info(f'Дайджесты отправлены {digest_sent_count} пользователям')
        
        return {
            'status': 'completed',
            'digests_sent': digest_sent_count
        }
        
    except Exception as e:
        logger.error(f'Ошибка отправки дайджестов: {str(e)}')
        return {'status': 'error', 'message': str(e)}


@shared_task
def update_notification_stats():
    """Обновление статистики уведомлений"""
    try:
        from django.core.cache import cache
        
        # Общая статистика
        total_notifications = Notification.objects.count()
        unread_notifications = Notification.objects.filter(is_read=False).count()
        
        # Статистика за сегодня
        today = timezone.now().date()
        today_notifications = Notification.objects.filter(created_at__date=today).count()
        
        # Статистика по типам
        type_stats = {}
        for type_code, type_name in Notification.NOTIFICATION_TYPES:
            count = Notification.objects.filter(notification_type=type_code).count()
            type_stats[type_code] = {'name': type_name, 'count': count}
        
        # Статистика по категориям
        category_stats = {}
        for category_code, category_name in Notification.CATEGORIES:
            count = Notification.objects.filter(category=category_code).count()
            category_stats[category_code] = {'name': category_name, 'count': count}
        
        # Сохраняем в кеш
        stats_data = {
            'total_notifications': total_notifications,
            'unread_notifications': unread_notifications,
            'today_notifications': today_notifications,
            'type_stats': type_stats,
            'category_stats': category_stats,
            'updated_at': timezone.now().isoformat()
        }
        
        cache.set('notification_stats', stats_data, timeout=3600)  # Кешируем на час
        
        logger.info('Статистика уведомлений обновлена')
        
        return {
            'status': 'completed',
            'stats': stats_data
        }
        
    except Exception as e:
        logger.error(f'Ошибка обновления статистики: {str(e)}')
        return {'status': 'error', 'message': str(e)}


@shared_task
def process_notification_webhooks(notification_id: int, webhook_urls: List[str]):
    """Обработка webhook'ов для уведомлений"""
    try:
        import requests
        
        notification = Notification.objects.get(id=notification_id)
        
        # Формируем данные для webhook'а
        webhook_data = {
            'id': notification.id,
            'recipient': {
                'id': notification.recipient.id,
                'username': notification.recipient.username,
                'email': notification.recipient.email
            },
            'sender': {
                'id': notification.sender.id if notification.sender else None,
                'username': notification.sender.username if notification.sender else None
            } if notification.sender else None,
            'title': notification.title,
            'message': notification.message,
            'notification_type': notification.notification_type,
            'category': notification.category,
            'priority': notification.priority,
            'is_read': notification.is_read,
            'created_at': notification.created_at.isoformat(),
            'action_url': notification.action_url,
            'extra_data': notification.extra_data
        }
        
        successful_webhooks = 0
        failed_webhooks = 0
        
        # Отправляем webhook'и
        for webhook_url in webhook_urls:
            try:
                response = requests.post(
                    webhook_url,
                    json=webhook_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
                if response.status_code == 200:
                    successful_webhooks += 1
                else:
                    logger.warning(f'Webhook {webhook_url} вернул статус {response.status_code}')
                    failed_webhooks += 1
                    
            except Exception as e:
                logger.error(f'Ошибка отправки webhook {webhook_url}: {str(e)}')
                failed_webhooks += 1
        
        logger.info(f'Webhook\'и для уведомления {notification_id}: {successful_webhooks} успешно, {failed_webhooks} с ошибками')
        
        return {
            'status': 'completed',
            'successful_webhooks': successful_webhooks,
            'failed_webhooks': failed_webhooks
        }
        
    except Notification.DoesNotExist:
        logger.error(f'Уведомление с ID {notification_id} не найдено')
        return {'status': 'error', 'reason': 'notification_not_found'}
    
    except Exception as e:
        logger.error(f'Ошибка обработки webhook\'ов: {str(e)}')
        return {'status': 'error', 'message': str(e)}


@shared_task
def generate_notification_report(user_id: int, period: str = 'month'):
    """Генерация отчета по уведомлениям"""
    try:
        user = User.objects.get(id=user_id)
        
        # Определяем период
        now = timezone.now()
        if period == 'day':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'week':
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = now - timedelta(days=30)
        
        # Получаем уведомления за период
        notifications = Notification.objects.filter(
            recipient=user,
            created_at__gte=start_date
        )
        
        # Формируем отчет
        report_data = {
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            },
            'period': period,
            'start_date': start_date.isoformat(),
            'end_date': now.isoformat(),
            'total_notifications': notifications.count(),
            'read_notifications': notifications.filter(is_read=True).count(),
            'unread_notifications': notifications.filter(is_read=False).count(),
            'by_category': {},
            'by_priority': {},
            'by_type': {},
            'daily_stats': []
        }
        
        # Статистика по категориям
        for category_code, category_name in Notification.CATEGORIES:
            count = notifications.filter(category=category_code).count()
            if count > 0:
                report_data['by_category'][category_code] = {
                    'name': category_name,
                    'count': count
                }
        
        # Статистика по приоритету
        for priority_code, priority_name in Notification.PRIORITIES:
            count = notifications.filter(priority=priority_code).count()
            if count > 0:
                report_data['by_priority'][priority_code] = {
                    'name': priority_name,
                    'count': count
                }
        
        # Статистика по типам
        for type_code, type_name in Notification.NOTIFICATION_TYPES:
            count = notifications.filter(notification_type=type_code).count()
            if count > 0:
                report_data['by_type'][type_code] = {
                    'name': type_name,
                    'count': count
                }
        
        # Ежедневная статистика
        current_date = start_date.date()
        while current_date <= now.date():
            day_notifications = notifications.filter(created_at__date=current_date)
            report_data['daily_stats'].append({
                'date': current_date.isoformat(),
                'total': day_notifications.count(),
                'read': day_notifications.filter(is_read=True).count(),
                'unread': day_notifications.filter(is_read=False).count()
            })
            current_date += timedelta(days=1)
        
        # Сохраняем отчет в кеш
        from django.core.cache import cache
        cache_key = f'notification_report_{user_id}_{period}'
        cache.set(cache_key, report_data, timeout=3600)
        
        logger.info(f'Отчет по уведомлениям сгенерирован для пользователя {user_id}')
        
        return {
            'status': 'completed',
            'cache_key': cache_key,
            'report_data': report_data
        }
        
    except User.DoesNotExist:
        logger.error(f'Пользователь с ID {user_id} не найден')
        return {'status': 'error', 'reason': 'user_not_found'}
    
    except Exception as e:
        logger.error(f'Ошибка генерации отчета: {str(e)}')
        return {'status': 'error', 'message': str(e)}