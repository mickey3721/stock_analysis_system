"""
止盈模块

触发条件：
1. 固定止盈：盈利 ≥ 15% → 全部卖出
2. 跟踪止盈：盈利 ≥ 10% 且回落 ≥ 5% → 跟踪卖出
"""

from typing import Optional


def check_take_profit(
    current_price: float,
    buy_price: float,
    highest_price: float = None,
    fixed_pct: float = 0.15,
    trailing_pct: float = 0.05,
    start_pct: float = 0.10,
) -> dict:
    """
    检查是否触发止盈

    Args:
        current_price: 当前价格
        buy_price: 买入价格
        highest_price: 最高价（用于跟踪止盈）
        fixed_pct: 固定止盈比例，默认15%
        trailing_pct: 跟踪回撤比例，默认5%
        start_pct: 启动跟踪止盈的比例，默认10%

    Returns:
        检查结果字典
    """
    if highest_price is None:
        highest_price = current_price

    profit_pct = (current_price - buy_price) / buy_price
    highest_profit_pct = (highest_price - buy_price) / buy_price

    # 固定止盈
    if profit_pct >= fixed_pct:
        return {
            "triggered": True,
            "type": "fixed",
            "action": "sell_all",
            "reason": f"固定止盈，盈利{profit_pct * 100:.1f}%",
            "profit_pct": round(profit_pct * 100, 2),
        }

    # 跟踪止盈
    if highest_profit_pct >= start_pct:
        drawdown = (highest_price - current_price) / highest_price
        if drawdown >= trailing_pct:
            return {
                "triggered": True,
                "type": "trailing",
                "action": "sell_all",
                "reason": f"跟踪止盈，回落{drawdown * 100:.1f}%",
                "profit_pct": round(profit_pct * 100, 2),
            }

    return {
        "triggered": False,
        "type": "none",
        "action": "hold",
        "reason": f"未触发止盈，盈利{profit_pct * 100:.1f}%",
        "profit_pct": round(profit_pct * 100, 2),
    }


def calculate_take_profit_price(
    buy_price: float, take_profit_pct: float = 0.15
) -> float:
    """计算止盈价"""
    return round(buy_price * (1 + take_profit_pct), 2)


if __name__ == "__main__":
    result = check_take_profit(current_price=11.2, buy_price=10.0, highest_price=11.8)
    print(result)
