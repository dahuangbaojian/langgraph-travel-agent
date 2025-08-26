// 全局变量
let ws = null;
let messageId = 0;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeWebSocket();
    setupEventListeners();
    initializeAnimations();
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
            showToast('连接成功', 'success');
        };
        
        ws.onmessage = function(event) {
            handleWebSocketMessage(event.data);
        };
        
        ws.onclose = function() {
            console.log('WebSocket连接已关闭');
            updateConnectionStatus(false);
            showToast('连接已断开，正在重新连接...', 'warning');
            // 尝试重新连接
            setTimeout(initializeWebSocket, 3000);
        };
        
        ws.onerror = function(error) {
            console.error('WebSocket错误:', error);
            updateConnectionStatus(false);
            showToast('连接错误', 'error');
        };
        
    } catch (error) {
        console.error('WebSocket初始化失败:', error);
        updateConnectionStatus(false);
        showToast('连接初始化失败', 'error');
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

    // 输入框获得焦点时的效果
    document.getElementById('userInput').addEventListener('focus', function() {
        this.parentElement.classList.add('focused');
    });

    document.getElementById('userInput').addEventListener('blur', function() {
        this.parentElement.classList.remove('focused');
    });
}

// 初始化动画效果
function initializeAnimations() {
    // 页面加载时的渐入效果
    const elements = document.querySelectorAll('.input-card, .chat-card, .sidebar-card');
    elements.forEach((element, index) => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(30px)';
        
        setTimeout(() => {
            element.style.transition = 'all 0.6s ease';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, index * 200);
    });

    // 英雄区域的动画
    const heroElements = document.querySelectorAll('.hero-icon, .hero-title, .hero-subtitle, .hero-stats');
    heroElements.forEach((element, index) => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(50px)';
        
        setTimeout(() => {
            element.style.transition = 'all 0.8s ease';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, index * 300);
    });
}

// 发送消息
function sendMessage() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();
    
    if (!message) {
        showToast('请输入旅行需求', 'warning');
        input.focus();
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
    
    // 添加发送动画效果
    const sendButton = document.querySelector('.btn-primary-custom');
    sendButton.style.transform = 'scale(0.95)';
    setTimeout(() => {
        sendButton.style.transform = '';
    }, 150);
}

// 快速查询
function quickQuery(query) {
    const input = document.getElementById('userInput');
    input.value = query;
    
    // 添加输入动画效果
    input.style.transform = 'scale(1.02)';
    input.style.boxShadow = '0 0 0 4px rgba(37, 99, 235, 0.1)';
    
    setTimeout(() => {
        input.style.transform = '';
        input.style.boxShadow = '';
    }, 300);
    
    // 自动发送
    setTimeout(() => {
        sendMessage();
    }, 400);
}

// 清空对话
function clearChat() {
    const chatHistory = document.getElementById('chatHistory');
    
    // 添加淡出动画
    chatHistory.style.transition = 'all 0.3s ease';
    chatHistory.style.opacity = '0';
    chatHistory.style.transform = 'scale(0.95)';
    
    setTimeout(() => {
        // 恢复欢迎内容
        chatHistory.innerHTML = `
            <div class="chat-welcome">
                <div class="welcome-icon">
                    <i class="fas fa-plane-departure"></i>
                </div>
                <h6 class="welcome-title">开始您的AI旅行规划</h6>
                <p class="welcome-text">描述您的旅行需求，AI将为您提供专业的规划建议</p>
            </div>
        `;
        
        // 淡入动画
        chatHistory.style.opacity = '1';
        chatHistory.style.transform = 'scale(1)';
        
        showToast('对话已清空', 'success');
    }, 300);
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
    if (chatHistory.querySelector('.chat-welcome')) {
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
    const bgClass = sender === 'user' ? 'user-message' : 'assistant-message';
    
    messageDiv.innerHTML = `
        <div class="message-container ${bgClass}">
            <div class="message-header">
                <div class="message-avatar">
                    <i class="${icon}"></i>
                </div>
                <div class="message-info">
                    <div class="message-name">${name}</div>
                    <div class="message-time">${timestamp}</div>
                </div>
            </div>
            <div class="message-content">
                ${formatMessageContent(content)}
            </div>
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
    // 先处理Markdown格式，再处理其他
    content = parseMarkdown(content);
    
    // 高亮关键词
    const keywords = ['航班', '酒店', '景点', '预算', '天气', '汇率', '签证', '包车', '环线', '贝尔格莱德'];
    keywords.forEach(keyword => {
        const regex = new RegExp(keyword, 'g');
        content = content.replace(regex, `<span class="keyword-highlight">${keyword}</span>`);
    });
    
    return content;
}

// 解析Markdown格式
function parseMarkdown(content) {
    let result = content;
    
    // 1. 处理表格
    result = parseMarkdownTables(result);
    
    // 2. 处理列表
    result = parseMarkdownLists(result);
    
    // 3. 处理粗体和斜体
    result = parseMarkdownText(result);
    
    // 4. 处理换行符（最后处理）
    result = result.replace(/\n/g, '<br>');
    
    return result;
}

// 解析Markdown表格
function parseMarkdownTables(content) {
    const lines = content.split('\n');
    const result = [];
    let i = 0;
    
    while (i < lines.length) {
        const line = lines[i];
        
        // 检查是否是表格行
        if (isTableRow(line)) {
            const tableLines = [];
            let tableStart = i;
            
            // 收集表格行
            while (i < lines.length && isTableRow(lines[i])) {
                tableLines.push(lines[i]);
                i++;
            }
            
            // 生成表格HTML
            if (tableLines.length > 0) {
                const tableHTML = generateTableHTML(tableLines);
                result.push(tableHTML);
            }
        } else {
            result.push(line);
            i++;
        }
    }
    
    return result.join('\n');
}

// 判断是否是表格行
function isTableRow(line) {
    const trimmed = line.trim();
    if (!trimmed.includes('|')) return false;
    
    const cells = trimmed.split('|').filter(cell => cell.trim());
    return cells.length >= 2;
}

// 生成表格HTML
function generateTableHTML(tableLines) {
    let html = '<div class="table-container"><table class="custom-table">';
    
    tableLines.forEach((line, index) => {
        const trimmed = line.trim();
        const cells = trimmed.split('|').filter(cell => cell.trim());
        
        // 跳过分隔行（包含 --- 的行）
        if (cells.some(cell => cell.match(/^[-:\s]+$/))) {
            return;
        }
        
        const isHeader = index === 0; // 第一行作为表头
        const tag = isHeader ? 'th' : 'td';
        
        html += '<tr>';
        cells.forEach(cell => {
            const cleanCell = cell.trim();
            if (cleanCell) {
                html += `<${tag}>${cleanCell}</${tag}>`;
            }
        });
        html += '</tr>';
    });
    
    html += '</table></div>';
    return html;
}

// 解析Markdown列表
function parseMarkdownLists(content) {
    let result = content;
    
    // 数字列表
    result = result.replace(/^(\d+\.\s+)(.+)$/gm, 
        '<div class="numbered-list"><span class="list-number">$1</span><span class="list-item">$2</span></div>');
    
    // 项目符号列表
    result = result.replace(/^[-•]\s+(.+)$/gm, 
        '<div class="bullet-list"><span class="list-bullet">•</span><span class="list-item">$1</span></div>');
    
    return result;
}

// 解析Markdown文本格式
function parseMarkdownText(content) {
    let result = content;
    
    // 粗体
    result = result.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // 斜体
    result = result.replace(/\*(.+?)\*/g, '<em>$1</em>');
    
    // 代码块
    result = result.replace(/`(.+?)`/g, '<code>$1</code>');
    
    return result;
}

// 显示加载模态框
function showLoadingModal() {
    const modal = new bootstrap.Modal(document.getElementById('loadingModal'));
    modal.show();
    
    // 添加进度条动画
    const progressBar = document.querySelector('.progress-bar');
    if (progressBar) {
        progressBar.style.animation = 'progress 2s ease-in-out infinite';
    }
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
    const statusTexts = document.querySelectorAll('.status-text');
    
    statusElements.forEach(element => {
        if (isConnected) {
            element.className = 'status-indicator online';
            element.title = '在线';
        } else {
            element.className = 'status-indicator offline';
            element.title = '离线';
        }
    });
    
    statusTexts.forEach(element => {
        if (isConnected) {
            element.textContent = 'AI系统在线';
            element.style.color = 'var(--success-color)';
        } else {
            element.textContent = 'AI系统离线';
            element.style.color = 'var(--danger-color)';
        }
    });
}

// 更新系统状态
function updateSystemStatus(status) {
    console.log('系统状态更新:', status);
    
    // 更新状态指示器
    const statusItems = document.querySelectorAll('.status-item');
    statusItems.forEach(item => {
        const indicator = item.querySelector('.status-indicator');
        const desc = item.querySelector('.status-desc');
        
        if (status === 'online') {
            indicator.className = 'status-indicator online';
            desc.textContent = '系统正常运行';
        } else {
            indicator.className = 'status-indicator offline';
            desc.textContent = '系统维护中';
        }
    });
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
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
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
    const quickButtons = document.querySelectorAll('.quick-btn');
    quickButtons.forEach(button => {
        button.addEventListener('click', function() {
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
    });
    
    // 为卡片添加悬停效果
    const cards = document.querySelectorAll('.input-card, .chat-card, .sidebar-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = '';
        });
    });

    // 为功能项添加悬停效果
    const featureItems = document.querySelectorAll('.feature-item');
    featureItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(5px)';
        });
        
        item.addEventListener('mouseleave', function() {
            this.style.transform = '';
        });
    });
});
