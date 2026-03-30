"""
回撤控制模块

触发条件：
- 最大回撤 ≥ 15% → 熔断清仓，休息5天
- 单只回撤 ≥ 10% → 减仓50%
"""

from typing import Optional, List
from datetime import datetime, timedelta


def check_drawdown(
    current_value: float,
    peak_value: float,
    max_drawdown_pct: float = 0.15,
    reduce_pct: float = 0.10,
) -> dict:
    """
    检查回撤

    Args:
        current_value: 当前账户价值
        peak_value: 历史最高账户价值
        max_drawdown_pct: 最大回撤比例，默认15%
        reduce_pct: 减仓触发比例，默认10%

    Returns:
        检查结果字典
    """
    if peak_value == 0:
        return {"triggered": False, "action": "hold"}

    drawdown_pct = (peak_value - current_value) / peak_value

    # 熔断清仓
    if drawdown_pct >= max_drawdown_pct:
        return {
            "triggered": True,
            "type": "stop_loss",
            "action": "clear_all",
            "reason": f"最大回撤{drawdown_pct * 100:.1f}%，触发熔断",
            "drawdown_pct": round(drawdown_pct * 100, 2),
            "cooling_days": 5,
        }

    # 减仓预警
    if drawdown_pct >= reduce_pct:
        return {
            "triggered": True,
            "type": "reduce",
            "action": "reduce_50",
            "reason": f"回撤{drawdown_pct * 100:.1f}%，建议减仓",
            "drawdown_pct": round(drawdown_pct * 100, 2),
        }

    return {
        "triggered": False,
        "type": "none",
        "action": "hold",
        "reason": f"回撤{drawdown_pct * 100:.1f}%，正常",
        "drawdown_pct": round(drawdown_pct * 100, 2),
    }


def check_position_drawdown(
    current_price: float, buy_price: float, reduce_pct: float = 0.10
) -> dict:
    """
    检查单只股票回撤

    Args:
        current_price: 当前价格
        buy_price: 买入价格
        reduce_pct: 减仓触发比例，默认10%

    Returns:
        检查结果
    """
    if buy_price == 0:
        return {"triggered": False, "action": "hold"}

    drawdown_pct = (buy_price - current_price) / buy_price

    if drawdown_pct >= reduce_pct:
        return {
            "triggered": True,
            "action": "reduce_50",
            "reason": f"单只回撤{drawdown_pct * 100:.1f}%，减仓50%",
            "drawdown_pct": round(drawdown_pct * 100, 2),
        }

    return {
        "triggered": False,
        "action": "hold",
        "reason": "正常",
        "drawdown_pct": round(drawdown_pct * 100, 2),
    }


class CoolingPeriodManager:
    """冷却期管理器"""

    def __init__(self):
        self.last_clear_date = None

    def should_wait(self) -> bool:
        """检查是否在冷却期"""
        if self.last_clear_date is None:
            return False

        days_since_clear = (datetime.now() - self.last_clear_date).days
        return days_since_clear < 5

    def record_clear(self):
        """记录熔断清仓"""
        self.last_clear_date = datetime.now()

    def reset(self):
        """重置冷却期"""
        self.last_clear_date = None


if __name__ == "__main__":
    result = check_drawdown(current_value=85000, peak_value=100000)
    print(result)
