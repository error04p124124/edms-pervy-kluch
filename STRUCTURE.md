# Полная структура проекта ЭДО "Первый ключ"

## 📂 Файловая структура

```
d:\12112\
│
├── 📄 manage.py                    # Управление Django проектом
├── 📄 requirements.txt             # Python зависимости
├── 📄 README.md                    # Основная документация
├── 📄 PROJECT_INFO.md              # Информация о проекте
├── 📄 USER_GUIDE.md                # Руководство пользователя
├── 📄 init_data.py                 # Скрипт инициализации тестовых данных
├── 📄 .env                         # Переменные окружения (не в Git)
├── 📄 .env.example                 # Пример .env
├── 📄 .gitignore                   # Исключения для Git
│
├── 🪟 install.bat                  # Установка (Windows)
├── 🪟 start_server.bat             # Запуск сервера (Windows)
├── 🐧 install.sh                   # Установка (Linux/Mac)
├── 🐧 start_server.sh              # Запуск сервера (Linux/Mac)
│
├── 📁 edms_pervy_kluch/            # Основные настройки проекта
│   ├── __init__.py
│   ├── settings.py                 # Настройки Django
│   ├── urls.py                     # Главные URL маршруты
│   ├── wsgi.py                     # WSGI конфигурация
│   └── asgi.py                     # ASGI конфигурация
│
├── 📁 accounts/                    # Приложение управления пользователями
│   ├── __init__.py
│   ├── models.py                   # UserProfile модель
│   ├── views.py                    # Вход, регистрация, профиль
│   ├── forms.py                    # Формы пользователей
│   ├── urls.py                     # URL маршруты аккаунтов
│   ├── admin.py                    # Админка пользователей
│   ├── apps.py                     # Конфигурация приложения
│   └── migrations/                 # Миграции БД
│
├── 📁 documents/                   # Основное приложение ЭДО
│   ├── __init__.py
│   ├── models.py                   # Document, Template, History и др.
│   ├── views.py                    # CBV для работы с документами
│   ├── forms.py                    # Формы документов
│   ├── urls.py                     # URL маршруты документов
│   ├── admin.py                    # Админка документов
│   ├── apps.py                     # Конфигурация приложения
│   ├── context_processors.py       # Процессор уведомлений
│   └── migrations/                 # Миграции БД
│
├── 📁 templates/                   # HTML шаблоны
│   ├── base.html                   # Базовый шаблон
│   │
│   ├── 📁 accounts/                # Шаблоны аутентификации
│   │   ├── login.html              # Страница входа
│   │   ├── register.html           # Страница регистрации
│   │   └── profile.html            # Профиль пользователя
│   │
│   └── 📁 documents/               # Шаблоны документов
│       ├── dashboard.html          # Главная панель
│       ├── document_list.html      # Реестр документов
│       ├── document_detail.html    # Детали документа
│       ├── document_form.html      # Форма создания/редактирования
│       ├── document_confirm_delete.html
│       ├── create_from_template.html
│       ├── setup_workflow.html     # Настройка маршрута
│       ├── notifications.html      # Список уведомлений
│       ├── reports.html            # Отчеты
│       ├── template_list.html      # Список шаблонов
│       ├── template_form.html      # Форма шаблона
│       └── template_confirm_delete.html
│
├── 📁 static/                      # Статические файлы
│   └── 📁 css/
│       └── style.css               # Кастомные стили
│
├── 📁 media/                       # Загруженные файлы (создается автоматически)
│   ├── documents/                  # PDF/DOCX документов
│   └── avatars/                    # Аватары пользователей
│
└── 📁 venv/                        # Виртуальное окружение (не в Git)
```

## 🎯 Ключевые файлы

### Конфигурация
- **edms_pervy_kluch/settings.py** - все настройки проекта
- **.env** - секретные переменные (SECRET_KEY, DEBUG, и т.д.)

### Модели данных
- **accounts/models.py** - UserProfile
- **documents/models.py** - Document, DocumentTemplate, DocumentHistory, Notification, WorkflowStep

### Представления (Views)
- **accounts/views.py** - аутентификация и профиль
- **documents/views.py** - все операции с документами

### Формы
- **accounts/forms.py** - формы пользователей
- **documents/forms.py** - формы документов и шаблонов

### Маршруты (URLs)
- **edms_pervy_kluch/urls.py** - главный роутер
- **accounts/urls.py** - маршруты аккаунтов
- **documents/urls.py** - маршруты документов

### Админ-панель
- **accounts/admin.py** - настройка админки пользователей
- **documents/admin.py** - настройка админки документов

## 📊 Модели базы данных

### UserProfile (accounts/models.py)
```python
- user (OneToOne → User)
- role (clerk/manager/employee/admin)
- department (отдел)
- position (должность)
- avatar (фото)
- phone (телефон)
```

### DocumentTemplate (documents/models.py)
```python
- name (название)
- type (order/contract/act/memo/letter/report/application)
- html_template (HTML с плейсхолдерами)
- description (описание)
- is_active (активен)
```

### Document (documents/models.py)
```python
- registry_number (авто: ГГГГ/ММ/НННН)
- title (название)
- template (FK → DocumentTemplate)
- status (draft/in_review/approved/rejected/archived)
- created_by (FK → User)
- assigned_to (FK → User)
- file (FileField)
- content (текст)
- deadline (срок)
- workflow_route (JSONField)
- metadata (JSONField)
```

### DocumentHistory (documents/models.py)
```python
- document (FK → Document)
- user (FK → User)
- action (действие)
- comment (комментарий)
- created_at (дата/время)
```

### Notification (documents/models.py)
```python
- user (FK → User)
- message (сообщение)
- document (FK → Document)
- is_read (прочитано)
- created_at (дата/время)
```

### WorkflowStep (documents/models.py)
```python
- document (FK → Document)
- step_number (номер этапа)
- user (FK → User - согласующий)
- status (pending/approved/rejected)
- comment (комментарий)
- completed_at (дата завершения)
```

## 🔗 URL маршруты

### Аккаунты (/accounts/)
```
/accounts/login/                    - Вход
/accounts/logout/                   - Выход
/accounts/register/                 - Регистрация
/accounts/profile/                  - Профиль
```

### Документы (/)
```
/                                   - Дашборд
/documents/                         - Реестр документов
/documents/create/                  - Создание документа
/documents/create-from-template/    - Создание из шаблона
/documents/<id>/                    - Детали документа
/documents/<id>/edit/               - Редактирование
/documents/<id>/delete/             - Удаление
/documents/<id>/register/           - Регистрация (присвоение номера)
/documents/<id>/archive/            - Архивирование
/documents/<id>/workflow/           - Настройка маршрута
/documents/<id>/approve/            - Утверждение/отклонение
/documents/bulk-archive/            - Массовое архивирование
```

### Шаблоны (/templates/)
```
/templates/                         - Список шаблонов
/templates/create/                  - Создание шаблона
/templates/<id>/edit/               - Редактирование
/templates/<id>/delete/             - Удаление
```

### Отчеты и уведомления
```
/reports/                           - Отчеты и аналитика
/notifications/                     - Список уведомлений
/notifications/<id>/read/           - Отметить как прочитанное
/notifications/read-all/            - Отметить все
```

## 🎨 Интерфейс

### Bootstrap 5 компоненты
- Навбар с уведомлениями
- Карточки (cards) для статистики
- Таблицы с сортировкой
- Формы с валидацией
- Модальные окна
- Бейджи для статусов

### Chart.js графики
- Doughnut chart (статусы)
- Bar chart (типы документов)

### Font Awesome иконки
- fa-file-alt, fa-folder-open
- fa-check, fa-times, fa-exclamation
- fa-user, fa-bell
- И многие другие

### Кастомные стили (static/css/style.css)
- Анимации (fadeIn, hover эффекты)
- Цветовая схема (темно-синий, акценты)
- Адаптивный дизайн
- Кастомный scrollbar

## 🚀 Процесс разработки

### 1. Начальная настройка
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Создание миграций
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Создание суперпользователя
```bash
python manage.py createsuperuser
```

### 4. Инициализация данных
```bash
python init_data.py
```

### 5. Запуск сервера
```bash
python manage.py runserver
```

## 📦 Зависимости (requirements.txt)

```
Django==5.1.4               # Основной фреймворк
python-dotenv==1.0.0        # Переменные окружения
django-crispy-forms==2.1    # Красивые формы
crispy-bootstrap5==2.0.0    # Bootstrap 5 интеграция
weasyprint==61.2            # Экспорт в PDF
Pillow==10.4.0             # Обработка изображений
```

## 🔐 Права доступа

### Делопроизводитель (clerk)
- ✅ Все документы
- ✅ Создание/редактирование/удаление
- ✅ Регистрация
- ✅ Маршрутизация
- ✅ Массовые операции
- ✅ Шаблоны
- ✅ Отчеты

### Руководитель (manager)
- ✅ Назначенные документы
- ✅ Утверждение/отклонение
- ✅ Просмотр

### Сотрудник (employee)
- ✅ Свои документы
- ✅ Создание из шаблонов
- ✅ Просмотр

### Администратор (admin)
- ✅ Полный доступ через админ-панель

## 📝 Changelog

### Версия 1.0.0 (Январь 2026)
- ✅ Базовая функциональность ЭДО
- ✅ Автоматическая нумерация
- ✅ Система шаблонов
- ✅ Маршрутизация согласования
- ✅ Отчеты и аналитика
- ✅ Уведомления
- ✅ Современный интерфейс

## 🎓 Обучение

1. Изучите README.md
2. Прочитайте USER_GUIDE.md
3. Войдите под тестовыми аккаунтами
4. Создайте документ из шаблона
5. Попробуйте все роли

---

**Готово к использованию!** 🎉
