# 🎨 Руководство по новым UI компонентам

## 📑 Оглавление
1. [Список задач (task_list.html)](#задачи)
2. [История версий (document_versions.html)](#версии)
3. [Электронные подписи (document_signatures.html)](#подписи)
4. [Архив документов (archive_list.html)](#архив)
5. [Печать документа (document_print.html)](#печать)
6. [Система комментариев (comments.js)](#комментарии)
7. [Dropdown уведомлений](#уведомления)
8. [Drag & Drop загрузка файлов (file-upload.js)](#файлы)

---

## 📋 Задачи

### Файл: `templates/documents/task_list.html`

**URL:** `/tasks/`

**Функции:**
- Список задач (назначенные мне / созданные мной)
- Фильтры по статусу и приоритету
- Сортировка
- Обновление статуса задачи (AJAX)
- Цветовая индикация приоритета

**Использование:**
```python
# В views.py уже реализовано:
from documents.views_extended import task_list

# URL уже настроен:
path('tasks/', views_extended.task_list, name='task_list'),
```

**Фильтры:**
- `?tab=assigned` - назначенные мне
- `?tab=created` - созданные мной
- `?status=pending` - ожидающие
- `?priority=urgent` - срочные
- `?sort=deadline` - по сроку

---

## 📚 Версии

### Файл: `templates/documents/document_versions.html`

**URL:** `/documents/<id>/versions/`

**Функции:**
- Timeline версий документа
- Создание новой версии
- Восстановление предыдущей версии
- Скачивание файлов версий
- Индикация текущей версии

**Использование:**
```python
# View уже реализован:
from documents.views_extended import document_versions

# URL настроен:
path('documents/<int:document_id>/versions/', views_extended.document_versions, name='document_versions'),
```

**Дизайн:**
- Вертикальный timeline с точками
- Текущая версия выделена синим
- Информация о создателе и времени
- Описание изменений

---

## ✍️ Подписи

### Файл: `templates/documents/document_signatures.html`

**URL:** `/documents/<id>/signatures/`

**Функции:**
- Просмотр всех подписей
- Подписание документа (если утвержден)
- Проверка валидности подписи
- Информация о сертификате
- SHA256 хеш подписи

**Использование:**
```python
# Views уже реализованы:
from documents.views_extended import sign_document_view, document_signatures

# URLs настроены:
path('documents/<int:document_id>/sign/', views_extended.sign_document_view, name='sign_document'),
path('documents/<int:document_id>/signatures/', views_extended.document_signatures, name='document_signatures'),
```

**Статусы:**
- ✅ Действительна (зеленый)
- ❌ Недействительна (красный)

---

## 📦 Архив

### Файл: `templates/documents/archive_list.html`

**URL:** `/archive/`

**Функции:**
- Список архивных документов
- Фильтры (поиск, дата, тип)
- Статистика архива
- Восстановление из архива
- Просмотр архивных документов

**Использование:**
```python
# View уже реализован:
from documents.views_extended import archive_list

# URL настроен:
path('archive/', views_extended.archive_list, name='archive_list'),
```

**Фильтры:**
- `?search=текст` - поиск
- `?archived_after=2024-01-01` - дата
- `?template_type=order` - тип

---

## 🖨️ Печать

### Файл: `templates/documents/document_print.html`

**URL:** `/documents/<id>/print/`

**Функции:**
- Печатная форма документа
- Автоматическая печать (опционально)
- Профессиональное оформление
- Метаданные и подписи
- QR-код (placeholder)

**Использование:**
```python
# View уже реализован:
from documents.views_extended import print_document

# URL настроен:
path('documents/<int:document_id>/print/', views_extended.print_document, name='print_document'),
```

**Особенности:**
- Отдельный layout без навигации
- @media print стили
- Форматирование для A4
- Футер с реквизитами

---

## 💬 Комментарии

### Файл: `static/js/comments.js`

**Класс:** `CommentsManager`

**Функции:**
- Добавление комментариев
- Ответы на комментарии (threading)
- Редактирование своих комментариев
- Удаление комментариев
- Упоминания пользователей (@username)
- AJAX загрузка и отправка

**Интеграция:**

```html
<!-- В document_detail.html -->
{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/comments-upload.css' %}">
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/comments.js' %}"></script>
{% endblock %}

<!-- В содержимом страницы -->
<div class="comments-section" id="commentsSection" data-document-id="{{ document.id }}">
    <div id="commentsContainer"></div>
    
    <form id="commentForm" class="comment-form">
        {% csrf_token %}
        <textarea id="commentText" class="comment-textarea"></textarea>
        <button type="submit" class="comment-submit-btn">
            <i class="fas fa-paper-plane"></i> Отправить
        </button>
        <button type="button" id="cancelCommentBtn" class="comment-cancel-btn">Отмена</button>
    </form>
</div>
```

**API Endpoints (уже реализованы):**
- `GET /documents/<id>/comments/` - получить комментарии
- `POST /documents/<id>/comments/add/` - добавить
- `POST /comments/<id>/edit/` - редактировать
- `POST /comments/<id>/delete/` - удалить

**JavaScript API:**
```javascript
// Автоматически создается при наличии #commentsSection
window.commentsManager.loadComments();
window.commentsManager.startReply(commentId, authorName);
window.commentsManager.deleteComment(commentId);
```

---

## 🔔 Уведомления

### Файл: `templates/base_modern.html` (обновлен)

**Функции:**
- Dropdown уведомлений в navbar
- Счетчик непрочитанных
- Отметка как прочитанное
- Отметить все как прочитанные
- Автообновление каждые 60 сек
- Последние 10 уведомлений

**Использование:**
Уже интегрировано в `base_modern.html`. Доступно на всех страницах для авторизованных пользователей.

**HTML структура:**
```html
<div class="modern-topbar-action" id="notificationBell" onclick="toggleNotifications(event)">
    <i class="fas fa-bell"></i>
    <span class="modern-topbar-notification-badge" id="notificationBadge"></span>
</div>

<div class="notifications-dropdown" id="notificationsDropdown">
    <!-- Dropdown content -->
</div>
```

**JavaScript API:**
```javascript
toggleNotifications(event);      // Открыть/закрыть dropdown
loadNotifications();             // Загрузить уведомления
markAsRead(notificationId);      // Отметить как прочитанное
markAllAsRead();                 // Отметить все
updateNotificationCount();       // Обновить счетчик
```

**API Endpoints (уже реализованы):**
- `GET /notifications/` - список уведомлений
- `POST /notifications/<id>/read/` - отметить прочитанным
- `POST /notifications/read-all/` - отметить все
- `GET /api/notifications/count/` - счетчик

---

## 📎 Файлы

### Файл: `static/js/file-upload.js`

**Класс:** `FileUploadManager`

**Функции:**
- Drag & Drop загрузка файлов
- Индикация прогресса
- Валидация файлов (тип, размер)
- Список вложений
- Удаление вложений
- Поддержка множественной загрузки

**Интеграция:**

```html
<!-- В document_detail.html -->
{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/comments-upload.css' %}">
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/file-upload.js' %}"></script>
{% endblock %}

<!-- В содержимом страницы -->
<div class="attachments-section" id="attachmentsSection" data-document-id="{{ document.id }}">
    <div id="dropZone" class="drop-zone">
        <i class="fas fa-cloud-upload-alt"></i>
        <div>Перетащите файлы сюда</div>
        <input type="file" id="fileInput" multiple>
    </div>
    
    <div id="uploadProgressContainer"></div>
    <div id="attachmentsList"></div>
</div>
```

**Параметры:**
- Максимальный размер: 50 МБ
- Разрешенные типы: PDF, Word, Excel, изображения, архивы

**API Endpoints (уже реализованы):**
- `POST /documents/<id>/attachments/upload/` - загрузить
- `GET /documents/<id>/attachments/` - список
- `POST /attachments/<id>/delete/` - удалить

**JavaScript API:**
```javascript
// Автоматически создается при наличии #attachmentsSection
window.fileUploadManager.uploadFile(file);
window.fileUploadManager.loadAttachments();
window.fileUploadManager.deleteAttachment(attachmentId);
```

---

## 🎨 Стили

### Файлы CSS:
1. `static/css/modern.css` - основные стили (уже существует)
2. `static/css/comments-upload.css` - новые стили для комментариев и файлов

### Переменные CSS:
```css
--primary-500: #3b82f6;
--success-500: #10b981;
--error-500: #ef4444;
--warning-500: #f59e0b;
--text-primary: #111827;
--text-secondary: #6b7280;
--radius-lg: 12px;
--space-4: 1rem;
```

---

## 📱 Адаптивность

Все компоненты адаптивны:
- Мобильные устройства (< 768px)
- Планшеты (768px - 1024px)
- Десктопы (> 1024px)

**Медиа-запросы:**
```css
@media (max-width: 768px) {
    /* Мобильные стили */
}
```

---

## 🔧 Интеграция в существующий проект

### Шаг 1: Добавить в document_detail.html

См. файл `templates/documents/INTEGRATION_GUIDE.html`

### Шаг 2: Подключить статические файлы

```html
{% load static %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/comments-upload.css' %}">
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/comments.js' %}"></script>
<script src="{% static 'js/file-upload.js' %}"></script>
{% endblock %}
```

### Шаг 3: Собрать статику

```bash
python manage.py collectstatic --noinput
```

### Шаг 4: Проверить URL patterns

Все URL patterns уже настроены в `documents/urls.py`

---

## 🧪 Тестирование

### Проверка компонентов:

1. **Задачи:**
   - Перейти на `/tasks/`
   - Переключить вкладки
   - Применить фильтры
   - Обновить статус задачи

2. **Версии:**
   - Открыть документ
   - Перейти на `/documents/<id>/versions/`
   - Создать версию
   - Восстановить версию

3. **Подписи:**
   - Утвердить документ
   - Перейти на `/documents/<id>/signatures/`
   - Подписать документ
   - Проверить отображение подписи

4. **Архив:**
   - Перейти на `/archive/`
   - Применить фильтры
   - Восстановить документ

5. **Печать:**
   - Открыть `/documents/<id>/print/`
   - Проверить корректность данных
   - Нажать Ctrl+P

6. **Комментарии:**
   - Открыть документ
   - Добавить комментарий
   - Ответить на комментарий
   - Использовать @mention
   - Редактировать/удалить

7. **Уведомления:**
   - Кликнуть на колокольчик
   - Проверить список
   - Отметить как прочитанное

8. **Файлы:**
   - Перетащить файл в drop zone
   - Проверить прогресс загрузки
   - Скачать вложение
   - Удалить вложение

---

## 🐛 Troubleshooting

### Проблема: Комментарии не загружаются

**Решение:**
1. Проверить наличие `data-document-id` атрибута
2. Проверить CSRF токен
3. Открыть консоль браузера для ошибок
4. Проверить URL endpoints

### Проблема: Файлы не загружаются

**Решение:**
1. Проверить настройку MEDIA_ROOT в settings.py
2. Проверить права доступа к папке media
3. Проверить максимальный размер загрузки (settings: DATA_UPLOAD_MAX_MEMORY_SIZE)
4. Проверить CSRF токен

### Проблема: Уведомления не отображаются

**Решение:**
1. Проверить авторизацию пользователя
2. Проверить JavaScript консоль
3. Проверить URL endpoints
4. Очистить кэш браузера

### Проблема: Стили не применяются

**Решение:**
```bash
python manage.py collectstatic --clear --noinput
```

---

## 📚 Дополнительные ресурсы

- [Основная документация](НОВЫЕ_ФУНКЦИИ.md)
- [Интеграция в document_detail](templates/documents/INTEGRATION_GUIDE.html)
- [Права доступа](ACCESS_CONTROL.md)

---

## 🚀 Что дальше?

1. **Улучшения:**
   - Real-time уведомления (WebSocket)
   - Улучшенный autocomplete для @mentions
   - Сравнение версий (diff)
   - Экспорт в Word
   - Криптографическая ЭП

2. **Оптимизация:**
   - Pagination для комментариев
   - Lazy loading для вложений
   - Кэширование уведомлений
   - Оптимизация запросов к БД

3. **Тестирование:**
   - Unit tests для JavaScript
   - Integration tests для API
   - UI тесты (Selenium)

---

**Создано:** 05.03.2026  
**Версия:** 1.0.0  
**Статус:** ✅ Готово к использованию
