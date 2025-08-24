"""RAG知识库检索工具"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DocumentInfo:
    """文档信息"""

    title: str
    content: str
    source: str
    relevance_score: float
    metadata: Dict[str, Any]


class RAGTool:
    """RAG知识库检索工具"""

    def __init__(self):
        self.knowledge_base = self._init_knowledge_base()

    def _init_knowledge_base(self) -> Dict[str, List[DocumentInfo]]:
        """初始化知识库"""
        return {
            "旅行攻略": [
                DocumentInfo(
                    "北京旅行攻略",
                    "北京是中国的首都，拥有丰富的历史文化遗产。故宫、天安门、颐和园是必游景点。建议春秋季节前往，避开暑期人流高峰。",
                    "travel_guide_beijing",
                    0.0,
                    {"city": "北京", "category": "攻略", "language": "中文"},
                ),
                DocumentInfo(
                    "东京旅行攻略",
                    "东京是日本的首都，现代化都市与传统文化并存。浅草寺、东京塔、秋叶原都是热门景点。春季樱花季和秋季红叶季最美。",
                    "travel_guide_tokyo",
                    0.0,
                    {"city": "东京", "category": "攻略", "language": "中文"},
                ),
            ],
            "签证信息": [
                DocumentInfo(
                    "日本旅游签证",
                    "中国公民前往日本旅游需要申请旅游签证。通常需要护照、照片、在职证明、银行流水等材料。办理时间约5-7个工作日。",
                    "visa_japan",
                    0.0,
                    {"country": "日本", "type": "旅游签证", "language": "中文"},
                ),
                DocumentInfo(
                    "申根签证申请",
                    "申根签证适用于欧洲申根区国家。需要提供行程单、酒店预订、机票预订、保险等材料。建议提前3个月申请。",
                    "visa_schengen",
                    0.0,
                    {"region": "欧洲", "type": "申根签证", "language": "中文"},
                ),
            ],
            "美食推荐": [
                DocumentInfo(
                    "北京美食指南",
                    "北京烤鸭、炸酱面、豆汁、驴打滚都是北京特色美食。全聚德、便宜坊是著名的烤鸭店。",
                    "food_beijing",
                    0.0,
                    {"city": "北京", "category": "美食", "language": "中文"},
                )
            ],
        }

    def search_knowledge(
        self, query: str, category: Optional[str] = None, limit: int = 5
    ) -> List[DocumentInfo]:
        """搜索知识库"""
        results = []

        for cat, documents in self.knowledge_base.items():
            if category and cat != category:
                continue

            for doc in documents:
                # 简单的关键词匹配
                score = self._calculate_relevance(query, doc)
                if score > 0:
                    doc.relevance_score = score
                    results.append(doc)

        # 按相关性排序
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:limit]

    def _calculate_relevance(self, query: str, document: DocumentInfo) -> float:
        """计算相关性分数"""
        query_lower = query.lower()
        content_lower = document.content.lower()
        title_lower = document.title.lower()

        score = 0.0

        # 标题匹配
        for word in query_lower.split():
            if word in title_lower:
                score += 10

        # 内容匹配
        for word in query_lower.split():
            if word in content_lower:
                score += 5

        # 元数据匹配
        for key, value in document.metadata.items():
            if isinstance(value, str) and value.lower() in query_lower:
                score += 8

        return score

    def get_travel_tips(self, city: str, topic: str = None) -> List[Dict[str, Any]]:
        """获取旅行贴士"""
        query = f"{city} {topic or '旅行'}"
        documents = self.search_knowledge(query, limit=3)

        tips = []
        for doc in documents:
            tips.append(
                {
                    "标题": doc.title,
                    "内容": doc.content,
                    "来源": doc.source,
                    "相关性": doc.relevance_score,
                }
            )

        return tips

    def get_visa_info(self, country: str) -> Optional[Dict[str, Any]]:
        """获取签证信息"""
        query = f"{country} 签证"
        documents = self.search_knowledge(query, category="签证信息", limit=1)

        if documents:
            doc = documents[0]
            return {
                "国家": country,
                "签证类型": doc.metadata.get("type", "未知"),
                "申请要求": doc.content,
                "来源": doc.source,
            }

        return None


# 全局实例
rag_tool = RAGTool()


def search_knowledge(query: str, **kwargs) -> List[Dict[str, Any]]:
    """搜索知识库的便捷函数"""
    documents = rag_tool.search_knowledge(query, **kwargs)
    return [doc.__dict__ for doc in documents]


def get_travel_tips(city: str, topic: str = None) -> List[Dict[str, Any]]:
    """获取旅行贴士的便捷函数"""
    return rag_tool.get_travel_tips(city, topic)


def get_visa_info(country: str) -> Optional[Dict[str, Any]]:
    """获取签证信息的便捷函数"""
    return rag_tool.get_visa_info(country)
