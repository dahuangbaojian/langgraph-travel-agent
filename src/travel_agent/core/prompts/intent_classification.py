"""意图分类Prompt"""

INTENT_CLASSIFICATION_PROMPT = """你是一个专业的旅游规划AI助手。请分析以下用户消息，并返回JSON格式的意图分析：

用户消息: {message}

请分析并返回：
{{
    "intent_type": "travel_planning|travel_modification|travel_consultation|error_recovery",
    "complexity_level": "simple|medium|complex",
    "confidence_score": 0.0-1.0,
    "primary_concern": "主要关注点",
    "suggested_approach": "建议的处理方法",
    "requires_specialization": true/false,
    "specialization_areas": ["需要专业化的领域"]
}}"""
