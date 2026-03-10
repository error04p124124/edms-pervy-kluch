"""
Вспомогательные утилиты для работы с документами
"""
from django.contrib.auth.models import User
from django.utils import timezone
from .models import (
    Document, DocumentVersion, DocumentHistory, Notification, 
    AuditLog, Task, DocumentComment, ElectronicSignature
)
import hashlib
import json
import random
import re


def get_client_ip(request):
    """Получить IP адрес клиента"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_audit(user, action, object_type='', object_id=None, object_repr='', details='', request=None):
    """
    Логирование действий в систему аудита
    
    Args:
        user: пользователь
        action: действие (из AuditLog.ACTION_CHOICES)
        object_type: тип объекта (например, 'Document', 'Template')
        object_id: ID объекта
        object_repr: строковое представление объекта
        details: дополнительные детали
        request: HTTP запрос (для получения IP и User-Agent)
    """
    ip_address = None
    user_agent = ''
    
    if request:
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    AuditLog.objects.create(
        user=user,
        action=action,
        object_type=object_type,
        object_id=object_id,
        object_repr=object_repr,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details
    )


def create_document_version(document, user, changes_description=''):
    """
    Создать новую версию документа
    
    Args:
        document: документ для версионирования
        user: пользователь, создающий версию
        changes_description: описание изменений
    
    Returns:
        DocumentVersion: созданная версия
    """
    version_number = document.version
    
    version = DocumentVersion.objects.create(
        document=document,
        version_number=version_number,
        title=document.title,
        file=document.file,
        content=document.content,
        changes_description=changes_description,
        created_by=user
    )
    
    # Увеличиваем номер версии документа
    document.version += 1
    document.save()
    
    # Логируем создание версии
    DocumentHistory.objects.create(
        document=document,
        user=user,
        action=f'Создана версия {version_number}',
        comment=changes_description
    )
    
    return version


def send_notification(users, message, document=None):
    """
    Отправить уведомление пользователям
    
    Args:
        users: список пользователей или один пользователь
        message: текст уведомления
        document: связанный документ (опционально)
    """
    if not isinstance(users, list):
        users = [users]
    
    notifications = []
    for user in users:
        notifications.append(
            Notification(
                user=user,
                message=message,
                document=document
            )
        )
    
    Notification.objects.bulk_create(notifications)


def process_mentions(text, comment, document):
    """
    Обработать упоминания пользователей в комментарии (@username)
    
    Args:
        text: текст комментария
        comment: объект комментария
        document: документ
    """
    # Находим все упоминания (@username)
    mentions = re.findall(r'@(\w+)', text)
    
    if mentions:
        mentioned_users = User.objects.filter(username__in=mentions)
        comment.mentions.set(mentioned_users)
        
        # Отправляем уведомления упомянутым пользователям
        for user in mentioned_users:
            send_notification(
                user,
                f'{comment.author.get_full_name()} упомянул вас в комментарии к документу "{document.title}"',
                document
            )


def create_task_from_document(document, task_type, assigned_to, created_by, deadline=None):
    """
    Создать задачу из документа
    
    Args:
        document: документ
        task_type: тип задачи ('review', 'sign', 'approve')
        assigned_to: кому назначена
        created_by: кто создал
        deadline: срок выполнения
    
    Returns:
        Task: созданная задача
    """
    task_titles = {
        'review': f'Проверить документ "{document.title}"',
        'sign': f'Подписать документ "{document.title}"',
        'approve': f'Согласовать документ "{document.title}"',
    }
    
    task_descriptions = {
        'review': f'Необходимо проверить документ №{document.registry_number or "Б/Н"} - {document.title}',
        'sign': f'Необходимо подписать документ №{document.registry_number or "Б/Н"} - {document.title}',
        'approve': f'Необходимо согласовать документ №{document.registry_number or "Б/Н"} - {document.title}',
    }
    
    task = Task.objects.create(
        title=task_titles.get(task_type, f'Выполнить действие с документом "{document.title}"'),
        description=task_descriptions.get(task_type, f'Необходимо выполнить действие с документом {document.title}'),
        document=document,
        assigned_to=assigned_to,
        created_by=created_by,
        deadline=deadline,
        priority='high' if deadline else 'medium'
    )
    
    # Отправляем уведомление
    send_notification(
        assigned_to,
        f'Вам назначена задача: {task.title}',
        document
    )
    
    return task


def sign_document(document, user, request=None):
    """
    Подписать документ электронной подписью

    Args:
        document: документ для подписи
        user: пользователь, подписывающий документ
        request: HTTP запрос

    Returns:
        ElectronicSignature: созданная подпись
    """
    now = timezone.now()

    # --- Данные подписанта ---
    full_name = user.get_full_name() or user.username
    try:
        profile = user.employee
        position = profile.position or 'Сотрудник'
        department = profile.department or ''
    except Exception:
        position = 'Сотрудник'
        department = ''

    # --- Серийный номер сертификата (20 байт, hex с двоеточием) ---
    rng = random.Random(f"{user.id}:{document.id}:{now.date()}")
    serial_bytes = [format(rng.randint(0, 255), '02X') for _ in range(20)]
    serial_number = ':'.join(serial_bytes)

    # --- Тело подписи (SHA-256 содержимого + метаданных) ---
    sig_input = f"{document.id}:{document.content or ''}:{user.id}:{now.isoformat()}:{serial_number}"
    signature_data = hashlib.sha256(sig_input.encode('utf-8')).hexdigest().upper()

    # --- Отпечаток сертификата (SHA-1, в hex с двоеточием) ---
    fpr_raw = hashlib.sha1(f"{serial_number}:{full_name}".encode()).hexdigest().upper()
    thumbprint = ':'.join(fpr_raw[i:i+2] for i in range(0, len(fpr_raw), 2))

    # --- Псевдо-ИНН и СНИЛС ---
    inn = ''.join([str(rng.randint(0, 9)) for _ in range(12)])
    snils_parts = (rng.randint(100, 999), rng.randint(100, 999), rng.randint(100, 999), rng.randint(10, 99))
    snils = f"{snils_parts[0]}-{snils_parts[1]}-{snils_parts[2]} {snils_parts[3]}"

    valid_from = now
    valid_to = now.replace(year=now.year + 1)

    certificate_info = json.dumps({
        'serial_number': serial_number,
        'cert_type': 'Квалифицированный сертификат ключа проверки ЭП',
        'subject': {
            'cn': full_name,
            'position': position,
            'organization': 'ООО "Первый ключ"',
            'department': department,
            'inn': inn,
            'snils': snils,
            'country': 'RU',
        },
        'issuer': {
            'cn': 'АО «Удостоверяющий центр КриптоПро»',
            'o': 'АО «КриптоПро»',
            'country': 'RU',
            'ogrn': '1027700002607',
        },
        'valid_from': valid_from.strftime('%d.%m.%Y'),
        'valid_to': valid_to.strftime('%d.%m.%Y'),
        'algorithm': 'ГОСТ Р 34.10-2012 / 34.11-2012',
        'key_usage': 'Цифровая подпись, Неотказуемость',
        'thumbprint': thumbprint,
    }, ensure_ascii=False)

    ip_address = get_client_ip(request) if request else None

    signature = ElectronicSignature.objects.create(
        document=document,
        signer=user,
        signature_data=signature_data,
        certificate_info=certificate_info,
        ip_address=ip_address
    )
    
    # Обновляем документ
    document.is_signed = True
    document.signed_at = timezone.now()
    document.signed_by = user
    document.save()
    
    # Логируем
    DocumentHistory.objects.create(
        document=document,
        user=user,
        action='Документ подписан электронной подписью'
    )
    
    log_audit(
        user=user,
        action='sign',
        object_type='Document',
        object_id=document.id,
        object_repr=str(document),
        details=f'Электронная подпись: {signature_data[:16]}...',
        request=request
    )
    
    return signature


def advance_workflow(document, user, decision='approved', comment=''):
    """
    Продвинуть документ по workflow
    
    Args:
        document: документ
        user: пользователь, принимающий решение
        decision: решение ('approved', 'rejected')
        comment: комментарий
    
    Returns:
        bool: успешность операции
    """
    from .models import WorkflowStep
    
    # Находим текущий этап
    try:
        current_step = WorkflowStep.objects.get(
            document=document,
            step_number=document.current_step,
            status='pending'
        )
    except WorkflowStep.DoesNotExist:
        return False
    
    # Обновляем этап
    current_step.status = decision
    current_step.comment = comment
    current_step.completed_at = timezone.now()
    current_step.save()
    
    # Логируем
    action = 'Этап согласования пройден' if decision == 'approved' else 'Этап согласования отклонен'
    DocumentHistory.objects.create(
        document=document,
        user=user,
        action=action,
        comment=comment
    )
    
    if decision == 'approved':
        # Если последовательное согласование, переходим к следующему этапу
        if document.approval_type == 'sequential':
            document.current_step += 1
            
            # Проверяем, есть ли еще этапы
            next_step_exists = WorkflowStep.objects.filter(
                document=document,
                step_number=document.current_step
            ).exists()
            
            if not next_step_exists:
                # Все этапы пройдены
                document.status = 'approved'
                send_notification(
                    document.created_by,
                    f'Документ "{document.title}" успешно согласован',
                    document
                )
            else:
                document.status = 'coordination'
                # Уведомляем следующего согласующего
                next_step = WorkflowStep.objects.get(
                    document=document,
                    step_number=document.current_step
                )
                send_notification(
                    next_step.user,
                    f'Документ "{document.title}" ожидает вашего согласования',
                    document
                )
        else:
            # Параллельное согласование
            pending_steps = WorkflowStep.objects.filter(
                document=document,
                status='pending'
            ).count()
            
            if pending_steps == 0:
                # Все согласовали
                document.status = 'approved'
                send_notification(
                    document.created_by,
                    f'Документ "{document.title}" успешно согласован всеми',
                    document
                )
    else:
        # Отклонено
        document.status = 'returned'
        send_notification(
            document.created_by,
            f'Документ "{document.title}" возвращен на доработку',
            document
        )
    
    document.save()
    return True


def archive_document(document, user):
    """
    Переместить документ в архив
    
    Args:
        document: документ для архивации
        user: пользователь, архивирующий документ
    """
    document.status = 'archived'
    document.save()
    
    DocumentHistory.objects.create(
        document=document,
        user=user,
        action='Документ перемещен в архив'
    )
    
    log_audit(
        user=user,
        action='update',
        object_type='Document',
        object_id=document.id,
        object_repr=str(document),
        details='Документ архивирован'
    )


def restore_from_archive(document, user):
    """
    Восстановить документ из архива
    
    Args:
        document: документ для восстановления
        user: пользователь, восстанавливающий документ
    """
    document.status = 'draft'
    document.save()
    
    DocumentHistory.objects.create(
        document=document,
        user=user,
        action='Документ восстановлен из архива'
    )
    
    log_audit(
        user=user,
        action='update',
        object_type='Document',
        object_id=document.id,
        object_repr=str(document),
        details='Документ восстановлен из архива'
    )
