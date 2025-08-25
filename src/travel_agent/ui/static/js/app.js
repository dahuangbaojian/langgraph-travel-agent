// 全局变量
let ws = null;
let messageId = 0;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeWebSocket();
    setupEventListeners();
});

// 初始化WebSocket连接
function initializeWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    try {
        ws = new WebSocket(wsUrl);
        
        ws.onopen = function() {
            console.log('WebSocket连接已建立');
            updateConnectionStatus(true);
        };
        
        ws.onmessage = function(event) {
            handleWebSocketMessage(event.data);
        };
        
        ws.onclose = function() {
            console.log('WebSocket连接已关闭');
            updateConnectionStatus(false);
            // 尝试重新连接
            setTimeout(initializeWebSocket, 3000);
        };
        
        ws.onerror = function(error) {
            console.error('WebSocket错误:', error);
            updateConnectionStatus(false);
        };
        
    } catch (error) {
        console.error('WebSocket初始化失败:', error);
        updateConnectionStatus(false);
    }
}

// 设置事件监听器
function setupEventListeners() {
    // 回车键发送消息
    document.getElementById('userInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // 输入框自动调整高度
    document.getElementById('userInput').addEventListener('input', function() {
        autoResizeTextarea(this);
    });
}

// 发送消息
function sendMessage() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();
    
    if (!message) {
        showToast('请输入旅行需求', 'warning');
        return;
    }
    
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        showToast('连接已断开，正在重新连接...', 'warning');
        return;
    }
    
    // 显示加载模态框
    showLoadingModal();
    
    // 添加用户消息到聊天历史
    addMessageToChat('user', message);
    
    // 发送消息到WebSocket
    const messageData = {
        type: 'message',
        content: message,
        timestamp: new Date().toISOString()
    };
    
    ws.send(JSON.stringify(messageData));
    
    // 清空输入框
    input.value = '';
    autoResizeTextarea(input);
}

// 快速查询
function quickQuery(query) {
    document.getElementById('userInput').value = query;
    sendMessage();
}

// 处理WebSocket消息
function handleWebSocketMessage(data) {
    try {
        const message = JSON.parse(data);
        
        if (message.type === 'response') {
            // 隐藏加载模态框
            hideLoadingModal();
            
            // 添加AI回复到聊天历史
            addMessageToChat('assistant', message.content);
            
        } else if (message.type === 'error') {
            hideLoadingModal();
            showToast('发生错误: ' + message.content, 'error');
            
        } else if (message.type === 'status') {
            updateSystemStatus(message.content);
        }
        
    } catch (error) {
        console.error('解析WebSocket消息失败:', error);
        hideLoadingModal();
        showToast('消息解析失败', 'error');
    }
}

// 添加消息到聊天历史
function addMessageToChat(sender, content) {
    const chatHistory = document.getElementById('chatHistory');
    
    // 如果是第一条消息，清空欢迎内容
    if (chatHistory.querySelector('.text-center')) {
        chatHistory.innerHTML = '';
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}`;
    
    const timestamp = new Date().toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
    });
    
    const icon = sender === 'user' ? 'fas fa-user' : 'fas fa-robot';
    const name = sender === 'user' ? '你' : 'AI助手';
    
    messageDiv.innerHTML = `
        <div class="message-header">
            <i class="${icon} me-2"></i>
            <span>${name}</span>
            <span class="message-time">${timestamp}</span>
        </div>
        <div class="message-content">
            ${formatMessageContent(content)}
        </div>
    `;
    
    chatHistory.appendChild(messageDiv);
    
    // 滚动到底部
    chatHistory.scrollTop = chatHistory.scrollHeight;
    
    // 添加动画效果
    messageDiv.style.opacity = '0';
    messageDiv.style.transform = 'translateY(20px)';
    
    setTimeout(() => {
        messageDiv.style.transition = 'all 0.5s ease';
        messageDiv.style.opacity = '1';
        messageDiv.style.transform = 'translateY(0)';
    }, 100);
}

// 格式化消息内容
function formatMessageContent(content) {
    // 将换行符转换为HTML
    content = content.replace(/\n/g, '<br>');
    
    // 高亮关键词
    const keywords = ['航班', '酒店', '景点', '预算', '天气', '汇率', '签证'];
    keywords.forEach(keyword => {
        const regex = new RegExp(keyword, 'g');
        content = content.replace(regex, `<span class="badge bg-primary me-1">${keyword}</span>`);
    });
    
    return content;
}

// 显示加载模态框
function showLoadingModal() {
    const modal = new bootstrap.Modal(document.getElementById('loadingModal'));
    modal.show();
}

// 隐藏加载模态框
function hideLoadingModal() {
    const modal = bootstrap.Modal.getInstance(document.getElementById('loadingModal'));
    if (modal) {
        modal.hide();
    }
}

// 更新连接状态
function updateConnectionStatus(isConnected) {
    const statusElements = document.querySelectorAll('.status-indicator');
    statusElements.forEach(element => {
        if (isConnected) {
            element.className = 'status-indicator status-online';
            element.title = '在线';
        } else {
            element.className = 'status-indicator bg-danger';
            element.title = '离线';
        }
    });
}

// 更新系统状态
function updateSystemStatus(status) {
    // 这里可以更新系统状态显示
    console.log('系统状态更新:', status);
}

// 显示提示消息
function showToast(message, type = 'info') {
    // 创建Toast元素
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas fa-${getToastIcon(type)} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // 显示Toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // 自动移除Toast
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// 创建Toast容器
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// 获取Toast图标
function getToastIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// 自动调整文本框高度
function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

// 页面卸载时关闭WebSocket
window.addEventListener('beforeunload', function() {
    if (ws) {
        ws.close();
    }
});

// 添加一些交互效果
document.addEventListener('DOMContentLoaded', function() {
    // 为快速操作按钮添加点击效果
    const quickButtons = document.querySelectorAll('.btn-outline-primary, .btn-outline-success, .btn-outline-info');
    quickButtons.forEach(button => {
        button.addEventListener('click', function() {
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
    });
    
    // 为卡片添加悬停效果
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = '';
        });
    });
});
