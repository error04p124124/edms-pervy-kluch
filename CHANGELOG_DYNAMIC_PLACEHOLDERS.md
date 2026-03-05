# Журнал изменений: Система динамических плейсхолдеров

## Дата: 2024
## Версия: 2.0 - Динамические плейсхолдеры

---

## Обзор изменений

Реализована полная система динамических плейсхолдеров для шаблонов документов. Теперь администраторы могут определять свои собственные поля при создании шаблонов, вместо использования жестко заданных полей.

---

## Измененные файлы

### 1. `documents/forms.py`

#### Изменения в DocumentFromTemplateForm:

**Было:**
```python
class DocumentFromTemplateForm(forms.Form):
    template = forms.ModelChoiceField(...)
    title = forms.CharField(...)
    full_name = forms.CharField(...)  # Жестко заданные поля
    position = forms.CharField(...)
    department = forms.CharField(...)
    custom_field_1 = forms.CharField(...)
    custom_field_2 = forms.CharField(...)
    assigned_to = forms.ModelChoiceField(...)
    deadline = forms.DateField(...)
```

**Стало:**
```python
class DocumentFromTemplateForm(forms.Form):
    template = forms.ModelChoiceField(...)
    title = forms.CharField(...)
    assigned_to = forms.ModelChoiceField(...)
    deadline = forms.DateField(...)
    
    def __init__(self, *args, template_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Динамическое создание полей на основе template.placeholders
        if template_id:
            try:
                template = DocumentTemplate.objects.get(pk=template_id)
                if template.placeholders:
                    for key, config in template.placeholders.items():
                        # Создание поля нужного типа
                        field_type = config.get('type', 'text')
                        label = config.get('label', key)
                        required = config.get('required', False)
                        help_text = config.get('help_text', '')
                        default_value = config.get('default', '')
                        
                        # Создание поля в зависимости от типа
                        if field_type == 'textarea':
                            field = forms.CharField(widget=forms.Textarea(...))
                        elif field_type == 'date':
                            field = forms.DateField(widget=forms.DateInput(...))
                        elif field_type == 'number':
                            field = forms.IntegerField(...)
                        else:  # text
                            field = forms.CharField(...)
                        
                        # Добавление поля с префиксом
                        self.fields[f'placeholder_{key}'] = field
            except DocumentTemplate.DoesNotExist:
                pass
```

**Причина изменения:**
- Убраны жестко заданные поля (full_name, position, department, custom_field_1, custom_field_2)
- Добавлен метод `__init__` для динамического создания полей
- Поля создаются на основе JSON конфигурации из template.placeholders
- Поддержка разных типов полей: text, textarea, date, number
- Автоматическое применение label, required, help_text, default

---

### 2. `documents/views.py`

#### A. Добавлен импорт date:

```python
from datetime import datetime, timedelta, date  # Добавлен date
```

#### B. Изменена функция create_from_template:

**Было:**
```python
@login_required
@login_required  # Дубликат
def create_from_template(request):
    if request.method == 'POST':
        form = DocumentFromTemplateForm(request.POST)
        if form.is_valid():
            template = form.cleaned_data['template']
            
            # Жестко заданные замены
            replacements = {
                'имя': form.cleaned_data.get('full_name', ''),
                'должность': form.cleaned_data.get('position', ''),
                'отдел': form.cleaned_data.get('department', ''),
                'дата': timezone.now().strftime('%d.%m.%Y'),
                'время': timezone.now().strftime('%H:%M'),
                'custom1': form.cleaned_data.get('custom_field_1', ''),
                'custom2': form.cleaned_data.get('custom_field_2', ''),
            }
            # ... создание документа ...
    else:
        form = DocumentFromTemplateForm()
```

**Стало:**
```python
@login_required
def create_from_template(request):
    if request.method == 'POST':
        # Получаем template_id для создания формы с правильными полями
        template_id = request.POST.get('template')
        form = DocumentFromTemplateForm(request.POST, template_id=template_id)
        if form.is_valid():
            template = form.cleaned_data['template']
            
            # Автоматические плейсхолдеры
            replacements = {
                'дата': timezone.now().strftime('%d.%m.%Y'),
                'время': timezone.now().strftime('%H:%M'),
                'название': form.cleaned_data.get('title', ''),
            }
            
            # Добавляем динамические плейсхолдеры
            if template.placeholders:
                for key in template.placeholders.keys():
                    field_name = f'placeholder_{key}'
                    value = form.cleaned_data.get(field_name, '')
                    # Форматируем дату если это поле типа date
                    if isinstance(value, date):
                        value = value.strftime('%d.%m.%Y')
                    replacements[key] = str(value) if value else ''
            
            # ... создание документа ...
    else:
        # Получаем template_id из GET параметра
        template_id = request.GET.get('template')
        form = DocumentFromTemplateForm(template_id=template_id)
```

**Изменения:**
- Убран дубликат декоратора `@login_required`
- При POST: извлекаем template_id из request.POST и передаем в форму
- При GET: извлекаем template_id из query параметра (?template=X)
- Заменены жестко заданные плейсхолдеры на динамическое извлечение
- Автоматическое форматирование дат (date → строка ДД.ММ.ГГГГ)
- Добавлен автоматический плейсхолдер `название`

---

### 3. `templates/documents/create_from_template.html`

**Было:**
- Форма с жестко заданными полями:
  - ФИО (full_name)
  - Должность (position)
  - Отдел (department)
  - Дополнительное поле 1 (custom_field_1)
  - Дополнительное поле 2 (custom_field_2)
- Статичная справка по плейсхолдерам

**Стало:**
```html
<form method="post" id="document-form">
    {% csrf_token %}
    
    <!-- Выбор шаблона -->
    <div class="mb-3">
        <label>Шаблон документа *</label>
        {{ form.template }}
    </div>
    
    <!-- Название -->
    <div class="mb-3">
        <label>Название документа *</label>
        {{ form.title }}
    </div>
    
    <!-- Динамические поля (заполняется JavaScript'ом) -->
    <div id="dynamic-fields-section"></div>
    
    <!-- Параметры документа -->
    <div class="row">
        <div class="col-md-6">
            {{ form.assigned_to }}
        </div>
        <div class="col-md-6">
            {{ form.deadline }}
        </div>
    </div>
</form>

<script>
// При изменении шаблона - перезагрузить страницу с параметром template
document.getElementById('id_template').addEventListener('change', function() {
    const templateId = this.value;
    if (templateId) {
        window.location.href = '{% url "documents:create_from_template" %}?template=' + templateId;
    }
});

// Отображение динамических полей
document.addEventListener('DOMContentLoaded', function() {
    const dynamicSection = document.getElementById('dynamic-fields-section');
    const allFields = document.querySelectorAll('[name^="placeholder_"]');
    
    if (allFields.length > 0) {
        // Создаем заголовок секции
        const header = document.createElement('div');
        header.innerHTML = '<hr><h6 class="mb-3">Заполнение полей шаблона</h6>';
        dynamicSection.appendChild(header);
        
        // Перемещаем динамические поля в секцию
        allFields.forEach(field => {
            const formGroup = field.closest('.mb-3') || field.parentElement;
            if (formGroup) {
                dynamicSection.appendChild(formGroup);
            }
        });
    }
});
</script>
```

**Изменения:**
- Удалены все жестко заданные поля
- Добавлен контейнер `#dynamic-fields-section` для динамических полей
- JavaScript автоматически перезагружает страницу при выборе шаблона
- JavaScript находит все поля с префиксом `placeholder_` и группирует их
- Обновлена справка: только автоматические плейсхолдеры (дата, время, название)

---

## Новые возможности

### Для администраторов:

1. **Визуальное управление плейсхолдерами** (из предыдущей версии)
   - Интерфейс добавления/редактирования/удаления плейсхолдеров
   - Модальное окно с полями:
     - Ключ плейсхолдера
     - Отображаемое название
     - Тип поля (text, textarea, date, number)
     - Текст подсказки
     - Значение по умолчанию
     - Обязательное поле (галочка)

2. **Динамическое создание форм**
   - При выборе шаблона форма автоматически обновляется
   - Показываются только те поля, которые определены в шаблоне
   - Правильные типы полей (текст, многострочный текст, дата, число)

3. **Автоматические плейсхолдеры**
   - `{{дата}}` - текущая дата (ДД.ММ.ГГГГ)
   - `{{время}}` - текущее время (ЧЧ:ММ)
   - `{{название}}` - название документа

### Для пользователей:

1. **Интуитивно понятная форма**
   - Видны только релевантные поля для выбранного шаблона
   - Подсказки помогают правильно заполнить данные
   - Валидация обязательных полей

2. **Автозаполнение**
   - Значения по умолчанию экономят время
   - Можно изменить предзаполненные значения

---

## Технические детали

### Структура placeholders в базе данных:

```json
{
  "фио_сотрудника": {
    "label": "ФИО сотрудника",
    "type": "text",
    "required": true,
    "help_text": "Введите полное ФИО",
    "default": ""
  },
  "адрес": {
    "label": "Адрес проживания",
    "type": "textarea",
    "required": true,
    "help_text": "Укажите полный адрес с индексом",
    "default": ""
  },
  "дата_приема": {
    "label": "Дата приема на работу",
    "type": "date",
    "required": true,
    "help_text": "",
    "default": ""
  },
  "оклад": {
    "label": "Оклад (руб.)",
    "type": "number",
    "required": true,
    "help_text": "Укажите размер оклада",
    "default": ""
  }
}
```

### Префикс полей формы:

Все динамические поля в HTML форме имеют префикс `placeholder_`:
- Ключ `фио_сотрудника` → HTML name `placeholder_фио_сотрудника`
- Ключ `адрес` → HTML name `placeholder_адрес`

Это позволяет:
- Отличить динамические поля от стандартных (template, title, assigned_to, deadline)
- Избежать конфликтов имен
- Легко извлечь значения в view

### Процесс создания документа:

1. **Пользователь выбирает шаблон**
   - JavaScript: `window.location.href = '?template=X'`
   - Страница перезагружается с GET параметром

2. **View создает форму с динамическими полями**
   - `DocumentFromTemplateForm(template_id=X)`
   - `__init__` читает template.placeholders
   - Создает поля: `self.fields[f'placeholder_{key}']`

3. **Django рендерит форму**
   - Стандартные поля: template, title, assigned_to, deadline
   - Динамические поля: placeholder_XXX с правильными типами

4. **JavaScript организует отображение**
   - Находит все поля с `name^="placeholder_"`
   - Группирует их в секцию "Заполнение полей шаблона"
   - Показывает после стандартных полей

5. **Пользователь заполняет и отправляет форму**
   - POST данные содержат: template, title, placeholder_XXX, assigned_to, deadline

6. **View обрабатывает данные**
   - Создает форму: `DocumentFromTemplateForm(request.POST, template_id=...)`
   - Валидирует поля
   - Извлекает значения: `form.cleaned_data.get(f'placeholder_{key}')`
   - Форматирует даты: `value.strftime('%d.%m.%Y')`
   - Создает replacements dict: `{key: value}`

7. **Генерация файла**
   - `generate_document_from_template(template_path, output_path, replacements)`
   - Заменяет `{{key}}` на значения в Word/Excel/PowerPoint

---

## Миграция данных

### Не требуется миграция базы данных:

- Поле `DocumentTemplate.placeholders` уже существует (JSONField)
- Старые шаблоны без placeholders продолжают работать
- Новые шаблоны используют динамическую систему

### Обратная совместимость:

Старые документы, созданные с жестко заданными плейсхолдерами (`{{имя}}`, `{{должность}}`), продолжат работать, но:
- Эти плейсхолдеры не будут заменяться в новых документах
- Рекомендуется пересоздать шаблоны с новой системой

---

## Тестирование

### Тестовый сценарий 1: Создание шаблона с плейсхолдерами

1. Перейти в "Шаблоны" → "Добавить шаблон"
2. Заполнить название, выбрать формат (Word)
3. Добавить плейсхолдеры:
   - `фио` (text, обязательное)
   - `адрес` (textarea, обязательное)
   - `дата_рождения` (date, необязательное)
4. Загрузить Word файл с `{{фио}}`, `{{адрес}}`, `{{дата_рождения}}`
5. Сохранить шаблон

### Тестовый сценарий 2: Создание документа

1. Перейти в "Документы" → "Создать из шаблона"
2. Выбрать созданный шаблон
3. Проверить, что появились поля: ФИО, Адрес проживания, Дата рождения
4. Заполнить:
   - ФИО: "Иванов Иван Иванович"
   - Адрес: "г. Москва, ул. Ленина, д. 1"
   - Дата рождения: "01.01.1990"
5. Создать документ
6. Скачать сгенерированный Word файл
7. Проверить, что плейсхолдеры заменены на введенные значения

### Тестовый сценарий 3: Валидация

1. Создать документ из шаблона с обязательными полями
2. Оставить обязательное поле пустым
3. Попытаться отправить форму
4. Проверить, что появилась ошибка валидации

---

## Известные ограничения

1. **Изменение шаблона требует перезагрузки страницы**
   - При выборе другого шаблона страница перезагружается
   - Несохраненные данные будут потеряны

2. **Максимум полей не ограничен**
   - Технически можно создать сколько угодно плейсхолдеров
   - Рекомендуется: 5-10 полей для удобства

3. **Типы данных ограничены**
   - Поддерживаются: text, textarea, date, number
   - Нет: checkbox, select, radio, file upload

---

## Будущие улучшения

Возможные улучшения в следующих версиях:

1. **AJAX обновление формы без перезагрузки**
   - Использовать fetch() для получения полей шаблона
   - Динамически создавать поля без reload

2. **Больше типов полей**
   - Select (выпадающий список)
   - Checkbox (галочка)
   - Email (валидация email)
   - Phone (валидация телефона)

3. **Группировка плейсхолдеров**
   - Организация полей по категориям
   - Секции "Личные данные", "Адрес", "Контакты" и т.д.

4. **Условная видимость полей**
   - Показывать/скрывать поля в зависимости от других значений

5. **Валидация плейсхолдеров**
   - Регулярные выражения для проверки формата
   - Минимальная/максимальная длина

---

## Документация

Созданы следующие файлы документации:

1. **DYNAMIC_PLACEHOLDERS_GUIDE.md** (этот файл)
   - Подробное руководство для пользователей
   - Примеры использования
   - Советы и рекомендации
   - Устранение проблем

2. **CHANGELOG_DYNAMIC_PLACEHOLDERS.md**
   - Технический журнал изменений
   - Список измененных файлов
   - Детали реализации

---

## Контакты

При возникновении вопросов или проблем обращайтесь к администратору системы или разработчику.

**Система:** ЭДО "Первый ключ"  
**Версия:** 2.0 - Динамические плейсхолдеры  
**Дата:** 2024
