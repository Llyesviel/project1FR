#!/usr/bin/env python
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facilities_system.settings')
django.setup()

from accounts.models import User

def update_test_users():
    """Обновляет тестовых пользователей - удаляет старых и создает новых с правильными ролями"""
    
    # Удаляем всех тестовых пользователей (кроме суперпользователя)
    test_usernames = ['admin_user', 'manager_user', 'engineer_user', 'executive_user', 'customer_user', 'executor_user', 'viewer_user']
    deleted_count = User.objects.filter(username__in=test_usernames).delete()[0]
    print(f"Удалено {deleted_count} старых тестовых пользователей")
    
    # Создаем новых тестовых пользователей с правильными ролями
    test_users = [
        {
            'username': 'admin_user',
            'email': 'admin@test.com',
            'password': 'admin123',
            'role': User.Role.ADMIN,
            'first_name': 'Админ',
            'last_name': 'Администратор'
        },
        {
            'username': 'manager_user',
            'email': 'manager@facilities.com',
            'password': 'manager123',
            'role': User.Role.MANAGER,
            'first_name': 'Менеджер',
            'last_name': 'Управляющий'
        },
        {
            'username': 'engineer_user',
            'email': 'engineer@facilities.com',
            'password': 'engineer123',
            'role': User.Role.ENGINEER,
            'first_name': 'Инженер',
            'last_name': 'Технический'
        },
        {
            'username': 'executive_user',
            'email': 'executive@facilities.com',
            'password': 'executive123',
            'role': User.Role.EXECUTIVE,
            'first_name': 'Руководитель',
            'last_name': 'Главный'
        },
        {
            'username': 'customer_user',
            'email': 'customer@facilities.com',
            'password': 'customer123',
            'role': User.Role.CUSTOMER,
            'first_name': 'Заказчик',
            'last_name': 'Клиент'
        }
    ]
    
    created_users = []
    for user_data in test_users:
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            password=user_data['password'],
            role=user_data['role'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name']
        )
        created_users.append(user)
        print(f"Создан пользователь: {user.username} ({user.get_role_display()})")
    
    print(f"\nВсего создано {len(created_users)} тестовых пользователей")
    print("\n=== ДАННЫЕ ДЛЯ ВХОДА ===")
    for user_data in test_users:
        print(f"{user_data['role']}: {user_data['username']} / {user_data['password']}")
    
    return created_users

if __name__ == '__main__':
    update_test_users()