/**
 * Comments System with AJAX
 * Система комментариев с AJAX загрузкой
 */

class CommentsManager {
    constructor(documentId, csrfToken) {
        this.documentId = documentId;
        this.csrfToken = csrfToken;
        this.comments = [];
        this.editingCommentId = null;
        this.replyToCommentId = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadComments();
    }
    
    setupEventListeners() {
        // Submit comment form
        const form = document.getElementById('commentForm');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitComment();
            });
        }
        
        // Comment textarea auto-resize
        const textarea = document.getElementById('commentText');
        if (textarea) {
            textarea.addEventListener('input', () => {
                textarea.style.height = 'auto';
                textarea.style.height = textarea.scrollHeight + 'px';
            });
            
            // @ mention autocomplete (simplified)
            textarea.addEventListener('input', (e) => {
                this.handleMentionAutocomplete(e);
            });
        }
        
        // Cancel reply/edit
        const cancelBtn = document.getElementById('cancelCommentBtn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                this.cancelEdit();
            });
        }
    }
    
    async loadComments() {
        const container = document.getElementById('commentsContainer');
        if (!container) return;
        
        container.innerHTML = '<div class="comments-loading"><i class="fas fa-spinner fa-spin"></i> Загрузка комментариев...</div>';
        
        try {
            const response = await fetch(`/documents/${this.documentId}/comments/`);
            const data = await response.json();
            
            this.comments = data.comments || [];
            this.renderComments();
        } catch (error) {
            console.error('Error loading comments:', error);
            container.innerHTML = '<div class="comments-error">Ошибка загрузки комментариев</div>';
        }
    }
    
    renderComments() {
        const container = document.getElementById('commentsContainer');
        if (!container) return;
        
        if (this.comments.length === 0) {
            container.innerHTML = `
                <div class="comments-empty">
                    <i class="fas fa-comments"></i>
                    <p>Пока нет комментариев. Будьте первым!</p>
                </div>
            `;
            return;
        }
        
        // Render root comments (no parent)
        const rootComments = this.comments.filter(c => !c.parent_id);
        container.innerHTML = rootComments.map(comment => this.renderComment(comment)).join('');
    }
    
    renderComment(comment, depth = 0) {
        const replies = this.comments.filter(c => c.parent_id === comment.id);
        const isEdited = comment.is_edited ? '<span class="comment-edited">(изменено)</span>' : '';
        const canModify = comment.can_edit || comment.can_delete;
        
        let html = `
            <div class="comment-item ${depth > 0 ? 'comment-reply' : ''}" data-comment-id="${comment.id}" style="margin-left: ${depth * 2}rem;">
                <div class="comment-avatar">
                    ${this.getInitials(comment.author_name)}
                </div>
                <div class="comment-content">
                    <div class="comment-header">
                        <div class="comment-author">
                            <strong>${this.escapeHtml(comment.author_name)}</strong>
                            <span class="comment-time">${this.formatTime(comment.created_at)}</span>
                            ${isEdited}
                        </div>
                        ${canModify ? `
                        <div class="comment-actions">
                            ${comment.can_edit ? `<button onclick="commentsManager.startEdit(${comment.id})" class="comment-action-btn"><i class="fas fa-edit"></i></button>` : ''}
                            ${comment.can_delete ? `<button onclick="commentsManager.deleteComment(${comment.id})" class="comment-action-btn comment-action-delete"><i class="fas fa-trash"></i></button>` : ''}
                        </div>
                        ` : ''}
                    </div>
                    <div class="comment-text" id="commentText${comment.id}">
                        ${this.formatCommentText(comment.text)}
                    </div>
                    ${depth < 3 ? `
                    <button onclick="commentsManager.startReply(${comment.id}, '${this.escapeHtml(comment.author_name)}')" class="comment-reply-btn">
                        <i class="fas fa-reply"></i> Ответить
                    </button>
                    ` : ''}
                </div>
            </div>
        `;
        
        // Add replies recursively
        if (replies.length > 0 && depth < 3) {
            html += replies.map(reply => this.renderComment(reply, depth + 1)).join('');
        }
        
        return html;
    }
    
    formatCommentText(text) {
        // Escape HTML
        text = this.escapeHtml(text);
        
        // Convert line breaks
        text = text.replace(/\n/g, '<br>');
        
        // Highlight mentions
        text = text.replace(/@(\w+)/g, '<span class="comment-mention">@$1</span>');
        
        return text;
    }
    
    async submitComment() {
        const textarea = document.getElementById('commentText');
        const text = textarea.value.trim();
        
        if (!text) {
            this.showToast('Введите текст комментария', 'warning');
            return;
        }
        
        const submitBtn = document.querySelector('#commentForm button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Отправка...';
        
        try {
            let url, method;
            const formData = new FormData();
            formData.append('text', text);
            
            if (this.editingCommentId) {
                // Edit existing comment
                url = `/comments/${this.editingCommentId}/edit/`;
                method = 'POST';
            } else {
                // Add new comment
                url = `/documents/${this.documentId}/comments/add/`;
                method = 'POST';
                if (this.replyToCommentId) {
                    formData.append('parent_id', this.replyToCommentId);
                }
            }
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'X-CSRFToken': this.csrfToken
                },
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast(this.editingCommentId ? 'Комментарий обновлен' : 'Комментарий добавлен', 'success');
                textarea.value = '';
                textarea.style.height = 'auto';
                this.cancelEdit();
                this.loadComments();
            } else {
                this.showToast(data.error || 'Ошибка при сохранении комментария', 'error');
            }
        } catch (error) {
            console.error('Error submitting comment:', error);
            this.showToast('Ошибка при отправке комментария', 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    }
    
    startEdit(commentId) {
        const comment = this.comments.find(c => c.id === commentId);
        if (!comment) return;
        
        this.editingCommentId = commentId;
        const textarea = document.getElementById('commentText');
        const submitBtn = document.querySelector('#commentForm button[type="submit"]');
        const cancelBtn = document.getElementById('cancelCommentBtn');
        const formTitle = document.getElementById('commentFormTitle');
        
        textarea.value = comment.text;
        textarea.focus();
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
        
        submitBtn.innerHTML = '<i class="fas fa-save"></i> Сохранить';
        cancelBtn.style.display = 'inline-flex';
        if (formTitle) formTitle.textContent = 'Редактирование комментария';
        
        // Scroll to form
        document.getElementById('commentForm').scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    
    startReply(commentId, authorName) {
        this.replyToCommentId = commentId;
        const textarea = document.getElementById('commentText');
        const submitBtn = document.querySelector('#commentForm button[type="submit"]');
        const cancelBtn = document.getElementById('cancelCommentBtn');
        const formTitle = document.getElementById('commentFormTitle');
        
        textarea.value = `@${authorName} `;
        textarea.focus();
        
        submitBtn.innerHTML = '<i class="fas fa-reply"></i> Ответить';
        cancelBtn.style.display = 'inline-flex';
        if (formTitle) formTitle.textContent = `Ответ на комментарий ${authorName}`;
        
        // Scroll to form
        document.getElementById('commentForm').scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    
    cancelEdit() {
        this.editingCommentId = null;
        this.replyToCommentId = null;
        
        const textarea = document.getElementById('commentText');
        const submitBtn = document.querySelector('#commentForm button[type="submit"]');
        const cancelBtn = document.getElementById('cancelCommentBtn');
        const formTitle = document.getElementById('commentFormTitle');
        
        textarea.value = '';
        textarea.style.height = 'auto';
        submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Отправить';
        cancelBtn.style.display = 'none';
        if (formTitle) formTitle.textContent = 'Добавить комментарий';
    }
    
    async deleteComment(commentId) {
        if (!confirm('Удалить комментарий?')) return;
        
        try {
            const response = await fetch(`/comments/${commentId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast('Комментарий удален', 'success');
                this.loadComments();
            } else {
                this.showToast(data.error || 'Ошибка при удалении', 'error');
            }
        } catch (error) {
            console.error('Error deleting comment:', error);
            this.showToast('Ошибка при удалении комментария', 'error');
        }
    }
    
    handleMentionAutocomplete(e) {
        // Simplified mention autocomplete
        // In production, implement proper user search
        const text = e.target.value;
        const cursorPos = e.target.selectionStart;
        const textBeforeCursor = text.substring(0, cursorPos);
        const lastAt = textBeforeCursor.lastIndexOf('@');
        
        if (lastAt === -1) return;
        
        const searchText = textBeforeCursor.substring(lastAt + 1);
        
        // Here you would fetch users matching searchText
        // and show autocomplete dropdown
        console.log('Mention search:', searchText);
    }
    
    getInitials(name) {
        const parts = name.split(' ');
        if (parts.length >= 2) {
            return parts[0][0] + parts[1][0];
        }
        return name[0] + (name[1] || '');
    }
    
    formatTime(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);
        
        if (days > 7) {
            return date.toLocaleDateString('ru-RU');
        } else if (days > 0) {
            return `${days} ${this.pluralize(days, 'день', 'дня', 'дней')} назад`;
        } else if (hours > 0) {
            return `${hours} ${this.pluralize(hours, 'час', 'часа', 'часов')} назад`;
        } else if (minutes > 0) {
            return `${minutes} ${this.pluralize(minutes, 'минуту', 'минуты', 'минут')} назад`;
        } else {
            return 'только что';
        }
    }
    
    pluralize(n, one, two, five) {
        n = Math.abs(n) % 100;
        const n1 = n % 10;
        if (n > 10 && n < 20) return five;
        if (n1 > 1 && n1 < 5) return two;
        if (n1 === 1) return one;
        return five;
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
    const commentsSection = document.getElementById('commentsSection');
    if (commentsSection) {
        const documentId = commentsSection.dataset.documentId;
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (documentId && csrfToken) {
            window.commentsManager = new CommentsManager(documentId, csrfToken);
        }
    }
});
