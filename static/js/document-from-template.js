/**
 * Динамическое отображение плейсхолдеров при создании документа из шаблона
 */

class DocumentFromTemplateManager {
    constructor() {
        this.templateSelect = document.getElementById('id_template');
        this.contentField = document.getElementById('id_content');
        this.contentWrapper = document.querySelector('.content-field-wrapper');
        this.placeholdersContainer = document.getElementById('template-placeholders-container');
        
        if (!this.templateSelect) return;
        
        this.init();
    }
    
    init() {
        // Обработчик изменения шаблона
        this.templateSelect.addEventListener('change', () => {
            this.onTemplateChange();
        });
        
        // Загрузить плейсхолдеры при загрузке страницы если шаблон уже выбран
        if (this.templateSelect.value) {
            this.onTemplateChange();
        }
        
        // Обработчик отправки формы
        const form = this.templateSelect.closest('form');
        if (form) {
            form.addEventListener('submit', (e) => {
                if (this.placeholdersContainer && this.placeholdersContainer.style.display !== 'none') {
                    // Если показаны плейсхолдеры, собрать их значения
                    this.collectPlaceholderValues();
                }
            });
        }
    }
    
    async onTemplateChange() {
        const templateId = this.templateSelect.value;
        
        if (!templateId) {
            this.showContentField();
            return;
        }
        
        try {
            // Загрузить данные о шаблоне
            const response = await fetch(`/api/templates/${templateId}/placeholders/`);
            const data = await response.json();
            
            if (data.placeholders && data.placeholders.length > 0) {
                // Показать плейсхолдеры, скрыть обычное поле
                this.showPlaceholders(data.placeholders);
            } else {
                // Показать обычное поле содержимого
                this.showContentField();
            }
        } catch (error) {
            console.error('Error loading template placeholders:', error);
            this.showContentField();
        }
    }
    
    showPlaceholders(placeholders) {
        // Скрыть обычное поле содержимого
        if (this.contentWrapper) {
            this.contentWrapper.style.display = 'none';
        }
        
        // Показать контейнер плейсхолдеров
        if (this.placeholdersContainer) {
            this.placeholdersContainer.style.display = 'block';
            this.renderPlaceholders(placeholders);
        }
    }
    
    showContentField() {
        // Показать обычное поле содержимого
        if (this.contentWrapper) {
            this.contentWrapper.style.display = 'block';
        }
        
        // Скрыть контейнер плейсхолдеров
        if (this.placeholdersContainer) {
            this.placeholdersContainer.style.display = 'none';
            this.placeholdersContainer.innerHTML = '';
        }
    }
    
    renderPlaceholders(placeholders) {
        if (!this.placeholdersContainer) return;

        const inputStyle = `
            width:100%; height:44px; padding:0 14px;
            border:2px solid var(--border-light,#e5e7eb);
            border-radius:10px; font-size:14px; background:white;
            color:var(--text-primary,#111827); transition:all 0.2s;
            box-sizing:border-box;
        `;
        const textareaStyle = `
            width:100%; min-height:100px; padding:10px 14px;
            border:2px solid var(--border-light,#e5e7eb);
            border-radius:10px; font-size:14px; background:white;
            color:var(--text-primary,#111827); transition:all 0.2s;
            resize:vertical; font-family:inherit; box-sizing:border-box;
        `;
        const labelStyle = `
            font-size:14px; font-weight:500;
            color:var(--text-primary,#111827);
            display:flex; align-items:center; gap:6px; margin-bottom:6px;
        `;

        let html = `
            <div style="padding:12px 16px; border-radius:10px; background:var(--primary-50,#eef2ff);
                        border:1px solid var(--primary-200,#c7d2fe); color:var(--primary-700,#4338ca);
                        font-size:14px; display:flex; align-items:center; gap:10px; margin-bottom:1.25rem;">
                <i class="fas fa-info-circle"></i>
                Заполните поля ниже — данные будут подставлены в шаблон документа.
            </div>
        `;

        placeholders.forEach((ph) => {
            const fid = `placeholder_${ph.name}`;
            const req = ph.required ? 'required' : '';
            const star = ph.required ? '<span style="color:#ef4444;">*</span>' : '';

            html += `<div style="display:flex;flex-direction:column;margin-bottom:1.25rem;">
                <label for="${fid}" style="${labelStyle}">
                    <i class="fas fa-pen" style="color:var(--primary-500,#6366f1);font-size:12px;"></i>
                    ${ph.label} ${star}
                </label>`;

            if (ph.type === 'textarea') {
                html += `<textarea id="${fid}" name="placeholder_${ph.name}"
                    class="template-placeholder-input"
                    data-placeholder-name="${ph.name}"
                    style="${textareaStyle}" rows="4" ${req}></textarea>`;
            } else {
                const typeMap = {number:'number', date:'date', email:'email', tel:'tel'};
                const t = typeMap[ph.type] || 'text';
                const ph_placeholder = ph.type === 'tel' ? 'placeholder="+7 (___) ___-__-__"'
                                    : ph.type === 'email' ? 'placeholder="example@email.com"' : '';
                html += `<input type="${t}" id="${fid}" name="placeholder_${ph.name}"
                    class="template-placeholder-input"
                    data-placeholder-name="${ph.name}"
                    style="${inputStyle}" ${ph_placeholder} ${req}>`;
            }

            html += `</div>`;
        });

        this.placeholdersContainer.innerHTML = html;

        // фокус-подсветка
        this.placeholdersContainer.querySelectorAll('.template-placeholder-input').forEach(el => {
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
    }
    
    collectPlaceholderValues() {
        // Собрать значения всех плейсхолдеров и сохранить в скрытое поле
        const inputs = this.placeholdersContainer.querySelectorAll('.template-placeholder-input');
        const values = {};
        
        inputs.forEach(input => {
            const name = input.dataset.placeholderName;
            values[name] = input.value;
        });
        
        // Создать или обновить скрытое поле с данными
        let hiddenInput = document.getElementById('placeholder_values');
        if (!hiddenInput) {
            hiddenInput = document.createElement('input');
            hiddenInput.type = 'hidden';
            hiddenInput.id = 'placeholder_values';
            hiddenInput.name = 'placeholder_values';
            this.templateSelect.closest('form').appendChild(hiddenInput);
        }
        
        hiddenInput.value = JSON.stringify(values);
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('id_template')) {
        window.documentFromTemplateManager = new DocumentFromTemplateManager();
    }
});
