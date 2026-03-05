"""
Middleware для аудита и логирования
"""
from django.utils import timezone
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from documents.models import AuditLog


def get_client_ip(request):
    """Получить IP адрес клиента"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Логирование входа пользователя"""
    AuditLog.objects.create(
        user=user,
        action='login',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        details=f'Успешный вход в систему'
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Логирование выхода пользователя"""
    if user:
        AuditLog.objects.create(
            user=user,
            action='logout',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details=f'Выход из системы'
        )


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """Логирование неудачной попытки входа"""
    AuditLog.objects.create(
        user=None,
        action='error',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        details=f'Неудачная попытка входа с username: {credentials.get("username", "unknown")}'
    )


class AuditMiddleware:
    """
    Middleware для автоматического аудита действий
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Код перед обработкой view
        response = self.get_response(request)
        
        # Логируем важные действия
        if request.user.is_authenticated and request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            # Определяем тип действия
            if request.method == 'POST':
                action = 'create'
            elif request.method in ['PUT', 'PATCH']:
                action = 'update'
            elif request.method == 'DELETE':
                action = 'delete'
            else:
                action = 'view'
            
            # Определяем тип объекта из URL
            path = request.path
            object_type = ''
            if '/documents/' in path:
                object_type = 'Document'
            elif '/templates/' in path:
                object_type = 'Template'
            elif '/tasks/' in path:
                object_type = 'Task'
            
            # Логируем только если это важное действие
            if object_type and response.status_code < 400:
                try:
                    AuditLog.objects.create(
                        user=request.user,
                        action=action,
                        object_type=object_type,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        details=f'{request.method} {path}'
                    )
                except Exception:
                    # Игнорируем ошибки логирования
                    pass
        
        return response
    
    def process_exception(self, request, exception):
        """Логирование исключений"""
        if request.user.is_authenticated:
            try:
                AuditLog.objects.create(
                    user=request.user,
                    action='error',
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    details=f'Ошибка: {str(exception)[:200]}'
                )
            except Exception:
                pass
        return None
