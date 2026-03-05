"""
Скрипт для инициализации тестовых данных
Запуск: python init_data.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms_pervy_kluch.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserProfile
from documents.models import DocumentTemplate
from datetime import datetime, timedelta

def create_users():
    """Создание тестовых пользователей"""
    print("Создание пользователей...")
    
    # Делопроизводитель
    if not User.objects.filter(username='clerk').exists():
        clerk = User.objects.create_user(
            username='clerk',
            email='clerk@pervykluch.ru',
            password='clerk123',
            first_name='Мария',
            last_name='Петрова'
        )
        clerk.profile.role = 'clerk'
        clerk.profile.department = 'Канцелярия'
        clerk.profile.position = 'Делопроизводитель'
        clerk.profile.phone = '+7 (495) 123-45-67'
        clerk.profile.save()
        print("✓ Делопроизводитель создан: clerk / clerk123")
    
    # Руководитель
    if not User.objects.filter(username='manager').exists():
        manager = User.objects.create_user(
            username='manager',
            email='manager@pervykluch.ru',
            password='manager123',
            first_name='Алексей',
            last_name='Смирнов'
        )
        manager.profile.role = 'manager'
        manager.profile.department = 'Администрация'
        manager.profile.position = 'Генеральный директор'
        manager.profile.phone = '+7 (495) 123-45-68'
        manager.profile.save()
        print("✓ Руководитель создан: manager / manager123")
    
    # Сотрудник
    if not User.objects.filter(username='employee').exists():
        employee = User.objects.create_user(
            username='employee',
            email='employee@pervykluch.ru',
            password='employee123',
            first_name='Екатерина',
            last_name='Иванова'
        )
        employee.profile.role = 'employee'
        employee.profile.department = 'Отдел продаж'
        employee.profile.position = 'Менеджер'
        employee.profile.phone = '+7 (495) 123-45-69'
        employee.profile.save()
        print("✓ Сотрудник создан: employee / employee123")


def create_templates():
    """Создание шаблонов документов"""
    print("\nСоздание шаблонов документов...")
    
    templates_data = [
        {
            'name': 'Приказ о приеме на работу',
            'type': 'order',
            'html_template': '''<div style="text-align: center;">
<h2>ПРИКАЗ</h2>
<p>от {{дата}}</p>
</div>

<h3>О приеме на работу</h3>

<p>Приказываю принять на должность <strong>{{должность}}</strong> в <strong>{{отдел}}</strong> 
сотрудника <strong>{{имя}}</strong>.</p>

<p>Дата начала работы: {{custom1}}</p>
<p>Оклад: {{custom2}} руб.</p>

<p>Основание: Заявление сотрудника, Трудовой договор</p>

<br><br>
<p>Генеральный директор<br>
_______________  /_______________/</p>''',
            'description': 'Шаблон приказа о приеме сотрудника на работу'
        },
        {
            'name': 'Служебная записка',
            'type': 'memo',
            'html_template': '''<div style="text-align: right;">
<p>Генеральному директору<br>
ООО "Первый ключ"<br>
от {{должность}}<br>
{{имя}}</p>
</div>

<div style="text-align: center;">
<h3>СЛУЖЕБНАЯ ЗАПИСКА</h3>
<p>{{дата}}</p>
</div>

<p>{{custom1}}</p>

<br><br>
<p>_______________  {{имя}}</p>''',
            'description': 'Шаблон служебной записки'
        },
        {
            'name': 'Заявление на отпуск',
            'type': 'application',
            'html_template': '''<div style="text-align: right;">
<p>Генеральному директору<br>
ООО "Первый ключ"<br>
от {{должность}} {{отдел}}<br>
{{имя}}</p>
</div>

<div style="text-align: center;">
<h3>ЗАЯВЛЕНИЕ</h3>
</div>

<p>Прошу предоставить мне ежегодный оплачиваемый отпуск с {{custom1}} по {{custom2}}.</p>

<br>
<p>{{дата}}<br>
_______________  {{имя}}</p>''',
            'description': 'Шаблон заявления на отпуск'
        },
        {
            'name': 'Договор',
            'type': 'contract',
            'html_template': '''<div style="text-align: center;">
<h2>ДОГОВОР №___</h2>
<p>г. Москва, {{дата}}</p>
</div>

<p><strong>ООО "Первый ключ"</strong>, именуемое в дальнейшем "Заказчик", 
в лице {{имя}}, действующего на основании Устава, с одной стороны, и 
<strong>{{custom1}}</strong>, именуемое в дальнейшем "Исполнитель", с другой стороны, 
заключили настоящий договор о нижеследующем:</p>

<h4>1. ПРЕДМЕТ ДОГОВОРА</h4>
<p>{{custom2}}</p>

<br><br>
<table width="100%">
<tr>
<td width="50%">
<p><strong>ЗАКАЗЧИК:</strong><br>
ООО "Первый ключ"<br><br>
_______________  {{имя}}</p>
</td>
<td width="50%">
<p><strong>ИСПОЛНИТЕЛЬ:</strong><br>
{{custom1}}<br><br>
_______________</p>
</td>
</tr>
</table>''',
            'description': 'Универсальный шаблон договора'
        },
        {
            'name': 'Акт выполненных работ',
            'type': 'act',
            'html_template': '''<div style="text-align: center;">
<h2>АКТ ВЫПОЛНЕННЫХ РАБОТ</h2>
<p>№___ от {{дата}}</p>
</div>

<p>Мы, нижеподписавшиеся, <strong>ООО "Первый ключ"</strong> в лице {{имя}}, 
действующего на основании Устава, именуемое в дальнейшем "Заказчик", 
и <strong>{{custom1}}</strong>, именуемое в дальнейшем "Исполнитель", 
составили настоящий акт о нижеследующем:</p>

<p>Исполнитель выполнил, а Заказчик принял следующие работы:</p>

<p>{{custom2}}</p>

<p><strong>Стоимость выполненных работ:</strong> {{custom3}} руб.</p>

<br><br>
<table width="100%">
<tr>
<td width="50%">
<p><strong>ЗАКАЗЧИК:</strong><br>
_______________  {{имя}}</p>
</td>
<td width="50%">
<p><strong>ИСПОЛНИТЕЛЬ:</strong><br>
_______________</p>
</td>
</tr>
</table>''',
            'description': 'Шаблон акта выполненных работ'
        }
    ]
    
    for template_data in templates_data:
        if not DocumentTemplate.objects.filter(name=template_data['name']).exists():
            DocumentTemplate.objects.create(**template_data)
            print(f"✓ Создан шаблон: {template_data['name']}")


def main():
    print("="*60)
    print("ИНИЦИАЛИЗАЦИЯ ТЕСТОВЫХ ДАННЫХ")
    print("Система ЭДО 'Первый ключ'")
    print("="*60)
    
    create_users()
    create_templates()
    
    print("\n" + "="*60)
    print("✓ Инициализация завершена успешно!")
    print("="*60)
    print("\nДанные для входа:")
    print("-"*60)
    print("Делопроизводитель: clerk / clerk123")
    print("Руководитель:      manager / manager123")
    print("Сотрудник:         employee / employee123")
    print("-"*60)
    print("\nЗапустите сервер: python manage.py runserver")
    print("Откройте: http://127.0.0.1:8000")
    print("="*60)


if __name__ == '__main__':
    main()
