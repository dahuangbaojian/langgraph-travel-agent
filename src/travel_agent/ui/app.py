"""Travel Agent Web UI"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import json
import uuid
from typing import Dict, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="智能旅行规划助手", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 存储WebSocket连接
connections: Dict[str, WebSocket] = {}

# 存储对话历史
conversations: Dict[str, list] = {}


@app.get("/", response_class=HTMLResponse)
async def get_chat_interface():
    """获取聊天界面"""
    return """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>智能旅行规划助手</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .chat-container {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                width: 90%;
                max-width: 800px;
                height: 80vh;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            
            .chat-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 20px 20px 0 0;
            }
            
            .chat-header h1 {
                font-size: 24px;
                font-weight: 600;
                margin-bottom: 5px;
            }
            
            .chat-header p {
                opacity: 0.9;
                font-size: 14px;
            }
            
            .chat-messages {
                flex: 1;
                padding: 20px;
                overflow-y: auto;
                background: #f8f9fa;
            }
            
            .message {
                margin-bottom: 20px;
                display: flex;
                align-items: flex-start;
            }
            
            .message.user {
                justify-content: flex-end;
            }
            
            .message-content {
                max-width: 70%;
                padding: 15px 20px;
                border-radius: 20px;
                word-wrap: break-word;
                line-height: 1.5;
            }
            
            .message.user .message-content {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-bottom-right-radius: 5px;
            }
            
            .message.assistant .message-content {
                background: white;
                color: #333;
                border: 1px solid #e9ecef;
                border-bottom-left-radius: 5px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            }
            
            .message.assistant .message-content h3 {
                color: #667eea;
                margin-bottom: 10px;
                font-size: 18px;
            }
            
            .message.assistant .message-content ul {
                margin: 10px 0;
                padding-left: 20px;
            }
            
            .message.assistant .message-content li {
                margin: 5px 0;
            }
            
            .chat-input {
                padding: 20px;
                background: white;
                border-top: 1px solid #e9ecef;
                display: flex;
                gap: 10px;
            }
            
            .chat-input input {
                flex: 1;
                padding: 15px 20px;
                border: 2px solid #e9ecef;
                border-radius: 25px;
                font-size: 16px;
                outline: none;
                transition: border-color 0.3s;
            }
            
            .chat-input input:focus {
                border-color: #667eea;
            }
            
            .chat-input button {
                padding: 15px 25px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 25px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s;
            }
            
            .chat-input button:hover {
                transform: translateY(-2px);
            }
            
            .chat-input button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            
            .typing-indicator {
                display: none;
                padding: 15px 20px;
                background: white;
                border: 1px solid #e9ecef;
                border-radius: 20px;
                border-bottom-left-radius: 5px;
                margin-bottom: 20px;
                color: #666;
                font-style: italic;
            }
            
            .example-queries {
                margin-top: 20px;
                text-align: center;
            }
            
            .example-queries h4 {
                color: #666;
                margin-bottom: 10px;
                font-size: 14px;
            }
            
            .example-queries .examples {
                display: flex;
                gap: 10px;
                justify-content: center;
                flex-wrap: wrap;
            }
            
            .example-queries .example {
                background: rgba(102, 126, 234, 0.1);
                color: #667eea;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 12px;
                cursor: pointer;
                transition: background 0.3s;
            }
            
            .example-queries .example:hover {
                background: rgba(102, 126, 234, 0.2);
            }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <div class="chat-header">
                <h1>🧳 智能旅行规划助手</h1>
                <p>为您定制完美旅程，包含路线规划、住宿推荐、美食指南</p>
            </div>
            
            <div class="chat-messages" id="chatMessages">
                <div class="message assistant">
                    <div class="message-content">
                        <h3>👋 欢迎使用智能旅行规划助手！</h3>
                        <p>我可以帮您：</p>
                        <ul>
                            <li>🎯 制定个性化旅行路线</li>
                            <li>🏨 推荐合适的酒店住宿</li>
                            <li>🍽️ 介绍当地特色美食</li>
                            <li>💰 合理分配旅行预算</li>
                            <li>🚄 提供交通出行建议</li>
                        </ul>
                        <p>请告诉我您的旅行需求，比如：</p>
                        <p><strong>"我想去北京玩3天，预算5000元，2个人"</strong></p>
                    </div>
                </div>
            </div>
            
            <div class="typing-indicator" id="typingIndicator">
                正在为您规划旅行... ✈️
            </div>
            
            <div class="chat-input">
                <input type="text" id="messageInput" placeholder="输入您的旅行需求..." autocomplete="off">
                <button id="sendButton" onclick="sendMessage()">发送</button>
            </div>
            
            <div class="example-queries">
                <h4>💡 示例查询</h4>
                <div class="examples">
                    <div class="example" onclick="setExample('我想去上海玩2天，预算3000元')">上海2日游</div>
                    <div class="example" onclick="setExample('推荐广州的酒店和美食')">广州推荐</div>
                    <div class="example" onclick="setExample('北京5日游，预算8000元，3个人')">北京5日游</div>
                    <div class="example" onclick="setExample('杭州西湖周边有什么好玩的？')">杭州攻略</div>
                </div>
            </div>
        </div>

        <script>
            let ws = null;
            let conversationId = null;
            
            function connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws`;
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function() {
                    console.log('WebSocket连接已建立');
                    conversationId = generateConversationId();
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    if (data.type === 'message') {
                        addMessage(data.content, 'assistant');
                        hideTypingIndicator();
                    }
                };
                
                ws.onclose = function() {
                    console.log('WebSocket连接已关闭');
                    setTimeout(connectWebSocket, 1000);
                };
                
                ws.onerror = function(error) {
                    console.error('WebSocket错误:', error);
                };
            }
            
            function generateConversationId() {
                return 'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            }
            
            function sendMessage() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                
                if (!message) return;
                
                // 添加用户消息
                addMessage(message, 'user');
                input.value = '';
                
                // 显示输入指示器
                showTypingIndicator();
                
                // 发送消息到WebSocket
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: 'message',
                        content: message,
                        conversation_id: conversationId
                    }));
                } else {
                    // 如果WebSocket不可用，显示模拟回复
                    setTimeout(() => {
                        hideTypingIndicator();
                        addMessage('抱歉，服务暂时不可用，请稍后重试。', 'assistant');
                    }, 1000);
                }
            }
            
            function addMessage(content, sender) {
                const chatMessages = document.getElementById('chatMessages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${sender}`;
                
                const contentDiv = document.createElement('div');
                contentDiv.className = 'message-content';
                
                if (sender === 'assistant') {
                    // 处理Markdown格式
                    contentDiv.innerHTML = formatMessage(content);
                } else {
                    contentDiv.textContent = content;
                }
                
                messageDiv.appendChild(contentDiv);
                chatMessages.appendChild(messageDiv);
                
                // 滚动到底部
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
            
            function formatMessage(content) {
                // 简单的Markdown格式化
                return content
                    .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
                    .replace(/\\*(.*?)\\*/g, '<em>$1</em>')
                    .replace(/\\n/g, '<br>')
                    .replace(/🎉/g, '<span style="font-size: 20px;">🎉</span>')
                    .replace(/📍/g, '<span style="font-size: 18px;">📍</span>')
                    .replace(/📅/g, '<span style="font-size: 18px;">📅</span>')
                    .replace(/💰/g, '<span style="font-size: 18px;">💰</span>')
                    .replace(/👥/g, '<span style="font-size: 18px;">👥</span>')
                    .replace(/📊/g, '<span style="font-size: 18px;">📊</span>')
                    .replace(/🚄/g, '<span style="font-size: 18px;">🚄</span>')
                    .replace(/📋/g, '<span style="font-size: 18px;">📋</span>')
                    .replace(/💡/g, '<span style="font-size: 18px;">💡</span>');
            }
            
            function showTypingIndicator() {
                document.getElementById('typingIndicator').style.display = 'block';
                document.getElementById('chatMessages').scrollTop = document.getElementById('chatMessages').scrollHeight;
            }
            
            function hideTypingIndicator() {
                document.getElementById('typingIndicator').style.display = 'none';
            }
            
            function setExample(text) {
                document.getElementById('messageInput').value = text;
                document.getElementById('messageInput').focus();
            }
            
            // 回车发送消息
            document.getElementById('messageInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
            
            // 页面加载完成后连接WebSocket
            window.addEventListener('load', function() {
                connectWebSocket();
            });
        </script>
    </body>
    </html>
    """


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点"""
    await websocket.accept()
    connection_id = str(uuid.uuid4())
    connections[connection_id] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            if message_data["type"] == "message":
                # 这里可以集成LangGraph API调用
                # 暂时返回模拟回复
                response = generate_mock_response(message_data["content"])

                await websocket.send_text(
                    json.dumps({"type": "message", "content": response})
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket连接断开: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
    finally:
        if connection_id in connections:
            del connections[connection_id]


def generate_mock_response(message: str) -> str:
    """生成模拟回复（实际项目中会调用LangGraph API）"""
    if "北京" in message:
        return """🎉 为您制定了详细的北京旅行计划！

📍 **目的地**: 北京
📅 **行程天数**: 3天
💰 **总预算**: 5000元
👥 **人数**: 2人

📊 **预算分配**:
• 住宿: 2000元 (40%)
• 餐饮: 1250元 (25%)
• 景点: 750元 (15%)
• 交通: 750元 (15%)
• 其他: 250元 (5%)

🚄 **交通建议**:
• 高铁: 4.5小时, 553元 (中国铁路)

📋 **每日行程**:

第1天 (09-01):
• 上午: 故宫博物院 (历史文化)
• 午餐: 全聚德烤鸭店 (中餐)

第2天 (09-02):
• 上午: 天安门广场 (城市景观)
• 午餐: 老北京炸酱面 (当地特色)

第3天 (09-03):
• 上午: 颐和园 (自然风光)
• 午餐: 北京烤鸭 (当地特色)

💡 **温馨提示**: 这是初步计划，您可以根据实际情况调整。需要修改任何部分吗？"""

    elif "上海" in message:
        return """🎉 为您制定了详细的上海旅行计划！

📍 **目的地**: 上海
📅 **行程天数**: 2天
💰 **总预算**: 3000元
👥 **人数**: 2人

📊 **预算分配**:
• 住宿: 1200元 (40%)
• 餐饮: 750元 (25%)
• 景点: 450元 (15%)
• 交通: 450元 (15%)
• 其他: 150元 (5%)

🚄 **交通建议**:
• 高铁: 4.5小时, 553元 (中国铁路)

📋 **每日行程**:

第1天 (09-01):
• 上午: 外滩 (城市景观)
• 午餐: 南翔小笼包 (当地特色)

第2天 (09-02):
• 上午: 豫园 (历史文化)
• 午餐: 上海本帮菜 (当地特色)

💡 **温馨提示**: 这是初步计划，您可以根据实际情况调整。需要修改任何部分吗？"""

    else:
        return "请告诉我您的具体旅行需求，比如目的地、时间、预算等。我可以为您制定详细的旅行计划！"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
