"""Travel Agent Web UI"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import json
import uuid
from typing import Dict, Any
from ..config.logging_config import get_logger, log_startup, log_shutdown

# 获取logger
logger = get_logger("ui")

app = FastAPI(title="智能旅行规划助手", version="1.0.0")

# 设置模板和静态文件
templates = Jinja2Templates(directory="src/travel_agent/ui/templates")
app.mount("/static", StaticFiles(directory="src/travel_agent/ui/static"), name="static")

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
async def get_chat_interface(request: Request):
    """获取聊天界面"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/favicon.ico")
async def favicon():
    """返回网站图标"""
    # 返回一个简单的SVG图标
    svg_icon = """<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
        <circle cx="16" cy="16" r="14" fill="#3B82F6" stroke="#1E40AF" stroke-width="2"/>
        <path d="M12 12 L20 16 L12 20 Z" fill="white"/>
        <circle cx="16" cy="16" r="6" fill="none" stroke="white" stroke-width="1.5"/>
    </svg>"""
    return Response(content=svg_icon, media_type="image/svg+xml")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点处理实时通信"""
    await websocket.accept()

    # 为每个连接生成唯一ID
    connection_id = str(uuid.uuid4())
    connections[connection_id] = websocket

    # 初始化对话历史
    if connection_id not in conversations:
        conversations[connection_id] = []

    logger.info(f"WebSocket连接建立: {connection_id}")

    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # 记录用户消息
            user_message = message_data.get("content", "")
            conversations[connection_id].append(
                {
                    "role": "user",
                    "content": user_message,
                    "timestamp": message_data.get("timestamp"),
                }
            )

            logger.info(f"收到用户消息: {user_message[:50]}...")

            # 调用LangGraph处理消息
            try:
                from ..graph import create_travel_agent

                # 创建旅行代理实例
                agent = create_travel_agent()

                # 调用代理处理用户消息
                result = await agent.ainvoke(
                    {"messages": [{"role": "user", "content": user_message}]}
                )

                # 提取AI响应
                logger.info(f"LangGraph返回结果: {result}")

                if result and "messages" in result:
                    ai_messages = result["messages"]
                    if ai_messages and len(ai_messages) > 0:
                        last_message = ai_messages[-1]
                        # 检查消息格式
                        if hasattr(last_message, "content"):
                            response_content = last_message.content
                        elif (
                            isinstance(last_message, dict) and "content" in last_message
                        ):
                            response_content = last_message["content"]
                        else:
                            response_content = str(last_message)
                    else:
                        response_content = "抱歉，我无法处理您的请求，请稍后重试。"
                elif result and "output" in result:
                    # 如果结果在output字段中
                    response_content = str(result["output"])
                elif result:
                    # 直接使用结果
                    response_content = str(result)
                else:
                    response_content = "抱歉，处理过程中出现错误，请稍后重试。"

            except Exception as e:
                logger.error(f"LangGraph处理错误: {e}")
                response_content = f"抱歉，AI服务暂时不可用。错误信息：{str(e)}"

            # 记录AI响应
            conversations[connection_id].append(
                {
                    "role": "assistant",
                    "content": response_content,
                    "timestamp": message_data.get("timestamp"),
                }
            )

            # 发送响应
            response = {
                "type": "response",
                "content": response_content,
                "timestamp": message_data.get("timestamp"),
            }

            await websocket.send_text(json.dumps(response))
            logger.info(f"发送AI响应: {response_content[:50]}...")

    except WebSocketDisconnect:
        logger.info(f"WebSocket连接断开: {connection_id}")
        if connection_id in connections:
            del connections[connection_id]
        if connection_id in conversations:
            del conversations[connection_id]
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        if connection_id in connections:
            del connections[connection_id]
        if connection_id in conversations:
            del conversations[connection_id]


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    log_startup()


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    log_shutdown()
    # 关闭所有WebSocket连接
    for connection_id, websocket in connections.items():
        try:
            await websocket.close()
        except:
            pass
    connections.clear()
    conversations.clear()
