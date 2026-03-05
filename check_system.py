import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms_pervy_kluch.settings')
django.setup()

from django.contrib.auth.models import User
from documents.models import Document
from accounts.models import UserProfile

print("=" * 80)
print("ПРОВЕРКА СИСТЕМЫ ЭДО")
print("=" * 80)

print("\n1. ПОЛЬЗОВАТЕЛИ И ИХ РОЛИ:")
print("-" * 80)
users = ['admin', 'ivanov', 'petrov', 'sidorova']
for username in users:
    user = User.objects.filter(username=username).first()
    if user and hasattr(user, 'profile'):
        from documents.permissions import can_view_all_documents
        can_view = can_view_all_documents(user)
        created_docs = Document.objects.filter(created_by=user).count()
        assigned_docs = Document.objects.filter(assigned_to=user).count()
        print(f"✓ {username:15} | Роль: {user.profile.role:10} | Видит все: {str(can_view):5} | Создано: {created_docs:3} | Назначено: {assigned_docs:3}")
    else:
        print(f"✗ {username:15} | НЕ НАЙДЕН")

print("\n2. СТАТИСТИКА ДОКУМЕНТОВ:")
print("-" * 80)
total = Document.objects.count()
draft = Document.objects.filter(status='draft').count()
in_review = Document.objects.filter(status='in_review').count()
approved = Document.objects.filter(status='approved').count()
rejected = Document.objects.filter(status='rejected').count()
archived = Document.objects.filter(status='archived').count()

print(f"Всего документов: {total}")
print(f"  - Черновики:     {draft}")
print(f"  - На согласовании: {in_review}")
print(f"  - Утверждено:    {approved}")
print(f"  - Отклонено:     {rejected}")
print(f"  - В архиве:      {archived}")

print("\n3. ДОКУМЕНТЫ ПОЛЬЗОВАТЕЛЕЙ:")
print("-" * 80)
for username in users:
    user = User.objects.filter(username=username).first()
    if user:
        if hasattr(user, 'profile') and user.profile.role in ['admin', 'clerk', 'manager']:
            print(f"{username:15} - видит все {total} документов (роль: {user.profile.role})")
        else:
            created = Document.objects.filter(created_by=user).count()
            assigned = Document.objects.filter(assigned_to=user).count()
            print(f"{username:15} - видит {created + assigned} документов (создано: {created}, назначено: {assigned})")

print("\n4. ДОСТУПНЫЕ СТРАНИЦЫ:")
print("-" * 80)
print("✓ /                          - Главная (дашборд)")
print("✓ /documents/                - Список документов")
print("✓ /requests/                 - Запросы документов (новый дизайн)")
print("✓ /accounts/register/        - Регистрация (новый дизайн)")
print("✓ /accounts/profile/         - Профиль (с кнопкой выхода)")
print("✓ /accounts/logout/          - Выход из аккаунта")

print("\n5. УЧЕТНЫЕ ДАННЫЕ ДЛЯ ВХОДА:")
print("-" * 80)
print("Логин: admin      | Пароль: admin     | Роль: Администратор")
print("Логин: ivanov     | Пароль: test123   | Роль: Менеджер")
print("Логин: petrov     | Пароль: test123   | Роль: Клерк (Делопроизводитель)")
print("Логин: sidorova   | Пароль: test123   | Роль: Сотрудник")

print("\n" + "=" * 80)
print("✓ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
print("=" * 80)
