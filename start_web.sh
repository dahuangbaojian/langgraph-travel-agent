#!/bin/bash

# 设置环境变量
export $(grep -v '^#' .env | grep -v '^$' | xargs)

# 启动web服务
echo "启动智能旅行规划助手..."
echo "环境变量已设置:"
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:0:10}..."
echo "OPENAI_BASE_URL: $OPENAI_BASE_URL"
echo "OPENAI_MODEL: $OPENAI_MODEL"

uvicorn src.travel_agent.ui.app:app --host 0.0.0.0 --port 8000 --reload
