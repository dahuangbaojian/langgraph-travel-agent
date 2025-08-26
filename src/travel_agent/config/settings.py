"""Travel Agent Configuration Settings"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

# 导入LLM和Prompt
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from ..core.llm_factory import get_llm

logger = logging.getLogger(__name__)


@dataclass
class TravelAgentConfig:
    """Travel Agent 配置类"""

    # OpenAI配置
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 4000

    # 应用配置
    app_name: str = "Travel Agent"
    app_version: str = "1.0.0"
    debug_mode: bool = False

    # 日志配置
    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    def __post_init__(self):
        """初始化后处理"""
        # 从环境变量加载配置
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL")
        self.openai_model = os.getenv("OPENAI_MODEL", self.openai_model)
        self.openai_temperature = float(
            os.getenv("OPENAI_TEMPERATURE", str(self.openai_temperature))
        )
        self.openai_max_tokens = int(
            os.getenv("OPENAI_MAX_TOKENS", str(self.openai_max_tokens))
        )
        self.debug_mode = os.getenv("DEBUG", "false").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", self.log_level)

    @property
    def llm_instance(self):
        """获取LLM实例"""
        return get_llm()

    def validate_config(self) -> bool:
        """验证配置是否有效"""
        if not self.openai_api_key:
            logger.warning("OpenAI API Key 未设置")
            return False
        return True

    def get_config_summary(self) -> dict:
        """获取配置摘要"""
        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "openai_model": self.openai_model,
            "debug_mode": self.debug_mode,
            "log_level": self.log_level,
        }


# 创建全局配置实例
config = TravelAgentConfig()
