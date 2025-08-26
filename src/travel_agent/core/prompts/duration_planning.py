"""
时长规划相关的Prompt模板
"""

DURATION_PLANNING_PROMPT = """
你是一个专业的旅行时长规划专家，请为以下旅行制定智能时长计划：

目的地：{destination}
预算：{budget}元
偏好：{preferences}

请考虑以下因素：
1. 目的地特点：城市游、自然风光、文化体验等
2. 预算限制：经济型、中等、中高端、豪华
3. 旅行类型：商务、休闲、家庭、探险等
4. 季节因素：春季赏花、夏季避暑、秋季观景、冬季滑雪等

请制定智能时长计划：
{{
    "recommended_duration": 推荐天数（数字）,
    "reason": "时长建议理由",
    "time_optimization": "时间优化建议"
}}

请直接输出JSON，不要有任何解释：
"""
