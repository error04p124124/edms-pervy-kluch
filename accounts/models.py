from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Профиль пользователя с ролью и дополнительной информацией"""
    
    ROLE_CHOICES = [
        ('clerk', 'Делопроизводитель'),
        ('manager', 'Руководитель'),
        ('employee', 'Сотрудник'),
        ('admin', 'Администратор'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='Пользователь')
    role = models.CharField('Роль', max_length=20, choices=ROLE_CHOICES, default='employee')
    department = models.CharField('Отдел', max_length=200, blank=True)
    position = models.CharField('Должность', max_length=200, blank=True)
    avatar = models.ImageField('Аватар', upload_to='avatars/', blank=True, null=True)
    phone = models.CharField('Телефон', max_length=20, blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'
        ordering = ['user__last_name', 'user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"
    
    def get_full_name(self):
        return self.user.get_full_name() or self.user.username
    
    @property
    def is_clerk(self):
        return self.role == 'clerk'
    
    @property
    def is_manager(self):
        return self.role == 'manager'
    
    @property
    def is_employee(self):
        return self.role == 'employee'
    
    @property
    def is_admin(self):
        return self.role == 'admin'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Автоматическое создание профиля при создании пользователя"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Сохранение профиля при сохранении пользователя"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
