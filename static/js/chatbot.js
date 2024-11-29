// Chatbot implementation
class FitTabChatbot {
    constructor() {
        this.isOpen = false;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        const container = document.getElementById('chatbot-container');
        const minimizeButton = document.getElementById('chatbot-minimize');
        const sendButton = document.getElementById('chatbot-send');
        const inputField = document.getElementById('chatbot-input');

        if (!container || !minimizeButton || !sendButton || !inputField) {
            console.error('Required chatbot elements not found');
            return;
        }

        minimizeButton.addEventListener('click', () => this.toggleChat());
        sendButton.addEventListener('click', () => this.sendMessage());
        
        inputField.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Open chat by default
        this.isOpen = true;
        container.classList.remove('chatbot-minimized');
    }

    toggleChat() {
        const container = document.getElementById('chatbot-container');
        if (!container) return;
        
        this.isOpen = !this.isOpen;
        if (this.isOpen) {
            container.classList.remove('chatbot-minimized');
        } else {
            container.classList.add('chatbot-minimized');
        }
    }

    async sendMessage() {
        const inputField = document.getElementById('chatbot-input');
        const messagesContainer = document.getElementById('chatbot-messages');
        
        if (!inputField || !messagesContainer) {
            console.error('Required chatbot elements not found');
            return;
        }

        const message = inputField.value.trim();
        if (!message) return;

        // Add user message to chat
        this.addMessageToChat('user', message);
        inputField.value = '';

        try {
            // Show typing indicator
            this.showTypingIndicator();

            // Make API call
            const response = await fetch('/chatbot/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message })
            });

            // Remove typing indicator
            this.hideTypingIndicator();

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to get response from server');
            }

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            if (data.response || data.html_response) {
                this.addMessageToChat('bot', data.response || 'No response text', data.html_response);
            } else {
                throw new Error('Invalid response format from server');
            }

        } catch (error) {
            console.error('Error in sendMessage:', error);
            this.hideTypingIndicator();
            this.addMessageToChat('bot', 'Sorry, I encountered an error. Please try again.');
        }
    }

    addMessageToChat(sender, text, html = null) {
        const messagesContainer = document.getElementById('chatbot-messages');
        if (!messagesContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `chatbot-message ${sender}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (sender === 'bot' && html) {
            contentDiv.innerHTML = html;
        } else {
            contentDiv.textContent = text;
        }
        
        messageDiv.appendChild(contentDiv);
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    showTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.style.display = 'flex';
        }
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.style.display = 'none';
        }
    }
}

// Initialize chatbot when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const chatbot = new FitTabChatbot();
});
