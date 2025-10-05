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
        def handle_project_creation():
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
        
        # Выполняем операции после завершения транзакции
        transaction.on_commit(handle_project_creation)


@receiver(pre_save, sender=Project)
def project_pre_save_handler(sender, instance, **kwargs):
    """Обработчик перед сохранением проекта"""
    # Получаем данные старого проекта до транзакции (если это обновление)
    old_instance_data = None
    if instance.pk:
        try:
            old_project = Project.objects.get(pk=instance.pk)
            old_instance_data = {
                'manager': old_project.manager,
                'status': old_project.status,
                'status_display': old_project.get_status_display()
            }
        except Project.DoesNotExist:
            pass  # Новый проект
    
    try:
        # Проверяем изменение менеджера
        if old_instance_data:
            # Если менеджер изменился
            if old_instance_data['manager'] != instance.manager:
                def handle_manager_change():
                    try:
                        # Деактивируем старого менеджера в команде (если он не создатель)
                        if old_instance_data['manager'] and old_instance_data['manager'] != instance.created_by:
                            ProjectMembership.objects.filter(
                                project=instance,
                                user=old_instance_data['manager'],
                                role=ProjectMembership.Role.MANAGER
                            ).update(is_active=False, left_at=timezone.now())
                        
                        # Отправляем уведомление старому менеджеру
                        if old_instance_data['manager'] and old_instance_data['manager'].email:
                            send_notification_email(
                                old_instance_data['manager'].email,
                                'Изменение роли в проекте',
                                f'Вы больше не являетесь менеджером проекта "{instance.name}".'
                            )
                    except Exception as e:
                        logger.error(f'Ошибка при изменении менеджера проекта: {str(e)}')
                
                # Выполняем операции после завершения транзакции
                transaction.on_commit(handle_manager_change)
            
            # Проверяем изменение статуса
            if old_instance_data['status'] != instance.status:
                logger.info(
                    f'Статус проекта {instance.name} изменен с '
                    f'{old_instance_data["status_display"]} на {instance.get_status_display()}'
                )
                
                def handle_status_change():
                    try:
                        # Уведомляем команду об изменении статуса
                        notify_team_about_status_change(instance, old_instance_data['status'], instance.status)
                    except Exception as e:
                        logger.error(f'Ошибка при уведомлении об изменении статуса: {str(e)}')
                
                # Выполняем операции после завершения транзакции
                transaction.on_commit(handle_status_change)
    
    except Exception as e:
        logger.error(f'Ошибка в pre_save для проекта {instance.id}: {str(e)}')


@receiver(post_save, sender=ProjectMembership)
def project_membership_handler(sender, instance, created, **kwargs):
    """Обработчик изменений в составе команды проекта"""
    # Получаем данные старого участия до транзакции (если это обновление)
    old_instance_data = None
    if not created:
        try:
            old_membership = ProjectMembership.objects.get(pk=instance.pk)
            old_instance_data = {
                'is_active': old_membership.is_active
            }
        except ProjectMembership.DoesNotExist:
            pass  # Новое участие
    
    def handle_membership_change():
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
            
            elif not created and old_instance_data:
                # Проверяем изменения в существующем участии
                # Если участник деактивирован
                if old_instance_data['is_active'] and not instance.is_active:
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
    
    # Выполняем операции после завершения транзакции
    transaction.on_commit(handle_membership_change)


@receiver(post_save, sender=Facility)
def facility_created_handler(sender, instance, created, **kwargs):
    """Обработчик создания/изменения объекта"""
    # Получаем данные старого объекта до транзакции (если это обновление)
    old_instance_data = None
    if not created:
        try:
            # Сохраняем только необходимые данные для сравнения
            old_facility = Facility.objects.get(pk=instance.pk)
            old_instance_data = {
                'responsible_person': old_facility.responsible_person,
                'status': old_facility.status,
                'status_display': old_facility.get_status_display()
            }
        except Facility.DoesNotExist:
            pass  # Новый объект
    
    def handle_facility_change():
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
                if old_instance_data:
                    # Проверяем изменение ответственного
                    if old_instance_data['responsible_person'] != instance.responsible_person:
                        # Уведомляем старого ответственного
                        if old_instance_data['responsible_person'] and old_instance_data['responsible_person'].email:
                            send_notification_email(
                                old_instance_data['responsible_person'].email,
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
                    if old_instance_data['status'] != instance.status:
                        logger.info(
                            f'Статус объекта {instance.name} изменен с '
                            f'{old_instance_data["status_display"]} на {instance.get_status_display()}'
                        )
                        
                        # Уведомляем заинтересованных лиц об изменении статуса
                        notify_about_facility_status_change(instance, old_instance_data['status'], instance.status)
        
        except Exception as e:
            logger.error(f'Ошибка при обработке объекта {instance.id}: {str(e)}')
    
    # Выполняем операции после завершения транзакции
    transaction.on_commit(handle_facility_change)


@receiver(post_save, sender=FacilityDocument)
def document_uploaded_handler(sender, instance, created, **kwargs):
    """Обработчик загрузки документа"""
    if created:
        def handle_document_upload():
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
        
        # Выполняем операции после завершения транзакции
        transaction.on_commit(handle_document_upload)


@receiver(post_delete, sender=Project)
def project_deleted_handler(sender, instance, **kwargs):
    """Обработчик удаления проекта"""
    # Сохраняем данные проекта для использования после транзакции
    project_name = instance.name
    project_id = instance.id
    
    def handle_project_deletion():
        try:
            logger.info(f'Удален проект: {project_name} (ID: {project_id})')
            
            # Уведомляем команду об удалении проекта
            # Поскольку проект уже удален, мы не можем получить участников через связи
            # Этот функционал требует предварительного сохранения данных участников
            
        except Exception as e:
            logger.error(f'Ошибка при обработке удаления проекта: {str(e)}')
    
    # Выполняем операции после завершения транзакции
    transaction.on_commit(handle_project_deletion)


@receiver(post_delete, sender=Facility)
def facility_deleted_handler(sender, instance, **kwargs):
    """Обработчик удаления объекта"""
    # Сохраняем данные объекта для использования после транзакции
    facility_name = instance.name
    project_name = instance.project.name
    responsible_person_email = instance.responsible_person.email if instance.responsible_person else None
    
    def handle_facility_deletion():
        try:
            logger.info(f'Удален объект: {facility_name} из проекта {project_name}')
            
            # Уведомляем ответственного
            if responsible_person_email:
                send_notification_email(
                    responsible_person_email,
                    'Объект удален',
                    f'Объект "{facility_name}", за который вы были ответственны, был удален.'
                )
        
        except Exception as e:
            logger.error(f'Ошибка при обработке удаления объекта: {str(e)}')
    
    # Выполняем операции после завершения транзакции
    transaction.on_commit(handle_facility_deletion)


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