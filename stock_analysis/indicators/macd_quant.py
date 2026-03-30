"""
MACD定量结构 - 徐小明定量结构

算法公式：
1. MACD计算：
   DIF = EMA(close, 12) - EMA(close, 26)
   DEA = EMA(DIF, 9)
   MACD = (DIF - DEA) × 2

2. 钝化判定（观察窗口120周期）：
   顶部钝化 = 价格创新高(120周期) AND DIF未创新高(120周期)
   底部钝化 = 价格新低(120周期) AND DIF未新低(120周期)

3. 定量级别：
   75%结构 = 钝化状态 AND DIF发生转向
   100%结构 = 75%结构 AND DIF与DEA交叉
"""

import pandas as pd
import numpy as np


def calculate_macd_quant(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    lookback: int = None,
) -> pd.DataFrame:
    """
    计算MACD及定量结构

    Args:
        df: 包含close, high, low的DataFrame
        fast: 快线周期，默认12
        slow: 慢线周期，默认26
        signal: 信号线周期，默认9
        lookback: 钝化观察窗口，默认根据数据量自动调整

    Returns:
        包含MACD及结构的DataFrame
    """
    result = df.copy()
    close = result["close"]
    high = result["high"]
    low = result["low"]

    # 自动调整lookback：至少需要60周期，否则用30周期
    if lookback is None:
        data_len = len(df)
        if data_len >= 120:
            lookback = 120
        elif data_len >= 60:
            lookback = 60
        else:
            lookback = 30

    # 标准MACD计算
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    result["dif"] = ema_fast - ema_slow
    result["dea"] = result["dif"].ewm(span=signal, adjust=False).mean()
    result["macd"] = (result["dif"] - result["dea"]) * 2

    # DIF方向
    result["dif_direction"] = np.where(
        result["dif"] > result["dif"].shift(1), "up", "down"
    )

    # 钝化判定 - 使用调整后的lookback窗口
    price_high = high.rolling(lookback).max()
    price_low = low.rolling(lookback).min()
    dif_high = result["dif"].rolling(lookback).max()
    dif_low = result["dif"].rolling(lookback).min()

    # 顶部钝化：价格创新高（120周期内），DIF未创新高
    result["top_divergence"] = (high >= price_high.shift(1)) & (
        result["dif"] < dif_high.shift(1)
    )

    # 底部钝化：价格新低（120周期内），DIF未新低
    result["bottom_divergence"] = (low <= price_low.shift(1)) & (
        result["dif"] > dif_low.shift(1)
    )

    # 结构级别判定
    structure = []
    for i in range(len(result)):
        if pd.isna(result["top_divergence"].iloc[i]) or pd.isna(
            result["bottom_divergence"].iloc[i]
        ):
            structure.append("none")
            continue

        top_div = result["top_divergence"].iloc[i]
        bot_div = result["bottom_divergence"].iloc[i]
        dif_dir = result["dif_direction"].iloc[i]
        dif_val = result["dif"].iloc[i]
        dea_val = result["dea"].iloc[i]

        if top_div:
            if dif_dir == "down":
                if dif_val < dea_val:
                    structure.append("top_100")
                else:
                    structure.append("top_75")
            else:
                structure.append("divergence_top")

        elif bot_div:
            if dif_dir == "up":
                if dif_val > dea_val:
                    structure.append("bottom_100")
                else:
                    structure.append("bottom_75")
            else:
                structure.append("divergence_bottom")

        else:
            structure.append("none")

    result["macd_structure"] = structure

    return result


def get_macd_structure(df: pd.DataFrame) -> dict:
    """
    获取MACD结构信号

    Args:
        df: 包含MACD结构的DataFrame

    Returns:
        MACD结构信号字典
    """
    last = df.iloc[-1]

    structure = last.get("macd_structure", "none")
    dif = last.get("dif")
    dea = last.get("dea")
    macd = last.get("macd")

    signal_desc = ""
    if structure == "top_100":
        signal_desc = "顶100%=逃顶信号"
    elif structure == "top_75":
        signal_desc = "顶75%=风险累积"
    elif structure == "bottom_100":
        signal_desc = "底100%=低吸机会"
    elif structure == "bottom_75":
        signal_desc = "底75%=逐步建仓"
    elif structure == "divergence_top":
        signal_desc = "顶背驰，谨慎"
    elif structure == "divergence_bottom":
        signal_desc = "底背驰，关注"
    else:
        # 增加无结构时的更多信息
        if macd > 0:
            signal_desc = "多头运行中"
        elif macd < 0:
            signal_desc = "空头运行中"
        else:
            signal_desc = "横盘整理"

    return {
        "structure": structure,
        "signal_desc": signal_desc,
        "dif": dif,
        "dea": dea,
        "macd": macd,
    }


if __name__ == "__main__":
    np.random.seed(42)
    close = np.cumsum(np.random.randn(50)) + 100
    data = {
        "date": pd.date_range("2024-01-01", periods=50),
        "open": close - np.random.randn(50),
        "high": close + np.random.randn(50),
        "low": close - np.random.randn(50),
        "close": close,
    }
    df = pd.DataFrame(data)
    result = calculate_macd_quant(df)
    signal = get_macd_structure(result)
    print(result[["date", "dif", "dea", "macd", "macd_structure"]].tail(10))
    print(signal)
