"""汇率转换工具"""

import logging
from typing import Dict, Optional, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class CurrencyTool:
    """汇率转换工具"""

    def __init__(self):
        self.exchange_rates = self._init_exchange_rates()
        self.last_update = datetime.now()

    def _init_exchange_rates(self) -> Dict[str, float]:
        """初始化汇率"""
        return {
            "USD": 7.2,  # 1 USD = 7.2 CNY
            "EUR": 7.8,  # 1 EUR = 7.8 CNY
            "JPY": 0.048,  # 1 JPY = 0.048 CNY
            "KRW": 0.0054,  # 1 KRW = 0.0054 CNY
            "GBP": 9.1,  # 1 GBP = 9.1 CNY
            "AUD": 4.8,  # 1 AUD = 4.8 CNY
            "CAD": 5.3,  # 1 CAD = 5.3 CNY
        }

    def convert_currency(
        self, amount: float, from_currency: str, to_currency: str = "CNY"
    ) -> Optional[float]:
        """货币转换"""
        try:
            if from_currency == to_currency:
                return amount

            if from_currency != "CNY":
                if from_currency not in self.exchange_rates:
                    return None
                cny_amount = amount * self.exchange_rates[from_currency]
            else:
                cny_amount = amount

            if to_currency != "CNY":
                if to_currency not in self.exchange_rates:
                    return None
                result = cny_amount / self.exchange_rates[to_currency]
            else:
                result = cny_amount

            return round(result, 2)

        except Exception as e:
            logger.error(f"货币转换失败: {e}")
            return None


# 全局实例
currency_tool = CurrencyTool()


def convert_currency(
    amount: float, from_currency: str, to_currency: str = "CNY"
) -> Optional[float]:
    """货币转换的便捷函数"""
    return currency_tool.convert_currency(amount, from_currency, to_currency)


async def get_exchange_rate(
    from_currency: str, to_currency: str = "CNY"
) -> Optional[str]:
    """获取格式化的汇率信息字符串"""
    try:
        if from_currency == to_currency:
            return f"1 {from_currency} = 1 {to_currency}"

        if from_currency == "CNY":
            # 从人民币转换到其他货币
            if to_currency in currency_tool.exchange_rates:
                rate = 1 / currency_tool.exchange_rates[to_currency]
                return f"1 CNY = {rate:.4f} {to_currency}"
        else:
            # 从其他货币转换到人民币
            if from_currency in currency_tool.exchange_rates:
                rate = currency_tool.exchange_rates[from_currency]
                return f"1 {from_currency} = {rate:.2f} CNY"

        return None
    except Exception as e:
        logger.error(f"获取汇率信息失败: {e}")
        return None
