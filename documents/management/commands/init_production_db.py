import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Инициализация БД на production: создаёт admin-пользователя если его нет'

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_ADMIN_USERNAME', 'admin')
        password = os.environ.get('DJANGO_ADMIN_PASSWORD', 'Admin1234!')
        email = os.environ.get('DJANGO_ADMIN_EMAIL', 'admin@example.com')

        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            # Ensure profile has admin role
            profile, _ = UserProfile.objects.get_or_create(user=user)
            if profile.role != 'admin':
                profile.role = 'admin'
                profile.save()
            self.stdout.write(self.style.SUCCESS(f'✅ Пользователь "{username}" уже существует'))
            return

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            first_name='Администратор',
            last_name='Системы',
        )
        UserProfile.objects.create(
            user=user,
            role='admin',
            position='Системный администратор',
            department='IT отдел',
        )
        self.stdout.write(self.style.SUCCESS(
            f'✅ Создан пользователь "{username}" (роль: admin)\n'
            f'   Логин: {username}\n'
            f'   Пароль: {password}'
        ))
