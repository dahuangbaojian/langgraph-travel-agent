"""配置生成Prompt"""

BUDGET_RATIO_PROMPT = """你是一个专业的旅游预算分配专家。请根据以下信息，智能生成预算分配比例：

旅行信息: {travel_info}
目的地: {destination}
预算等级: {budget_level}
旅行天数: {duration_days}
人数: {people_count}

请返回JSON格式的预算分配建议：
{{
    "hotel": 0.0-1.0,        # 住宿比例
    "restaurant": 0.0-1.0,   # 餐饮比例
    "attractions": 0.0-1.0,  # 景点比例
    "transport": 0.0-1.0,    # 交通比例
    "other": 0.0-1.0,        # 其他比例
    "reasoning": "分配理由",
    "adjustment_tips": ["调整建议"]
}}

注意：所有比例总和必须等于1.0"""


EXCHANGE_RATE_PROMPT = """你是一个专业的汇率分析专家。请根据当前市场情况，智能估算以下货币对人民币的汇率：

货币: {currency}
当前时间: {current_time}
市场趋势: {market_trend}

请返回JSON格式的汇率估算：
{{
    "estimated_rate": 0.0,           # 估算汇率
    "confidence_level": 0.0-1.0,    # 置信度
    "market_analysis": "市场分析",
    "trend_prediction": "趋势预测",
    "update_frequency": "建议更新频率"
}}

注意：汇率应该反映当前市场实际情况"""


CITY_VALIDATION_PROMPT = """你是一个专业的地理和旅游专家。请验证以下城市信息：

城市名称: {city_name}
用户需求: {user_requirements}
旅行类型: {travel_type}

请返回JSON格式的验证结果：
{{
    "is_valid": true/false,
    "city_type": "domestic|international|unknown",
    "country": "国家",
    "region": "地区",
    "timezone": "时区",
    "best_season": "最佳旅行季节",
    "travel_tips": ["旅行建议"],
    "safety_level": "安全等级",
    "cost_level": "消费水平"
}}"""
