# Настройка Email-уведомлений ЭДО "Первый ключ"

## ✅ Статус: Email настроены и работают!

Система отправляет email-уведомления через Gmail SMTP.

## Когда отправляются уведомления

### 1. **При создании документа**
- Если при создании указан ответственный пользователь
- Получатель: `assigned_to`
- Тема: "Вам назначен документ"

### 2. **При регистрации документа**
- При присвоении регистрационного номера
- Получатель: `assigned_to`
- Тема: "Вам назначен документ"

### 3. **При настройке маршрута согласования**
- Первый согласующий получает уведомление
- Получатель: первый в списке согласующих
- Тема: "Требуется согласование документа"

### 4. **При согласовании этапа**
- Следующий согласующий получает уведомление
- Получатель: следующий в маршруте
- Тема: "Требуется согласование документа"

### 5. **При полном согласовании**
- Создатель документа получает уведомление
- Получатель: `created_by`
- Тема: "Документ одобрен"

### 6. **При отклонении документа**
- Создатель получает уведомление с комментарием
- Получатель: `created_by`
- Тема: "Документ отклонен"

### 7. **Сообщения в чате**
- При новом сообщении в чате документа
- Получатель: адресат сообщения
- Тема: "Новое сообщение от [Имя]"

## Текущие настройки

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'error04p@gmail.com'
EMAIL_HOST_PASSWORD = 'yylwzszlqrmniixd'  # App Password
DEFAULT_FROM_EMAIL = 'error04p@gmail.com'
```

## Тестирование email

Для проверки работы email-уведомлений используйте команду:

```bash
python manage.py test_email
```

Или отправить на конкретный адрес:

```bash
python manage.py test_email --to your@email.com
```

### Что проверяет команда:
1. ✅ Настройки EMAIL в settings.py
2. ✅ Наличие пароля приложения
3. ✅ Отправку простого текстового письма
4. ✅ Отправку HTML-уведомления через систему

## Требования к пользователям

Для получения email-уведомлений:

1. У пользователя должен быть **указан email** в профиле
2. Email должен быть **валидным**
3. Проверьте папку **"Спам"** при первом получении

## Изменение настроек email

### Изменить отправителя

1. Откройте `edms_pervy_kluch/settings.py`
2. Измените:
```python
EMAIL_HOST_USER = 'your_email@gmail.com'
DEFAULT_FROM_EMAIL = 'your_email@gmail.com'
```

### Изменить пароль приложения

1. Создайте пароль приложения Gmail: https://myaccount.google.com/apppasswords
2. В `settings.py` измените:
```python
EMAIL_HOST_PASSWORD = 'ваш_пароль_приложения'
```

### Использовать другой SMTP сервер

#### Яндекс.Почта:
```python
EMAIL_HOST = 'smtp.yandex.ru'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
```

#### Mail.ru:
```python
EMAIL_HOST = 'smtp.mail.ru'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
```

#### Корпоративная почта:
```python
EMAIL_HOST = 'smtp.your-company.com'
EMAIL_PORT = 587  # или 465 для SSL
EMAIL_USE_TLS = True  # или EMAIL_USE_SSL = True
```

## Отключение email-уведомлений

Для отключения email (например, на этапе разработки):

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

Письма будут выводиться в консоль вместо отправки.

## Troubleshooting (Решение проблем)

### 📧 Письма не приходят

**1. Проверьте настройки Gmail:**
- Включена ли двухфакторная аутентификация?
- Создан ли пароль приложения?
- Используете ли вы пароль приложения (не основной пароль)?

**2. Проверьте email пользователя:**
```bash
python manage.py shell
>>> from django.contrib.auth.models import User
>>> user = User.objects.get(username='имя_пользователя')
>>> print(user.email)
```

**3. Запустите тест:**
```bash
python manage.py test_email
```

**4. Проверьте папку "Спам"**

**5. Проверьте логи сервера:**
При `fail_silently=False` ошибки будут видны в консоли.

### ⚠️ SMTPAuthenticationError

```
SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted')
```

**Причина:** Неверный пароль или не включена 2FA.

**Решение:**
1. Включите двухфакторную аутентификацию в Google Account
2. Создайте новый пароль приложения
3. Используйте его в `EMAIL_HOST_PASSWORD`

### ⚠️ Connection refused

```
ConnectionRefusedError: [Errno 10061] No connection could be made
```

**Причина:** Неверный хост или порт, или блокировка файрволом.

**Решение:**
1. Проверьте `EMAIL_HOST` и `EMAIL_PORT`
2. Проверьте настройки файрвола
3. Попробуйте другой порт (465 для SSL)

### ⚠️ Письма отправляются, но не приходят

**Причина:** Gmail может блокировать подозрительную активность.

**Решение:**
1. Проверьте https://myaccount.google.com/security
2. Разрешите доступ "менее безопасным приложениям" (если требуется)
3. Проверьте папку "Спам"
4. Попробуйте отправить на другой email

## Список всех email-функций

Все функции находятся в `documents/email_utils.py`:

| Функция | Описание | Получатель |
|---------|----------|------------|
| `send_notification_email()` | Базовая функция отправки | Любой user |
| `send_document_assigned_email()` | Документ назначен | assigned_to |
| `send_document_approved_email()` | Документ одобрен | created_by |
| `send_document_rejected_email()` | Документ отклонен | created_by |
| `send_workflow_step_notification()` | Новый этап согласования | step.user |
| `send_chat_message_email()` | Новое сообщение | Адресат |
| `send_document_request_email()` | Новый запрос документа | Все clerks/admins |
| `send_overdue_document_reminder()` | Напоминание о просрочке | assigned_to |

## Проверка email пользователей

Список пользователей с email:

```bash
python manage.py shell
>>> from django.contrib.auth.models import User
>>> for user in User.objects.all():
>>>     print(f"{user.username}: {user.email or 'НЕ УКАЗАН'}")
```

## Массовая рассылка

Для отправки уведомлений всем пользователям определенной роли:

```python
from accounts.models import UserProfile
from documents.email_utils import send_notification_email

# Все администраторы
admins = UserProfile.objects.filter(role='admin')
for profile in admins:
    send_notification_email(
        user=profile.user,
        subject='Важное уведомление',
        message='Текст сообщения',
        document=None
    )
```

## Безопасность

⚠️ **ВАЖНО:**

1. **Никогда не храните пароли в коде**
   - Используйте переменные окружения (.env)
   - Добавьте `.env` в `.gitignore`

2. **Используйте пароли приложений**
   - Не используйте основной пароль аккаунта
   - Регулярно обновляйте пароли приложений

3. **Ограничьте доступ к settings.py**
   - Не коммитьте файлы с реальными паролями
   - Используйте разные настройки для dev/prod

## Контакты технической поддержки

При проблемах с email:
- Проверьте настройки Gmail
- Запустите `python manage.py test_email`
- Проверьте логи сервера
- Обратитесь к системному администратору

---

**Дата обновления:** 16.02.2026  
**Версия:** 2.0  
**Статус:** ✅ Работает
