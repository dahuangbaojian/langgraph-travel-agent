"""旅行助手工具包"""

from .flights import (
    search_flights,
    get_flight_price_comparison,
    get_route_recommendations
)

from .hotels import (
    search_hotels,
    get_hotel_recommendations
)

from .places import (
    search_attractions
)

from .currency import (
    convert_currency
)

from .weather import (
    get_current_weather
)

from .rag import (
    search_knowledge,
    get_travel_tips,
    get_visa_info
)

__all__ = [
    # 航班工具
    "search_flights",
    "get_flight_price_comparison", 
    "get_route_recommendations",
    
    # 酒店工具
    "search_hotels",
    "get_hotel_recommendations",
    
    # 景点工具
    "search_attractions",
    
    # 汇率工具
    "convert_currency",
    
    # 天气工具
    "get_current_weather",
    
    # 知识库工具
    "search_knowledge",
    "get_travel_tips",
    "get_visa_info"
]
