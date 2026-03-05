from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile


class UserRegistrationForm(UserCreationForm):
    """Форма регистрации пользователя"""
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(required=True, label='Имя')
    last_name = forms.CharField(required=True, label='Фамилия')
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    """Форма редактирования профиля"""
    first_name = forms.CharField(
        required=True,
        label='Имя',
        widget=forms.TextInput(attrs={
            'class': 'modern-input',
            'placeholder': 'Введите имя'
        })
    )
    last_name = forms.CharField(
        required=True,
        label='Фамилия',
        widget=forms.TextInput(attrs={
            'class': 'modern-input',
            'placeholder': 'Введите фамилию'
        })
    )
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'modern-input',
            'placeholder': 'example@company.com'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = ('department', 'position', 'phone', 'avatar')
        labels = {
            'department': 'Отдел',
            'position': 'Должность',
            'phone': 'Телефон',
            'avatar': 'Фото',
        }
        widgets = {
            'department': forms.TextInput(attrs={
                'class': 'modern-input',
                'placeholder': 'Например: Бухгалтерия'
            }),
            'position': forms.TextInput(attrs={
                'class': 'modern-input',
                'placeholder': 'Например: Главный бухгалтер'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'modern-input',
                'placeholder': '+7 (999) 123-45-67'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'modern-file-input',
                'accept': 'image/*'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            user = profile.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.save()
            profile.save()
        return profile


class CustomAuthenticationForm(AuthenticationForm):
    """Кастомная форма входа"""
    username = forms.CharField(
        label='Имя пользователя',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите имя пользователя'})
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Введите пароль'})
    )
