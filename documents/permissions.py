"""
Декораторы и миксины для разграничения доступа по ролям
"""
from functools import wraps
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """
    Декоратор для проверки роли пользователя
    
    Использование:
        @role_required('admin', 'clerk')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Необходима авторизация')
                return redirect('accounts:login')
            
            if not hasattr(request.user, 'profile'):
                messages.error(request, 'Профиль пользователя не найден')
                return redirect('documents:dashboard')
            
            user_role = request.user.profile.role
            
            if user_role not in roles and user_role != 'admin':
                messages.error(request, 'У вас нет прав для выполнения этого действия')
                return redirect('documents:dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_required(view_func):
    """Декоратор для проверки роли администратора"""
    return role_required('admin')(view_func)


def clerk_required(view_func):
    """Декоратор для проверки роли делопроизводителя или администратора"""
    return role_required('clerk', 'admin')(view_func)


def manager_required(view_func):
    """Декоратор для проверки роли руководителя или администратора"""
    return role_required('manager', 'admin')(view_func)


def clerk_or_manager_required(view_func):
    """Декоратор для проверки роли делопроизводителя, руководителя или администратора"""
    return role_required('clerk', 'manager', 'admin')(view_func)


class RoleRequiredMixin(UserPassesTestMixin):
    """
    Миксин для class-based views с проверкой роли
    
    Использование:
        class MyView(RoleRequiredMixin, ListView):
            required_roles = ['admin', 'clerk']
            ...
    """
    required_roles = []
    
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        
        if not hasattr(self.request.user, 'profile'):
            return False
        
        user_role = self.request.user.profile.role
        
        # Администратор имеет доступ ко всему
        if user_role == 'admin':
            return True
        
        return user_role in self.required_roles
    
    def handle_no_permission(self):
        messages.error(self.request, 'У вас нет прав для выполнения этого действия')
        return redirect('documents:dashboard')


class AdminRequiredMixin(RoleRequiredMixin):
    """Миксин для проверки роли администратора"""
    required_roles = ['admin']


class ClerkRequiredMixin(RoleRequiredMixin):
    """Миксин для проверки роли делопроизводителя"""
    required_roles = ['clerk']


class ManagerRequiredMixin(RoleRequiredMixin):
    """Миксин для проверки роли руководителя"""
    required_roles = ['manager']


class ClerkOrManagerRequiredMixin(RoleRequiredMixin):
    """Миксин для проверки роли делопроизводителя или руководителя"""
    required_roles = ['clerk', 'manager']


def can_edit_document(user, document=None):
    """
    Проверка прав на редактирование документа

    - Админ / делопроизводитель — любые документы
    - Руководитель / сотрудник — только свои (created_by или assigned_to)
    """
    if not user.is_authenticated:
        return False

    if not hasattr(user, 'profile'):
        return False

    user_role = user.profile.role

    if user_role in ['admin', 'clerk']:
        return True

    # manager и employee могут редактировать только свои документы
    if document is not None:
        return document.created_by == user or document.assigned_to == user

    return True  # общая проверка без конкретного документа


def can_delete_document(user, document=None):
    """
    Проверка прав на удаление документа — только admin и clerk.
    """
    if not user.is_authenticated:
        return False

    if not hasattr(user, 'profile'):
        return False

    return user.profile.role in ['admin', 'clerk']


def can_approve_document(user, document=None):
    """
    Проверка прав на утверждение / отклонение документа.

    - Администратор, руководитель и делопроизводитель могут утверждать.
    """
    if not user.is_authenticated:
        return False

    if not hasattr(user, 'profile'):
        return False

    return user.profile.role in ['admin', 'manager', 'clerk']


def can_manage_templates(user):
    """
    Проверка прав на работу с шаблонами — все авторизованные пользователи.
    Удаление шаблонов остаётся только для admin и clerk.
    """
    return bool(user.is_authenticated)


def can_view_all_documents(user):
    """
    Проверка прав на просмотр всех документов
    
    - Админ видит все документы
    - Делопроизводитель видит все документы  
    - Руководитель видит все документы (для отслеживания и утверждения)
    - Сотрудник видит только документы, где он создатель или ответственный
    """
    if not user.is_authenticated:
        return False
    
    if not hasattr(user, 'profile'):
        return False
    
    user_role = user.profile.role
    
    return user_role in ['admin', 'clerk', 'manager']

def can_create_document(user):
    """
    Все авторизованные пользователи могут создавать документы.
    """
    return bool(user.is_authenticated)