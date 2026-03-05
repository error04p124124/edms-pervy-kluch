"""
Расширенные views для новых функций ЭДО
Комментарии, задачи, версии, подписи, экспорт, архив
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q
from io import BytesIO

from .models import (
    Document, DocumentComment, Task, DocumentVersion,
    ElectronicSignature, DocumentAttachment, Notification, DocumentTemplate
)
from .utils import (
    create_document_version, send_notification, process_mentions,
    create_task_from_document, sign_document, log_audit,
    archive_document, restore_from_archive, advance_workflow
)
from .permissions import can_edit_document, can_delete_document


# ============== КОММЕНТАРИИ ============== #

@login_required
@require_POST
def add_comment(request, document_id):
    """Добавить комментарий к документу"""
    document = get_object_or_404(Document, pk=document_id)
    
    text = request.POST.get('text', '').strip()
    parent_id = request.POST.get('parent_id')
    
    if not text:
        return JsonResponse({'success': False, 'error': 'Комментарий не может быть пустым'})
    
    parent = None
    if parent_id:
        parent = get_object_or_404(DocumentComment, pk=parent_id)
    
    comment = DocumentComment.objects.create(
        document=document,
        author=request.user,
        parent=parent,
        text=text
    )
    
    # Обрабатываем упоминания (@username)
    process_mentions(text, comment, document)
    
    # Уведомляем создателя документа (если это не он комментирует)
    if document.created_by != request.user:
        send_notification(
            document.created_by,
            f'{request.user.get_full_name()} оставил комментарий к документу "{document.title}"',
            document
        )
    
    # Логируем
    log_audit(
        user=request.user,
        action='create',
        object_type='Comment',
        object_id=comment.id,
        object_repr=f'Комментарий к {document.title}',
        request=request
    )
    
    return JsonResponse({
        'success': True,
        'comment': {
            'id': comment.id,
            'author': comment.author.get_full_name(),
            'text': comment.text,
            'created_at': comment.created_at.strftime('%d.%m.%Y %H:%M')
        }
    })


@login_required
def get_comments(request, document_id):
    """Получить комментарии документа"""
    document = get_object_or_404(Document, pk=document_id)
    comments = document.comments.filter(parent__isnull=True).select_related('author').prefetch_related('replies')
    
    def serialize_comment(comment):
        return {
            'id': comment.id,
            'author': comment.author.get_full_name(),
            'author_avatar': comment.author.profile.avatar.url if hasattr(comment.author, 'profile') and comment.author.profile.avatar else None,
            'text': comment.text,
            'created_at': comment.created_at.strftime('%d.%m.%Y %H:%M'),
            'is_edited': comment.is_edited,
            'can_edit': comment.author == request.user,
            'replies': [serialize_comment(reply) for reply in comment.replies.all()]
        }
    
    data = [serialize_comment(c) for c in comments]
    return JsonResponse({'comments': data})


@login_required
@require_POST
def edit_comment(request, comment_id):
    """Редактировать комментарий"""
    comment = get_object_or_404(DocumentComment, pk=comment_id)
    
    if comment.author != request.user:
        return JsonResponse({'success': False, 'error': 'Нет прав на редактирование'})
    
    text = request.POST.get('text', '').strip()
    if not text:
        return JsonResponse({'success': False, 'error': 'Комментарий не может быть пустым'})
    
    comment.text = text
    comment.is_edited = True
    comment.save()
    
    # Обновляем упоминания
    process_mentions(text, comment, comment.document)
    
    return JsonResponse({
        'success': True,
        'comment': {
            'id': comment.id,
            'text': comment.text,
            'is_edited': True
        }
    })


@login_required
@require_POST
def delete_comment(request, comment_id):
    """Удалить комментарий"""
    comment = get_object_or_404(DocumentComment, pk=comment_id)
    
    if comment.author != request.user and not request.user.profile.role in ['admin', 'clerk']:
        return JsonResponse({'success': False, 'error': 'Нет прав на удаление'})
    
    comment.delete()
    return JsonResponse({'success': True})


# ============== ЗАДАЧИ ============== #

@login_required
def task_list(request):
    """Список задач пользователя"""
    # Задачи назначенные пользователю
    my_tasks = Task.objects.filter(assigned_to=request.user).select_related('document', 'created_by')
    
    # Фильтры
    status = request.GET.get('status')
    if status:
        my_tasks = my_tasks.filter(status=status)
    
    priority = request.GET.get('priority')
    if priority:
        my_tasks = my_tasks.filter(priority=priority)
    
    my_tasks = my_tasks.order_by('-created_at')
    
    # Созданные пользователем задачи
    created_tasks = Task.objects.filter(created_by=request.user).select_related('document', 'assigned_to')
    
    context = {
        'my_tasks': my_tasks,
        'created_tasks': created_tasks,
        'pending_count': my_tasks.filter(status='pending').count(),
        'inprogress_count': my_tasks.filter(status='in_progress').count(),
        'overdue_count': my_tasks.filter(
            deadline__lt=timezone.now(),
            status__in=['pending', 'in_progress']
        ).count(),
    }
    
    return render(request, 'documents/task_list.html', context)


@login_required
@require_POST
def create_task(request):
    """Создать задачу"""
    title = request.POST.get('title')
    description = request.POST.get('description', '')
    assigned_to_id = request.POST.get('assigned_to')
    document_id = request.POST.get('document_id')
    priority = request.POST.get('priority', 'medium')
    deadline = request.POST.get('deadline')
    
    if not title or not assigned_to_id:
        messages.error(request, 'Заполните все обязательные поля')
        return redirect('documents:document_detail', pk=document_id)
    
    from django.contrib.auth.models import User
    assigned_to = get_object_or_404(User, pk=assigned_to_id)
    document = get_object_or_404(Document, pk=document_id) if document_id else None
    
    task = Task.objects.create(
        title=title,
        description=description,
        document=document,
        assigned_to=assigned_to,
        created_by=request.user,
        priority=priority,
        deadline=deadline if deadline else None
    )
    
    # Уведомляем ответственного
    send_notification(
        assigned_to,
        f'Вам назначена задача: {title}',
        document
    )
    
    messages.success(request, 'Задача успешно создана')
    return redirect('documents:task_list')


@login_required
@require_POST
def update_task_status(request, task_id):
    """Обновить статус задачи"""
    task = get_object_or_404(Task, pk=task_id)
    
    if task.assigned_to != request.user and task.created_by != request.user:
        return JsonResponse({'success': False, 'error': 'Нет прав на изменение'})
    
    status = request.POST.get('status')
    if status not in ['pending', 'in_progress', 'completed', 'cancelled']:
        return JsonResponse({'success': False, 'error': 'Неверный статус'})
    
    task.status = status
    
    if status == 'completed':
        task.completed_at = timezone.now()
        # Уведомляем создателя
        if task.created_by != request.user:
            send_notification(
                task.created_by,
                f'Задача "{task.title}" выполнена',
                task.document
            )
    
    task.save()
    
    return JsonResponse({'success': True, 'status': task.get_status_display()})


# ============== ВЕРСИИ ДОКУМЕНТОВ ============== #

@login_required
def document_versions(request, document_id):
    """Список версий документа"""
    document = get_object_or_404(Document, pk=document_id)
    versions = document.document_versions.all().select_related('created_by')
    
    context = {
        'document': document,
        'versions': versions,
        'current_version': document.version
    }
    
    return render(request, 'documents/document_versions.html', context)


@login_required
@require_POST
def create_version(request, document_id):
    """Создать новую версию документа"""
    document = get_object_or_404(Document, pk=document_id)
    
    if not can_edit_document(request.user, document):
        messages.error(request, 'Нет прав на редактирование документа')
        return redirect('documents:document_detail', pk=document_id)
    
    changes_description = request.POST.get('changes_description', '')
    
    version = create_document_version(document, request.user, changes_description)
    
    messages.success(request, f'Создана версия {version.version_number}')
    return redirect('documents:document_versions', document_id=document_id)


@login_required
def restore_version(request, version_id):
    """Восстановить версию документа"""
    version = get_object_or_404(DocumentVersion, pk=version_id)
    document = version.document
    
    if not can_edit_document(request.user, document):
        messages.error(request, 'Нет прав на редактирование документа')
        return redirect('documents:document_detail', pk=document.id)
    
    # Создаем версию перед восстановлением
    create_document_version(document, request.user, f'Восстановление версии {version.version_number}')
    
    # Восстанавливаем данные
    document.title = version.title
    document.content = version.content
    if version.file:
        document.file = version.file
    document.save()
    
    messages.success(request, f'Версия {version.version_number} восстановлена')
    return redirect('documents:document_detail', pk=document.id)


# ============== ЭЛЕКТРОННАЯ ПОДПИСЬ ============== #

@login_required
@require_POST
def sign_document_view(request, document_id):
    """Подписать документ электронной подписью"""
    document = get_object_or_404(Document, pk=document_id)
    
    # Проверка: документ должен быть утвержден для подписания
    if document.status != 'approved':
        messages.error(request, 'Документ должен быть утвержден перед подписанием')
        return redirect('documents:document_detail', pk=document_id)
    
    # Создаем подпись
    signature = sign_document(document, request.user, request)
    
    # Уведомляем создателя
    if document.created_by != request.user:
        send_notification(
            document.created_by,
            f'Документ "{document.title}" подписан {request.user.get_full_name()}',
            document
        )
    
    messages.success(request, 'Документ успешно подписан электронной подписью')
    return redirect('documents:document_detail', pk=document_id)


@login_required
def document_signatures(request, document_id):
    """Список подписей документа"""
    document = get_object_or_404(Document, pk=document_id)
    signatures = document.signatures.all().select_related('signer')
    
    context = {
        'document': document,
        'signatures': signatures
    }
    
    return render(request, 'documents/document_signatures.html', context)


# ============== АРХИВ ДОКУМЕНТОВ ============== #

@login_required
@require_POST
def archive_document_view(request, document_id):
    """Переместить документ в архив"""
    document = get_object_or_404(Document, pk=document_id)
    
    if not can_delete_document(request.user, document):
        messages.error(request, 'Нет прав на архивирование документа')
        return redirect('documents:document_detail', pk=document_id)
    
    archive_document(document, request.user)
    
    messages.success(request, 'Документ перемещен в архив')
    return redirect('documents:document_list')


@login_required
@require_POST
def restore_document_view(request, document_id):
    """Восстановить документ из архива"""
    document = get_object_or_404(Document, pk=document_id)
    
    if not can_edit_document(request.user, document):
        messages.error(request, 'Нет прав на восстановление документа')
        return redirect('documents:document_detail', pk=document_id)
    
    restore_from_archive(document, request.user)
    
    messages.success(request, 'Документ восстановлен из архива')
    return redirect('documents:document_detail', pk=document_id)


@login_required
def archive_list(request):
    """Список архивных документов"""
    from .permissions import can_view_all_documents
    
    if can_view_all_documents(request.user):
        documents = Document.objects.filter(status='archived')
    else:
        documents = Document.objects.filter(
            Q(created_by=request.user) | Q(assigned_to=request.user),
            status='archived'
        )
    
    documents = documents.select_related('created_by', 'assigned_to', 'template').order_by('-updated_at')
    
    context = {
        'documents': documents
    }
    
    return render(request, 'documents/archive_list.html', context)


# ============== ЭКСПОРТ ДОКУМЕНТОВ ============== #

@login_required
def export_document_pdf(request, document_id):
    """Экспорт документа в PDF"""
    document = get_object_or_404(Document, pk=document_id)
    
    # Создаем PDF
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    
    styles = getSampleStyleSheet()
    
    # Заголовок
    title = Paragraph(f"<b>{document.title}</b>", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Информация о документе
    data = [
        ['Регистрационный номер:', document.registry_number or 'Не присвоен'],
        ['Статус:', document.get_status_display()],
        ['Создатель:', document.created_by.get_full_name()],
        ['Дата создания:', document.created_at.strftime('%d.%m.%Y %H:%M')],
    ]
    
    if document.assigned_to:
        data.append(['Ответственный:', document.assigned_to.get_full_name()])
    
    if document.deadline:
        data.append(['Срок исполнения:', document.deadline.strftime('%d.%m.%Y')])
    
    table = Table(data, colWidths=[150, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Содержание
    if document.content:
        content_title = Paragraph("<b>Содержание:</b>", styles['Heading2'])
        story.append(content_title)
        story.append(Spacer(1, 12))
        
        content = Paragraph(document.content.replace('\n', '<br/>'), styles['BodyText'])
        story.append(content)
    
    # Генерируем PDF
    doc.build(story)
    
    buffer.seek(0)
    
    # Логируем
    log_audit(
        user=request.user,
        action='download',
        object_type='Document',
        object_id=document.id,
        object_repr=str(document),
        details='Экспорт в PDF',
        request=request
    )
    
    response = FileResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="document_{document.id}.pdf"'
    
    return response


@login_required
def print_document(request, document_id):
    """Страница для печати документа"""
    document = get_object_or_404(Document, pk=document_id)
    
    context = {
        'document': document
    }
    
    return render(request, 'documents/document_print.html', context)


# ============== ВЛОЖЕНИЯ ============== #

@login_required
@require_POST
def upload_attachment(request, document_id):
    """Загрузить вложение к документу"""
    document = get_object_or_404(Document, pk=document_id)
    
    if not can_edit_document(request.user, document):
        return JsonResponse({'success': False, 'error': 'Нет прав на добавление вложений'})
    
    file = request.FILES.get('file')
    description = request.POST.get('description', '')
    
    if not file:
        return JsonResponse({'success': False, 'error': 'Файл не выбран'})
    
    attachment = DocumentAttachment.objects.create(
        document=document,
        file=file,
        original_filename=file.name,
        file_size=file.size,
        file_type=file.content_type,
        uploaded_by=request.user,
        description=description
    )
    
    return JsonResponse({
        'success': True,
        'attachment': {
            'id': attachment.id,
            'filename': attachment.original_filename,
            'size': attachment.file_size_mb,
            'url': attachment.file.url
        }
    })


@login_required
def delete_attachment(request, attachment_id):
    """Удалить вложение"""
    attachment = get_object_or_404(DocumentAttachment, pk=attachment_id)
    document = attachment.document
    
    if not can_edit_document(request.user, document):
        return JsonResponse({'success': False, 'error': 'Нет прав на удаление вложений'})
    
    attachment.file.delete()
    attachment.delete()
    
    return JsonResponse({'success': True})


# ============== УВЕДОМЛЕНИЯ ============== #

@login_required
def notifications_list(request):
    """Список уведомлений пользователя"""
    notifications = request.user.notifications.all().order_by('-created_at')[:50]
    
    return render(request, 'documents/notifications_modern.html', {'notifications': notifications})


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """Отметить уведомление как прочитанное"""
    notification = get_object_or_404(Notification, pk=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    return JsonResponse({'success': True})


@login_required
@require_POST
def mark_all_notifications_read(request):
    """Отметить все уведомления как прочитанные"""
    request.user.notifications.filter(is_read=False).update(is_read=True)
    # If AJAX request, return JSON; otherwise redirect back
    if request.headers.get('Content-Type') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    from django.shortcuts import redirect
    return redirect('documents:notifications_list')


@login_required
def unread_notifications_count(request):
    """Количество непрочитанных уведомлений (API)"""
    count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({'count': count})


# ============== ЭЛЕКТРОННЫЕ ПОДПИСИ ============== #

@login_required
def document_signatures(request, document_id):
    """Список электронных подписей документа"""
    document = get_object_or_404(Document, pk=document_id)
    signatures = ElectronicSignature.objects.filter(document=document).select_related('signer').order_by('-signed_at')
    return render(request, 'documents/document_signatures.html', {
        'document': document,
        'signatures': signatures,
    })


@login_required
@require_POST
def sign_document_view(request, document_id):
    """Подписать документ электронной подписью"""
    from .utils import sign_document
    document = get_object_or_404(Document, pk=document_id)

    if document.status != 'approved':
        messages.error(request, 'Документ должен быть утверждён перед подписанием.')
        return redirect('documents:document_signatures', document_id=document_id)

    already_signed = ElectronicSignature.objects.filter(document=document, signer=request.user).exists()
    if already_signed:
        messages.warning(request, 'Вы уже подписали этот документ.')
        return redirect('documents:document_signatures', document_id=document_id)

    sign_document(document, request.user, request)
    messages.success(request, 'Документ успешно подписан электронной подписью!')
    return redirect('documents:document_signatures', document_id=document_id)


@login_required
def get_template_placeholders(request, template_id):
    """API: Получить плейсхолдеры шаблона"""
    try:
        template = DocumentTemplate.objects.get(id=template_id, is_active=True)
        placeholders = template.placeholders if template.placeholders else []
        
        return JsonResponse({
            'success': True,
            'placeholders': placeholders,
            'template_name': template.name,
            'template_type': template.get_type_display()
        })
    except DocumentTemplate.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Шаблон не найден'
        }, status=404)
