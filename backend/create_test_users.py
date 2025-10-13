#!/usr/bin/env python
"""
Скрипт для создания тестовых пользователей с разными ролями
"""

import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facilities_system.settings')
django.setup()

from accounts.models import User

def create_test_users():
    """Создает тестовых пользователей для каждой роли"""
    
    test_users = [
        {
            'username': 'admin_user',
            'email': 'admin@facilities.com',
            'password': 'admin123',
            'role': User.Role.ADMIN,
            'first_name': 'Админ',
            'last_name': 'Системы',
            'phone': '+79001234567'
        },
        {
            'username': 'manager_user',
            'email': 'manager@facilities.com',
            'password': 'manager123',
            'role': User.Role.MANAGER,
            'first_name': 'Менеджер',
            'last_name': 'Проектов',
            'phone': '+79001234568'
        },
        {
            'username': 'engineer_user',
            'email': 'engineer@facilities.com',
            'password': 'engineer123',
            'role': User.Role.ENGINEER,
            'first_name': 'Инженер',
            'last_name': 'Технический',
            'phone': '+79001234569'
        },
        {
            'username': 'executive_user',
            'email': 'executive@facilities.com',
            'password': 'executive123',
            'role': User.Role.EXECUTIVE,
            'first_name': 'Руководитель',
            'last_name': 'Отдела',
            'phone': '+79001234570'
        },
        {
            'username': 'customer_user',
            'email': 'customer@facilities.com',
            'password': 'customer123',
            'role': User.Role.CUSTOMER,
            'first_name': 'Заказчик',
            'last_name': 'Внешний',
            'phone': '+79001234571'
        }
    ]
    
    created_users = []
    updated_users = []
    
    for user_data in test_users:
        username = user_data['username']
        
        # Проверяем, существует ли пользователь
        user, created = User.objects.get_or_create(
            username=username,
            defaults=user_data
        )
        
        if created:
            user.set_password(user_data['password'])
            user.save()
            created_users.append(username)
            print(f"✅ Создан пользователь: {username} ({user_data['role']})")
        else:
            # Обновляем существующего пользователя
            for key, value in user_data.items():
                if key != 'password':
                    setattr(user, key, value)
            user.set_password(user_data['password'])
            user.save()
            updated_users.append(username)
            print(f"🔄 Обновлен пользователь: {username} ({user_data['role']})")
    
    print(f"\n📊 Итого:")
    print(f"   Создано: {len(created_users)} пользователей")
    print(f"   Обновлено: {len(updated_users)} пользователей")
    print(f"   Всего тестовых пользователей: {len(test_users)}")
    
    return created_users, updated_users

if __name__ == '__main__':
    print("🚀 Создание тестовых пользователей...")
    print("=" * 50)
    
    try:
        created, updated = create_test_users()
        print("\n✅ Скрипт выполнен успешно!")
        
        print("\n📋 Данные для входа:")
        print("-" * 30)
        roles_info = [
            ("admin_user", "admin123", "ADMIN", "Полный доступ ко всем функциям"),
            ("manager_user", "manager123", "MANAGER", "Управление задачами и проектами"),
            ("engineer_user", "engineer123", "ENGINEER", "Техническая панель и инженерные задачи"),
            ("executive_user", "executive123", "EXECUTIVE", "Аналитика и отчеты"),
            ("customer_user", "customer123", "CUSTOMER", "Клиентская панель")
        ]
        
        for username, password, role, description in roles_info:
            print(f"👤 {username}")
            print(f"   Пароль: {password}")
            print(f"   Роль: {role}")
            print(f"   Описание: {description}")
            print()
            
    except Exception as e:
        print(f"❌ Ошибка при создании пользователей: {e}")
        sys.exit(1)