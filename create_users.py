import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms_pervy_kluch.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserProfile

# Создание пользователя admin
admin, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@pervykluch.ru',
        'first_name': 'Администратор',
        'last_name': 'Системы',
        'is_staff': True,
        'is_superuser': True
    }
)
if created:
    admin.set_password('admin')
    admin.save()
    print(f"✓ Создан admin | admin@pervykluch.ru | Пароль: admin")
else:
    print(f"✓ admin уже существует")

# Создание профиля для admin
profile, created = UserProfile.objects.get_or_create(
    user=admin,
    defaults={
        'role': 'admin',
        'department': 'Администрация',
        'position': 'Системный администратор',
        'phone': '+7 (900) 000-00-00'
    }
)

# Создание тестовых пользователей с латинскими логинами
test_users = [
    {
        'username': 'ivanov',
        'email': 'ivanov@pervykluch.ru',
        'first_name': 'Александр',
        'last_name': 'Иванов',
        'password': 'test123',
        'role': 'manager',
        'department': 'Руководство',
        'position': 'Начальник отдела',
        'phone': '+7 (911) 111-11-11'
    },
    {
        'username': 'petrov',
        'email': 'petrov@pervykluch.ru',
        'first_name': 'Дмитрий',
        'last_name': 'Петров',
        'password': 'test123',
        'role': 'clerk',
        'department': 'Бухгалтерия',
        'position': 'Бухгалтер',
        'phone': '+7 (922) 222-22-22'
    },
    {
        'username': 'sidorova',
        'email': 'sidorova@pervykluch.ru',
        'first_name': 'Мария',
        'last_name': 'Сидорова',
        'password': 'test123',
        'role': 'employee',
        'department': 'Общий отдел',
        'position': 'Специалист',
        'phone': '+7 (933) 333-33-33'
    }
]

print("\nСоздание тестовых пользователей:")
print("-" * 80)

for user_data in test_users:
    user, created = User.objects.get_or_create(
        username=user_data['username'],
        defaults={
            'email': user_data['email'],
            'first_name': user_data['first_name'],
            'last_name': user_data['last_name']
        }
    )
    
    if created:
        user.set_password(user_data['password'])
        user.save()
        print(f"✓ Создан {user_data['username']} | {user_data['email']} | Пароль: {user_data['password']}")
    else:
        print(f"✓ {user_data['username']} уже существует")
    
    # Создание профиля
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'role': user_data['role'],
            'department': user_data['department'],
            'position': user_data['position'],
            'phone': user_data['phone']
        }
    )

print("\n" + "=" * 80)
print("Готово! Используйте эти учетные данные для входа:")
print("=" * 80)
print("\nЛогин: admin      | Пароль: admin     | Роль: Администратор")
print("Логин: ivanov     | Пароль: test123   | Роль: Менеджер")
print("Логин: petrov     | Пароль: test123   | Роль: Клерк")
print("Логин: sidorova   | Пароль: test123   | Роль: Сотрудник")
