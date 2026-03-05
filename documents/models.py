from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime
import json


class DocumentTemplate(models.Model):
    """Шаблон документа"""
    
    TYPE_CHOICES = [
        ('order', 'Приказ'),
        ('contract', 'Договор'),
        ('act', 'Акт'),
        ('memo', 'Служебная записка'),
        ('letter', 'Письмо'),
        ('report', 'Отчет'),
        ('application', 'Заявление'),
        ('other', 'Другое'),
    ]
    
    FORMAT_CHOICES = [
        ('docx', 'Word документ (.docx)'),
        ('xlsx', 'Excel таблица (.xlsx)'),
        ('pdf', 'PDF документ (.pdf)'),
    ]
    
    name = models.CharField('Название шаблона', max_length=200)
    type = models.CharField('Тип документа', max_length=50, choices=TYPE_CHOICES)
    file_format = models.CharField('Формат файла', max_length=10, choices=FORMAT_CHOICES, default='docx')
    
    # Для файловых шаблонов (Word, Excel, etc)
    template_file = models.FileField('Файл шаблона', upload_to='templates/%Y/%m/', blank=True, null=True,
                                     help_text='Загрузите файл шаблона с плейсхолдерами {{переменная}}')
    
    # Для HTML шаблонов (устаревшее, оставлено для совместимости)
    html_template = models.TextField('HTML шаблон', blank=True,
                                     help_text='Используйте {{placeholder}} для переменных (только для HTML)')
    
    description = models.TextField('Описание', blank=True)
    placeholders = models.JSONField('Плейсхолдеры', default=list, blank=True,
                                    help_text='Список плейсхолдеров для заполнения: [{"name": "company_name", "label": "Название компании", "type": "text", "required": true}]')
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Шаблон документа'
        verbose_name_plural = 'Шаблоны документов'
        ordering = ['type', 'name']
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.name}"


class Document(models.Model):
    """Документ"""
    
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('sent_for_approval', 'Отправлен на согласование'),
        ('coordination', 'Согласование'),
        ('approval', 'Утверждение'),
        ('approved', 'Утвержден'),
        ('execution', 'Исполнение'),
        ('rejected', 'Отклонен'),
        ('returned', 'Возвращен на доработку'),
        ('archived', 'В архиве'),
    ]
    
    APPROVAL_TYPE_CHOICES = [
        ('sequential', 'Последовательное согласование'),
        ('parallel', 'Параллельное согласование'),
    ]
    
    registry_number = models.CharField('Регистрационный номер', max_length=50, unique=True, blank=True, null=True)
    title = models.CharField('Название документа', max_length=300)
    template = models.ForeignKey(DocumentTemplate, on_delete=models.SET_NULL, null=True, blank=True, 
                                  verbose_name='Шаблон', related_name='documents')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_documents', 
                                    verbose_name='Создатель')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                     related_name='assigned_documents', verbose_name='Ответственный')
    file = models.FileField('Файл документа', upload_to='documents/%Y/%m/', blank=True, null=True)
    generated_file = models.FileField('Сгенерированный файл', upload_to='generated/%Y/%m/', blank=True, null=True,
                                      help_text='Автоматически сгенерированный файл из шаблона')
    content = models.TextField('Содержание', blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    deadline = models.DateField('Срок исполнения', null=True, blank=True)
    metadata = models.JSONField('Метаданные', default=dict, blank=True)
    
    # Поля для маршрутизации
    workflow_route = models.JSONField('Маршрут согласования', default=list, blank=True, 
                                       help_text='Список ID пользователей для согласования')
    current_step = models.IntegerField('Текущий этап', default=0)
    approval_type = models.CharField('Тип согласования', max_length=20, 
                                      choices=APPROVAL_TYPE_CHOICES, default='sequential')
    
    # Версионность
    version = models.IntegerField('Версия', default=1)
    parent_version = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='versions', verbose_name='Родительская версия')
    
    # Электронная подпись
    is_signed = models.BooleanField('Подписан электронной подписью', default=False)
    signed_at = models.DateTimeField('Дата подписания', null=True, blank=True)
    signed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='signed_documents', verbose_name='Кем подписан')
    
    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'
        ordering = ['-created_at']
        permissions = [
            ('can_register_document', 'Может регистрировать документы'),
            ('can_approve_document', 'Может утверждать документы'),
            ('can_manage_workflow', 'Может управлять маршрутизацией'),
        ]
    
    def __str__(self):
        return f"{self.registry_number or 'Б/Н'} - {self.title}"
    
    def save(self, *args, **kwargs):
        """Сохранение документа (регистрационный номер должен быть установлен до вызова)"""
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """Проверка просрочки"""
        if self.deadline and self.status not in ['approved', 'archived']:
            return timezone.now().date() > self.deadline
        return False
    
    @property
    def days_until_deadline(self):
        """Количество дней до дедлайна"""
        if self.deadline:
            delta = self.deadline - timezone.now().date()
            return delta.days
        return None


class DocumentHistory(models.Model):
    """История изменений документа"""
    
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='history', 
                                  verbose_name='Документ')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    action = models.CharField('Действие', max_length=200)
    comment = models.TextField('Комментарий', blank=True)
    created_at = models.DateTimeField('Дата и время', auto_now_add=True)
    
    class Meta:
        verbose_name = 'История документа'
        verbose_name_plural = 'История документов'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.document} - {self.action} ({self.created_at.strftime('%d.%m.%Y %H:%M')})"


class Notification(models.Model):
    """Уведомление пользователя"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', 
                             verbose_name='Пользователь')
    message = models.TextField('Сообщение')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, null=True, blank=True, 
                                  related_name='notifications', verbose_name='Документ')
    is_read = models.BooleanField('Прочитано', default=False)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.message[:50]}"


class WorkflowStep(models.Model):
    """Этап маршрутизации документа"""
    
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='workflow_steps', 
                                  verbose_name='Документ')
    step_number = models.IntegerField('Номер этапа')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Согласующий')
    status = models.CharField('Статус', max_length=20, 
                              choices=[('pending', 'Ожидает'), ('approved', 'Согласовано'), 
                                       ('rejected', 'Отклонено')], 
                              default='pending')
    comment = models.TextField('Комментарий', blank=True)
    completed_at = models.DateTimeField('Дата завершения', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Этап согласования'
        verbose_name_plural = 'Этапы согласования'
        ordering = ['document', 'step_number']
        unique_together = ['document', 'step_number']
    
    def __str__(self):
        return f"{self.document} - Этап {self.step_number} - {self.user.get_full_name()}"


class ChatMessage(models.Model):
    """Сообщение в чате"""
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages', verbose_name='Отправитель')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', verbose_name='Получатель')
    message = models.TextField('Сообщение')
    is_read = models.BooleanField('Прочитано', default=False)
    created_at = models.DateTimeField('Дата отправки', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.get_full_name()} → {self.recipient.get_full_name()}: {self.message[:50]}"



class QuickTemplate(models.Model):
    """Быстрые шаблоны документов (для делопроизводителей)"""
    
    name = models.CharField('Название шаблона', max_length=200)
    document_type = models.CharField('Тип документа', max_length=50, choices=DocumentTemplate.TYPE_CHOICES)
    description = models.TextField('Описание', blank=True)
    content_template = models.TextField('Шаблон содержимого', blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_quick_templates', verbose_name='Создал')
    is_active = models.BooleanField('Активен', default=True)
    usage_count = models.IntegerField('Количество использований', default=0)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Быстрый шаблон'
        verbose_name_plural = 'Быстрые шаблоны'
        ordering = ['-usage_count', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_document_type_display()})"


class WorkflowApproval(models.Model):
    """Одобрения в рамках workflow (для руководителей)"""
    
    DECISION_CHOICES = [
        ('pending', 'Ожидает решения'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
        ('delegated', 'Делегировано'),
    ]
    
    workflow_step = models.ForeignKey(WorkflowStep, on_delete=models.CASCADE, related_name='approvals', verbose_name='Этап')
    approver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workflow_approvals', verbose_name='Утверждающий')
    decision = models.CharField('Решение', max_length=20, choices=DECISION_CHOICES, default='pending')
    comments = models.TextField('Комментарии', blank=True)
    decision_date = models.DateTimeField('Дата решения', null=True, blank=True)
    delegated_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='delegated_approvals', verbose_name='Делегировано')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Одобрение'
        verbose_name_plural = 'Одобрения'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.approver.get_full_name()}: {self.workflow_step.document.title} ({self.get_decision_display()})"


class TeamStats(models.Model):
    """Статистика работы команды (для руководителей)"""
    
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_stats', verbose_name='Руководитель')
    date = models.DateField('Дата', auto_now_add=True)
    documents_created = models.IntegerField('Создано документов', default=0)
    documents_approved = models.IntegerField('Одобрено документов', default=0)
    documents_rejected = models.IntegerField('Отклонено документов', default=0)
    avg_approval_time = models.FloatField('Среднее время одобрения (часы)', default=0)
    team_members_count = models.IntegerField('Количество членов команды', default=0)
    
    class Meta:
        verbose_name = 'Статистика команды'
        verbose_name_plural = 'Статистика команд'
        ordering = ['-date']
        unique_together = ['manager', 'date']
    
    def __str__(self):
        return f"{self.manager.get_full_name()}: {self.date}"


class DocumentVersion(models.Model):
    """Версия документа"""
    
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='document_versions',
                                  verbose_name='Документ')
    version_number = models.IntegerField('Номер версии')
    title = models.CharField('Название', max_length=300)
    file = models.FileField('Файл версии', upload_to='document_versions/%Y/%m/')
    content = models.TextField('Содержание', blank=True)
    changes_description = models.TextField('Описание изменений', blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Создал')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Версия документа'
        verbose_name_plural = 'Версии документов'
        ordering = ['-version_number']
        unique_together = ['document', 'version_number']
    
    def __str__(self):
        return f"{self.document.title} - Версия {self.version_number}"


class DocumentComment(models.Model):
    """Комментарий к документу"""
    
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='comments',
                                  verbose_name='Документ')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                                related_name='replies', verbose_name='Родительский комментарий')
    text = models.TextField('Текст комментария')
    mentions = models.ManyToManyField(User, related_name='mentioned_in_comments', blank=True,
                                       verbose_name='Упомянутые пользователи')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    is_edited = models.BooleanField('Отредактирован', default=False)
    
    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.author.get_full_name()}: {self.text[:50]}"


class Task(models.Model):
    """Задача"""
    
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('in_progress', 'В работе'),
        ('completed', 'Выполнена'),
        ('cancelled', 'Отменена'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('urgent', 'Срочный'),
    ]
    
    title = models.CharField('Название задачи', max_length=300)
    description = models.TextField('Описание')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, null=True, blank=True,
                                  related_name='tasks', verbose_name='Связанный документ')
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_tasks',
                                     verbose_name='Ответственный')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks',
                                    verbose_name='Создатель')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField('Приоритет', max_length=20, choices=PRIORITY_CHOICES, default='medium')
    deadline = models.DateTimeField('Срок выполнения', null=True, blank=True)
    completed_at = models.DateTimeField('Дата выполнения', null=True, blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.assigned_to.get_full_name()}"
    
    @property
    def is_overdue(self):
        if self.deadline and self.status not in ['completed', 'cancelled']:
            return timezone.now() > self.deadline
        return False


class DocumentAttachment(models.Model):
    """Вложение к документу"""
    
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='attachments',
                                  verbose_name='Документ')
    file = models.FileField('Файл', upload_to='attachments/%Y/%m/')
    original_filename = models.CharField('Оригинальное имя файла', max_length=255)
    file_size = models.IntegerField('Размер файла (байт)')
    file_type = models.CharField('Тип файла', max_length=100)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Загрузил')
    uploaded_at = models.DateTimeField('Дата загрузки', auto_now_add=True)
    description = models.TextField('Описание', blank=True)
    
    class Meta:
        verbose_name = 'Вложение'
        verbose_name_plural = 'Вложения'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.document.title} - {self.original_filename}"
    
    @property
    def file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2)


class AuditLog(models.Model):
    """Журнал аудита"""
    
    ACTION_CHOICES = [
        ('login', 'Вход в систему'),
        ('logout', 'Выход из системы'),
        ('create', 'Создание'),
        ('update', 'Обновление'),
        ('delete', 'Удаление'),
        ('view', 'Просмотр'),
        ('download', 'Скачивание'),
        ('sign', 'Подписание'),
        ('approve', 'Утверждение'),
        ('reject', 'Отклонение'),
        ('error', 'Ошибка'),
        ('access_denied', 'Отказ в доступе'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Пользователь')
    action = models.CharField('Действие', max_length=20, choices=ACTION_CHOICES)
    object_type = models.CharField('Тип объекта', max_length=50, blank=True)
    object_id = models.IntegerField('ID объекта', null=True, blank=True)
    object_repr = models.CharField('Представление объекта', max_length=200, blank=True)
    ip_address = models.GenericIPAddressField('IP адрес', null=True, blank=True)
    user_agent = models.TextField('User Agent', blank=True)
    details = models.TextField('Детали', blank=True)
    created_at = models.DateTimeField('Дата и время', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Запись аудита'
        verbose_name_plural = 'Журнал аудита'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]
    
    def __str__(self):
        user_str = self.user.username if self.user else 'Анонимный'
        return f"{user_str}: {self.get_action_display()} - {self.created_at.strftime('%d.%m.%Y %H:%M')}"


class ElectronicSignature(models.Model):
    """Электронная подпись документа"""
    
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='signatures',
                                  verbose_name='Документ')
    signer = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Подписант')
    signature_data = models.TextField('Данные подписи', help_text='Хеш или криптографические данные')
    certificate_info = models.TextField('Информация о сертификате', blank=True)
    signed_at = models.DateTimeField('Дата подписания', auto_now_add=True)
    ip_address = models.GenericIPAddressField('IP адрес', null=True, blank=True)
    is_valid = models.BooleanField('Подпись действительна', default=True)
    
    class Meta:
        verbose_name = 'Электронная подпись'
        verbose_name_plural = 'Электронные подписи'
        ordering = ['-signed_at']
    
    def __str__(self):
        return f"{self.document.title} - {self.signer.get_full_name()} ({self.signed_at.strftime('%d.%m.%Y %H:%M')})"
