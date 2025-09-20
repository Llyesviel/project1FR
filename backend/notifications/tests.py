from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core import mail
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from datetime import timedelta

from .models import (
    Notification, NotificationTemplate, NotificationSettings, 
    NotificationBatch
)
from .serializers import (
    NotificationSerializer, NotificationTemplateSerializer,
    NotificationSettingsSerializer, NotificationBatchSerializer
)
from .utils import NotificationSender, NotificationRenderer
from .tasks import (
    send_email_notification, send_push_notification,
    process_notification_batch, cleanup_old_notifications
)

User = get_user_model()


class NotificationModelTest(TestCase):
    """Тесты для модели Notification"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.sender = User.objects.create_user(
            username='sender',
            email='sender@example.com',
            password='testpass123'
        )
    
    def test_create_notification(self):
        """Тест создания уведомления"""
        notification = Notification.objects.create(
            recipient=self.user,
            sender=self.sender,
            title='Test Notification',
            message='This is a test message',
            notification_type='info',
            category='general'
        )
        
        self.assertEqual(notification.recipient, self.user)
        self.assertEqual(notification.sender, self.sender)
        self.assertEqual(notification.title, 'Test Notification')
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)
    
    def test_mark_as_read(self):
        """Тест отметки уведомления как прочитанного"""
        notification = Notification.objects.create(
            recipient=self.user,
            title='Test Notification',
            message='Test message'
        )
        
        # Отмечаем как прочитанное
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)
    
    def test_notification_expiration(self):
        """Тест истечения срока действия уведомления"""
        expires_at = timezone.now() + timedelta(days=7)
        notification = Notification.objects.create(
            recipient=self.user,
            title='Expiring Notification',
            message='This notification will expire',
            expires_at=expires_at
        )
        
        self.assertEqual(notification.expires_at, expires_at)
        self.assertFalse(notification.is_expired)
        
        # Устанавливаем дату истечения в прошлом
        notification.expires_at = timezone.now() - timedelta(days=1)
        notification.save()
        
        self.assertTrue(notification.is_expired)


class NotificationTemplateModelTest(TestCase):
    """Тесты для модели NotificationTemplate"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
    
    def test_create_template(self):
        """Тест создания шаблона уведомления"""
        template = NotificationTemplate.objects.create(
            name='Welcome Template',
            code='welcome',
            title_template='Welcome {{ user.first_name }}!',
            message_template='Hello {{ user.first_name }}, welcome to our system!',
            notification_type='info',
            category='user',
            created_by=self.user
        )
        
        self.assertEqual(template.name, 'Welcome Template')
        self.assertEqual(template.code, 'welcome')
        self.assertTrue(template.is_active)
        self.assertEqual(template.created_by, self.user)
    
    def test_template_rendering(self):
        """Тест рендеринга шаблона"""
        template = NotificationTemplate.objects.create(
            name='Test Template',
            code='test',
            title_template='Hello {{ user.first_name }}!',
            message_template='Welcome {{ user.first_name }} {{ user.last_name }}!'
        )
        
        user = User.objects.create_user(
            username='john',
            first_name='John',
            last_name='Doe',
            email='john@example.com'
        )
        
        renderer = NotificationRenderer()
        context = {'user': user}
        
        rendered_title = renderer.render_template(template.title_template, context)
        rendered_message = renderer.render_template(template.message_template, context)
        
        self.assertEqual(rendered_title, 'Hello John!')
        self.assertEqual(rendered_message, 'Welcome John Doe!')


class NotificationSettingsModelTest(TestCase):
    """Тесты для модели NotificationSettings"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_settings(self):
        """Тест создания настроек уведомлений"""
        settings = NotificationSettings.objects.create(
            user=self.user,
            email_notifications=True,
            push_notifications=False,
            digest_frequency='weekly'
        )
        
        self.assertEqual(settings.user, self.user)
        self.assertTrue(settings.email_notifications)
        self.assertFalse(settings.push_notifications)
        self.assertEqual(settings.digest_frequency, 'weekly')
    
    def test_default_settings(self):
        """Тест настроек по умолчанию"""
        settings = NotificationSettings.objects.create(user=self.user)
        
        self.assertTrue(settings.email_notifications)
        self.assertTrue(settings.push_notifications)
        self.assertEqual(settings.digest_frequency, 'daily')
        self.assertEqual(settings.auto_delete_read_after_days, 30)


class NotificationAPITest(APITestCase):
    """Тесты для API уведомлений"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Создаем тестовые уведомления
        self.notification1 = Notification.objects.create(
            recipient=self.user,
            title='Test Notification 1',
            message='First test message',
            notification_type='info'
        )
        self.notification2 = Notification.objects.create(
            recipient=self.user,
            title='Test Notification 2',
            message='Second test message',
            notification_type='warning',
            is_read=True
        )
    
    def test_list_notifications(self):
        """Тест получения списка уведомлений"""
        url = reverse('notification-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_filter_unread_notifications(self):
        """Тест фильтрации непрочитанных уведомлений"""
        url = reverse('notification-list')
        response = self.client.get(url, {'is_read': 'false'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.notification1.id)
    
    def test_mark_notification_as_read(self):
        """Тест отметки уведомления как прочитанного"""
        url = reverse('notification-mark-read', kwargs={'pk': self.notification1.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.notification1.refresh_from_db()
        self.assertTrue(self.notification1.is_read)
        self.assertIsNotNone(self.notification1.read_at)
    
    def test_get_unread_count(self):
        """Тест получения количества непрочитанных уведомлений"""
        url = reverse('notification-unread')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
    
    def test_bulk_mark_as_read(self):
        """Тест массовой отметки уведомлений как прочитанных"""
        url = reverse('notification-bulk-mark-read')
        data = {'notification_ids': [self.notification1.id]}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.notification1.refresh_from_db()
        self.assertTrue(self.notification1.is_read)


class NotificationUtilsTest(TestCase):
    """Тесты для утилит уведомлений"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.template = NotificationTemplate.objects.create(
            name='Test Template',
            code='test',
            title_template='Hello {{ user.first_name }}!',
            message_template='Welcome {{ user.first_name }}!',
            email_subject_template='Welcome {{ user.first_name }}',
            email_body_template='Hello {{ user.first_name }}, welcome!'
        )
    
    def test_notification_sender(self):
        """Тест отправки уведомлений"""
        sender = NotificationSender()
        context = {'user': self.user}
        
        notification = sender.send_from_template(
            template_code='test',
            recipient=self.user,
            context=context
        )
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.recipient, self.user)
        self.assertEqual(notification.title, f'Hello {self.user.first_name}!')
    
    @patch('notifications.tasks.send_email_notification.delay')
    def test_email_notification_task(self, mock_task):
        """Тест задачи отправки email уведомления"""
        notification = Notification.objects.create(
            recipient=self.user,
            title='Test Email',
            message='Test message'
        )
        
        # Вызываем задачу напрямую
        send_email_notification(notification.id)
        
        # Проверяем, что email был отправлен
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])


class NotificationBatchTest(TestCase):
    """Тесты для пакетной отправки уведомлений"""
    
    def setUp(self):
        self.users = [
            User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass123'
            ) for i in range(3)
        ]
        self.template = NotificationTemplate.objects.create(
            name='Batch Template',
            code='batch_test',
            title_template='Batch notification',
            message_template='This is a batch notification for {{ user.username }}'
        )
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
    
    def test_create_notification_batch(self):
        """Тест создания пакета уведомлений"""
        batch = NotificationBatch.objects.create(
            template=self.template,
            created_by=self.admin,
            context_data={'message': 'Test batch message'}
        )
        batch.recipients.set(self.users)
        
        self.assertEqual(batch.template, self.template)
        self.assertEqual(batch.created_by, self.admin)
        self.assertEqual(batch.recipients.count(), 3)
        self.assertFalse(batch.is_sent)
    
    @patch('notifications.tasks.process_notification_batch.delay')
    def test_process_batch_task(self, mock_task):
        """Тест обработки пакета уведомлений"""
        batch = NotificationBatch.objects.create(
            template=self.template,
            created_by=self.admin
        )
        batch.recipients.set(self.users)
        
        # Вызываем задачу напрямую
        process_notification_batch(batch.id)
        
        # Проверяем, что уведомления созданы
        notifications = Notification.objects.filter(
            title='Batch notification'
        )
        self.assertEqual(notifications.count(), 3)
        
        # Проверяем, что пакет отмечен как отправленный
        batch.refresh_from_db()
        self.assertTrue(batch.is_sent)
        self.assertIsNotNone(batch.sent_at)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class NotificationTasksTest(TestCase):
    """Тесты для задач Celery"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_cleanup_old_notifications(self):
        """Тест очистки старых уведомлений"""
        # Создаем старое уведомление
        old_notification = Notification.objects.create(
            recipient=self.user,
            title='Old Notification',
            message='This is old',
            is_read=True
        )
        old_notification.created_at = timezone.now() - timedelta(days=35)
        old_notification.save()
        
        # Создаем новое уведомление
        new_notification = Notification.objects.create(
            recipient=self.user,
            title='New Notification',
            message='This is new'
        )
        
        # Запускаем очистку
        cleanup_old_notifications()
        
        # Проверяем, что старое уведомление удалено
        self.assertFalse(
            Notification.objects.filter(id=old_notification.id).exists()
        )
        # Проверяем, что новое уведомление осталось
        self.assertTrue(
            Notification.objects.filter(id=new_notification.id).exists()
        )


class NotificationPermissionsTest(APITestCase):
    """Тесты для разрешений уведомлений"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        self.notification = Notification.objects.create(
            recipient=self.user1,
            title='Private Notification',
            message='This is private'
        )
    
    def test_user_can_access_own_notifications(self):
        """Тест доступа пользователя к своим уведомлениям"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('notification-detail', kwargs={'pk': self.notification.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_user_cannot_access_others_notifications(self):
        """Тест запрета доступа к чужим уведомлениям"""
        self.client.force_authenticate(user=self.user2)
        url = reverse('notification-detail', kwargs={'pk': self.notification.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_anonymous_user_cannot_access_notifications(self):
        """Тест запрета доступа анонимных пользователей"""
        url = reverse('notification-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)