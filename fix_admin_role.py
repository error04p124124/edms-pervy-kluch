"""
Скрипт для проверки и исправления роли пользователя
"""
from django.contrib.auth.models import User
from accounts.models import UserProfile

# Получить пользователя admin123
try:
    user = User.objects.get(username='admin123')
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    print(f"Пользователь: {user.username}")
    print(f"Email: {user.email}")
    print(f"Имя: {user.get_full_name()}")
    print(f"Текущая роль: {profile.role} ({profile.get_role_display()})")
    print(f"Is superuser: {user.is_superuser}")
    print(f"Is staff: {user.is_staff}")
    
    # Если роль не admin, устанавливаем admin
    if profile.role != 'admin':
        print(f"\n⚠️  Роль пользователя не 'admin'!")
        print(f"Меняю роль с '{profile.role}' на 'admin'...")
        profile.role = 'admin'
        profile.save()
        print("✅ Роль успешно изменена на 'admin'")
    else:
        print("\n✅ Роль уже установлена как 'admin'")
    
    # Проверяем флаги superuser и staff
    if not user.is_superuser or not user.is_staff:
        print(f"\n⚠️  Флаги superuser или staff не установлены!")
        user.is_superuser = True
        user.is_staff = True
        user.save()
        print("✅ Флаги superuser и staff установлены")
    else:
        print("✅ Флаги superuser и staff установлены")
        
except User.DoesNotExist:
    print("❌ Пользователь admin123 не найден!")
    print("\nСоздаём пользователя admin123...")
    user = User.objects.create_user(
        username='admin123',
        email='admin@example.com',
        password='admin123',
        first_name='Администратор',
        last_name='Системы',
        is_superuser=True,
        is_staff=True
    )
    profile = UserProfile.objects.create(
        user=user,
        role='admin',
        phone='+7 (999) 999-99-99',
        position='Системный администратор',
        department='IT отдел'
    )
    print("✅ Пользователь admin123 создан с ролью admin")
    print(f"    Логин: admin123")
    print(f"    Пароль: admin123")
