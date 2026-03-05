from django import forms
from django.contrib.auth.models import User
from .models import Document, DocumentTemplate, DocumentHistory, WorkflowStep


class DocumentTemplateForm(forms.ModelForm):
    """Форма для создания/редактирования шаблона с поддержкой файлов"""

    class Meta:
        model = DocumentTemplate
        fields = ['name', 'type', 'file_format', 'template_file', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название шаблона'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'file_format': forms.Select(attrs={'class': 'form-select'}),
            'template_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.docx,.xlsx,.pdf'
            }),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Краткое описание назначения шаблона'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        template_file = cleaned_data.get('template_file')
        file_format = cleaned_data.get('file_format')

        if not template_file:
            if not self.instance.pk or not self.instance.template_file:
                raise forms.ValidationError(
                    f'Для формата {(file_format or "").upper()} необходимо загрузить файл-шаблон'
                )

        return cleaned_data


class DocumentForm(forms.ModelForm):
    """Форма для создания/редактирования документа"""
    
    class Meta:
        model = Document
        fields = ['title', 'template', 'content', 'file', 'assigned_to', 'deadline', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название документа'}),
            'template': forms.Select(attrs={'class': 'form-select', 'id': 'id_template'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Фильтруем пользователей для назначения
        if user:
            self.fields['assigned_to'].queryset = User.objects.exclude(id=user.id).filter(is_active=True)
        
        self.fields['assigned_to'].required = False
        self.fields['template'].required = False
        self.fields['template'].empty_label = '— Без шаблона —'
        self.fields['template'].queryset = DocumentTemplate.objects.filter(is_active=True).order_by('name')


class DocumentFromTemplateForm(forms.Form):
    """Форма для создания документа из шаблона с динамическими полями"""
    
    template = forms.ModelChoiceField(
        queryset=DocumentTemplate.objects.filter(is_active=True),
        label='Шаблон документа',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'template-select'})
    )
    title = forms.CharField(
        label='Название документа',
        max_length=300,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название документа'})
    )
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        label='Ответственный',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    deadline = forms.DateField(
        label='Срок исполнения',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    def __init__(self, *args, **kwargs):
        template_id = kwargs.pop('template_id', None)
        super().__init__(*args, **kwargs)
        
        # Если передан template_id, добавляем динамические поля
        if template_id:
            try:
                template = DocumentTemplate.objects.get(id=template_id, is_active=True)
                placeholders = template.placeholders or []
                # placeholders is a list of {name, label, type, required, ...}
                if isinstance(placeholders, dict):
                    # legacy dict format — convert on-the-fly
                    placeholders = [{'name': k, **v} for k, v in placeholders.items()]

                # Добавляем динамические поля на основе плейсхолдеров
                for item in placeholders:
                    key = item.get('name', '')
                    if not key:
                        continue
                    config = item
                    field_type = config.get('type', 'text')
                    label = config.get('label', key)
                    required = config.get('required', False)
                    help_text = config.get('help_text', '')
                    default_value = config.get('default', '')
                    
                    # Создаем поле в зависимости от типа
                    if field_type == 'textarea':
                        field = forms.CharField(
                            label=label,
                            required=required,
                            initial=default_value,
                            help_text=help_text,
                            widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
                        )
                    elif field_type == 'date':
                        field = forms.DateField(
                            label=label,
                            required=required,
                            initial=default_value,
                            help_text=help_text,
                            widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
                        )
                    elif field_type == 'number':
                        field = forms.IntegerField(
                            label=label,
                            required=required,
                            initial=default_value if default_value else None,
                            help_text=help_text,
                            widget=forms.NumberInput(attrs={'class': 'form-control'})
                        )
                    else:  # text
                        field = forms.CharField(
                            label=label,
                            required=required,
                            initial=default_value,
                            help_text=help_text,
                            widget=forms.TextInput(attrs={'class': 'form-control'})
                        )
                    
                    # Добавляем поле в форму с префиксом placeholder_
                    self.fields[f'placeholder_{key}'] = field
                    
            except DocumentTemplate.DoesNotExist:
                pass


class WorkflowRouteForm(forms.Form):
    """Форма для настройки маршрута согласования"""
    
    approvers = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        label='Согласующие (в порядке согласования)',
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '10'}),
        help_text='Выберите пользователей в том порядке, в котором они должны согласовать документ'
    )


class DocumentFilterForm(forms.Form):
    """Форма для фильтрации документов"""
    
    STATUS_CHOICES = [('', 'Все статусы')] + Document.STATUS_CHOICES
    
    search = forms.CharField(
        label='Поиск',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Поиск по названию или номеру'})
    )
    status = forms.ChoiceField(
        label='Статус',
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    template_type = forms.ChoiceField(
        label='Тип документа',
        choices=[('', 'Все типы')] + DocumentTemplate.TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        label='Дата от',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        label='Дата до',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    only_overdue = forms.BooleanField(
        label='Только просроченные',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class ApprovalForm(forms.Form):
    """Форма для утверждения/отклонения документа"""
    
    ACTION_CHOICES = [
        ('approve', 'Утвердить'),
        ('reject', 'Отклонить'),
    ]
    
    action = forms.ChoiceField(
        label='Действие',
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    comment = forms.CharField(
        label='Комментарий',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 
                                      'placeholder': 'Укажите причину отклонения или оставьте комментарий'})
    )
