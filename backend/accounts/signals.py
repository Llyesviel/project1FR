from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils import timezone
import logging

from .models import User, UserProfile, UserSession

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Создание профиля пользователя при создании пользователя"""
    if created:
        profile, profile_created = UserProfile.objects.get_or_create(user=instance)
        if profile_created:
            logger.info(f'Создан профиль для пользователя {instance.email}')
        else:
            logger.info(f'Профиль для пользователя {instance.email} уже существует')


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Сохранение профиля пользователя при сохранении пользователя"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        # Если профиль не существует, создаем его
        profile, created = UserProfile.objects.get_or_create(user=instance)
        if created:
            logger.info(f'Создан отсутствующий профиль для пользователя {instance.email}')


@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    """Обработка входа пользователя в систему"""
    # Обновляем время последней активности
    user.last_activity = timezone.now()
    user.save(update_fields=['last_activity'])
    
    # Получаем информацию о сессии
    session_key = request.session.session_key
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Создаем или обновляем запись о сессии
    if session_key:
        UserSession.objects.update_or_create(
            session_key=session_key,
            defaults={
                'user': user,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'is_active': True
            }
        )
    
    logger.info(
        f'Пользователь {user.email} вошел в систему. '
        f'IP: {ip_address}, User-Agent: {user_agent[:50]}...'
    )


@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    """Обработка выхода пользователя из системы"""
    if user:
        # Деактивируем сессию
        session_key = request.session.session_key
        if session_key:
            UserSession.objects.filter(
                session_key=session_key,
                user=user
            ).update(is_active=False)
        
        logger.info(f'Пользователь {user.email} вышел из системы')


@receiver(pre_save, sender=User)
def user_pre_save_handler(sender, instance, **kwargs):
    """Обработка изменений пользователя перед сохранением"""
    if instance.pk:
        try:
            old_instance = User.objects.get(pk=instance.pk)
            
            # Логируем изменение роли
            if old_instance.role != instance.role:
                logger.info(
                    f'Роль пользователя {instance.email} изменена '
                    f'с {old_instance.get_role_display()} на {instance.get_role_display()}'
                )
            
            # Логируем изменение статуса активности
            if old_instance.is_active != instance.is_active:
                status = 'активирован' if instance.is_active else 'деактивирован'
                logger.info(f'Пользователь {instance.email} {status}')
                
                # Если пользователь деактивирован, деактивируем все его сессии
                if not instance.is_active:
                    UserSession.objects.filter(user=instance).update(is_active=False)
            
            # Логируем изменение email
            if old_instance.email != instance.email:
                logger.info(
                    f'Email пользователя изменен с {old_instance.email} на {instance.email}'
                )
        
        except User.DoesNotExist:
            pass


@receiver(post_delete, sender=User)
def user_deleted_handler(sender, instance, **kwargs):
    """Обработка удаления пользователя"""
    logger.warning(f'Пользователь {instance.email} удален из системы')


@receiver(post_save, sender=UserSession)
def user_session_created_handler(sender, instance, created, **kwargs):
    """Обработка создания новой сессии пользователя"""
    if created:
        # Ограничиваем количество активных сессий для одного пользователя
        max_sessions = 5
        active_sessions = UserSession.objects.filter(
            user=instance.user,
            is_active=True
        ).order_by('-created_at')
        
        if active_sessions.count() > max_sessions:
            # Деактивируем старые сессии
            old_sessions = active_sessions[max_sessions:]
            for session in old_sessions:
                session.is_active = False
                session.save()
            
            logger.info(
                f'Деактивированы старые сессии пользователя {instance.user.email}. '
                f'Превышен лимит в {max_sessions} активных сессий.'
            )


def get_client_ip(request):
    """Получение IP адреса клиента"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# Дополнительные сигналы для безопасности

@receiver(post_save, sender=User)
def check_suspicious_activity(sender, instance, **kwargs):
    """Проверка подозрительной активности"""
    if not kwargs.get('created', False):
        # Проверяем количество неудачных попыток входа
        # Это можно расширить для более сложной логики безопасности
        pass


@receiver(post_save, sender=UserSession)
def detect_multiple_logins(sender, instance, created, **kwargs):
    """Обнаружение множественных входов с разных устройств"""
    if created:
        # Проверяем, есть ли активные сессии с других IP
        other_active_sessions = UserSession.objects.filter(
            user=instance.user,
            is_active=True
        ).exclude(id=instance.id).exclude(ip_address=instance.ip_address)
        
        if other_active_sessions.exists():
            logger.warning(
                f'Пользователь {instance.user.email} вошел с нового IP {instance.ip_address}. '
                f'Обнаружены активные сессии с других IP адресов.'
            )