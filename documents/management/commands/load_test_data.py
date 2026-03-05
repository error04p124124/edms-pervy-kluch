"""
Management command для загрузки большого количества тестовых данных
для имитации реальной корпоративной системы документооборота
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from documents.models import (
    Document, DocumentTemplate, WorkflowStep,
    WorkflowApproval, DocumentHistory, Notification
)
from accounts.models import UserProfile
from datetime import datetime, timedelta, date
import random
import os


class Command(BaseCommand):
    help = 'Загружает большой объем тестовых данных для имитации реальной корпоративной системы'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=50,
            help='Количество пользователей для создания (по умолчанию: 50)'
        )
        parser.add_argument(
            '--documents',
            type=int,
            default=200,
            help='Количество документов для создания (по умолчанию: 200)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующие тестовые данные перед загрузкой'
        )

    def handle(self, *args, **options):
        users_count = options['users']
        documents_count = options['documents']
        clear_data = options['clear']

        if clear_data:
            self.stdout.write(self.style.WARNING('Очистка существующих тестовых данных...'))
            self.clear_test_data()

        self.stdout.write(self.style.SUCCESS('Начало загрузки тестовых данных...'))
        
        # Создание пользователей и профилей
        users = self.create_users(users_count)
        self.stdout.write(self.style.SUCCESS(f'✓ Создано {len(users)} пользователей'))
        
        # Создание шаблонов документов
        templates = self.create_templates()
        self.stdout.write(self.style.SUCCESS(f'✓ Создано {len(templates)} шаблонов'))
        
        # Создание документов
        documents = self.create_documents(documents_count, users, templates)
        self.stdout.write(self.style.SUCCESS(f'✓ Создано {len(documents)} документов'))
        
        # Создание workflow и согласований
        workflows = self.create_workflows(documents, users)
        self.stdout.write(self.style.SUCCESS(f'✓ Создано {workflows} workflow шагов'))
        
        # Создание истории изменений
        history_count = self.create_history(documents, users)
        self.stdout.write(self.style.SUCCESS(f'✓ Создано {history_count} записей истории'))
        
        # Создание уведомлений
        notifications_count = self.create_notifications(users, documents)
        self.stdout.write(self.style.SUCCESS(f'✓ Создано {notifications_count} уведомлений'))

        # Создание заполненных документов из шаблонов
        tpl_docs_count = self.create_template_documents(users)
        self.stdout.write(self.style.SUCCESS(f'✓ Создано {tpl_docs_count} заполненных документов из шаблонов'))

        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('Загрузка завершена успешно!'))
        self.stdout.write(self.style.SUCCESS('='*60))

    def clear_test_data(self):
        """Очистка тестовых данных (кроме admin и шаблонов с файлами)"""
        User.objects.exclude(username='admin').delete()
        Document.objects.all().delete()
        # Удаляем только шаблоны-заглушки (без прикреплённого файла)
        DocumentTemplate.objects.filter(template_file='').delete()
        DocumentTemplate.objects.filter(template_file__isnull=True).delete()
        WorkflowStep.objects.all().delete()
        WorkflowApproval.objects.all().delete()
        DocumentHistory.objects.all().delete()
        Notification.objects.all().delete()

    def create_users(self, count):
        """Создание пользователей с различными ролями"""
        users = []
        
        # Имена и фамилии для генерации
        first_names = [
            'Александр', 'Дмитрий', 'Сергей', 'Андрей', 'Евгений', 
            'Максим', 'Роман', 'Владимир', 'Игорь', 'Павел',
            'Михаил', 'Алексей', 'Николай', 'Виктор', 'Константин',
            'Елена', 'Ольга', 'Наталья', 'Татьяна', 'Ирина',
            'Анна', 'Мария', 'Светлана', 'Екатерина', 'Юлия'
        ]
        
        last_names = [
            'Иванов', 'Петров', 'Сидоров', 'Козлов', 'Смирнов',
            'Соколов', 'Морозов', 'Волков', 'Новиков', 'Попов',
            'Федоров', 'Михайлов', 'Васильев', 'Александров', 'Кузнецов',
            'Лебедев', 'Павлов', 'Егоров', 'Медведев', 'Захаров'
        ]
        
        departments = [
            'Бухгалтерия', 'Отдел кадров', 'IT отдел', 'Юридический отдел',
            'Отдел продаж', 'Маркетинг', 'Производство', 'Логистика',
            'Закупки', 'Административный отдел', 'Финансовый отдел',
            'Отдел качества', 'Служба безопасности', 'PR отдел'
        ]
        
        positions = {
            'admin': ['Генеральный директор', 'Технический директор', 'Финансовый директор'],
            'manager': ['Руководитель отдела', 'Начальник управления', 'Директор департамента', 'Заместитель директора'],
            'clerk': ['Главный специалист', 'Ведущий специалист', 'Офис-менеджер', 'Делопроизводитель', 'Секретарь'],
            'employee': ['Специалист', 'Менеджер', 'Инженер', 'Аналитик', 'Консультант', 'Эксперт']
        }
        
        # Распределение ролей
        role_distribution = {
            'admin': int(count * 0.05),  # 5% администраторов
            'manager': int(count * 0.15),  # 15% руководителей
            'clerk': int(count * 0.10),  # 10% делопроизводителей
            'employee': count - int(count * 0.30)  # 70% сотрудников
        }
        
        user_id = 1
        for role, role_count in role_distribution.items():
            for i in range(role_count):
                first_name = random.choice(first_names)
                last_name = random.choice(last_names)
                username = f"{last_name.lower()}.{first_name.lower()}{user_id}"
                email = f"{username}@pervykluch.ru"
                
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name
                    }
                )
                if created:
                    user.set_password('test123')
                    user.save()
                
                UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'role': role,
                        'department': random.choice(departments),
                        'position': random.choice(positions[role]),
                        'phone': f"+7 (9{random.randint(10, 99)}) {random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}"
                    }
                )
                
                users.append(user)
                user_id += 1
        
        return users

    def create_templates(self):
        """Создание шаблонов документов"""
        templates_data = [
            {
                'name': 'Приказ о приеме на работу',
                'type': 'order',
                'description': 'Стандартный приказ о приеме сотрудника на работу'
            },
            {
                'name': 'Приказ об отпуске',
                'type': 'order',
                'description': 'Приказ о предоставлении ежегодного оплачиваемого отпуска'
            },
            {
                'name': 'Приказ о премировании',
                'type': 'order',
                'description': 'Приказ о выплате премии сотрудникам'
            },
            {
                'name': 'Приказ о командировке',
                'type': 'order',
                'description': 'Приказ о направлении сотрудника в командировку'
            },
            {
                'name': 'Трудовой договор',
                'type': 'contract',
                'description': 'Стандартный трудовой договор с сотрудником'
            },
            {
                'name': 'Договор поставки',
                'type': 'contract',
                'description': 'Договор на поставку товаров/услуг'
            },
            {
                'name': 'Договор подряда',
                'type': 'contract',
                'description': 'Договор подряда с подрядчиком'
            },
            {
                'name': 'Акт приема-передачи',
                'type': 'act',
                'description': 'Акт приема-передачи документов/имущества'
            },
            {
                'name': 'Акт выполненных работ',
                'type': 'act',
                'description': 'Акт о выполнении работ по договору'
            },
            {
                'name': 'Служебная записка',
                'type': 'memo',
                'description': 'Служебная записка для внутренней переписки'
            },
            {
                'name': 'Докладная записка',
                'type': 'memo',
                'description': 'Докладная записка руководству'
            },
            {
                'name': 'Письмо контрагенту',
                'type': 'letter',
                'description': 'Официальное письмо внешнему контрагенту'
            },
            {
                'name': 'Квартальный отчет',
                'type': 'report',
                'description': 'Отчет о деятельности за квартал'
            },
            {
                'name': 'Финансовый отчет',
                'type': 'report',
                'description': 'Финансовый отчет о доходах и расходах'
            }
        ]
        
        templates = []
        for data in templates_data:
            template, created = DocumentTemplate.objects.get_or_create(
                name=data['name'],
                defaults={
                    'type': data['type'],
                    'description': data['description'],
                    'file_format': 'docx',
                    'html_template': f"<h1>{{{{title}}}}</h1>\n\n<p>Содержимое документа: {data['name']}</p>"
                }
            )
            templates.append(template)
        
        return templates

    def create_documents(self, count, users, templates):
        """Создание документов с различными статусами"""
        documents = []
        document_titles = [
            'О приёме на работу {name}',
            'О предоставлении отпуска {name}',
            'О премировании сотрудников отдела {dept}',
            'О командировке {name} в г. {city}',
            'Договор № {num} с ООО "{company}"',
            'Служебная записка от {dept}',
            'Докладная записка о {subject}',
            'Письмо в адрес {company}',
            'Отчет о работе {dept} за {period}',
            'Акт приёма-передачи № {num}',
            'Финансовый отчёт за {period}',
            'План работы на {period}',
            'Заявка на закупку оборудования',
            'Согласование бюджета {dept}'
        ]
        
        cities = ['Санкт-Петербург', 'Казань', 'Новосибирск', 'Екатеринбург', 'Нижний Новгород']
        companies = ['Альфа', 'Бета', 'Гамма', 'Дельта', 'Омега', 'Прогресс', 'Инновация', 'Развитие']
        subjects = ['закупке оборудования', 'проблеме с поставкой', 'нарушении сроков', 'качестве работы']
        periods = ['январь 2026', 'февраль 2026', 'март 2026', 'I квартал 2026', 'II квартал 2026']
        statuses = ['draft', 'in_review', 'approved', 'rejected', 'archived']
        
        # Распределение статусов
        status_weights = [0.15, 0.25, 0.45, 0.05, 0.10]  # draft, in_review, approved, rejected, archived
        
        for i in range(count):
            template = random.choice(templates)
            creator = random.choice(users)
            
            # Генерация заголовка
            title_template = random.choice(document_titles)
            title = title_template.format(
                name=f"{creator.first_name} {creator.last_name}",
                dept=creator.profile.department,
                city=random.choice(cities),
                num=f"{random.randint(100, 999)}/{timezone.now().year}",
                company=random.choice(companies),
                subject=random.choice(subjects),
                period=random.choice(periods)
            )
            
            # Случайная дата создания (последние 6 месяцев)
            days_ago = random.randint(0, 180)
            created_date = timezone.now() - timedelta(days=days_ago)
            
            # Выбор статуса
            status = random.choices(statuses, weights=status_weights)[0]
            
            # Назначенный сотрудник (если не черновик)
            assigned_to = None if status == 'draft' else random.choice(users)
            
            document = Document.objects.create(
                title=title,
                template=template,
                status=status,
                content=f"Содержимое документа:\n\n{title}\n\nДата создания: {created_date.strftime('%d.%m.%Y')}",
                created_by=creator,
                assigned_to=assigned_to
            )
            
            # Установка дат создания и обновления
            Document.objects.filter(pk=document.pk).update(
                created_at=created_date,
                updated_at=created_date + timedelta(hours=random.randint(1, 48))
            )
            
            documents.append(document)
        
        return documents

    def create_workflows(self, documents, users):
        """Создание workflow шагов и согласований"""
        workflow_count = 0
        
        # Только для документов в процессе или утвержденных
        workflow_documents = [d for d in documents if d.status in ['in_review', 'approved', 'rejected']]
        
        managers = [u for u in users if hasattr(u, 'profile') and u.profile.role in ['manager', 'admin']]
        
        # Если нет менеджеров, используем всех пользователей
        if not managers:
            managers = users[:5] if len(users) > 5 else users
        
        for document in workflow_documents:
            # Создание 1-3 шагов согласования
            steps_count = random.randint(1, 3)
            
            for step_num in range(1, steps_count + 1):
                approver = random.choice(managers)
                
                # Определение статуса шага
                if document.status == 'approved':
                    step_status = 'approved'
                elif document.status == 'rejected' and step_num == steps_count:
                    step_status = 'rejected'
                elif document.status == 'in_review' and step_num < steps_count:
                    step_status = 'approved'
                else:
                    step_status = 'pending'
                
                # Комментарий для шага
                comment_text = ''
                if step_status != 'pending':
                    comment_text = random.choice([
                        'Согласовано',
                        'Утверждаю',
                        'Без замечаний',
                        'С замечаниями, но согласовано',
                        'Не согласовано. Требуется доработка',
                        'Отклонено по причине несоответствия'
                    ])
                
                # Дата завершения для завершенных шагов
                completed_date = None
                if step_status != 'pending':
                    completed_date = document.created_at + timedelta(hours=step_num * 2 + random.randint(1, 24))
                
                step = WorkflowStep.objects.create(
                    document=document,
                    user=approver,
                    status=step_status,
                    step_number=step_num,
                    comment=comment_text,
                    completed_at=completed_date
                )
                
                # Создание записи согласования
                if step_status != 'pending':
                    WorkflowApproval.objects.create(
                        workflow_step=step,
                        approver=approver,
                        decision='approved' if step_status == 'approved' else 'rejected',
                        comments=comment_text,
                        decision_date=completed_date
                    )
                
                workflow_count += 1
        
        return workflow_count

    def create_history(self, documents, users):
        """Создание истории изменений документов"""
        history_count = 0
        
        actions = [
            'Документ создан',
            'Статус изменен',
            'Документ отправлен на согласование',
            'Документ утвержден',
            'Документ отклонен',
            'Содержимое отредактировано',
            'Назначен ответственный',
            'Добавлен комментарий',
            'Файл загружен',
            'Документ архивирован'
        ]
        
        for document in documents:
            # Создание 2-5 записей истории для каждого документа
            history_entries = random.randint(2, 5)
            
            for i in range(history_entries):
                action = random.choice(actions)
                user = random.choice(users)
                
                DocumentHistory.objects.create(
                    document=document,
                    user=user,
                    action=action,
                    comment=f"Действие выполнено пользователем {user.get_full_name()}"
                )
                
                history_count += 1
        
        return history_count

    def create_notifications(self, users, documents):
        """Создание уведомлений для пользователей"""
        notifications_count = 0
        
        notification_templates = [
            'Новый документ "{title}" требует вашего внимания',
            'Документ "{title}" был утвержден',
            'Документ "{title}" отклонен. Требуется доработка',
            'Вы назначены ответственным за документ "{title}"',
            'Документ "{title}" ожидает вашего согласования',
            'Добавлен комментарий к документу "{title}"',
            'Срок согласования документа "{title}" истекает через 2 дня',
            'Документ "{title}" отправлен на следующий этап согласования'
        ]
        
        for user in users:
            # Создание 5-15 уведомлений для каждого пользователя
            notifications_per_user = random.randint(5, 15)
            
            for _ in range(notifications_per_user):
                document = random.choice(documents)
                message = random.choice(notification_templates).format(title=document.title)
                
                Notification.objects.create(
                    user=user,
                    document=document,
                    message=message,
                    is_read=random.choice([True, False])
                )
                
                notifications_count += 1
        
        return notifications_count

    # ─────────────────────────────────────────────────────────────────────────
    # ДОКУМЕНТЫ ИЗ ШАБЛОНОВ С ЗАПОЛНЕННЫМИ ДАННЫМИ
    # ─────────────────────────────────────────────────────────────────────────

    # Пулы фейковых данных
    _COMPANIES = [
        'ООО «Альфа Технологии»', 'ЗАО «Бизнес Партнёр»', 'АО «Инновации Плюс»',
        'ООО «Развитие»', 'ПАО «ТехноСтрой»', 'ООО «Прогресс Консалтинг»',
        'ЗАО «Горизонт»', 'АО «Системы и Решения»', 'ООО «Меридиан»',
        'ЗАО «ФинансГрупп»',
    ]
    _FIRST = ['Александр', 'Дмитрий', 'Сергей', 'Андрей', 'Максим',
              'Елена', 'Ольга', 'Наталья', 'Ирина', 'Анна']
    _LAST  = ['Иванов', 'Петров', 'Сидоров', 'Козлов', 'Смирнов',
              'Иванова', 'Петрова', 'Сидорова', 'Козлова', 'Смирнова']
    _PATR  = ['Иванович', 'Петрович', 'Александрович', 'Дмитриевич',
              'Ивановна', 'Петровна', 'Александровна', 'Дмитриевна']
    _DEPTS = ['Отдел кадров', 'Бухгалтерия', 'Юридический отдел',
              'IT-отдел', 'Отдел продаж', 'Финансовый отдел',
              'Отдел маркетинга', 'Производственный отдел']
    _POSITIONS = ['Директор', 'Заместитель директора', 'Начальник отдела',
                  'Специалист', 'Менеджер', 'Главный бухгалтер', 'Юрист',
                  'Инженер', 'Аналитик', 'Руководитель проекта']
    _CITIES = ['Москва', 'Санкт-Петербург', 'Казань', 'Екатеринбург',
               'Новосибирск', 'Нижний Новгород', 'Самара', 'Ростов-на-Дону']
    _BANKS  = ['Сбербанк России', 'ВТБ Банк', 'Газпромбанк',
               'Альфа-Банк', 'Россельхозбанк']
    _MEETINGS = [
        'Итоги квартала', 'Планирование на следующий период',
        'Рассмотрение бюджета', 'Обсуждение кадровых вопросов',
        'Оценка рисков проекта',
    ]
    _MEMO_TOPICS = [
        'Запрос на закупку оборудования', 'Согласование командировки',
        'Уточнение производственных показателей', 'Передача материалов',
        'Информирование о результатах проверки',
    ]
    _WORKS = [
        'Разработка программного обеспечения', 'Монтаж оборудования',
        'Консультационные услуги', 'Техническое обслуживание',
        'Поставка расходных материалов', 'Аудит документации',
    ]
    _GOODS = [
        'Компьютерная техника', 'Офисная мебель', 'Расходные материалы',
        'Программное обеспечение', 'Производственное оборудование',
    ]
    _UNITS = ['шт.', 'компл.', 'усл.', 'м²', 'кг', 'л']
    _EXPLANATIONS = [
        'В связи с непредвиденными техническими обстоятельствами',
        'По причине сбоя в информационной системе',
        'Вследствие задержки поставки материалов от контрагента',
        'По семейным обстоятельствам',
        'В связи с производственной необходимостью',
    ]
    _OBLIGATIONS = [
        'Обязуюсь не допускать подобных ситуаций в будущем.',
        'Принимаю меры по устранению причин нарушения.',
        'Гарантирую соблюдение установленного регламента.',
    ]

    def _rnd_date(self, days_back=180, days_forward=30):
        delta = random.randint(-days_back, days_forward)
        return (timezone.now().date() + timedelta(days=delta)).strftime('%d.%m.%Y')

    def _rnd_fio(self):
        return f"{random.choice(self._LAST)} {random.choice(self._FIRST)} {random.choice(self._PATR)}"

    def _rnd_money(self, lo=10000, hi=500000, step=1000):
        return str(round(random.randint(lo, hi) // step * step))

    def _fake_value(self, name):
        """Генерация реалистичных значений по имени плейсхолдера"""
        mapping = {
            # ── персона ──────────────────────────────────────────────────
            'фамилия':            lambda: random.choice(self._LAST),
            'имя':                lambda: random.choice(self._FIRST),
            'отчество':           lambda: random.choice(self._PATR),
            'руководитель':       lambda: self._rnd_fio(),
            'руководитель_отдела':lambda: self._rnd_fio(),
            'председатель':       lambda: self._rnd_fio(),
            'секретарь':          lambda: self._rnd_fio(),
            'докладчик_1':        lambda: self._rnd_fio(),
            'докладчик_2':        lambda: self._rnd_fio(),
            'ответственный_1':    lambda: self._rnd_fio(),
            'ответственный_2':    lambda: self._rnd_fio(),
            'участник_1':         lambda: self._rnd_fio(),
            'участник_2':         lambda: self._rnd_fio(),
            'кому_фио':           lambda: self._rnd_fio(),
            'от_фио':             lambda: self._rnd_fio(),
            'сотрудник_подпись':  lambda: self._rnd_fio(),
            'главный_бухгалтер':  lambda: self._rnd_fio(),
            'бухгалтер':          lambda: self._rnd_fio(),
            'ответственный':      lambda: self._rnd_fio(),
            'фио_1':              lambda: self._rnd_fio(),
            'фио_2':              lambda: self._rnd_fio(),
            'фио_3':              lambda: self._rnd_fio(),
            'фио_подотчётного':   lambda: self._rnd_fio(),
            # ── организация ──────────────────────────────────────────────
            'компания':           lambda: random.choice(self._COMPANIES),
            'компания_заказчик':  lambda: random.choice(self._COMPANIES),
            'компания_исполнитель':lambda: random.choice(self._COMPANIES),
            'компания_поставщик': lambda: random.choice(self._COMPANIES),
            'компания_покупатель':lambda: random.choice(self._COMPANIES),
            'продавец':           lambda: random.choice(self._COMPANIES),
            'покупатель':         lambda: random.choice(self._COMPANIES),
            # ── должности ────────────────────────────────────────────────
            'должность':           lambda: random.choice(self._POSITIONS),
            'должность_руководителя':lambda: random.choice(self._POSITIONS),
            'должность_заказчика': lambda: random.choice(self._POSITIONS),
            'должность_исполнителя':lambda: random.choice(self._POSITIONS),
            'должность_участника_1':lambda: random.choice(self._POSITIONS),
            'должность_участника_2':lambda: random.choice(self._POSITIONS),
            'должность_1':         lambda: random.choice(self._POSITIONS),
            'должность_2':         lambda: random.choice(self._POSITIONS),
            'должность_3':         lambda: random.choice(self._POSITIONS),
            'кому_должность':      lambda: random.choice(self._POSITIONS),
            'от_должность':        lambda: random.choice(self._POSITIONS),
            # ── отделы ───────────────────────────────────────────────────
            'отдел':               lambda: random.choice(self._DEPTS),
            # ── даты ─────────────────────────────────────────────────────
            'дата':                lambda: self._rnd_date(0, 0),
            'дата_начала':         lambda: self._rnd_date(-30, 30),
            'дата_окончания':      lambda: self._rnd_date(14, 60),
            'дата_договора':       lambda: self._rnd_date(90, 0),
            'дата_выдачи':         lambda: self._rnd_date(3650, 0),
            'дата_увольнения':     lambda: self._rnd_date(-10, 10),
            'дата_документа':      lambda: self._rnd_date(30, 0),
            'дата_ознакомления':   lambda: self._rnd_date(5, 0),
            'дата_начала_отпуска': lambda: self._rnd_date(-30, 30),  # alias
            'дата_согласования':   lambda: self._rnd_date(10, 0),
            'срок_1':              lambda: self._rnd_date(-10, 30),
            'срок_2':              lambda: self._rnd_date(-10, 60),
            'срок_действия':       lambda: self._rnd_date(0, 365),
            'дата_выплаты_1':      lambda: '10',
            'дата_выплаты_2':      lambda: '25',
            'дата_передачи':       lambda: self._rnd_date(0, 30),
            'дата_расхода_1':      lambda: self._rnd_date(30, 0),
            # ── номера ───────────────────────────────────────────────────
            'номер_приказа':       lambda: f"{random.randint(1,999)}-К",
            'номер_договора':      lambda: f"{random.randint(100,999)}/{timezone.now().year}",
            'номер_акта':          lambda: str(random.randint(1, 500)),
            'номер_счета':         lambda: f"СЧ-{random.randint(1,9999):04d}",
            'номер_протокола':     lambda: str(random.randint(1, 50)),
            'номер_доверенности':  lambda: f"{random.randint(1,99)}-Д",
            'номер_договора':      lambda: f"{random.randint(100,999)}/{timezone.now().year}",
            'номер_отчёта':        lambda: str(random.randint(1, 200)),
            'табельный_номер':     lambda: str(random.randint(1000, 9999)),
            'номер':               lambda: str(random.randint(1, 999)),
            'серия_паспорта':      lambda: f"{random.randint(40,99)} {random.randint(0,9):02d}",
            'номер_паспорта':      lambda: f"{random.randint(100000,999999)}",
            # ── деньги / числа ───────────────────────────────────────────
            'оклад':               lambda: self._rnd_money(50000, 300000),
            'оклад_прописью':      lambda: 'Сто пятьдесят тысяч рублей',
            'итого':               lambda: self._rnd_money(5000, 2000000),
            'итого_прописью':      lambda: 'Двести тысяч рублей',
            'ндс':                 lambda: '20',
            'сумма_ндс':           lambda: self._rnd_money(1000, 400000),
            'сумма_1':             lambda: self._rnd_money(5000, 500000),
            'сумма_2':             lambda: self._rnd_money(5000, 500000),
            'количество_1':        lambda: str(random.randint(1, 100)),
            'количество_2':        lambda: str(random.randint(1, 100)),
            'количество':          lambda: str(random.randint(1, 50)),
            'испытательный_срок':  lambda: str(random.choice([1, 2, 3])),
            'продолжительность_отпуска': lambda: str(random.choice([14, 21, 28])),
            'цена_единицы':        lambda: self._rnd_money(500, 50000),
            'общая_стоимость':     lambda: self._rnd_money(5000, 2000000),
            'стоимость_прописью':  lambda: 'Пятьсот тысяч рублей',
            'часы_в_неделю':       lambda: '40',
            'обеденный_перерыв':   lambda: '60',
            'отпуск':              lambda: '28',
            'срок_оплаты':         lambda: str(random.choice([3, 5, 10, 30])),
            'пеня':                lambda: '0.1',
            'итого_расходов':      lambda: self._rnd_money(5000, 150000),
            'итого_ндс':           lambda: self._rnd_money(1000, 30000),
            'итого_принято':       lambda: self._rnd_money(5000, 150000),
            'выдан_аванс':         lambda: self._rnd_money(5000, 100000),
            'остаток_перерасход':  lambda: '0',
            'итого_к_выплате':     lambda: self._rnd_money(200000, 2000000),
            'сумма_без_ндс':       lambda: self._rnd_money(5000, 1000000),
            # ── банковские реквизиты ─────────────────────────────────────
            'банк_поставщик':      lambda: random.choice(self._BANKS),
            'расчетный_счет':      lambda: f"4070281{random.randint(10000000000,99999999999)}",
            'бик':                 lambda: f"04{random.randint(4000000,4999999)}",
            'инн_поставщик':       lambda: str(random.randint(1000000000, 9999999999)),
            'кпп_поставщик':       lambda: str(random.randint(100000000, 999999999)),
            'инн_компании':        lambda: str(random.randint(1000000000, 9999999999)),
            'инн_продавца':        lambda: str(random.randint(1000000000, 9999999999)),
            'инн_покупателя':      lambda: str(random.randint(1000000000, 9999999999)),
            'счет_продавца':       lambda: f"4070281{random.randint(10000000000,99999999999)}",
            'счет_покупателя':     lambda: f"4070281{random.randint(10000000000,99999999999)}",
            # ── адреса ───────────────────────────────────────────────────
            'город':               lambda: random.choice(self._CITIES),
            'адрес':               lambda: f"г. {random.choice(self._CITIES)}, ул. Ленина, д. {random.randint(1,150)}",
            'адрес_компании':      lambda: f"г. {random.choice(self._CITIES)}, ул. Пушкина, д. {random.randint(1,99)}",
            'адрес_покупателя':    lambda: f"г. {random.choice(self._CITIES)}, пр. Мира, д. {random.randint(1,200)}",
            'адрес_работы':        lambda: f"г. {random.choice(self._CITIES)}, ул. Советская, д. {random.randint(1,50)}",
            'адрес_работника':     lambda: f"г. {random.choice(self._CITIES)}, ул. Гагарина, д. {random.randint(1,80)}",
            'адрес_передачи':      lambda: f"г. {random.choice(self._CITIES)}, ул. Мира, д. {random.randint(1,100)}",
            # ── текстовые поля ───────────────────────────────────────────
            'основание':           lambda: 'Устав организации',
            'основание_заказчика': lambda: 'Устав организации',
            'основание_исполнителя':lambda: 'Устав организации',
            'основание_увольнения':lambda: random.choice(['Соглашение сторон', 'По собственному желанию', 'Истечение срока договора']),
            'статья_тк':           lambda: random.choice(['77 ч.1 п.1 ТК РФ', '77 ч.1 п.3 ТК РФ', '77 ч.1 п.2 ТК РФ']),
            'документ_основание':  lambda: random.choice(['Заявление работника', 'Соглашение о расторжении', 'Акт о нарушении']),
            'тип_занятости':       lambda: random.choice(['Полная занятость', 'Частичная занятость', 'Совместительство']),
            'срок_договора':       lambda: random.choice(['бессрочный', 'на 1 год', 'на 2 года']),
            'режим_работы':        lambda: random.choice(['5/2', '6/1', '2/2']),
            'время_начала':        lambda: random.choice(['09:00', '08:30', '10:00']),
            'время_окончания':     lambda: random.choice(['18:00', '17:30', '19:00']),
            'кем_выдан':           lambda: f"УМВД России по г. {random.choice(self._CITIES)}",
            'место_представления': lambda: f"ИФНС № {random.randint(1,50)} по г. {random.choice(self._CITIES)}",
            'предмет_доверенности':lambda: 'Представление интересов организации в государственных органах',
            'перечень_действий':   lambda: ('Подписывать документы, получать документы, '
                                             'представлять интересы организации'),
            'наименование_работы_1':lambda: random.choice(self._WORKS),
            'наименование_работы_2':lambda: random.choice(self._WORKS),
            'наименование_товара': lambda: random.choice(self._GOODS),
            'единица_измерения':   lambda: random.choice(self._UNITS),
            'единица_1':           lambda: random.choice(self._UNITS),
            'единица_2':           lambda: random.choice(self._UNITS),
            'характеристики':      lambda: 'Согласно технической документации и спецификации',
            'тема':                lambda: random.choice(self._MEMO_TOPICS),
            'текст_сообщения':     lambda: ('В соответствии с производственной необходимостью '
                                             'прошу рассмотреть данный вопрос в установленные сроки.'),
            'просьба':             lambda: random.choice([
                'Прошу согласовать данный запрос.',
                'Прошу принять соответствующие меры.',
                'Прошу рассмотреть и утвердить предложение.',
            ]),
            'приложения':          lambda: random.choice(['нет', 'Копия договора на 2 л.', 'Справка на 1 л.']),
            'предмет_объяснения':  lambda: random.choice(['опозданию на работу', 'отсутствию на рабочем месте', 'нарушению дедлайна']),
            'текст_объяснения':    lambda: random.choice(self._EXPLANATIONS),
            'причина':             lambda: random.choice(self._EXPLANATIONS),
            'обязательство':       lambda: random.choice(self._OBLIGATIONS),
            'наименование_1':      lambda: random.choice(self._GOODS),
            'вопрос_1':            lambda: random.choice(self._MEETINGS),
            'вопрос_2':            lambda: random.choice(self._MEETINGS),
            'содержание_доклада_1':lambda: ('Докладчик ознакомил участников совещания с текущим '
                                              'положением дел и предложил пути решения проблемы.'),
            'содержание_доклада_2':lambda: ('Представлен анализ выполнения плана и ключевые '
                                              'показатели эффективности за отчётный период.'),
            'решение_1':           lambda: ('Принять к сведению. Поручить ответственному лицу '
                                             'подготовить план мероприятий в срок.'),
            'решение_2':           lambda: ('Утвердить представленные показатели. Продолжить '
                                             'работу в штатном режиме.'),
            'место':               lambda: f"Переговорная комната, {random.choice(self._COMPANIES)}",
            'время_начала':        lambda: random.choice(['10:00', '09:30', '11:00', '14:00', '15:30']),
            'время_окончания':     lambda: random.choice(['11:30', '12:00', '13:00', '16:00', '17:00']),
            'назначение':          lambda: random.choice(['Командировочные расходы', 'Хозяйственные нужды', 'Представительские расходы']),
            'даты_командировки':   lambda: f"{self._rnd_date(10, 0)} — {self._rnd_date(0, 5)}",
            'наименование_расхода_1':lambda: random.choice(['Авиабилеты', 'Гостиница', 'Такси', 'Суточные', 'Канцтовары']),
            'сумма_расхода_1':     lambda: self._rnd_money(1000, 50000),
            'ндс_расхода_1':       lambda: self._rnd_money(200, 10000),
            'принято_1':           lambda: self._rnd_money(1000, 50000),
            'ставка_ндс':          lambda: '20',
            'срок_оплаты':         lambda: f"в течение {random.choice([3,5,10,30])} банковских дней",
            'месяц':               lambda: random.choice(['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']),
            'год':                 lambda: str(timezone.now().year),
            'копейки':             lambda: '00',
            'образование':         lambda: random.choice(['Высшее', 'Неполное высшее', 'Среднее специальное']),
            'специальность':       lambda: random.choice(['Информатика и вычислительная техника', 'Экономика и управление', 'Юриспруденция', 'Машиностроение']),
            'опыт_работы':         lambda: f"{random.randint(1,15)} лет в сфере {random.choice(self._POSITIONS).lower()}",
            'телефон':             lambda: f"+7 (9{random.randint(10,99)}) {random.randint(100,999)}-{random.randint(10,99)}-{random.randint(10,99)}",
        }

        fn = mapping.get(name)
        return fn() if fn else f'[{name}]'

    def create_template_documents(self, users):
        """Создание документов из шаблонов с заполненными плейсхолдерами и сгенерированными файлами"""
        from documents.office_utils import generate_document_from_template
        from django.conf import settings

        templates = DocumentTemplate.objects.filter(is_active=True).exclude(template_file='')
        templates = [t for t in templates if t.placeholders]

        if not templates:
            self.stdout.write(self.style.WARNING(
                '  ! Шаблоны с файлами не найдены. Запустите python manage.py create_template_files'))
            return 0

        statuses = ['draft', 'in_review', 'approved', 'approved', 'approved', 'approved']
        total = 0
        now = timezone.now()

        for template in templates:
            docs_per_template = random.randint(3, 6)
            for _ in range(docs_per_template):
                # ── собираем replacements ─────────────────────────────────
                replacements = {}
                for ph in template.placeholders:
                    replacements[ph['name']] = self._fake_value(ph['name'])

                # ── заголовок ─────────────────────────────────────────────
                company_or_name = (
                    replacements.get('компания')
                    or replacements.get('фамилия', '')
                )
                title = f"{template.name} — {company_or_name}"

                creator = random.choice(users)
                status  = random.choice(statuses)

                doc = Document.objects.create(
                    title=title,
                    template=template,
                    status=status,
                    created_by=creator,
                    assigned_to=random.choice(users) if status != 'draft' else None,
                    content='\n'.join(f'{k}: {v}' for k, v in replacements.items()),
                    metadata={'placeholder_values': replacements},
                )

                # ── генерация файла ───────────────────────────────────────
                try:
                    year_str  = str(now.year)
                    month_str = str(now.month).zfill(2)
                    out_dir   = os.path.join(str(settings.MEDIA_ROOT), 'generated', year_str, month_str)
                    os.makedirs(out_dir, exist_ok=True)
                    out_name  = f"tpl_doc_{doc.pk}.{template.file_format}"
                    out_path  = os.path.join(out_dir, out_name)

                    success, _ = generate_document_from_template(
                        template_file_path=template.template_file.path,
                        template_format=template.file_format,
                        output_path=out_path,
                        replacements=replacements,
                    )
                    if success:
                        rel = os.path.join('generated', year_str, month_str, out_name)
                        Document.objects.filter(pk=doc.pk).update(generated_file=rel)
                except Exception:
                    pass  # файл не сгенерирован, но запись в БД создана

                # ── случайная дата создания ───────────────────────────────
                days_ago = random.randint(1, 120)
                created_date = now - timedelta(days=days_ago)
                Document.objects.filter(pk=doc.pk).update(
                    created_at=created_date,
                    updated_at=created_date + timedelta(hours=random.randint(1, 24)),
                )
                total += 1

        return total
