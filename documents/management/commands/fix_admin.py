from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Проверка и исправление роли пользователя admin123'

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username='admin123')
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            self.stdout.write(f"Пользователь: {user.username}")
            self.stdout.write(f"Email: {user.email}")
            self.stdout.write(f"Имя: {user.get_full_name()}")
            self.stdout.write(f"Текущая роль: {profile.role} ({profile.get_role_display()})")
            self.stdout.write(f"Is superuser: {user.is_superuser}")
            self.stdout.write(f"Is staff: {user.is_staff}")
            
            # Если роль не admin, устанавливаем admin
            if profile.role != 'admin':
                self.stdout.write(self.style.WARNING(f"\n⚠️  Роль пользователя не 'admin'!"))
                self.stdout.write(f"Меняю роль с '{profile.role}' на 'admin'...")
                profile.role = 'admin'
                profile.save()
                self.stdout.write(self.style.SUCCESS("✅ Роль успешно изменена на 'admin'"))
            else:
                self.stdout.write(self.style.SUCCESS("\n✅ Роль уже установлена как 'admin'"))
            
            # Проверяем флаги superuser и staff
            if not user.is_superuser or not user.is_staff:
                self.stdout.write(self.style.WARNING(f"\n⚠️  Флаги superuser или staff не установлены!"))
                user.is_superuser = True
                user.is_staff = True
                user.save()
                self.stdout.write(self.style.SUCCESS("✅ Флаги superuser и staff установлены"))
            else:
                self.stdout.write(self.style.SUCCESS("✅ Флаги superuser и staff установлены"))
                
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ Пользователь admin123 не найден!"))
            self.stdout.write("\nСоздаём пользователя admin123...")
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
            self.stdout.write(self.style.SUCCESS("✅ Пользователь admin123 создан с ролью admin"))
            self.stdout.write("    Логин: admin123")
            self.stdout.write("    Пароль: admin123")
