"""
预算分析相关的Prompt模板
"""

BUDGET_ANALYSIS_PROMPT = """
你是一个专业的旅行预算分析专家，请分析以下旅行预算信息：

旅行信息：{travel_info}

请进行智能预算分析：
1. 预算等级：经济/中等/中高端/豪华
2. 预算分配：住宿、餐饮、景点、交通、其他
3. 预算建议：如何优化预算使用
4. 性价比分析：预算与行程的匹配度

请用JSON格式回答：
{{
    "budget_level": "预算等级",
    "budget_analysis": "预算分析说明",
    "budget_allocation": {{
        "hotel": "住宿预算建议",
        "restaurant": "餐饮预算建议", 
        "attractions": "景点预算建议",
        "transport": "交通预算建议",
        "other": "其他预算建议"
    }},
    "budget_tips": "预算优化建议"
}}

请直接输出JSON，不要有任何解释：
"""
