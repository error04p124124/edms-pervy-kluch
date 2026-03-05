"""
Утилиты для отправки email-уведомлений
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_notification_email(user, subject, message, document=None):
    """
    Отправка email-уведомления пользователю
    
    Args:
        user: Пользователь-получатель
        subject: Тема письма
        message: Текст сообщения
        document: Документ (опционально)
    """
    if not user.email:
        return False
    
    try:
        # Формируем HTML-сообщение
        context = {
            'user': user,
            'subject': subject,
            'message': message,
            'document': document,
        }
        
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                <h2 style="color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px;">
                    ЭДО "Первый ключ"
                </h2>
                
                <p>Здравствуйте, <strong>{user.get_full_name() or user.username}</strong>!</p>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0; font-size: 16px;">{message}</p>
                </div>
                
                {f'<p><strong>Документ:</strong> {document.title} ({document.registry_number})</p>' if document else ''}
                
                <hr style="margin: 20px 0; border: none; border-top: 1px solid #ddd;">
                
                <p style="font-size: 12px; color: #666;">
                    Это автоматическое уведомление из системы электронного документооборота.<br>
                    Пожалуйста, не отвечайте на это письмо.
                </p>
                
                <p style="font-size: 12px; color: #666;">
                    <a href="http://127.0.0.1:3000" style="color: #667eea;">Перейти в систему</a>
                </p>
            </div>
        </body>
        </html>
        """
        
        plain_message = strip_tags(message)
        
        send_mail(
            subject=f'[ЭДО] {subject}',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=True,
        )
        
        return True
    except Exception as e:
        print(f"Ошибка отправки email: {e}")
        return False


def send_document_assigned_email(document):
    """Уведомление о назначении документа"""
    if document.assigned_to:
        send_notification_email(
            user=document.assigned_to,
            subject='Вам назначен документ',
            message=f'Вам назначен документ "{document.title}"',
            document=document
        )


def send_document_approved_email(document, approver):
    """Уведомление об одобрении документа"""
    send_notification_email(
        user=document.created_by,
        subject='Документ одобрен',
        message=f'Ваш документ "{document.title}" был одобрен пользователем {approver.get_full_name() or approver.username}',
        document=document
    )


def send_document_rejected_email(document, rejector, comment=''):
    """Уведомление об отклонении документа"""
    message = f'Ваш документ "{document.title}" был отклонен пользователем {rejector.get_full_name() or rejector.username}'
    if comment:
        message += f'\n\nКомментарий: {comment}'
    
    send_notification_email(
        user=document.created_by,
        subject='Документ отклонен',
        message=message,
        document=document
    )


def send_workflow_step_notification(step, document):
    """Уведомление о новом этапе согласования"""
    if step.user:
        send_notification_email(
            user=step.user,
            subject='Требуется согласование документа',
            message=f'Документ "{document.title}" ({document.registry_number or "Б/Н"}) ожидает вашего согласования на этапе {step.step_number}',
            document=document
        )


def send_chat_message_email(sender, recipient, message_text):
    """Уведомление о новом сообщении в чате"""
    send_notification_email(
        user=recipient,
        subject=f'Новое сообщение от {sender.get_full_name() or sender.username}',
        message=f'{message_text[:200]}{"..." if len(message_text) > 200 else ""}',
        document=None
    )



def send_overdue_document_reminder(document):
    """Напоминание о просроченном документе"""
    if document.assigned_to:
        send_notification_email(
            user=document.assigned_to,
            subject='⚠️ Просрочен срок исполнения документа',
            message=f'Документ "{document.title}" просрочен. Срок исполнения был: {document.deadline.strftime("%d.%m.%Y")}',
            document=document
        )
