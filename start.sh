#!/bin/bash

# 旅行助手启动脚本
# 作者: 黄建
# 日期: 2025-01-27

echo "🚀 启动智能旅行规划助手..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3，请先安装Python3.11+"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 创建logs目录
if [ ! -d "logs" ]; then
    echo "📁 创建日志目录..."
    mkdir -p logs
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📥 安装依赖包..."
pip install -e .

# 检查端口是否被占用
if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  警告: 端口8001已被占用，正在停止占用进程..."
    lsof -ti:8001 | xargs kill -9
    sleep 2
fi

# 启动应用
echo "🌟 启动应用服务器..."
echo "📍 访问地址: http://localhost:8001"
echo "📝 日志文件: logs/app.log"
echo "🔄 按 Ctrl+C 停止服务"

# 启动应用（日志系统已集成在项目中）
python -m uvicorn travel_agent.ui.app:app --host 0.0.0.0 --port 8001 --reload
