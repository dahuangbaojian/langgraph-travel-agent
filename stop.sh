#!/bin/bash

# 旅行助手停止脚本
# 作者: 黄建
# 日期: 2025-01-27

echo "�� 停止智能旅行规划助手..."

# 通过端口查找进程
PID=$(lsof -ti:8001)

if [ -z "$PID" ]; then
    echo "✅ 应用未运行"
    exit 0
fi

echo "🔍 找到进程ID: $PID"

# 停止进程
echo "🔄 正在停止进程..."
kill $PID

# 等待进程停止
sleep 3

# 检查进程是否还在运行
if kill -0 $PID 2>/dev/null; then
    echo "⚠️  进程仍在运行，强制停止..."
    kill -9 $PID
    sleep 1
fi

# 最终检查
if kill -0 $PID 2>/dev/null; then
    echo "❌ 无法停止进程 $PID"
    exit 1
else
    echo "✅ 进程已停止"
fi

# 检查端口是否释放
if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  警告: 端口8001仍被占用"
else
    echo "✅ 端口8001已释放"
fi

echo "🎉 应用已完全停止"
