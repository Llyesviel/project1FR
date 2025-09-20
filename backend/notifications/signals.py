from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
import logging

from .models import (
    Notification, 
    NotificationTemplate, 
    NotificationSettings,
    NotificationBatch
)
from .utils import NotificationSender
from .tasks import (
    send_notification_email,
    send_push_notification,
    update_notification_stats
)

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=Notification)
def notification_created(sender, instance, created, **kwargs):
    """Обработчик создания уведомления"""
    if created:
        logger.info(f'Создано уведомление {instance.id} для пользователя {instance.recipient.username}')
        
        # Инвалидируем кеш статистики
        cache.delete('notification_stats')
        cache.delete(f'user_notification_stats_{instance.recipient.id}')
        
        # Обновляем счетчик непрочитанных уведомлений в кеше
        cache_key = f'unread_notifications_{instance.recipient.id}'
        current_count = cache.get(cache_key, 0)
        cache.set(cache_key, current_count + 1, timeout=3600)
        
        # Отправляем real-time уведомление (если настроено)
        if hasattr(settings, 'NOTIFICATIONS_REALTIME_ENABLED') and settings.NOTIFICATIONS_REALTIME_ENABLED:
            try:
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync
                
                channel_layer = get_channel_layer()
                if channel_layer:
                    group_name = f'notifications_{instance.recipient.id}'
                    
                    async_to_sync(channel_layer.group_send)(
                        group_name,
                        {
                            'type': 'notification_created',
                            'notification': {
                                'id': instance.id,
                                'title': instance.title,
                                'message': instance.message,
                                'category': instance.category,
                                'priority': instance.priority,
                                'created_at': instance.created_at.isoformat(),
                                'action_url': instance.action_url
                            }
                        }
                    )
            except ImportError:
                # Django Channels не установлен
                pass
            except Exception as e:
                logger.error(f'Ошибка отправки real-time уведомления: {str(e)}')


@receiver(post_save, sender=Notification)
def notification_read_status_changed(sender, instance, **kwargs):
    """Обработчик изменения статуса прочтения уведомления"""
    if instance.pk:  # Только для существующих объектов
        try:
            # Получаем предыдущее состояние из базы
            old_instance = Notification.objects.get(pk=instance.pk)
            
            # Проверяем, изменился ли статус прочтения
            if old_instance.is_read != instance.is_read:
                logger.info(f'Изменен статус прочтения уведомления {instance.id}: {instance.is_read}')
                
                # Обновляем счетчик в кеше
                cache_key = f'unread_notifications_{instance.recipient.id}'
                current_count = cache.get(cache_key, 0)
                
                if instance.is_read and current_count > 0:
                    cache.set(cache_key, current_count - 1, timeout=3600)
                elif not instance.is_read:
                    cache.set(cache_key, current_count + 1, timeout=3600)
                
                # Отправляем real-time обновление
                if hasattr(settings, 'NOTIFICATIONS_REALTIME_ENABLED') and settings.NOTIFICATIONS_REALTIME_ENABLED:
                    try:
                        from channels.layers import get_channel_layer
                        from asgiref.sync import async_to_sync
                        
                        channel_layer = get_channel_layer()
                        if channel_layer:
                            group_name = f'notifications_{instance.recipient.id}'
                            
                            async_to_sync(channel_layer.group_send)(
                                group_name,
                                {
                                    'type': 'notification_read_status_changed',
                                    'notification_id': instance.id,
                                    'is_read': instance.is_read,
                                    'read_at': instance.read_at.isoformat() if instance.read_at else None
                                }
                            )
                    except ImportError:
                        pass
                    except Exception as e:
                        logger.error(f'Ошибка отправки real-time обновления: {str(e)}')
        
        except Notification.DoesNotExist:
            # Это новый объект, ничего не делаем
            pass


@receiver(post_delete, sender=Notification)
def notification_deleted(sender, instance, **kwargs):
    """Обработчик удаления уведомления"""
    logger.info(f'Удалено уведомление {instance.id} пользователя {instance.recipient.username}')
    
    # Инвалидируем кеш
    cache.delete('notification_stats')
    cache.delete(f'user_notification_stats_{instance.recipient.id}')
    
    # Обновляем счетчик непрочитанных, если уведомление было непрочитанным
    if not instance.is_read:
        cache_key = f'unread_notifications_{instance.recipient.id}'
        current_count = cache.get(cache_key, 0)
        if current_count > 0:
            cache.set(cache_key, current_count - 1, timeout=3600)
    
    # Отправляем real-time обновление
    if hasattr(settings, 'NOTIFICATIONS_REALTIME_ENABLED') and settings.NOTIFICATIONS_REALTIME_ENABLED:
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            if channel_layer:
                group_name = f'notifications_{instance.recipient.id}'
                
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        'type': 'notification_deleted',
                        'notification_id': instance.id
                    }
                )
        except ImportError:
            pass
        except Exception as e:
            logger.error(f'Ошибка отправки real-time обновления об удалении: {str(e)}')


@receiver(post_save, sender=User)
def user_created(sender, instance, created, **kwargs):
    """Создание настроек уведомлений для нового пользователя"""
    if created:
        # Создаем настройки уведомлений по умолчанию
        NotificationSettings.objects.get_or_create(
            user=instance,
            defaults={
                'email_notifications': True,
                'push_notifications': True,
                'quiet_hours_start': None,
                'quiet_hours_end': None,
                'auto_delete_read_after_days': 30
            }
        )
        
        logger.info(f'Созданы настройки уведомлений для пользователя {instance.username}')
        
        # Отправляем приветственное уведомление
        try:
            welcome_template = NotificationTemplate.objects.get(code='user_welcome')
            sender = NotificationSender()
            
            sender.send_notification(
                recipient=instance,
                template=welcome_template,
                context={
                    'username': instance.username,
                    'first_name': instance.first_name or instance.username
                },
                priority='low'
            )
        except NotificationTemplate.DoesNotExist:
            logger.warning('Шаблон приветственного уведомления не найден')
        except Exception as e:
            logger.error(f'Ошибка отправки приветственного уведомления: {str(e)}')


@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    """Обработчик входа пользователя в систему"""
    # Обновляем время последнего входа в настройках уведомлений
    try:
        settings_obj, _ = NotificationSettings.objects.get_or_create(user=user)
        settings_obj.last_login_at = timezone.now()
        settings_obj.save(update_fields=['last_login_at'])
        
        # Отмечаем критические уведомления как доставленные
        critical_notifications = Notification.objects.filter(
            recipient=user,
            priority='critical',
            is_read=False
        )
        
        if critical_notifications.exists():
            logger.info(f'Пользователь {user.username} вошел в систему. Критических уведомлений: {critical_notifications.count()}')
    
    except Exception as e:
        logger.error(f'Ошибка обработки входа пользователя: {str(e)}')


@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    """Обработчик выхода пользователя из системы"""
    if user:
        try:
            settings_obj, _ = NotificationSettings.objects.get_or_create(user=user)
            settings_obj.last_logout_at = timezone.now()
            settings_obj.save(update_fields=['last_logout_at'])
            
            logger.info(f'Пользователь {user.username} вышел из системы')
        
        except Exception as e:
            logger.error(f'Ошибка обработки выхода пользователя: {str(e)}')


@receiver(post_save, sender=NotificationTemplate)
def notification_template_changed(sender, instance, created, **kwargs):
    """Обработчик изменения шаблона уведомлений"""
    action = 'создан' if created else 'изменен'
    logger.info(f'Шаблон уведомлений {instance.code} {action}')
    
    # Инвалидируем кеш шаблонов
    cache.delete('notification_templates')
    cache.delete(f'notification_template_{instance.code}')
    
    # Валидируем шаблон
    try:
        from .utils import NotificationRenderer
        
        # Тестируем рендеринг с пустым контекстом
        test_context = {'user': None, 'recipient': None}
        NotificationRenderer.render_notification_template(instance, test_context)
        
    except Exception as e:
        logger.warning(f'Потенциальная проблема с шаблоном {instance.code}: {str(e)}')


@receiver(post_save, sender=NotificationBatch)
def notification_batch_status_changed(sender, instance, created, **kwargs):
    """Обработчик изменения статуса пакета уведомлений"""
    if not created and instance.is_sent:
        logger.info(f'Пакет уведомлений {instance.id} отправлен: {instance.successful_sends} успешно, {instance.failed_sends} с ошибками')
        
        # Отправляем уведомление создателю пакета о завершении отправки
        if instance.created_by:
            try:
                completion_template = NotificationTemplate.objects.get(code='batch_completion')
                sender = NotificationSender()
                
                sender.send_notification(
                    recipient=instance.created_by,
                    template=completion_template,
                    context={
                        'batch_id': instance.id,
                        'template_name': instance.template.name,
                        'total_recipients': instance.total_recipients,
                        'successful_sends': instance.successful_sends,
                        'failed_sends': instance.failed_sends,
                        'success_rate': round((instance.successful_sends / instance.total_recipients) * 100, 1) if instance.total_recipients > 0 else 0
                    },
                    priority='low'
                )
            except NotificationTemplate.DoesNotExist:
                logger.warning('Шаблон уведомления о завершении пакета не найден')
            except Exception as e:
                logger.error(f'Ошибка отправки уведомления о завершении пакета: {str(e)}')


@receiver(post_save, sender=NotificationSettings)
def notification_settings_changed(sender, instance, created, **kwargs):
    """Обработчик изменения настроек уведомлений"""
    action = 'созданы' if created else 'изменены'
    logger.info(f'Настройки уведомлений пользователя {instance.user.username} {action}')
    
    # Инвалидируем кеш настроек пользователя
    cache.delete(f'notification_settings_{instance.user.id}')
    
    # Если пользователь отключил все уведомления, логируем это
    if not instance.email_notifications and not instance.push_notifications:
        logger.info(f'Пользователь {instance.user.username} отключил все уведомления')


# Сигналы для интеграции с другими приложениями

# Сигнал для проектов
try:
    from projects.models import Project, ProjectMembership
    
    @receiver(post_save, sender=Project)
    def project_created_notification(sender, instance, created, **kwargs):
        """Уведомление о создании проекта"""
        if created:
            try:
                template = NotificationTemplate.objects.get(code='project_created')
                notification_sender = NotificationSender()
                
                # Уведомляем всех администраторов
                admins = User.objects.filter(is_staff=True, is_active=True)
                
                for admin in admins:
                    notification_sender.send_notification(
                        recipient=admin,
                        template=template,
                        context={
                            'project': instance,
                            'project_name': instance.name,
                            'project_manager': instance.manager.get_full_name() if instance.manager else 'Не назначен'
                        },
                        sender=instance.manager,
                        priority='medium'
                    )
            
            except NotificationTemplate.DoesNotExist:
                pass
            except Exception as e:
                logger.error(f'Ошибка отправки уведомления о создании проекта: {str(e)}')
    
    @receiver(post_save, sender=ProjectMembership)
    def project_membership_notification(sender, instance, created, **kwargs):
        """Уведомление о добавлении в проект"""
        if created:
            try:
                template = NotificationTemplate.objects.get(code='project_member_added')
                notification_sender = NotificationSender()
                
                notification_sender.send_notification(
                    recipient=instance.user,
                    template=template,
                    context={
                        'project': instance.project,
                        'project_name': instance.project.name,
                        'role': instance.get_role_display(),
                        'added_by': instance.project.manager.get_full_name() if instance.project.manager else 'Администратор'
                    },
                    sender=instance.project.manager,
                    priority='medium'
                )
            
            except NotificationTemplate.DoesNotExist:
                pass
            except Exception as e:
                logger.error(f'Ошибка отправки уведомления о добавлении в проект: {str(e)}')

except ImportError:
    # Приложение projects не установлено
    pass


# Сигнал для объектов
try:
    from facilities.models import Facility, FacilityDocument
    
    @receiver(post_save, sender=Facility)
    def facility_status_changed_notification(sender, instance, **kwargs):
        """Уведомление об изменении статуса объекта"""
        if instance.pk:  # Только для существующих объектов
            try:
                old_instance = Facility.objects.get(pk=instance.pk)
                
                if old_instance.status != instance.status:
                    template = NotificationTemplate.objects.get(code='facility_status_changed')
                    notification_sender = NotificationSender()
                    
                    # Уведомляем ответственных за объект
                    if instance.project and instance.project.manager:
                        notification_sender.send_notification(
                            recipient=instance.project.manager,
                            template=template,
                            context={
                                'facility': instance,
                                'facility_name': instance.name,
                                'old_status': old_instance.get_status_display(),
                                'new_status': instance.get_status_display(),
                                'project_name': instance.project.name if instance.project else 'Не указан'
                            },
                            priority='medium'
                        )
            
            except (Facility.DoesNotExist, NotificationTemplate.DoesNotExist):
                pass
            except Exception as e:
                logger.error(f'Ошибка отправки уведомления об изменении статуса объекта: {str(e)}')
    
    @receiver(post_save, sender=FacilityDocument)
    def facility_document_uploaded_notification(sender, instance, created, **kwargs):
        """Уведомление о загрузке документа объекта"""
        if created:
            try:
                template = NotificationTemplate.objects.get(code='facility_document_uploaded')
                notification_sender = NotificationSender()
                
                # Уведомляем менеджера проекта
                if instance.facility.project and instance.facility.project.manager:
                    notification_sender.send_notification(
                        recipient=instance.facility.project.manager,
                        template=template,
                        context={
                            'document': instance,
                            'document_name': instance.name,
                            'facility_name': instance.facility.name,
                            'project_name': instance.facility.project.name,
                            'uploaded_by': instance.uploaded_by.get_full_name() if instance.uploaded_by else 'Неизвестно'
                        },
                        sender=instance.uploaded_by,
                        priority='low'
                    )
            
            except NotificationTemplate.DoesNotExist:
                pass
            except Exception as e:
                logger.error(f'Ошибка отправки уведомления о загрузке документа: {str(e)}')

except ImportError:
    # Приложение facilities не установлено
    pass


# Периодические задачи для обновления статистики
def schedule_periodic_tasks():
    """Планирует периодические задачи"""
    try:
        from django_celery_beat.models import PeriodicTask, CrontabSchedule
        import json
        
        # Очистка старых уведомлений (каждый день в 2:00)
        cleanup_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=2,
            day_of_week='*',
            day_of_month='*',
            month_of_year='*'
        )
        
        PeriodicTask.objects.get_or_create(
            name='Очистка старых уведомлений',
            defaults={
                'crontab': cleanup_schedule,
                'task': 'notifications.tasks.cleanup_old_notifications',
                'enabled': True
            }
        )
        
        # Отправка дайджестов (каждый день в 9:00)
        digest_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=9,
            day_of_week='*',
            day_of_month='*',
            month_of_year='*'
        )
        
        PeriodicTask.objects.get_or_create(
            name='Отправка дайджестов уведомлений',
            defaults={
                'crontab': digest_schedule,
                'task': 'notifications.tasks.send_digest_notifications',
                'enabled': True
            }
        )
        
        # Обновление статистики (каждый час)
        stats_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour='*',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*'
        )
        
        PeriodicTask.objects.get_or_create(
            name='Обновление статистики уведомлений',
            defaults={
                'crontab': stats_schedule,
                'task': 'notifications.tasks.update_notification_stats',
                'enabled': True
            }
        )
        
        logger.info('Периодические задачи для уведомлений настроены')
    
    except ImportError:
        logger.warning('django-celery-beat не установлен, периодические задачи не настроены')
    except Exception as e:
        logger.error(f'Ошибка настройки периодических задач: {str(e)}')


# Автоматическая настройка периодических задач при запуске
if hasattr(settings, 'NOTIFICATIONS_AUTO_SETUP_TASKS') and settings.NOTIFICATIONS_AUTO_SETUP_TASKS:
    schedule_periodic_tasks()