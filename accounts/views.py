from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.db.models import Q
from documents.permissions import admin_required
from .forms import UserRegistrationForm, UserProfileForm, CustomAuthenticationForm
from .models import UserProfile


class CustomLoginView(LoginView):
    """Кастомный вход в систему"""
    form_class = CustomAuthenticationForm
    template_name = 'accounts/login_modern.html'
    
    def get_success_url(self):
        return reverse_lazy('documents:dashboard')


def register(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('documents:dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register_modern.html', {'form': form})


@login_required
def profile(request):
    """Просмотр и редактирование профиля"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'accounts/profile_modern.html', {'form': form, 'profile': profile})


@login_required
def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.info(request, 'Вы вышли из системы.')
    return redirect('accounts:login')


@login_required
@admin_required
def user_management(request):
    """Управление пользователями — только для администратора"""
    search = request.GET.get('search', '').strip()
    role_filter = request.GET.get('role', '')

    users = User.objects.select_related('profile').order_by('last_name', 'first_name', 'username')

    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )

    if role_filter:
        users = users.filter(profile__role=role_filter)

    role_choices = UserProfile.ROLE_CHOICES

    # Count per role for stats (always total, not filtered)
    from django.db.models import Count as _Count
    role_counts_raw = {
        item['role']: item['cnt']
        for item in UserProfile.objects.values('role').annotate(cnt=_Count('id'))
    }
    # Merge into a list to pass to template (key, label, count)
    role_stats = [
        (rk, rn, role_counts_raw.get(rk, 0))
        for rk, rn in role_choices
    ]

    return render(request, 'accounts/user_management.html', {
        'users': users,
        'role_choices': role_choices,
        'role_stats': role_stats,
        'search': search,
        'role_filter': role_filter,
        'total_users': User.objects.count(),
    })


@login_required
@admin_required
def user_edit(request, user_id):
    """Редактирование пользователя администратором"""
    target_user = get_object_or_404(User, pk=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=target_user)

    if request.method == 'POST':
        # Update basic info
        target_user.first_name = request.POST.get('first_name', target_user.first_name).strip()
        target_user.last_name = request.POST.get('last_name', target_user.last_name).strip()
        target_user.email = request.POST.get('email', target_user.email).strip()
        is_active = request.POST.get('is_active') == 'on'
        target_user.is_active = is_active

        # Admin flag: only superusers can grant superuser
        if request.user.is_superuser:
            target_user.is_staff = request.POST.get('is_staff') == 'on'

        target_user.save()

        # Update profile
        new_role = request.POST.get('role', profile.role)
        profile.role = new_role
        profile.department = request.POST.get('department', profile.department).strip()
        profile.position = request.POST.get('position', profile.position).strip()
        profile.phone = request.POST.get('phone', profile.phone).strip()
        profile.save()

        messages.success(request, f'Пользователь {target_user.get_full_name() or target_user.username} обновлён.')
        return redirect('accounts:user_management')

    return render(request, 'accounts/user_edit.html', {
        'target_user': target_user,
        'profile': profile,
        'role_choices': UserProfile.ROLE_CHOICES,
    })


@login_required
@admin_required
def user_toggle_active(request, user_id):
    """Заблокировать / разблокировать пользователя"""
    if request.method == 'POST':
        target_user = get_object_or_404(User, pk=user_id)
        if target_user == request.user:
            messages.error(request, 'Нельзя заблокировать самого себя.')
        else:
            target_user.is_active = not target_user.is_active
            target_user.save()
            status = 'разблокирован' if target_user.is_active else 'заблокирован'
            messages.success(request, f'Пользователь {target_user.username} {status}.')
    return redirect('accounts:user_management')
