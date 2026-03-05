import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms_pervy_kluch.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserProfile

print("Проверка пользователей:")
print("-" * 80)

for username in ['admin', 'ivanov', 'petrov', 'sidorova']:
    user = User.objects.filter(username=username).first()
    if user:
        has_profile = hasattr(user, 'profile')
        role = user.profile.role if has_profile else "Нет профиля"
        print(f"{username:15} | Профиль: {str(has_profile):5} | Роль: {role}")
    else:
        print(f"{username:15} | НЕ НАЙДЕН")

print("\n" + "=" * 80)
print("Документы пользователя ivanov:")
print("=" * 80)

ivanov = User.objects.filter(username='ivanov').first()
if ivanov:
    from documents.models import Document
    from django.db.models import Q
    
    # Документы созданные им
    created = Document.objects.filter(created_by=ivanov).count()
    # Назначенные ему
    assigned = Document.objects.filter(assigned_to=ivanov).count()
    # Все документы (если есть права)
    all_docs = Document.objects.count()
    
    print(f"Создано им: {created}")
    print(f"Назначено ему: {assigned}")
    print(f"Всего в системе: {all_docs}")
    
    # Проверка прав
    from documents.permissions import can_view_all_documents
    can_view_all = can_view_all_documents(ivanov)
    print(f"Может видеть все документы: {can_view_all}")
