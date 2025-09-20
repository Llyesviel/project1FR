from django.db.models.signals import post_save, post_delete, pre_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from .models import Project, ProjectMembership, Facility, FacilityDocument
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=Project)
def project_created_handler(sender, instance, created, **kwargs):
    """Обработчик создания проекта"""
    if created:
        try:
            # Автоматически добавляем создателя как менеджера проекта
            if instance.created_by and instance.created_by != instance.manager:
                ProjectMembership.objects.get_or_create(
                    project=instance,
                    user=instance.created_by,
                    defaults={
                        'role': ProjectMembership.Role.MANAGER,
                        'joined_at': timezone.now(),
                        'is_active': True
                    }
                )
            
            # Добавляем менеджера проекта в команду
            if instance.manager:
                ProjectMembership.objects.get_or_create(
                    project=instance,
                    user=instance.manager,
                    defaults={
                        'role': ProjectMembership.Role.MANAGER,
                        'joined_at': timezone.now(),
                        'is_active': True
                    }
                )
            
            # Отправляем уведомление менеджеру
            if instance.manager and instance.manager.email:
                send_notification_email(
                    instance.manager.email,
                    'Новый проект назначен',
                    f'Вы назначены менеджером проекта "{instance.name}". '
                    f'Описание: {instance.description}'
                )
            
            logger.info(f'Создан новый проект: {instance.name} (ID: {instance.id})')
            
        except Exception as e:
            logger.error(f'Ошибка при обработке создания проекта {instance.id}: {str(e)}')


@receiver(pre_save, sender=Project)
def project_pre_save_handler(sender, instance, **kwargs):
    """Обработчик перед сохранением проекта"""
    try:
        # Проверяем изменение менеджера
        if instance.pk:
            old_instance = Project.objects.get(pk=instance.pk)
            
            # Если менеджер изменился
            if old_instance.manager != instance.manager:
                # Деактивируем старого менеджера в команде (если он не создатель)
                if old_instance.manager and old_instance.manager != instance.created_by:
                    ProjectMembership.objects.filter(
                        project=instance,
                        user=old_instance.manager,
                        role=ProjectMembership.Role.MANAGER
                    ).update(is_active=False, left_at=timezone.now())
                
                # Отправляем уведомление старому менеджеру
                if old_instance.manager and old_instance.manager.email:
                    send_notification_email(
                        old_instance.manager.email,
                        'Изменение роли в проекте',
                        f'Вы больше не являетесь менеджером проекта "{instance.name}".'
                    )
            
            # Проверяем изменение статуса
            if old_instance.status != instance.status:
                logger.info(
                    f'Статус проекта {instance.name} изменен с '
                    f'{old_instance.get_status_display()} на {instance.get_status_display()}'
                )
                
                # Уведомляем команду об изменении статуса
                notify_team_about_status_change(instance, old_instance.status, instance.status)
    
    except Project.DoesNotExist:
        pass  # Новый проект
    except Exception as e:
        logger.error(f'Ошибка в pre_save для проекта {instance.id}: {str(e)}')


@receiver(post_save, sender=ProjectMembership)
def project_membership_handler(sender, instance, created, **kwargs):
    """Обработчик изменений в составе команды проекта"""
    try:
        if created and instance.is_active:
            # Отправляем уведомление новому участнику
            if instance.user.email:
                send_notification_email(
                    instance.user.email,
                    'Добавление в команду проекта',
                    f'Вы добавлены в команду проекта "{instance.project.name}" '
                    f'с ролью {instance.get_role_display()}.'
                )
            
            logger.info(
                f'Пользователь {instance.user.username} добавлен в проект '
                f'{instance.project.name} с ролью {instance.get_role_display()}'
            )
        
        elif not created:
            # Проверяем изменения в существующем участии
            old_instance = ProjectMembership.objects.get(pk=instance.pk)
            
            # Если участник деактивирован
            if old_instance.is_active and not instance.is_active:
                if instance.user.email:
                    send_notification_email(
                        instance.user.email,
                        'Исключение из команды проекта',
                        f'Вы исключены из команды проекта "{instance.project.name}".'
                    )
                
                logger.info(
                    f'Пользователь {instance.user.username} исключен из проекта '
                    f'{instance.project.name}'
                )
    
    except Exception as e:
        logger.error(f'Ошибка при обработке участия в проекте {instance.id}: {str(e)}')


@receiver(post_save, sender=Facility)
def facility_created_handler(sender, instance, created, **kwargs):
    """Обработчик создания/изменения объекта"""
    try:
        if created:
            # Отправляем уведомление ответственному
            if instance.responsible_person and instance.responsible_person.email:
                send_notification_email(
                    instance.responsible_person.email,
                    'Назначение ответственным за объект',
                    f'Вы назначены ответственным за объект "{instance.name}" '
                    f'в проекте "{instance.project.name}".'
                )
            
            # Уведомляем менеджера проекта
            if instance.project.manager and instance.project.manager.email:
                send_notification_email(
                    instance.project.manager.email,
                    'Новый объект в проекте',
                    f'В проекте "{instance.project.name}" создан новый объект "{instance.name}".'
                )
            
            logger.info(
                f'Создан новый объект: {instance.name} в проекте {instance.project.name}'
            )
        
        else:
            # Проверяем изменения в существующем объекте
            old_instance = Facility.objects.get(pk=instance.pk)
            
            # Проверяем изменение ответственного
            if old_instance.responsible_person != instance.responsible_person:
                # Уведомляем старого ответственного
                if old_instance.responsible_person and old_instance.responsible_person.email:
                    send_notification_email(
                        old_instance.responsible_person.email,
                        'Изменение ответственности за объект',
                        f'Вы больше не являетесь ответственным за объект "{instance.name}".'
                    )
                
                # Уведомляем нового ответственного
                if instance.responsible_person and instance.responsible_person.email:
                    send_notification_email(
                        instance.responsible_person.email,
                        'Назначение ответственным за объект',
                        f'Вы назначены ответственным за объект "{instance.name}" '
                        f'в проекте "{instance.project.name}".'
                    )
            
            # Проверяем изменение статуса
            if old_instance.status != instance.status:
                logger.info(
                    f'Статус объекта {instance.name} изменен с '
                    f'{old_instance.get_status_display()} на {instance.get_status_display()}'
                )
                
                # Уведомляем заинтересованных лиц об изменении статуса
                notify_about_facility_status_change(instance, old_instance.status, instance.status)
    
    except Facility.DoesNotExist:
        pass  # Новый объект
    except Exception as e:
        logger.error(f'Ошибка при обработке объекта {instance.id}: {str(e)}')


@receiver(post_save, sender=FacilityDocument)
def document_uploaded_handler(sender, instance, created, **kwargs):
    """Обработчик загрузки документа"""
    if created:
        try:
            # Уведомляем ответственного за объект
            if instance.facility.responsible_person and instance.facility.responsible_person.email:
                send_notification_email(
                    instance.facility.responsible_person.email,
                    'Новый документ загружен',
                    f'К объекту "{instance.facility.name}" добавлен новый документ '
                    f'"{instance.name}" типа {instance.get_document_type_display()}.'
                )
            
            # Уведомляем менеджера проекта
            if instance.facility.project.manager and instance.facility.project.manager.email:
                send_notification_email(
                    instance.facility.project.manager.email,
                    'Новый документ в проекте',
                    f'В проекте "{instance.facility.project.name}" к объекту '
                    f'"{instance.facility.name}" добавлен документ "{instance.name}".'
                )
            
            logger.info(
                f'Загружен документ {instance.name} для объекта {instance.facility.name}'
            )
        
        except Exception as e:
            logger.error(f'Ошибка при обработке загрузки документа {instance.id}: {str(e)}')


@receiver(post_delete, sender=Project)
def project_deleted_handler(sender, instance, **kwargs):
    """Обработчик удаления проекта"""
    try:
        logger.info(f'Удален проект: {instance.name} (ID: {instance.id})')
        
        # Уведомляем команду об удалении проекта
        team_members = User.objects.filter(
            projectmembership__project=instance,
            projectmembership__is_active=True
        ).distinct()
        
        for member in team_members:
            if member.email:
                send_notification_email(
                    member.email,
                    'Проект удален',
                    f'Проект "{instance.name}", в котором вы участвовали, был удален.'
                )
    
    except Exception as e:
        logger.error(f'Ошибка при обработке удаления проекта: {str(e)}')


@receiver(post_delete, sender=Facility)
def facility_deleted_handler(sender, instance, **kwargs):
    """Обработчик удаления объекта"""
    try:
        logger.info(f'Удален объект: {instance.name} из проекта {instance.project.name}')
        
        # Уведомляем ответственного
        if instance.responsible_person and instance.responsible_person.email:
            send_notification_email(
                instance.responsible_person.email,
                'Объект удален',
                f'Объект "{instance.name}", за который вы были ответственны, был удален.'
            )
    
    except Exception as e:
        logger.error(f'Ошибка при обработке удаления объекта: {str(e)}')


def send_notification_email(email, subject, message):
    """Отправка уведомления по email"""
    try:
        if hasattr(settings, 'EMAIL_NOTIFICATIONS_ENABLED') and settings.EMAIL_NOTIFICATIONS_ENABLED:
            send_mail(
                subject=f'[Система управления объектами] {subject}',
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True
            )
    except Exception as e:
        logger.error(f'Ошибка отправки email уведомления: {str(e)}')


def notify_team_about_status_change(project, old_status, new_status):
    """Уведомление команды об изменении статуса проекта"""
    try:
        team_members = User.objects.filter(
            projectmembership__project=project,
            projectmembership__is_active=True
        ).distinct()
        
        for member in team_members:
            if member.email:
                send_notification_email(
                    member.email,
                    'Изменение статуса проекта',
                    f'Статус проекта "{project.name}" изменен с '
                    f'{Project.Status(old_status).label} на {Project.Status(new_status).label}.'
                )
    
    except Exception as e:
        logger.error(f'Ошибка уведомления команды о статусе проекта: {str(e)}')


def notify_about_facility_status_change(facility, old_status, new_status):
    """Уведомление об изменении статуса объекта"""
    try:
        # Уведомляем ответственного за объект
        if facility.responsible_person and facility.responsible_person.email:
            send_notification_email(
                facility.responsible_person.email,
                'Изменение статуса объекта',
                f'Статус объекта "{facility.name}" изменен с '
                f'{Facility.Status(old_status).label} на {Facility.Status(new_status).label}.'
            )
        
        # Уведомляем менеджера проекта
        if facility.project.manager and facility.project.manager.email:
            send_notification_email(
                facility.project.manager.email,
                'Изменение статуса объекта в проекте',
                f'В проекте "{facility.project.name}" статус объекта "{facility.name}" '
                f'изменен с {Facility.Status(old_status).label} на {Facility.Status(new_status).label}.'
            )
    
    except Exception as e:
        logger.error(f'Ошибка уведомления об изменении статуса объекта: {str(e)}')


@receiver(pre_delete, sender=FacilityDocument)
def document_pre_delete_handler(sender, instance, **kwargs):
    """Обработчик перед удалением документа"""
    try:
        # Логируем удаление документа
        logger.info(
            f'Удаляется документ {instance.name} объекта {instance.facility.name} '
            f'пользователем {instance.uploaded_by}'
        )
        
        # Можно добавить дополнительную логику, например:
        # - Создание резервной копии
        # - Уведомление заинтересованных лиц
        # - Проверка прав на удаление
        
    except Exception as e:
        logger.error(f'Ошибка при подготовке к удалению документа: {str(e)}')


# Функция для автоматического обновления прогресса проекта
def update_project_progress(project):
    """Автоматическое обновление прогресса проекта на основе статусов объектов"""
    try:
        facilities = project.facilities.all()
        total_facilities = facilities.count()
        
        if total_facilities == 0:
            project.progress = 0
        else:
            completed_facilities = facilities.filter(
                status__in=[Facility.Status.COMPLETED, Facility.Status.ACCEPTED]
            ).count()
            
            project.progress = (completed_facilities / total_facilities) * 100
        
        project.save(update_fields=['progress'])
        
    except Exception as e:
        logger.error(f'Ошибка обновления прогресса проекта {project.id}: {str(e)}')


# Сигнал для автоматического обновления прогресса при изменении статуса объекта
@receiver(post_save, sender=Facility)
def update_project_progress_on_facility_change(sender, instance, **kwargs):
    """Обновление прогресса проекта при изменении объекта"""
    try:
        # Обновляем прогресс проекта в отдельной транзакции
        transaction.on_commit(lambda: update_project_progress(instance.project))
    except Exception as e:
        logger.error(f'Ошибка обновления прогресса при изменении объекта: {str(e)}')