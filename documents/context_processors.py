from .models import Notification, WorkflowStep, ChatMessage
from .permissions import (
    can_edit_document, can_delete_document, can_approve_document, 
    can_manage_templates, can_view_all_documents
)


def notifications_processor(request):
    """Контекстный процессор для уведомлений"""
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(user=request.user, is_read=False)
        # Подсчет ожидающих согласований для менеджеров
        pending_approvals = WorkflowStep.objects.filter(
            user=request.user,
            status='pending'
        ).count()
        unread_chat_count = ChatMessage.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        return {
            'unread_notifications': unread_notifications,
            'unread_count': unread_notifications.count(),
            'pending_approvals': pending_approvals,
            'unread_chat_count': unread_chat_count,
        }
    return {
        'unread_notifications': [],
        'unread_count': 0,
        'pending_approvals': 0,
        'unread_chat_count': 0,
    }


def permissions_processor(request):
    """Контекстный процессор для прав доступа"""
    if not request.user.is_authenticated:
        return {}
    
    return {
        'can_edit_document': can_edit_document,
        'can_delete_document': can_delete_document,
        'can_approve_document': can_approve_document,
        'can_manage_templates': can_manage_templates,
        'can_view_all_documents': can_view_all_documents,
    }
