import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile


PRODUCTION_USERS = [
    {
        'username': 'admin',
        'password': 'admin',
        'first_name': 'Администратор',
        'last_name': 'Системы',
        'email': 'admin@example.com',
        'is_superuser': True,
        'is_staff': True,
        'role': 'admin',
        'position': 'Системный администратор',
        'department': 'IT отдел',
    },
    {
        'username': 'александров.алексей45',
        'password': 'Hfqcel779',
        'first_name': 'Алексей',
        'last_name': 'Александров',
        'email': 'alexey45@example.com',
        'is_superuser': False,
        'is_staff': False,
        'role': 'clerk',
        'position': 'Делопроизводитель',
        'department': 'Канцелярия',
    },
    {
        'username': 'александров.виктор47',
        'password': 'Hfqcel779',
        'first_name': 'Виктор',
        'last_name': 'Александров',
        'email': 'viktor47@example.com',
        'is_superuser': False,
        'is_staff': False,
        'role': 'manager',
        'position': 'Руководитель',
        'department': 'Управление',
    },
    {
        'username': 'александров.игорь10',
        'password': 'Hfqcel779',
        'first_name': 'Игорь',
        'last_name': 'Александров',
        'email': 'igor10@example.com',
        'is_superuser': False,
        'is_staff': False,
        'role': 'employee',
        'position': 'Сотрудник',
        'department': 'Отдел исполнения',
    },
]


class Command(BaseCommand):
    help = 'Инициализация БД на production: создаёт необходимых пользователей'

    def handle(self, *args, **options):
        for u in PRODUCTION_USERS:
            user, created = User.objects.get_or_create(username=u['username'])
            user.set_password(u['password'])
            user.first_name = u['first_name']
            user.last_name = u['last_name']
            user.email = u['email']
            user.is_superuser = u['is_superuser']
            user.is_staff = u['is_staff']
            user.save()

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = u['role']
            profile.position = u['position']
            profile.department = u['department']
            profile.save()

            action = 'Создан' if created else 'Обновлён'
            self.stdout.write(self.style.SUCCESS(
                f'✅ {action}: {u["username"]} ({u["role"]})'
            ))
