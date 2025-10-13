# Facilities Management System

## Описание проекта

Монолитное веб-приложение для централизованного управления дефектами на строительных объектах.

### Основные функции:
- Регистрация дефектов
- Назначение ответственных
- Контроль статусов
- Отчётность и аналитика

### Роли пользователей:
- **Engineer** - инженеры (создание и работа с дефектами)
- **Manager** - менеджеры (назначение задач, контроль)
- **Viewer/Customer** - руководители/заказчики (просмотр отчётов)

## Технологический стек

### Backend:
- Django 4.x
- Django REST Framework (DRF)
- PostgreSQL
- Celery + Redis
- Docker

### Frontend:
- React + Material-UI (MUI)
- TypeScript

### DevOps:
- GitHub Actions (CI/CD)
- Docker & Docker Compose
- Nginx
- Prometheus + Grafana

## Структура проекта

```
facilities-system/
├── backend/                 # Django backend
├── frontend/               # React frontend
├── docs/                   # Документация
├── .github/workflows/      # CI/CD pipeline
├── docker/                 # Docker конфигурации
├── scripts/               # Скрипты развертывания
├── reports/               # Отчеты тестирования
└── README.md
```

## Быстрый старт

### Требования
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### Локальная разработка

#### Запуск через Docker Compose
```bash
# Клонирование репозитория
git clone <repository-url>
cd facilities-system

# Копирование переменных окружения
cp .env.example .env

# Запуск через Docker Compose
docker-compose up -d

# Применение миграций
docker-compose exec backend python manage.py migrate

# Создание суперпользователя
docker-compose exec backend python manage.py createsuperuser

# Загрузка тестовых данных
docker-compose exec backend python manage.py loaddata fixtures/sample_data.json
```

#### Локальный запуск через терминал

**Backend (Django):**
```bash
# Переход в папку backend
cd backend

# Установка зависимостей Python
pip install Django==4.2.7
pip install djangorestframework==3.14.0 django-cors-headers==4.3.1

# Применение миграций
python manage.py migrate

# Запуск сервера разработки
с
```

**Frontend (React):**
```bash
# Переход в папку frontend (в новом терминале)
cd frontend

# Установка зависимостей Node.js
npm install

# Запуск сервера разработки
npm start
```

### Доступ к приложению
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/
- Admin панель: http://localhost:8000/admin/
- API документация: http://localhost:8000/api/docs/

## Тестовые пользователи

Для тестирования функционала системы созданы пользователи с различными ролями:

### Создание тестовых пользователей
```bash
# Запуск скрипта создания тестовых пользователей
cd backend
python update_test_users.py
```

### Данные для входа

| Пользователь | Пароль | Роль | Описание |
|-------------|--------|------|----------|
| `admin_user` | `admin123` | **ADMIN** | Полный доступ к админ-панели Django |
| `manager_user` | `manager123` | **MANAGER** | Управление объектами и бронированиями через dashboard |
| `engineer_user` | `engineer123` | **ENGINEER** | Загрузка дефектов и фотографий |
| `executive_user` | `executive123` | **EXECUTIVE** | Просмотр отчетов и аналитики |
| `customer_user` | `customer123` | **CUSTOMER** | Просмотр отчетов и статуса проектов |

### Особенности ролей

- **ADMIN** - Имеет доступ к основной админ-панели Django (http://localhost:8000/admin/)
- **MANAGER** - После авторизации автоматически перенаправляется на /dashboard для управления объектами и бронированиями
- **ENGINEER** - Загружает дефекты и фотографии, работает с техническими задачами
- **EXECUTIVE** - Просматривает отчеты и аналитику для принятия управленческих решений
- **CUSTOMER** - Просматривает отчеты и статус своих проектов

### Вход в систему
1. Откройте http://localhost:3000
2. Используйте любой из указанных логинов и паролей
3. Система автоматически определит роль и предоставит соответствующий интерфейс

## Тестирование

```bash
# Unit тесты
docker-compose exec backend pytest

# Тесты с покрытием
docker-compose exec backend pytest --cov=. --cov-report=html

# Нагрузочное тестирование
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

## Развертывание

### Production
```bash
# Сборка production образов
docker-compose -f docker-compose.prod.yml build

# Развертывание
docker-compose -f docker-compose.prod.yml up -d
```

### Мониторинг
- Grafana: http://localhost:3001
- Prometheus: http://localhost:9090

## Документация

- [SRS - Спецификация требований](docs/SRS.md)
- [Архитектура системы](docs/architecture.md)
- [UX Прототипы](docs/ux-prototypes.md)
- [План разработки](docs/development-plan.md)
- [Руководство по развертыванию](docs/deployment.md)
- [Акт приемки](docs/acceptance.md)

## Лицензия

MIT License