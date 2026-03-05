import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms_pervy_kluch.settings')
django.setup()

from django.contrib.auth.models import User
from documents.models import Document, DocumentTemplate
from django.utils import timezone
import random

print("Создание документов для пользователя sidorova...")
print("-" * 80)

sidorova = User.objects.filter(username='sidorova').first()
if not sidorova:
    print("✗ Пользователь sidorova не найден!")
    exit()

templates = list(DocumentTemplate.objects.all())
if not templates:
    print("✗ Нет шаблонов документов!")
    exit()

# Создаем 10 документов для sidorova
for i in range(10):
    template = random.choice(templates)
    
    doc = Document.objects.create(
        title=f"Документ {i+1} - {template.name}",
        template=template,
        status=random.choice(['draft', 'in_review', 'approved']),
        content=f"Содержимое документа {i+1} для пользователя sidorova",
        created_by=sidorova,
        assigned_to=sidorova if random.random() > 0.3 else None
    )
    
    print(f"✓ Создан документ #{i+1}: {doc.title} (статус: {doc.status})")

print("\n" + "=" * 80)
print(f"✓ Создано 10 документов для пользователя sidorova")
print("=" * 80)

# Проверка
created = Document.objects.filter(created_by=sidorova).count()
assigned = Document.objects.filter(assigned_to=sidorova).count()
total_visible = Document.objects.filter(created_by=sidorova).count() + Document.objects.filter(assigned_to=sidorova).exclude(created_by=sidorova).count()

print(f"\nСтатистика для sidorova:")
print(f"  Создано документов: {created}")
print(f"  Назначено документов: {assigned}")
print(f"  Всего видимых: {total_visible}")
