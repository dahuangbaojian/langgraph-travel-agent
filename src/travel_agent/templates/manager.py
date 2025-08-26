"""
模板管理器
负责加载、缓存和管理所有Jinja2模板
"""

import os
import logging
from pathlib import Path
from typing import Dict, Optional
from jinja2 import Template, Environment, FileSystemLoader

logger = logging.getLogger(__name__)


class TemplateManager:
    """模板管理器"""

    def __init__(self):
        self.templates_dir = Path(__file__).parent
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=False,  # Markdown不需要转义
            trim_blocks=True,  # 去除块级标签前后的空白
            lstrip_blocks=True,  # 去除块级标签前的空白
        )
        self._template_cache: Dict[str, Template] = {}

    def get_template(self, template_name: str) -> Optional[Template]:
        """获取模板，优先从缓存读取"""
        if template_name in self._template_cache:
            return self._template_cache[template_name]

        try:
            template = self.jinja_env.get_template(template_name)
            self._template_cache[template_name] = template
            logger.debug(f"模板 {template_name} 已加载并缓存")
            return template
        except Exception as e:
            logger.error(f"加载模板 {template_name} 失败: {e}")
            return None

    def render_template(self, template_name: str, **kwargs) -> Optional[str]:
        """渲染模板"""
        template = self.get_template(template_name)
        if template is None:
            return None

        try:
            result = template.render(**kwargs)
            return result
        except Exception as e:
            logger.error(f"渲染模板 {template_name} 失败: {e}")
            return None

    def list_templates(self) -> list:
        """列出所有可用模板"""
        templates = []
        for file_path in self.templates_dir.glob("*.j2"):
            templates.append(file_path.name)
        return templates

    def reload_template(self, template_name: str) -> bool:
        """重新加载指定模板"""
        if template_name in self._template_cache:
            del self._template_cache[template_name]

        template = self.get_template(template_name)
        return template is not None

    def reload_all_templates(self) -> bool:
        """重新加载所有模板"""
        self._template_cache.clear()
        try:
            # 重新初始化Jinja2环境
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(self.templates_dir)),
                autoescape=False,
                trim_blocks=True,
                lstrip_blocks=True,
            )
            logger.info("所有模板已重新加载")
            return True
        except Exception as e:
            logger.error(f"重新加载模板失败: {e}")
            return False


# 全局模板管理器实例
template_manager = TemplateManager()
