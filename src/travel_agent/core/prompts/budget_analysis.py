"""
预算分析相关的Prompt模板
"""

BUDGET_ANALYSIS_PROMPT = """
你是一个专业的旅行预算分析专家，请分析以下旅行预算信息：

目的地：{destination}
预算等级：{budget_level}
天数：{duration_days}天
人数：{people_count}人

请进行智能预算分析：
1. 预算等级：经济/中等/中高端/豪华
2. 预算分配：住宿、餐饮、景点、交通、其他
3. 预算建议：如何优化预算使用
4. 性价比分析：预算与行程的匹配度

请用JSON格式回答：
{{
    "total_budget": 总预算金额,
    "daily_budget": 日均预算,
    "budget_breakdown": {{
        "hotel": 0.4,
        "restaurant": 0.25,
        "attractions": 0.15,
        "transport": 0.15,
        "other": 0.05
    }},
    "budget_tips": "预算优化建议"
}}

请直接输出JSON，不要有任何解释：
"""
