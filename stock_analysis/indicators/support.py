"""
支撑/阻力位计算模块

包含：
- 均线支撑/阻力：MA5, MA26, MA89
- 通道支撑/阻力：多空通道上下轨
- 黄金分割位
- 成交密集区
"""

import pandas as pd
import numpy as np
from typing import List, Tuple


def calculate_support_resistance(
    df: pd.DataFrame, ma_periods: List[int] = None, channel_data: dict = None
) -> dict:
    """
    计算支撑/阻力位

    Args:
        df: 包含close, high, low的DataFrame
        ma_periods: 均线周期列表，默认[5, 26, 89]
        channel_data: 通道数据，包含short_upper, short_lower等

    Returns:
        支撑/阻力位字典
    """
    if ma_periods is None:
        ma_periods = [5, 26, 89]

    last = df.iloc[-1]
    close = last["close"]
    high = df["high"]
    low = df["low"]

    # 均线支撑/阻力
    support_levels = []
    resistance_levels = []

    for period in ma_periods:
        if f"ma{period}" in df.columns:
            ma_value = last.get(f"ma{period}")
            if ma_value is not None and not pd.isna(ma_value):
                # 收盘价在MA上方，MA为支撑
                if close > ma_value:
                    support_levels.append(
                        {"level": round(ma_value, 2), "type": f"MA{period}"}
                    )
                # 收盘价在MA下方，MA为阻力
                else:
                    resistance_levels.append(
                        {"level": round(ma_value, 2), "type": f"MA{period}"}
                    )

    # 通道支撑/阻力
    if channel_data:
        if "short_lower" in channel_data and close > channel_data["short_lower"]:
            support_levels.append(
                {"level": round(channel_data["short_lower"], 2), "type": "短线通道下轨"}
            )
        if "short_upper" in channel_data and close < channel_data["short_upper"]:
            resistance_levels.append(
                {"level": round(channel_data["short_upper"], 2), "type": "短线通道上轨"}
            )

        if "long_lower" in channel_data and close > channel_data["long_lower"]:
            support_levels.append(
                {"level": round(channel_data["long_lower"], 2), "type": "长线通道下轨"}
            )
        if "long_upper" in channel_data and close < channel_data["long_upper"]:
            resistance_levels.append(
                {"level": round(channel_data["long_upper"], 2), "type": "长线通道上轨"}
            )

    # 黄金分割（基于近期高低点）
    period = min(60, len(df))
    period_high = high.iloc[-period:].max()
    period_low = low.iloc[-period:].min()

    fib_ratios = [0.382, 0.5, 0.618]
    for ratio in fib_ratios:
        # 阻力位（从低点向上的回调）
        resistance = period_low + (period_high - period_low) * ratio
        if close < resistance:
            resistance_levels.append(
                {"level": round(resistance, 2), "type": f"黄金分割{ratio * 100:.0f}%"}
            )

        # 支撑位（从高点向下的回调）
        support = period_high - (period_high - period_low) * ratio
        if close > support:
            support_levels.append(
                {"level": round(support, 2), "type": f"黄金分割{ratio * 100:.0f}%"}
            )

    # 整数关口
    current_price = close
    base = 10 if current_price > 100 else 1

    for multiplier in range(1, 20):
        level = base * multiplier
        if level < current_price and current_price - level < current_price * 0.05:
            support_levels.append({"level": level, "type": f"整数关口"})
        elif level > current_price and level - current_price < current_price * 0.05:
            resistance_levels.append({"level": level, "type": f"整数关口"})

    # 按价格排序
    support_levels.sort(key=lambda x: x["level"], reverse=True)
    resistance_levels.sort(key=lambda x: x["level"])

    return {
        "support_levels": support_levels[:5],  # 最多5个
        "resistance_levels": resistance_levels[:5],
        "period_high": round(period_high, 2),
        "period_low": round(period_low, 2),
    }


def get_nearest_support(price: float, support_levels: List[dict]) -> float:
    """获取最近支撑位"""
    if not support_levels:
        return price * 0.95

    supports = [s["level"] for s in support_levels if s["level"] < price]
    if supports:
        return max(supports)
    return price * 0.95


def get_nearest_resistance(price: float, resistance_levels: List[dict]) -> float:
    """获取最近阻力位"""
    if not resistance_levels:
        return price * 1.05

    resistances = [r["level"] for r in resistance_levels if r["level"] > price]
    if resistances:
        return min(resistances)
    return price * 1.05


if __name__ == "__main__":
    np.random.seed(42)
    close = np.cumsum(np.random.randn(100)) + 100
    data = {
        "date": pd.date_range("2024-01-01", periods=100),
        "open": close - np.random.randn(100),
        "high": close + np.random.randn(100),
        "low": close - np.random.randn(100),
        "close": close,
    }
    df = pd.DataFrame(data)

    # 添加均线
    for period in [5, 26, 89]:
        df[f"ma{period}"] = df["close"].rolling(period).mean()

    result = calculate_support_resistance(df)
    print("支撑位:", result["support_levels"])
    print("阻力位:", result["resistance_levels"])
