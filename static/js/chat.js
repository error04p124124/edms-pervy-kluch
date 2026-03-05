/**
 * Виджет чата для ЭДО "Первый ключ"
 */

class ChatWidget {
    constructor() {
        this.isOpen = false;
        this.currentRecipient = null;
        this.messageCheckInterval = null;
        this.init();
    }

    init() {
        this.createWidget();
        this.attachEventListeners();
        this.loadUsers();
        this.startMessageCheck();
    }

    createWidget() {
        console.log('Создание виджета чата...');
        const chatHTML = `
            <!-- Chat Button -->
            <div id="chatButton" class="chat-button">
                <i class="fas fa-plus"></i>
                <span class="chat-badge" id="chatBadge" style="display: none;">0</span>
            </div>

            <!-- Chat Widget -->
            <div id="chatWidget" class="chat-widget">
                <!-- Chat Header -->
                <div class="chat-header">
                    <div class="d-flex align-items-center justify-content-between">
                        <div>
                            <h6 class="mb-0"><i class="fas fa-comments me-2"></i>Чат</h6>
                        </div>
                        <div class="d-flex gap-2">
                            <button class="btn btn-sm" id="chatClose" title="Закрыть">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Chat Body -->
                <div class="chat-body">
                    <!-- Users List -->
                    <div id="chatUsersList" class="chat-users-list">
                        <div class="p-3">
                            <h6 class="mb-3">Выберите пользователя:</h6>
                            <div id="usersList"></div>
                        </div>
                    </div>

                    <!-- Chat Conversation -->
                    <div id="chatConversation" class="chat-conversation" style="display: none;">
                        <div class="chat-conversation-header">
                            <button class="btn btn-sm" id="backToUsers">
                                <i class="fas fa-arrow-left"></i>
                            </button>
                            <span id="chatRecipientName" class="ms-2 fw-bold"></span>
                        </div>
                        <div id="chatMessages" class="chat-messages"></div>
                        <div class="chat-input">
                            <div class="input-group">
                                <input type="text" class="form-control" id="chatMessageInput" placeholder="Введите сообщение...">
                                <button class="btn btn-gradient" id="chatSendBtn">
                                    <i class="fas fa-paper-plane"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', chatHTML);
        console.log('Виджет чата создан');
        console.log('usersList элемент:', document.getElementById('usersList'));
    }

    attachEventListeners() {
        console.log('Привязка обработчиков событий...');
        // Открыть/закрыть чат
        document.getElementById('chatButton').addEventListener('click', () => this.toggleChat());
        document.getElementById('chatClose').addEventListener('click', () => this.closeChat());

        // Назад к списку пользователей
        document.getElementById('backToUsers').addEventListener('click', () => this.showUsersList());

        // Отправка сообщения
        document.getElementById('chatSendBtn').addEventListener('click', () => this.sendMessage());
        document.getElementById('chatMessageInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }

    toggleChat() {
        this.isOpen = !this.isOpen;
        const widget = document.getElementById('chatWidget');
        const button = document.getElementById('chatButton');

        if (this.isOpen) {
            widget.classList.add('active');
            button.innerHTML = '<i class="fas fa-times"></i>';
            this.loadUsers();
        } else {
            widget.classList.remove('active');
            button.innerHTML = '<i class="fas fa-plus"></i><span class="chat-badge" id="chatBadge" style="display: none;">0</span>';
        }
    }

    closeChat() {
        this.isOpen = false;
        document.getElementById('chatWidget').classList.remove('active');
        document.getElementById('chatButton').innerHTML = '<i class="fas fa-plus"></i><span class="chat-badge" id="chatBadge" style="display: none;">0</span>';
    }

    async loadUsers() {
        try {
            console.log('Загрузка пользователей...');
            const response = await fetch('/api/chat/users/');
            console.log('Response status:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Получены пользователи:', data);
            this.renderUsers(data.users);
        } catch (error) {
            console.error('Ошибка загрузки пользователей:', error);
            const usersList = document.getElementById('usersList');
            if (usersList) {
                usersList.innerHTML = '<p class="text-danger text-center small">Ошибка загрузки пользователей</p>';
            }
        }
    }

    renderUsers(users) {
        const usersList = document.getElementById('usersList');
        
        if (!usersList) {
            console.error('Элемент usersList не найден!');
            return;
        }
        
        console.log('Отрисовка пользователей:', users);
        
        if (!users || users.length === 0) {
            usersList.innerHTML = '<p class="text-muted text-center">Нет доступных пользователей</p>';
            return;
        }

        usersList.innerHTML = users.map(user => {
            console.log(`User ${user.full_name}: avatar_url = ${user.avatar_url}`);
            return `
            <div class="chat-user-item" data-user-id="${user.id}" data-user-name="${user.full_name}">
                <div class="d-flex align-items-center">
                    ${user.avatar_url ? 
                        `<div class="chat-user-avatar" style="background: none; padding: 0;">
                            <img src="${user.avatar_url}" alt="${user.full_name}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; display: block;">
                        </div>` : 
                        `<div class="chat-user-avatar">
                            <i class="fas fa-user"></i>
                        </div>`
                    }
                    <div class="flex-grow-1 ms-2">
                        <div class="fw-semibold">${user.full_name}</div>
                        <small class="text-muted">${user.role}</small>
                    </div>
                    ${user.unread_count > 0 ? `<span class="badge bg-danger rounded-pill">${user.unread_count}</span>` : ''}
                </div>
            </div>
        `;
        }).join('');

        // Attach click handlers
        document.querySelectorAll('.chat-user-item').forEach(item => {
            item.addEventListener('click', () => {
                const userId = item.dataset.userId;
                const userName = item.dataset.userName;
                this.openConversation(userId, userName);
            });
        });
    }

    showUsersList() {
        document.getElementById('chatUsersList').style.display = 'block';
        document.getElementById('chatConversation').style.display = 'none';
        this.currentRecipient = null;
    }

    async openConversation(userId, userName) {
        this.currentRecipient = userId;
        document.getElementById('chatRecipientName').textContent = userName;
        document.getElementById('chatUsersList').style.display = 'none';
        document.getElementById('chatConversation').style.display = 'flex';
        
        await this.loadMessages(userId);
    }

    async loadMessages(userId) {
        try {
            const response = await fetch(`/api/chat/messages/${userId}/`);
            const data = await response.json();
            this.renderMessages(data.messages);
        } catch (error) {
            console.error('Ошибка загрузки сообщений:', error);
        }
    }

    renderMessages(messages) {
        const messagesContainer = document.getElementById('chatMessages');
        
        if (messages.length === 0) {
            messagesContainer.innerHTML = '<p class="text-muted text-center p-3">Нет сообщений</p>';
            return;
        }

        messagesContainer.innerHTML = messages.map(msg => `
            <div class="chat-message ${msg.is_own ? 'own' : 'other'}">
                <div class="chat-message-content">
                    ${msg.message}
                </div>
                <div class="chat-message-time">${msg.created_at}</div>
            </div>
        `).join('');

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    async sendMessage() {
        const input = document.getElementById('chatMessageInput');
        const message = input.value.trim();

        if (!message || !this.currentRecipient) return;

        try {
            const response = await fetch('/api/chat/send/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    recipient_id: this.currentRecipient,
                    message: message
                })
            });

            const data = await response.json();

            if (data.success) {
                input.value = '';
                await this.loadMessages(this.currentRecipient);
            } else {
                alert('Ошибка отправки сообщения: ' + data.error);
            }
        } catch (error) {
            console.error('Ошибка отправки:', error);
            alert('Ошибка отправки сообщения');
        }
    }

    async checkUnreadMessages() {
        try {
            const response = await fetch('/api/chat/unread/');
            
            if (!response.ok) {
                if (response.status === 404) {
                    console.warn('Chat API endpoint not found');
                    return;
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            const badge = document.getElementById('chatBadge');
            
            if (badge && data.unread_count > 0) {
                badge.textContent = data.unread_count;
                badge.style.display = 'block';
            } else if (badge) {
                badge.style.display = 'none';
            }
        } catch (error) {
            console.error('Ошибка проверки сообщений:', error);
        }
    }

    startMessageCheck() {
        // Первая проверка через небольшую задержку
        setTimeout(() => {
            this.checkUnreadMessages();
        }, 1000);
        this.messageCheckInterval = setInterval(() => {
            this.checkUnreadMessages();
            
            // Обновляем текущий разговор, если открыт
            if (this.isOpen && this.currentRecipient) {
                this.loadMessages(this.currentRecipient);
            }
        }, 5000); // Проверка каждые 5 секунд
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.querySelector('meta[name="csrf-token"]')?.content ||
               document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1] || '';
    }
}

// Initialize chat when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM загружен');
    console.log('Authenticated:', document.body.dataset.authenticated);
    
    if (document.body.dataset.authenticated === 'true') {
        console.log('Инициализация чата...');
        new ChatWidget();
    } else {
        console.log('Пользователь не аутентифицирован, чат не загружается');
    }
});
