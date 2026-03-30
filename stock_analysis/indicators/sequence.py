"""
九转序列 - TD序列规则

TD序列算法（徐小明九转序列核心逻辑）：
- 买序列（TD买入计数）：当出现收盘价 >= 前第4根收盘价时，计数+1，否则重置为1
- 卖序列（TD卖出计数）：当出现收盘价 <= 前第4根收盘价时，计数+1，否则重置为1

关键点：允许中间有反向K线，只要满足与前第4根的比较条件即可计数
"""

import pandas as pd
import numpy as np


def calculate_sequence(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算TD九转序列

    Args:
        df: 包含close的DataFrame

    Returns:
        包含序列的DataFrame
    """
    result = df.copy()
    close = result["close"]

    # 初始化序列计数
    buy_seq = np.zeros(len(close), dtype=int)
    sell_seq = np.zeros(len(close), dtype=int)

    # TD序列计数（从第5根开始，因为需要与前第4根比较）
    for i in range(4, len(close)):
        # 买序列：收盘价 >= 前第4根收盘价
        if close.iloc[i] >= close.iloc[i - 4]:
            if i == 4:
                buy_seq[i] = 1
            else:
                buy_seq[i] = buy_seq[i - 1] + 1
        else:
            buy_seq[i] = 1

        # 卖序列：收盘价 <= 前第4根收盘价
        if close.iloc[i] <= close.iloc[i - 4]:
            if i == 4:
                sell_seq[i] = 1
            else:
                sell_seq[i] = sell_seq[i - 1] + 1
        else:
            sell_seq[i] = 1

    # 限制最大为9
    buy_seq = np.minimum(buy_seq, 9)
    sell_seq = np.minimum(sell_seq, 9)

    result["seq9_buy"] = buy_seq
    result["seq9_sell"] = sell_seq

    return result


def get_sequence_signal(df: pd.DataFrame) -> dict:
    """
    获取序列信号

    Args:
        df: 包含序列数据的DataFrame

    Returns:
        序列信号字典
    """
    last = df.iloc[-1]

    buy_seq = last.get("seq9_buy", 0)
    sell_seq = last.get("seq9_sell", 0)

    signal = "none"
    signal_desc = ""

    # 序列9信号（高概率反转点）
    if sell_seq == 9:
        signal = "sell_9"
        signal_desc = "卖9=风险窗口"
    elif buy_seq == 9:
        signal = "buy_9"
        signal_desc = "买9=机会窗口"
    # 序列8预警
    elif sell_seq == 8:
        signal = "sell_warning"
        signal_desc = "卖8=注意风险"
    elif buy_seq == 8:
        signal = "buy_warning"
        signal_desc = "买8=关注买入"
    # 序列7预警
    elif sell_seq == 7:
        signal = "sell_warning"
        signal_desc = "卖7=风险累积"
    elif buy_seq == 7:
        signal = "buy_warning"
        signal_desc = "买7=逐步低吸"
    # 序列6预警
    elif sell_seq == 6:
        signal = "sell_warning"
        signal_desc = "卖6=风险显现"
    elif buy_seq == 6:
        signal = "buy_warning"
        signal_desc = "买6=分批布局"
    # 序列5以下
    elif sell_seq >= 4:
        signal = "sell_forming"
        signal_desc = f"下跌{sell_seq}，调整中"
    elif buy_seq >= 4:
        signal = "buy_forming"
        signal_desc = f"反弹{buy_seq}，蓄势中"
    elif sell_seq > 0:
        signal = "sell_forming"
        signal_desc = f"卖序列{sell_seq}"
    elif buy_seq > 0:
        signal = "buy_forming"
        signal_desc = f"买序列{buy_seq}"
    else:
        signal_desc = "无序列"

    return {
        "signal": signal,
        "signal_desc": signal_desc,
        "buy_seq": int(buy_seq),
        "sell_seq": int(sell_seq),
    }


if __name__ == "__main__":
    # 测试TD序列
    np.random.seed(42)
    close = np.cumsum(np.random.randn(30)) + 100
    data = {"date": pd.date_range("2024-01-01", periods=30), "close": close}
    df = pd.DataFrame(data)
    result = calculate_sequence(df)
    signal = get_sequence_signal(result)
    print(result[["date", "close", "seq9_buy", "seq9_sell"]].tail(15))
    print(signal)
