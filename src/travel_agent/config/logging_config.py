"""Travel Agent Logging Configuration"""

import os
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional
from .settings import config


class TravelAgentLogger:
    """旅行助手日志管理器"""

    def __init__(self, name: str = "travel_agent"):
        self.name = name
        self.logger = None
        self.log_dir = Path("logs")
        self._setup_logging()

    def _setup_logging(self):
        """设置日志系统"""
        # 创建日志目录
        self.log_dir.mkdir(exist_ok=True)

        # 创建logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG if config.debug else logging.INFO)

        # 清除已有的handlers
        self.logger.handlers.clear()

        # 添加控制台handler
        self._add_console_handler()

        # 添加文件handlers
        self._add_file_handlers()

        # 设置格式
        self._set_formatters()

    def _add_console_handler(self):
        """添加控制台输出"""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)

    def _add_file_handlers(self):
        """添加文件输出handlers"""
        # 主日志文件 - 每天归档
        main_handler = logging.handlers.TimedRotatingFileHandler(
            filename=self.log_dir / "app.log",
            when="midnight",
            interval=1,
            backupCount=30,  # 保留30天的日志
            encoding="utf-8",
        )
        main_handler.setLevel(logging.INFO)
        main_handler.suffix = "%Y%m%d"  # 归档文件后缀格式
        self.logger.addHandler(main_handler)

        # 错误日志文件 - 每天归档
        error_handler = logging.handlers.TimedRotatingFileHandler(
            filename=self.log_dir / "error.log",
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.suffix = "%Y%m%d"
        self.logger.addHandler(error_handler)

        # 调试日志文件 - 每天归档
        if config.debug:
            debug_handler = logging.handlers.TimedRotatingFileHandler(
                filename=self.log_dir / "debug.log",
                when="midnight",
                interval=1,
                backupCount=7,  # 调试日志只保留7天
                encoding="utf-8",
            )
            debug_handler.setLevel(logging.DEBUG)
            debug_handler.suffix = "%Y%m%d"
            self.logger.addHandler(debug_handler)

    def _set_formatters(self):
        """设置日志格式"""
        # 详细格式（文件输出）
        detailed_formatter = logging.Formatter(
            fmt="%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(funcName)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # 简洁格式（控制台输出）
        simple_formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(message)s", datefmt="%H:%M:%S"
        )

        # 应用格式
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(
                handler, logging.FileHandler
            ):
                handler.setFormatter(simple_formatter)
            else:
                handler.setFormatter(detailed_formatter)

    def get_logger(self) -> logging.Logger:
        """获取配置好的logger"""
        return self.logger

    def log_startup(self):
        """记录启动信息"""
        self.logger.info("=" * 60)
        self.logger.info(f"🚀 {config.app_name} v{config.version} 启动")
        self.logger.info(f"📁 日志目录: {self.log_dir.absolute()}")
        self.logger.info(f"🐛 调试模式: {config.debug}")
        self.logger.info(f"🤖 默认模型: {config.default_model}")

        # 城市统计信息
        domestic_count = len(config.get_domestic_cities())
        international_count = len(config.get_international_cities())
        self.logger.info(f"🏠 国内城市: {domestic_count} 个")
        self.logger.info(f"🌏 国际城市: {international_count} 个")
        self.logger.info(f"🌍 总计: {len(config.supported_cities)} 个城市")

        # 货币信息
        currency_count = len(config.supported_currencies)
        self.logger.info(f"💱 支持货币: {currency_count} 种")

        self.logger.info("=" * 60)

    def log_shutdown(self):
        """记录关闭信息"""
        self.logger.info("=" * 60)
        self.logger.info(f"🛑 {config.app_name} 正在关闭")
        self.logger.info("=" * 60)

    def cleanup_old_logs(self, days: int = 30):
        """清理旧日志文件"""
        try:
            current_time = datetime.now()
            for log_file in self.log_dir.glob("*.log.*"):
                if log_file.is_file():
                    file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if (current_time - file_time).days > days:
                        log_file.unlink()
                        self.logger.info(f"🧹 清理旧日志文件: {log_file.name}")
        except Exception as e:
            self.logger.error(f"清理日志文件失败: {e}")


# 全局日志实例
travel_logger = TravelAgentLogger()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """获取logger实例"""
    if name:
        return logging.getLogger(f"travel_agent.{name}")
    return travel_logger.get_logger()


def setup_logging():
    """设置日志系统（供外部调用）"""
    return travel_logger


def log_startup():
    """记录启动日志"""
    travel_logger.log_startup()


def log_shutdown():
    """记录关闭日志"""
    travel_logger.log_shutdown()


def cleanup_logs(days: int = 30):
    """清理旧日志"""
    travel_logger.cleanup_old_logs(days)
