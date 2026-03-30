"""
徐小明多空通道 - 短线25日 / 长线89日

算法公式：
- 短线通道：上轨 = EMA(H, 25), 下轨 = EMA(L, 25)
- 长线通道：上轨 = EMA(H, 89), 下轨 = EMA(L, 89)

颜色信号：
- 红色：价格在通道内且通道向上
- 绿色：价格在通道内且通道向下
- 突破上轨：强势上涨
- 跌破下轨：趋势破坏
"""

import pandas as pd
import numpy as np


def calculate_trend_channel(
    df: pd.DataFrame, short_period: int = 25, long_period: int = 89
) -> pd.DataFrame:
    """
    计算徐小明多空通道

    Args:
        df: 包含high, low, close的DataFrame
        short_period: 短线周期，默认25
        long_period: 长线周期，默认89

    Returns:
        包含通道的DataFrame
    """
    result = df.copy()

    high = result["high"]
    low = result["low"]
    close = result["close"]

    # 短线通道（25日）
    result["short_upper"] = high.ewm(span=short_period, adjust=False).mean()
    result["short_lower"] = low.ewm(span=short_period, adjust=False).mean()
    result["short_mid"] = close.ewm(span=short_period, adjust=False).mean()

    # 长线通道（89日）
    result["long_upper"] = high.ewm(span=long_period, adjust=False).mean()
    result["long_lower"] = low.ewm(span=long_period, adjust=False).mean()
    result["long_mid"] = close.ewm(span=long_period, adjust=False).mean()

    # 通道方向判定
    result["short_direction"] = np.where(
        result["short_upper"] > result["short_upper"].shift(1), "red", "green"
    )
    result["long_direction"] = np.where(
        result["long_upper"] > result["long_upper"].shift(1), "purple", "blue"
    )

    return result


def get_channel_signal(df: pd.DataFrame, latest_price: float = None) -> dict:
    """
    获取通道信号

    颜色判定逻辑：
    - 价格 > 上轨：强势突破（strong_up/strong_down）
    - 价格 < 下轨：趋势破坏
    - 价格在通道内：根据通道内位置判断偏强/中性/偏弱

    Args:
        df: 包含通道数据的DataFrame
        latest_price: 最新价格

    Returns:
        通道信号字典
    """
    if latest_price is None:
        latest_price = df["close"].iloc[-1]

    last = df.iloc[-1]

    # 短线状态
    if latest_price > last["short_upper"]:
        short_status = "strong_up"  # 突破上轨，强势
    elif latest_price < last["short_lower"]:
        short_status = "strong_down"  # 跌破下轨，弱势
    else:
        # 价格在通道内，根据位置判断
        channel_range = last["short_upper"] - last["short_lower"]
        if channel_range > 0:
            position = (latest_price - last["short_lower"]) / channel_range
            if position > 0.6:
                short_status = "red"  # 偏强
            elif position < 0.4:
                short_status = "green"  # 偏弱
            else:
                short_status = "neutral"  # 中性
        else:
            short_status = "neutral"

    # 长线状态
    if latest_price > last["long_upper"]:
        long_status = "strong_up"
    elif latest_price < last["long_lower"]:
        long_status = "strong_down"
    else:
        channel_range = last["long_upper"] - last["long_lower"]
        if channel_range > 0:
            position = (latest_price - last["long_lower"]) / channel_range
            if position > 0.6:
                long_status = "purple"  # 长线偏强
            elif position < 0.4:
                long_status = "blue"  # 长线偏弱
            else:
                long_status = "neutral"
        else:
            long_status = "neutral"

    # 综合信号判定 - 增加更多状态组合
    signal_map = {
        # 长线突破 + 短线强势
        ("strong_up", "strong_up"): "强势突破",
        ("strong_up", "red"): "突破回踩",
        ("strong_up", "neutral"): "突破整固",
        # 长线突破 + 短线回调
        ("strong_up", "green"): "突破回调，谨慎",
        # 长线多头 + 短线强势
        ("purple", "strong_up"): "强烈做多",
        ("purple", "red"): "做多(短回调)",
        ("neutral", "strong_up"): "做多(突破)",
        # 长线跌破 + 短线弱势
        ("strong_down", "strong_down"): "强势跌破",
        ("strong_down", "green"): "跌破反弹",
        # 长线空头 + 短线弱势
        ("blue", "strong_down"): "强烈做空",
        ("blue", "green"): "做空(短反弹)",
        ("neutral", "strong_down"): "做空(跌破)",
        # 长线多头 + 短线回调/震荡
        ("purple", "green"): "谨慎做多",
        ("purple", "neutral"): "震荡上行",
        # 长线空头 + 短线反弹
        ("blue", "red"): "观望反弹",
        ("blue", "neutral"): "震荡下行",
        # 中性状态
        ("neutral", "neutral"): "震荡整理",
        ("neutral", "green"): "偏弱整理",
        ("neutral", "red"): "偏强整理",
    }

    signal = signal_map.get((long_status, short_status), "观望")

    # 获取通道内位置描述
    short_range = last["short_upper"] - last["short_lower"]
    if short_range > 0:
        short_pos = (latest_price - last["short_lower"]) / short_range * 100
    else:
        short_pos = 50

    return {
        "short_status": short_status,
        "long_status": long_status,
        "signal": signal,
        "short_upper": round(last["short_upper"], 2),
        "short_lower": round(last["short_lower"], 2),
        "long_upper": round(last["long_upper"], 2),
        "long_lower": round(last["long_lower"], 2),
        "short_position": round(short_pos, 1),
    }


if __name__ == "__main__":
    data = {
        "date": pd.date_range("2024-01-01", periods=100),
        "open": np.random.uniform(10, 15, 100),
        "high": np.random.uniform(15, 20, 100),
        "low": np.random.uniform(5, 10, 100),
        "close": np.random.uniform(10, 15, 100),
    }
    df = pd.DataFrame(data)
    result = calculate_trend_channel(df)
    signal = get_channel_signal(result)
    print(signal)
