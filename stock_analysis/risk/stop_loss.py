"""
止损模块

触发条件：当前价 ≤ 买入价 × (1 - 止损比例)
默认止损比例：7%
"""

from typing import Optional


def check_stop_loss(
    current_price: float, buy_price: float, stop_loss_pct: float = 0.07
) -> dict:
    """
    检查是否触发止损

    Args:
        current_price: 当前价格
        buy_price: 买入价格
        stop_loss_pct: 止损比例，默认7%

    Returns:
        检查结果字典
    """
    stop_price = buy_price * (1 - stop_loss_pct)

    triggered = current_price <= stop_price
    loss_pct = (buy_price - current_price) / buy_price

    return {
        "triggered": triggered,
        "stop_price": round(stop_price, 2),
        "loss_pct": round(loss_pct * 100, 2),
        "action": "sell" if triggered else "hold",
        "reason": "止损触发" if triggered else "未触发止损",
    }


def calculate_stop_loss_price(buy_price: float, stop_loss_pct: float = 0.07) -> float:
    """计算止损价"""
    return round(buy_price * (1 - stop_loss_pct), 2)


if __name__ == "__main__":
    result = check_stop_loss(current_price=9.2, buy_price=10.0, stop_loss_pct=0.07)
    print(result)
