from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model
from datetime import timedelta
import logging

from .models import Facility, MaintenanceSchedule, FacilityImage, FacilityDocument

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=Facility)
def facility_post_save(sender, instance, created, **kwargs):
    """Обработка после сохранения объекта недвижимости"""
    try:
        # Очищаем кэш статистики
        cache.delete_many([
            'facility_statistics',
            f'facility_stats_project_{instance.project_id}',
            f'facility_stats_manager_{instance.manager_id}',
        ])
        
        if created:
            logger.info(f'Создан новый объект недвижимости: {instance.name} (ID: {instance.id})')
            
            # Создаем уведомление для управляющего
            if instance.manager:
                try:
                    from notifications.models import Notification
                    Notification.objects.create(
                        user=instance.manager,
                        title='Новый объект недвижимости',
                        message=f'Вам назначен новый объект: {instance.name}',
                        notification_type='facility_assigned',
                        related_object_type='facility',
                        related_object_id=instance.id
                    )
                except ImportError:
                    logger.warning('Модуль notifications не найден')
            
            # Создаем базовый график обслуживания для нового объекта
            if instance.facility_type:
                create_default_maintenance_schedule(instance)
        
        else:
            logger.info(f'Обновлен объект недвижимости: {instance.name} (ID: {instance.id})')
            
            # Проверяем изменение состояния
            if hasattr(instance, '_original_condition'):
                if instance._original_condition != instance.condition:
                    handle_condition_change(instance, instance._original_condition)
    
    except Exception as e:
        logger.error(f'Ошибка в сигнале facility_post_save: {e}')


@receiver(post_save, sender=MaintenanceSchedule)
def maintenance_schedule_post_save(sender, instance, created, **kwargs):
    """Обработка после сохранения графика обслуживания"""
    try:
        # Очищаем кэш
        cache.delete_many([
            'maintenance_statistics',
            f'maintenance_stats_facility_{instance.facility_id}',
            f'maintenance_stats_responsible_{instance.responsible_person_id}',
        ])
        
        if created:
            logger.info(f'Создан график обслуживания: {instance.name} для {instance.facility.name}')
            
            # Уведомляем ответственного
            if instance.responsible_person:
                try:
                    from notifications.models import Notification
                    Notification.objects.create(
                        user=instance.responsible_person,
                        title='Новое задание по обслуживанию',
                        message=f'Вам назначено обслуживание: {instance.name} для объекта {instance.facility.name}',
                        notification_type='maintenance_assigned',
                        related_object_type='maintenance_schedule',
                        related_object_id=instance.id
                    )
                except ImportError:
                    pass
        
        # Проверяем приближающиеся даты обслуживания
        check_upcoming_maintenance(instance)
    
    except Exception as e:
        logger.error(f'Ошибка в сигнале maintenance_schedule_post_save: {e}')


@receiver(pre_delete, sender=Facility)
def facility_pre_delete(sender, instance, **kwargs):
    """Обработка перед удалением объекта недвижимости"""
    try:
        logger.info(f'Удаляется объект недвижимости: {instance.name} (ID: {instance.id})')
        
        # Уведомляем связанных пользователей
        users_to_notify = []
        if instance.manager:
            users_to_notify.append(instance.manager)
        
        # Добавляем ответственных за обслуживание
        responsible_users = User.objects.filter(
            maintenance_schedules__facility=instance
        ).distinct()
        users_to_notify.extend(responsible_users)
        
        # Отправляем уведомления
        try:
            from notifications.models import Notification
            for user in users_to_notify:
                Notification.objects.create(
                    user=user,
                    title='Объект недвижимости удален',
                    message=f'Объект "{instance.name}" был удален из системы',
                    notification_type='facility_deleted',
                    priority='high'
                )
        except ImportError:
            pass
    
    except Exception as e:
        logger.error(f'Ошибка в сигнале facility_pre_delete: {e}')


@receiver(post_delete, sender=FacilityImage)
def facility_image_post_delete(sender, instance, **kwargs):
    """Удаление файла изображения после удаления записи"""
    try:
        if instance.image and hasattr(instance.image, 'delete'):
            instance.image.delete(save=False)
            logger.info(f'Удален файл изображения: {instance.image.name}')
    except Exception as e:
        logger.error(f'Ошибка при удалении файла изображения: {e}')


@receiver(post_delete, sender=FacilityDocument)
def facility_document_post_delete(sender, instance, **kwargs):
    """Удаление файла документа после удаления записи"""
    try:
        if instance.document and hasattr(instance.document, 'delete'):
            instance.document.delete(save=False)
            logger.info(f'Удален файл документа: {instance.document.name}')
    except Exception as e:
        logger.error(f'Ошибка при удалении файла документа: {e}')


def create_default_maintenance_schedule(facility):
    """Создание базового графика обслуживания для нового объекта"""
    try:
        # Создаем стандартные графики обслуживания в зависимости от типа объекта
        default_schedules = {
            'office': [
                {
                    'name': 'Техническое обслуживание систем',
                    'description': 'Проверка и обслуживание инженерных систем',
                    'frequency': 'monthly',
                    'estimated_duration_hours': 4,
                    'estimated_cost': 5000.00
                },
                {
                    'name': 'Уборка и санитарная обработка',
                    'description': 'Генеральная уборка помещений',
                    'frequency': 'weekly',
                    'estimated_duration_hours': 8,
                    'estimated_cost': 3000.00
                }
            ],
            'warehouse': [
                {
                    'name': 'Проверка систем безопасности',
                    'description': 'Контроль работы охранных и пожарных систем',
                    'frequency': 'monthly',
                    'estimated_duration_hours': 2,
                    'estimated_cost': 2000.00
                }
            ],
            'residential': [
                {
                    'name': 'Обслуживание общих зон',
                    'description': 'Уборка и обслуживание подъездов, лифтов',
                    'frequency': 'weekly',
                    'estimated_duration_hours': 6,
                    'estimated_cost': 4000.00
                }
            ]
        }
        
        facility_type_name = facility.facility_type.name.lower() if facility.facility_type else 'office'
        schedules_to_create = default_schedules.get(facility_type_name, default_schedules['office'])
        
        for schedule_data in schedules_to_create:
            MaintenanceSchedule.objects.create(
                facility=facility,
                name=schedule_data['name'],
                description=schedule_data['description'],
                frequency=schedule_data['frequency'],
                estimated_duration_hours=schedule_data['estimated_duration_hours'],
                estimated_cost=schedule_data['estimated_cost'],
                start_date=timezone.now().date(),
                status='active'
            )
        
        logger.info(f'Созданы базовые графики обслуживания для объекта {facility.name}')
    
    except Exception as e:
        logger.error(f'Ошибка при создании базовых графиков обслуживания: {e}')


def handle_condition_change(facility, old_condition):
    """Обработка изменения состояния объекта"""
    try:
        # Если состояние ухудшилось до критического
        if facility.condition == 'critical' and old_condition != 'critical':
            # Уведомляем управляющего и администраторов
            users_to_notify = [facility.manager] if facility.manager else []
            
            # Добавляем администраторов
            admin_users = User.objects.filter(role='admin')
            users_to_notify.extend(admin_users)
            
            try:
                from notifications.models import Notification
                for user in users_to_notify:
                    if user:
                        Notification.objects.create(
                            user=user,
                            title='Критическое состояние объекта',
                            message=f'Объект "{facility.name}" находится в критическом состоянии и требует немедленного внимания',
                            notification_type='facility_critical',
                            priority='critical',
                            related_object_type='facility',
                            related_object_id=facility.id
                        )
            except ImportError:
                pass
        
        logger.info(f'Изменено состояние объекта {facility.name}: {old_condition} -> {facility.condition}')
    
    except Exception as e:
        logger.error(f'Ошибка при обработке изменения состояния: {e}')


def check_upcoming_maintenance(maintenance_schedule):
    """Проверка приближающихся дат обслуживания"""
    try:
        if not maintenance_schedule.next_maintenance_date:
            return
        
        days_until_maintenance = (maintenance_schedule.next_maintenance_date - timezone.now().date()).days
        
        # Уведомляем за 7 дней до обслуживания
        if days_until_maintenance == 7:
            users_to_notify = []
            if maintenance_schedule.responsible_person:
                users_to_notify.append(maintenance_schedule.responsible_person)
            if maintenance_schedule.facility.manager:
                users_to_notify.append(maintenance_schedule.facility.manager)
            
            try:
                from notifications.models import Notification
                for user in users_to_notify:
                    if user:
                        Notification.objects.create(
                            user=user,
                            title='Приближается обслуживание',
                            message=f'Через неделю запланировано обслуживание "{maintenance_schedule.name}" для объекта {maintenance_schedule.facility.name}',
                            notification_type='maintenance_reminder',
                            related_object_type='maintenance_schedule',
                            related_object_id=maintenance_schedule.id
                        )
            except ImportError:
                pass
        
        # Уведомляем о просроченном обслуживании
        elif days_until_maintenance < 0:
            users_to_notify = []
            if maintenance_schedule.responsible_person:
                users_to_notify.append(maintenance_schedule.responsible_person)
            if maintenance_schedule.facility.manager:
                users_to_notify.append(maintenance_schedule.facility.manager)
            
            try:
                from notifications.models import Notification
                for user in users_to_notify:
                    if user:
                        Notification.objects.create(
                            user=user,
                            title='Просроченное обслуживание',
                            message=f'Обслуживание "{maintenance_schedule.name}" для объекта {maintenance_schedule.facility.name} просрочено на {abs(days_until_maintenance)} дней',
                            notification_type='maintenance_overdue',
                            priority='high',
                            related_object_type='maintenance_schedule',
                            related_object_id=maintenance_schedule.id
                        )
            except ImportError:
                pass
    
    except Exception as e:
        logger.error(f'Ошибка при проверке дат обслуживания: {e}')