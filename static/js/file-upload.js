/**
 * Drag & Drop File Upload System
 * Система загрузки файлов с Drag & Drop
 */

class FileUploadManager {
    constructor(documentId, csrfToken, uploadUrl) {
        this.documentId = documentId;
        this.csrfToken = csrfToken;
        this.uploadUrl = uploadUrl || `/documents/${documentId}/attachments/upload/`;
        this.maxFileSize = 50 * 1024 * 1024; // 50MB
        this.allowedTypes = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'image/jpeg',
            'image/png',
            'image/gif',
            'application/zip',
            'application/x-rar-compressed'
        ];
        
        this.init();
    }
    
    init() {
        this.setupDropZone();
        this.setupFileInput();
        this.loadAttachments();
    }
    
    setupDropZone() {
        const dropZone = document.getElementById('dropZone');
        if (!dropZone) return;
        
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });
        
        // Highlight drop zone when item is dragged over
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.add('drag-active');
            }, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('drag-active');
            }, false);
        });
        
        // Handle dropped files
        dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            this.handleFiles(files);
        }, false);
        
        // Click to select files
        dropZone.addEventListener('click', () => {
            document.getElementById('fileInput')?.click();
        });
    }
    
    setupFileInput() {
        const fileInput = document.getElementById('fileInput');
        if (!fileInput) return;
        
        fileInput.addEventListener('change', (e) => {
            this.handleFiles(e.target.files);
        });
    }
    
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    handleFiles(files) {
        [...files].forEach(file => this.uploadFile(file));
    }
    
    async uploadFile(file) {
        // Validate file
        const validation = this.validateFile(file);
        if (!validation.valid) {
            this.showToast(validation.error, 'error');
            return;
        }
        
        // Create progress item in UI
        const progressId = this.createProgressItem(file);
        
        // Prepare form data
        const formData = new FormData();
        formData.append('file', file);
        formData.append('description', ''); // Can be enhanced with description input
        
        try {
            const xhr = new XMLHttpRequest();
            
            // Update progress
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    this.updateProgress(progressId, percentComplete);
                }
            });
            
            // Handle completion
            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    const response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        this.completeUpload(progressId, response.attachment);
                        this.showToast('Файл успешно загружен', 'success');
                        this.loadAttachments();
                    } else {
                        this.failUpload(progressId, response.error || 'Ошибка загрузки');
                    }
                } else {
                    this.failUpload(progressId, 'Ошибка сервера');
                }
            });
            
            // Handle errors
            xhr.addEventListener('error', () => {
                this.failUpload(progressId, 'Ошибка сети');
            });
            
            // Send request
            xhr.open('POST', this.uploadUrl);
            xhr.setRequestHeader('X-CSRFToken', this.csrfToken);
            xhr.send(formData);
            
        } catch (error) {
            console.error('Upload error:', error);
            this.failUpload(progressId, 'Ошибка загрузки');
        }
    }
    
    validateFile(file) {
        // Check file size
        if (file.size > this.maxFileSize) {
            return {
                valid: false,
                error: `Файл слишком большой. Максимум ${this.maxFileSize / 1024 / 1024}MB`
            };
        }
        
        // Check file type
        if (!this.allowedTypes.includes(file.type) && file.type !== '') {
            return {
                valid: false,
                error: 'Неподдерживаемый тип файла'
            };
        }
        
        return { valid: true };
    }
    
    createProgressItem(file) {
        const progressId = 'upload_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        const container = document.getElementById('uploadProgressContainer');
        if (!container) return progressId;
        
        const item = document.createElement('div');
        item.className = 'upload-progress-item';
        item.id = progressId;
        item.innerHTML = `
            <div class="upload-progress-info">
                <div class="upload-progress-icon">
                    <i class="fas fa-file"></i>
                </div>
                <div class="upload-progress-details">
                    <div class="upload-progress-name">${this.escapeHtml(file.name)}</div>
                    <div class="upload-progress-size">${this.formatFileSize(file.size)}</div>
                </div>
            </div>
            <div class="upload-progress-bar-container">
                <div class="upload-progress-bar" style="width: 0%"></div>
            </div>
            <div class="upload-progress-status">0%</div>
        `;
        
        container.appendChild(item);
        return progressId;
    }
    
    updateProgress(progressId, percent) {
        const item = document.getElementById(progressId);
        if (!item) return;
        
        const bar = item.querySelector('.upload-progress-bar');
        const status = item.querySelector('.upload-progress-status');
        
        if (bar) bar.style.width = percent + '%';
        if (status) status.textContent = Math.round(percent) + '%';
    }
    
    completeUpload(progressId, attachment) {
        const item = document.getElementById(progressId);
        if (!item) return;
        
        item.classList.add('upload-complete');
        const status = item.querySelector('.upload-progress-status');
        if (status) {
            status.innerHTML = '<i class="fas fa-check-circle"></i>';
        }
        
        // Remove after 3 seconds
        setTimeout(() => {
            item.style.transition = 'opacity 0.3s';
            item.style.opacity = '0';
            setTimeout(() => item.remove(), 300);
        }, 3000);
    }
    
    failUpload(progressId, errorMessage) {
        const item = document.getElementById(progressId);
        if (!item) return;
        
        item.classList.add('upload-error');
        const status = item.querySelector('.upload-progress-status');
        if (status) {
            status.innerHTML = '<i class="fas fa-exclamation-circle"></i>';
            status.title = errorMessage;
        }
        
        this.showToast(errorMessage, 'error');
        
        // Remove after 5 seconds
        setTimeout(() => {
            item.style.transition = 'opacity 0.3s';
            item.style.opacity = '0';
            setTimeout(() => item.remove(), 300);
        }, 5000);
    }
    
    async loadAttachments() {
        const container = document.getElementById('attachmentsList');
        if (!container) return;
        
        try {
            const response = await fetch(`/documents/${this.documentId}/attachments/`);
            if (!response.ok) return;
            
            const data = await response.json();
            const attachments = data.attachments || [];
            
            if (attachments.length === 0) {
                container.innerHTML = `
                    <div class="attachments-empty">
                        <i class="fas fa-paperclip"></i>
                        <p>Нет вложений</p>
                    </div>
                `;
                return;
            }
            
            container.innerHTML = attachments.map(att => this.renderAttachment(att)).join('');
        } catch (error) {
            console.error('Error loading attachments:', error);
        }
    }
    
    renderAttachment(attachment) {
        const icon = this.getFileIcon(attachment.file_type);
        
        return `
            <div class="attachment-item">
                <div class="attachment-icon">
                    <i class="fas fa-${icon}"></i>
                </div>
                <div class="attachment-info">
                    <div class="attachment-name">${this.escapeHtml(attachment.original_filename)}</div>
                    <div class="attachment-meta">
                        ${this.formatFileSize(attachment.file_size)} • 
                        ${this.formatDate(attachment.uploaded_at)} • 
                        ${this.escapeHtml(attachment.uploaded_by_name)}
                    </div>
                </div>
                <div class="attachment-actions">
                    <a href="${attachment.file_url}" download class="attachment-action-btn" title="Скачать">
                        <i class="fas fa-download"></i>
                    </a>
                    ${attachment.can_delete ? `
                    <button onclick="fileUploadManager.deleteAttachment(${attachment.id})" class="attachment-action-btn attachment-action-delete" title="Удалить">
                        <i class="fas fa-trash"></i>
                    </button>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    async deleteAttachment(attachmentId) {
        if (!confirm('Удалить вложение?')) return;
        
        try {
            const response = await fetch(`/attachments/${attachmentId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast('Вложение удалено', 'success');
                this.loadAttachments();
            } else {
                this.showToast(data.error || 'Ошибка при удалении', 'error');
            }
        } catch (error) {
            console.error('Error deleting attachment:', error);
            this.showToast('Ошибка при удалении вложения', 'error');
        }
    }
    
    getFileIcon(mimeType) {
        if (!mimeType) return 'file';
        
        if (mimeType.includes('pdf')) return 'file-pdf';
        if (mimeType.includes('word')) return 'file-word';
        if (mimeType.includes('excel') || mimeType.includes('spreadsheet')) return 'file-excel';
        if (mimeType.includes('image')) return 'file-image';
        if (mimeType.includes('zip') || mimeType.includes('rar')) return 'file-archive';
        
        return 'file';
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('ru-RU');
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    showToast(message, type) {
        if (typeof toastManager !== 'undefined') {
            toastManager.show(message, type);
        } else {
            alert(message);
        }
    }
}

// Auto-initialize on document pages
document.addEventListener('DOMContentLoaded', function() {
    const uploadSection = document.getElementById('attachmentsSection');
    if (uploadSection) {
        const documentId = uploadSection.dataset.documentId;
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (documentId && csrfToken) {
            window.fileUploadManager = new FileUploadManager(documentId, csrfToken);
        }
    }
});
