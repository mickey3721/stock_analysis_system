"""
综合分析器 - 整合所有技术指标
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List

from indicators.ma import calculate_ma, get_ma_status
from indicators.trend_channel import calculate_trend_channel, get_channel_signal
from indicators.sequence import calculate_sequence, get_sequence_signal
from indicators.macd_quant import calculate_macd_quant, get_macd_structure
from indicators.chanlun import ChanlunAnalyzer
from indicators.support import calculate_support_resistance


class StockAnalyzer:
    """股票综合分析器"""

    def __init__(self, df: pd.DataFrame, symbol: str = "000001"):
        """
        初始化分析器

        Args:
            df: 包含OHLCV数据的DataFrame
            symbol: 股票代码
        """
        self.df = df.copy()
        self.symbol = symbol
        self.results = {}

    def analyze(self) -> Dict:
        """
        执行完整分析

        Returns:
            分析结果字典
        """
        # 1. 计算均线
        self.df = calculate_ma(self.df)
        ma_status = get_ma_status(self.df)

        # 2. 计算多空通道
        self.df = calculate_trend_channel(self.df)
        channel_signal = get_channel_signal(self.df)

        # 3. 计算九转序列
        self.df = calculate_sequence(self.df)
        sequence_signal = get_sequence_signal(self.df)

        # 4. 计算MACD定量结构
        self.df = calculate_macd_quant(self.df)
        macd_signal = get_macd_structure(self.df)

        # 5. 缠论分析
        chanlun_analyzer = ChanlunAnalyzer(self.df, symbol=self.symbol)
        chanlun_result = chanlun_analyzer.analyze()

        # 6. 支撑/阻力位
        support_resistance = calculate_support_resistance(
            self.df, ma_periods=[5, 26, 89], channel_data=channel_signal
        )

        # 7. 综合信号
        signal = self._generate_signal(
            channel_signal, sequence_signal, macd_signal, ma_status
        )

        # 组装结果
        last = self.df.iloc[-1]

        result = {
            "symbol": self.df.get("symbol", "unknown"),
            "period": "daily",
            "trade_date": str(last.get("date", ""))[:10],
            "close": round(last["close"], 2),
            # 均线
            "ma5": round(last.get("ma5"), 2) if pd.notna(last.get("ma5")) else None,
            "ma26": round(last.get("ma26"), 2) if pd.notna(last.get("ma26")) else None,
            "ma89": round(last.get("ma89"), 2) if pd.notna(last.get("ma89")) else None,
            "ma144": round(last.get("ma144"), 2)
            if pd.notna(last.get("ma144"))
            else None,
            "ma_trend": ma_status["trend"],
            # 多空通道
            "short_upper": round(last.get("short_upper"), 2),
            "short_lower": round(last.get("short_lower"), 2),
            "long_upper": round(last.get("long_upper"), 2),
            "long_lower": round(last.get("long_lower"), 2),
            "short_status": channel_signal["short_status"],
            "long_status": channel_signal["long_status"],
            "channel_signal": channel_signal["signal"],
            # 九转序列（TEXT类型）
            "seq9_buy": f"buy_{sequence_signal.get('buy_seq', 0)}",
            "seq9_sell": f"sell_{sequence_signal.get('sell_seq', 0)}",
            "seq_signal": sequence_signal["signal"],
            "seq_desc": sequence_signal["signal_desc"],
            # MACD
            "dif": round(last.get("dif"), 4),
            "dea": round(last.get("dea"), 4),
            "macd": round(last.get("macd"), 4),
            "macd_structure": macd_signal["structure"],
            "macd_desc": macd_signal["signal_desc"],
            # 缠论
            "fenxing": chanlun_result.get("fenxing"),
            "bi_direction": chanlun_result.get("bi"),
            "beichi": chanlun_result.get("beichi"),
            # 支撑/阻力
            "support_levels": support_resistance["support_levels"],
            "resistance_levels": support_resistance["resistance_levels"],
            # 综合信号
            "signal": signal["signal"],
            "signal_desc": signal["signal_desc"],
            "confidence": signal["confidence"],
            "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        self.results = result
        return result

    def _generate_signal(
        self,
        channel_signal: dict,
        sequence_signal: dict,
        macd_signal: dict,
        ma_status: dict,
    ) -> dict:
        """
        生成综合信号

        Args:
            channel_signal: 通道信号
            sequence_signal: 序列信号
            macd_signal: MACD信号
            ma_status: 均线状态

        Returns:
            综合信号
        """
        buy_score = 0
        sell_score = 0

        # 多空通道评分
        channel = channel_signal["signal"]
        if channel == "强烈做多":
            buy_score += 30
        elif channel == "谨慎做多":
            buy_score += 15
        elif channel == "强烈做空":
            sell_score += 30
        elif channel == "谨慎观望":
            sell_score += 10

        # 九转序列评分
        seq = sequence_signal["signal"]
        if seq == "buy_9":
            buy_score += 30
        elif seq == "buy_warning":
            buy_score += 15
        elif seq == "sell_9":
            sell_score += 30
        elif seq == "sell_warning":
            sell_score += 15

        # MACD结构评分
        macd = macd_signal["structure"]
        if macd == "bottom_100":
            buy_score += 25
        elif macd == "bottom_75":
            buy_score += 15
        elif macd == "top_100":
            sell_score += 25
        elif macd == "top_75":
            sell_score += 15

        # 均线评分
        ma_trend = ma_status["trend"]
        if ma_trend == "strong_up":
            buy_score += 15
        elif ma_trend == "up":
            buy_score += 10
        elif ma_trend == "strong_down":
            sell_score += 15
        elif ma_trend == "down":
            sell_score += 10

        # 综合判定
        total = buy_score + sell_score
        if total == 0:
            return {"signal": "hold", "signal_desc": "无明确信号", "confidence": 0}

        if buy_score > sell_score:
            confidence = min(buy_score / (buy_score + sell_score) * 100, 95)
            if buy_score >= 70:
                return {
                    "signal": "强烈买入",
                    "signal_desc": f"买入评分:{buy_score}",
                    "confidence": round(confidence, 1),
                }
            else:
                return {
                    "signal": "买入",
                    "signal_desc": f"买入评分:{buy_score}",
                    "confidence": round(confidence, 1),
                }
        else:
            confidence = min(sell_score / (buy_score + sell_score) * 100, 95)
            if sell_score >= 70:
                return {
                    "signal": "强烈卖出",
                    "signal_desc": f"卖出评分:{sell_score}",
                    "confidence": round(confidence, 1),
                }
            else:
                return {
                    "signal": "卖出",
                    "signal_desc": f"卖出评分:{sell_score}",
                    "confidence": round(confidence, 1),
                }


def analyze_stock(symbol: str, df: pd.DataFrame) -> Dict:
    """
    分析单只股票

    Args:
        symbol: 股票代码
        df: K线数据

    Returns:
        分析结果
    """
    df = df.copy()
    df["symbol"] = symbol

    analyzer = StockAnalyzer(df)
    return analyzer.analyze()


if __name__ == "__main__":
    import numpy as np

    np.random.seed(42)
    close = np.cumsum(np.random.randn(100)) + 100
    data = {
        "date": pd.date_range("2024-01-01", periods=100),
        "open": close - np.random.randn(100),
        "high": close + np.random.randn(100),
        "low": close - np.random.randn(100),
        "close": close,
        "volume": np.random.randint(1000000, 10000000, 100),
    }
    df = pd.DataFrame(data)

    analyzer = StockAnalyzer(df)
    result = analyzer.analyze()

    for k, v in result.items():
        if k not in ["support_levels", "resistance_levels"]:
            print(f"{k}: {v}")
