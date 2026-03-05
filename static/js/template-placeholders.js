/**
 * Управление плейсхолдерами в форме шаблона
 */

class PlaceholderManager {
    constructor() {
        this.placeholders = [];
        this.container = document.getElementById('placeholders-container');
        this.addButton = document.getElementById('add-placeholder-btn');
        this.hiddenInput = document.getElementById('id_placeholders_json');
        
        if (!this.container) return;
        
        this.init();
    }
    
    init() {
        // Загрузить существующие плейсхолдеры
        this.loadPlaceholders();
        
        // Обработчик добавления нового плейсхолдера
        if (this.addButton) {
            this.addButton.addEventListener('click', () => this.addPlaceholder());
        }
        
        // Обработчик сохранения формы
        const form = this.container.closest('form');
        if (form) {
            form.addEventListener('submit', (e) => this.savePlaceholders());
        }
    }
    
    loadPlaceholders() {
        try {
            const data = this.hiddenInput.value;
            if (data) {
                this.placeholders = JSON.parse(data);
            } else {
                this.placeholders = [];
            }
        } catch (e) {
            console.error('Error parsing placeholders:', e);
            this.placeholders = [];
        }
        
        this.render();
    }
    
    addPlaceholder(data = null) {
        const placeholder = data || {
            name: '',
            label: '',
            type: 'text',
            required: false,
            options: []
        };
        
        this.placeholders.push(placeholder);
        this.render();
    }
    
    removePlaceholder(index) {
        if (confirm('Удалить этот плейсхолдер?')) {
            this.placeholders.splice(index, 1);
            this.render();
        }
    }
    
    updatePlaceholder(index, field, value) {
        if (this.placeholders[index]) {
            this.placeholders[index][field] = value;
        }
    }
    
    savePlaceholders() {
        // Собрать данные из полей
        const items = this.container.querySelectorAll('.placeholder-item');
        this.placeholders = [];
        
        items.forEach((item, index) => {
            const name = item.querySelector('.placeholder-name').value.trim();
            const label = item.querySelector('.placeholder-label').value.trim();
            const type = item.querySelector('.placeholder-type').value;
            const required = item.querySelector('.placeholder-required').checked;
            
            if (name && label) {
                this.placeholders.push({
                    name,
                    label,
                    type,
                    required
                });
            }
        });
        
        // Сохранить в скрытое поле
        this.hiddenInput.value = JSON.stringify(this.placeholders);
    }
    
    render() {
        this.container.innerHTML = '';
        
        if (this.placeholders.length === 0) {
            this.container.innerHTML = `
                <div style="padding:1.25rem; border-radius:10px; background:var(--primary-50,#eef2ff);
                            border:1px solid var(--primary-200,#c7d2fe); color:var(--primary-700,#4338ca);
                            font-size:14px; display:flex; align-items:center; gap:10px;">
                    <i class="fas fa-info-circle" style="font-size:16px;"></i>
                    Плейсхолдеры не добавлены. Нажмите «Добавить плейсхолдер» для создания полей.
                </div>
            `;
            return;
        }
        
        this.placeholders.forEach((placeholder, index) => {
            const item = this.createPlaceholderItem(placeholder, index);
            this.container.appendChild(item);
        });
    }
    
    createPlaceholderItem(placeholder, index) {
        const div = document.createElement('div');
        div.className = 'placeholder-item';
        div.style.cssText = `
            background: white;
            border: 2px solid var(--border-light, #e5e7eb);
            border-radius: 12px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 1rem;
            transition: border-color 0.2s;
        `;
        div.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
                <span style="font-size:13px; font-weight:600; color:var(--text-secondary,#6b7280); display:flex; align-items:center; gap:6px;">
                    <i class="fas fa-grip-vertical" style="color:var(--gray-400,#9ca3af);"></i>
                    Плейсхолдер #${index + 1}
                </span>
                <button type="button" class="remove-placeholder-btn" style="
                    display:inline-flex; align-items:center; gap:6px;
                    padding:0 14px; height:34px; border-radius:8px;
                    border:2px solid #fca5a5; background:white;
                    color:#dc2626; font-size:13px; font-weight:500;
                    cursor:pointer; transition:all 0.2s;">
                    <i class="fas fa-trash-alt"></i> Удалить
                </button>
            </div>

            <div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem;">
                <div style="display:flex; flex-direction:column; gap:6px;">
                    <label style="font-size:14px; font-weight:500; color:var(--text-primary,#111827); display:flex; align-items:center; gap:6px;">
                        <i class="fas fa-code" style="color:var(--primary-500,#6366f1);"></i>
                        Имя переменной <span style="color:#ef4444;">*</span>
                    </label>
                    <input type="text" class="placeholder-name"
                           value="${this._esc(placeholder.name)}"
                           placeholder="company_name"
                           pattern="[a-zA-Z_][a-zA-Z0-9_]*"
                           title="Только латинские буквы, цифры и подчёркивание"
                           style="height:44px; padding:0 14px; border:2px solid var(--border-light,#e5e7eb);
                                  border-radius:10px; font-size:14px; background:white;
                                  color:var(--text-primary,#111827); transition:all 0.2s; font-family:monospace;">
                    <span style="font-size:12px; color:var(--text-tertiary,#9ca3af);">
                        Используется в шаблоне: <code>{{${placeholder.name || 'имя'}}}</code>
                    </span>
                </div>

                <div style="display:flex; flex-direction:column; gap:6px;">
                    <label style="font-size:14px; font-weight:500; color:var(--text-primary,#111827); display:flex; align-items:center; gap:6px;">
                        <i class="fas fa-font" style="color:var(--primary-500,#6366f1);"></i>
                        Название поля <span style="color:#ef4444;">*</span>
                    </label>
                    <input type="text" class="placeholder-label"
                           value="${this._esc(placeholder.label)}"
                           placeholder="Название компании"
                           style="height:44px; padding:0 14px; border:2px solid var(--border-light,#e5e7eb);
                                  border-radius:10px; font-size:14px; background:white;
                                  color:var(--text-primary,#111827); transition:all 0.2s;">
                    <span style="font-size:12px; color:var(--text-tertiary,#9ca3af);">Отображается в форме создания документа</span>
                </div>

                <div style="display:flex; flex-direction:column; gap:6px;">
                    <label style="font-size:14px; font-weight:500; color:var(--text-primary,#111827); display:flex; align-items:center; gap:6px;">
                        <i class="fas fa-list" style="color:var(--primary-500,#6366f1);"></i>
                        Тип поля
                    </label>
                    <select class="placeholder-type"
                            style="height:44px; padding:0 14px; border:2px solid var(--border-light,#e5e7eb);
                                   border-radius:10px; font-size:14px; background:white;
                                   color:var(--text-primary,#111827); transition:all 0.2s; appearance:auto;">
                        <option value="text"     ${placeholder.type === 'text'     ? 'selected' : ''}>Текст (одна строка)</option>
                        <option value="textarea" ${placeholder.type === 'textarea' ? 'selected' : ''}>Текст (многострочный)</option>
                        <option value="number"   ${placeholder.type === 'number'   ? 'selected' : ''}>Число</option>
                        <option value="date"     ${placeholder.type === 'date'     ? 'selected' : ''}>Дата</option>
                        <option value="email"    ${placeholder.type === 'email'    ? 'selected' : ''}>Email</option>
                        <option value="tel"      ${placeholder.type === 'tel'      ? 'selected' : ''}>Телефон</option>
                    </select>
                </div>

                <div style="display:flex; flex-direction:column; gap:6px;">
                    <label style="font-size:14px; font-weight:500; color:var(--text-primary,#111827); display:flex; align-items:center; gap:6px;">
                        <i class="fas fa-toggle-on" style="color:var(--primary-500,#6366f1);"></i>
                        Опции
                    </label>
                    <label style="display:flex; align-items:center; gap:10px; height:44px; padding:0 14px;
                                  border:2px solid var(--border-light,#e5e7eb); border-radius:10px;
                                  background:var(--gray-50,#f9fafb); cursor:pointer; transition:all 0.2s; font-size:14px;
                                  color:var(--text-primary,#111827); font-weight:500;">
                        <input type="checkbox" class="placeholder-required"
                               id="required-${index}"
                               ${placeholder.required ? 'checked' : ''}
                               style="width:18px; height:18px; cursor:pointer; accent-color:var(--primary-500,#6366f1);">
                        Обязательное поле
                    </label>
                </div>
            </div>
        `;

        // фокус — подсветка рамки
        div.querySelectorAll('input[type="text"], input[type="text"], select').forEach(el => {
            el.addEventListener('focus', () => {
                el.style.borderColor = 'var(--primary-500,#6366f1)';
                el.style.boxShadow = '0 0 0 4px var(--primary-100,#e0e7ff)';
                el.style.outline = 'none';
            });
            el.addEventListener('blur', () => {
                el.style.borderColor = 'var(--border-light,#e5e7eb)';
                el.style.boxShadow = '';
            });
        });

        // hover кнопки удалить
        const removeBtn = div.querySelector('.remove-placeholder-btn');
        removeBtn.addEventListener('mouseenter', () => {
            removeBtn.style.background = '#fee2e2';
            removeBtn.style.borderColor = '#dc2626';
        });
        removeBtn.addEventListener('mouseleave', () => {
            removeBtn.style.background = 'white';
            removeBtn.style.borderColor = '#fca5a5';
        });
        removeBtn.addEventListener('click', () => this.removePlaceholder(index));

        // обновление подсказки {{имя}} при вводе
        const nameInput = div.querySelector('.placeholder-name');
        const hint = div.querySelector('.placeholder-name + span code, span code');
        nameInput.addEventListener('input', () => {
            const hint = nameInput.closest('div').querySelector('span code');
            if (hint) hint.textContent = `{{${nameInput.value || 'имя'}}}`;
        });

        return div;
    }

    // Экранирование для HTML-атрибутов
    _esc(str) {
        return (str || '').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('placeholders-container')) {
        window.placeholderManager = new PlaceholderManager();
    }
});
