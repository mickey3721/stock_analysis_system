"""
均线系统 - EMA5/EMA26/EMA89/EMA144

使用指数移动平均(EMA)，与MACD、通道等指标保持一致性
"""

import pandas as pd
import numpy as np


def calculate_ma(df: pd.DataFrame, periods: list = None) -> pd.DataFrame:
    """
    计算EMA均线

    Args:
        df: 包含收盘价的DataFrame
        periods: 均线周期列表，默认 [5, 26, 89, 144]

    Returns:
        包含EMA的DataFrame
    """
    if periods is None:
        periods = [5, 26, 89, 144]

    result = df.copy()

    for period in periods:
        # 使用EMA替代SMA，与MACD、通道指标保持一致
        result[f"ma{period}"] = result["close"].ewm(span=period, adjust=False).mean()

    return result


def get_ma_status(df: pd.DataFrame, latest_price: float = None) -> dict:
    """
    获取均线状态

    Args:
        df: 包含均线的DataFrame
        latest_price: 最新价格，默认取最后一行收盘价

    Returns:
        均线状态字典
    """
    if latest_price is None:
        latest_price = df["close"].iloc[-1]

    last_row = df.iloc[-1]

    ma_values = {}
    for period in [5, 26, 89, 144]:
        ma_values[f"ma{period}"] = last_row.get(f"ma{period}")

    if all(v is not None and not pd.isna(v) for v in ma_values.values()):
        ma_list = [
            (5, ma_values["ma5"]),
            (26, ma_values["ma26"]),
            (89, ma_values["ma89"]),
            (144, ma_values["ma144"]),
        ]

        if (
            latest_price
            > ma_values["ma5"]
            > ma_values["ma26"]
            > ma_values["ma89"]
            > ma_values["ma144"]
        ):
            trend = "strong_up"
        elif (
            latest_price
            < ma_values["ma5"]
            < ma_values["ma26"]
            < ma_values["ma89"]
            < ma_values["ma144"]
        ):
            trend = "strong_down"
        elif ma_values["ma5"] > ma_values["ma26"] > ma_values["ma89"]:
            trend = "up"
        elif ma_values["ma5"] < ma_values["ma26"] < ma_values["ma89"]:
            trend = "down"
        else:
            trend = "sideways"
    else:
        trend = "sideways"

    return {"ma_values": ma_values, "trend": trend, "price": latest_price}


if __name__ == "__main__":
    data = {
        "date": pd.date_range("2024-01-01", periods=100),
        "close": np.random.uniform(10, 20, 100),
    }
    df = pd.DataFrame(data)
    result = calculate_ma(df)
    print(result.tail())
