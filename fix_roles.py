import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms_pervy_kluch.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserProfile

print("Исправление ролей пользователей...")
print("-" * 80)

# Обновление ролей
updates = [
    ('admin', 'admin', 'Администрация', 'Системный администратор'),
    ('ivanov', 'manager', 'Руководство', 'Начальник отдела'),
    ('petrov', 'clerk', 'Бухгалтерия', 'Бухгалтер'),
    ('sidorova', 'employee', 'Общий отдел', 'Специалист'),
]

for username, role, department, position in updates:
    user = User.objects.filter(username=username).first()
    if user and hasattr(user, 'profile'):
        profile = user.profile
        profile.role = role
        profile.department = department
        profile.position = position
        profile.save()
        print(f"✓ {username:15} → Роль: {role:10} | {department} | {position}")
    else:
        print(f"✗ {username:15} - пользователь или профиль не найден")

print("\n" + "=" * 80)
print("Проверка после обновления:")
print("=" * 80)

for username in ['admin', 'ivanov', 'petrov', 'sidorova']:
    user = User.objects.filter(username=username).first()
    if user and hasattr(user, 'profile'):
        from documents.permissions import can_view_all_documents
        can_view = can_view_all_documents(user)
        print(f"{username:15} | Роль: {user.profile.role:10} | Видит все документы: {can_view}")

print("\n✓ Роли успешно обновлены!")
