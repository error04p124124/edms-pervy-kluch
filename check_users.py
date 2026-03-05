import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms_pervy_kluch.settings')
django.setup()

from django.contrib.auth.models import User

print(f"Всего пользователей: {User.objects.count()}\n")

print("Список всех пользователей:")
print("-" * 80)
for user in User.objects.all().order_by('id')[:20]:
    print(f"ID: {user.id:3} | Логин: {user.username:30} | Имя: {user.first_name} {user.last_name}")
    print(f"        Email: {user.email}")
    print()
