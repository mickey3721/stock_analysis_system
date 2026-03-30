"""
缠论分析模块 - 基于czsc库

参考：https://github.com/waditu/czsc

功能：
- 分型识别：顶分型/底分型
- 笔识别：基于缠论规则的笔
- 线段识别
- 中枢识别
- 背驰判定
- 买卖点信号
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

# 尝试导入czsc
CZSC_AVAILABLE = False
CZSC_ERROR = None

try:
    from czsc import traders, CzscSignals, RawBar

    CZSC_AVAILABLE = True
except ImportError as e:
    CZSC_ERROR = e
except Exception as e:
    CZSC_ERROR = e

if not CZSC_AVAILABLE and CZSC_ERROR:
    pass  # 静默处理，不在导入时打印
elif CZSC_AVAILABLE:
    pass  # 静默处理


class ChanlunAnalyzer:
    """缠论分析器（基于czsc库）"""

    def __init__(self, df: pd.DataFrame, symbol: str = "000001", use_czsc: bool = True):
        """
        初始化分析器

        Args:
            df: 包含OHLCV的DataFrame
            symbol: 股票代码
            use_czsc: 是否优先使用czsc库
        """
        self.df = df.copy()
        self.symbol = symbol.replace(".SH", "").replace(".SZ", "")
        self.use_czsc = use_czsc and CZSC_AVAILABLE
        self.results = {}
        self.czsc_bars = None

    def _prepare_czsc_bars(self) -> List:
        """准备czsc格式的K线数据"""
        bars = []
        for _, row in self.df.iterrows():
            bar = {
                "dt": row.get("date", pd.Timestamp.now()),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "vol": float(row.get("volume", 0)),
            }
            bars.append(bar)
        return bars

    def analyze_with_czsc(self) -> Dict:
        """使用czsc库进行缠论分析"""
        if not CZSC_AVAILABLE:
            return self._analyze_simple()

        try:
            if len(self.df) < 30:
                return self._analyze_simple()

            # 使用CZSC类
            from czsc import CZSC, Freq
            from czsc.traders.base import RawBar

            # 转换为RawBar列表
            bars = []
            for _, row in self.df.iterrows():
                rb = RawBar(
                    symbol=self.symbol,
                    freq=Freq.D,
                    dt=pd.Timestamp(row["date"]).to_pydatetime(),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    vol=float(row.get("volume", 0)),
                    amount=float(row.get("volume", 0)) * float(row["close"]),
                )
                bars.append(rb)

            # 创建CZSC分析对象
            czsc = CZSC(bars)

            # 获取分析结果
            result = {
                "fenxing": self._get_fenxing_status_cs(czsc),
                "bi": self._get_bi_status_cs(czsc),
                "zhongshu": self._get_zhongshu_status_cs(czsc),
                "beichi": self._get_beichi_status_cs(czsc),
                "signal": self._get_buy_sell_signal_cs(czsc),
            }

            return result

        except Exception as e:
            print(f"czsc分析失败: {e}, 使用简化版")
            return self._analyze_simple()

    def _get_fenxing_status_cs(self, czsc) -> str:
        """获取分型状态"""
        try:
            fx_list = czsc.fx_list
            if not fx_list:
                return "无分型"

            # 最近的分型
            last_fx = fx_list[-1]

            # 使用.value判断分型类型 (Mark枚举的value为"顶分型"或"底分型")
            if last_fx.mark.value == "顶分型":
                return "顶分型"
            elif last_fx.mark.value == "底分型":
                return "底分型"
            else:
                return "整理分型"

        except:
            return "无分型"

    def _get_bi_status_cs(self, czsc) -> str:
        """获取笔状态"""
        try:
            bi_list = czsc.bi_list
            if not bi_list:
                return "无笔"

            last_bi = bi_list[-1]

            # 使用.value判断笔方向 (Direction枚举的value为"向上"或"向下")
            if last_bi.direction.value == "向上":
                direction = "上涨笔"
            else:
                direction = "下跌笔"

            # 检查是否未完成笔
            if czsc.ubi:
                return f"{direction}(延伸中)"

            return f"{direction}(已确认)"

        except:
            return "笔分析中"

    def _get_zhongshu_status_cs(self, czsc) -> str:
        """获取中枢状态 - 通过笔重叠区域计算"""
        try:
            bi_list = czsc.bi_list
            if len(bi_list) < 3:
                return "中枢形成中"

            # 获取最近3笔，找出重叠区域
            recent_bis = bi_list[-3:]

            # 提取高低点
            highs = [(bi.high, bi.sdt, bi.edt) for bi in recent_bis]
            lows = [(bi.low, bi.sdt, bi.edt) for bi in recent_bis]

            # 检查是否有重叠（中枢形成条件）
            max_low = max(b[0] for b in lows)
            min_high = min(b[0] for b in highs)

            if max_low < min_high:
                return f"中枢形成({max_low:.2f}-{min_high:.2f})"
            else:
                return "中枢震荡中"

        except:
            return "中枢分析中"

    def _get_beichi_status_cs(self, czsc) -> str:
        """获取背驰状态"""
        try:
            bi_list = czsc.bi_list
            if len(bi_list) < 2:
                return "无背驰"

            last_bi = bi_list[-1]
            prev_bi = bi_list[-2]

            # 同方向才能比较背驰
            if last_bi.direction.value != prev_bi.direction.value:
                return "无背驰"

            # 使用power_price计算力度
            last_power = (
                last_bi.power_price
                if hasattr(last_bi, "power_price")
                else last_bi.power
            )
            prev_power = (
                prev_bi.power_price
                if hasattr(prev_bi, "power_price")
                else prev_bi.power
            )

            if last_bi.direction.value == "向上":
                # 上涨笔：创新高但力度减小 = 顶背驰
                if last_bi.high > prev_bi.high and last_power < prev_power * 0.8:
                    return f"顶背驰(力度减弱)"
                elif last_bi.high > prev_bi.high:
                    return "上涨延续(力度健康)"
                else:
                    return "上涨笔调整"
            else:
                # 下跌笔：创新低但力度减小 = 底背驰
                if last_bi.low < prev_bi.low and last_power < prev_power * 0.8:
                    return f"底背驰(力度减弱)"
                elif last_bi.low < prev_bi.low:
                    return "下跌延续(力度健康)"
                else:
                    return "下跌笔反弹"

        except Exception as e:
            return f"背驰分析中"

    def _get_buy_sell_signal_cs(self, czsc) -> str:
        """获取买卖信号"""
        try:
            # 综合判断：分型 + 笔方向 + 背驰
            fx_list = czsc.fx_list
            bi_list = czsc.bi_list

            if not bi_list:
                return "观望"

            last_bi = bi_list[-1]
            last_power = (
                last_bi.power_price
                if hasattr(last_bi, "power_price")
                else last_bi.power
            )

            # 笔方向判断
            if last_bi.direction.value == "向上":
                # 上涨笔：检查顶背驰
                if len(bi_list) >= 2:
                    prev_bi = bi_list[-2]
                    prev_power = (
                        prev_bi.power_price
                        if hasattr(prev_bi, "power_price")
                        else prev_bi.power
                    )
                    if last_bi.high > prev_bi.high and last_power < prev_power * 0.8:
                        return "减仓(顶背驰)"

                # 底分型出现时可考虑买入
                if fx_list:
                    last_fx = fx_list[-1]
                    if last_fx.mark.value == "底分型":
                        return "关注买入(底分型)"

                return "持有(上涨笔)"
            else:
                # 下跌笔：检查底背驰
                if len(bi_list) >= 2:
                    prev_bi = bi_list[-2]
                    prev_power = (
                        prev_bi.power_price
                        if hasattr(prev_bi, "power_price")
                        else prev_bi.power
                    )
                    if last_bi.low < prev_bi.low and last_power < prev_power * 0.8:
                        return "关注买入(底背驰)"

                # 顶分型出现时可考虑卖出
                if fx_list:
                    last_fx = fx_list[-1]
                    if last_fx.mark.value == "顶分型":
                        return "减仓(顶分型)"

                return "观望(下跌笔)"

        except:
            return "观望"

    def _get_fenxing_status(self, at) -> str:
        """获取分型状态"""
        try:
            # 最新分型
            if at.fenxs:
                fx = at.fenxs[-1]
                return fx.type.value if hasattr(fx, "type") else str(fx)
        except:
            pass
        return "none"

    def _get_bi_status(self, at) -> str:
        """获取笔状态"""
        try:
            if at.bi_list:
                bi = at.bi_list[-1]
                return bi.direction.value if hasattr(bi, "direction") else "unknown"
        except:
            pass
        return "none"

    def _get_zhongshu_status(self, at) -> Optional[Dict]:
        """获取中枢状态"""
        try:
            if at.zs_list:
                zs = at.zs_list[-1]
                return {
                    "high": zs.high if hasattr(zs, "high") else None,
                    "low": zs.low if hasattr(zs, "low") else None,
                }
        except:
            pass
        return None

    def _get_beichi_status(self, at) -> str:
        """获取背驰状态"""
        try:
            # 背驰判定逻辑
            if at.bi_list and len(at.bi_list) >= 2:
                bi1 = at.bi_list[-1]
                bi2 = at.bi_list[-2]
                # 简单判定：力度对比
                return "none"  # 简化处理
        except:
            pass
        return "none"

    def _get_buy_sell_signal(self, at) -> str:
        """获取买卖点信号"""
        try:
            # 基于最新笔和中枢判断
            if at.zs_list:
                return "none"  # 有中枢，观望
            if at.bi_list:
                bi = at.bi_list[-1]
                if bi.direction.value == "up":
                    return "buy"
                else:
                    return "sell"
        except:
            pass
        return "none"

    def _analyze_simple(self) -> Dict:
        """简化版缠论分析（不使用czsc）"""
        if len(self.df) < 10:
            return {
                "fenxing": "无分型",
                "bi": "无笔",
                "zhongshu": None,
                "beichi": "无背驰",
                "signal": "观望",
            }

        high = self.df["high"]
        low = self.df["low"]
        close = self.df["close"]

        # 分型识别
        fenxing = "无分型"
        for i in range(1, len(self.df) - 1):
            # 顶分型
            if (
                high.iloc[i] > high.iloc[i - 1]
                and high.iloc[i] > high.iloc[i + 1]
                and low.iloc[i] > low.iloc[i - 1]
                and low.iloc[i] > low.iloc[i + 1]
            ):
                fenxing = "顶分型"
                break
            # 底分型
            elif (
                low.iloc[i] < low.iloc[i - 1]
                and low.iloc[i] < low.iloc[i + 1]
                and high.iloc[i] < high.iloc[i - 1]
                and high.iloc[i] < high.iloc[i + 1]
            ):
                fenxing = "底分型"
                break

        # 笔方向（简化）
        ma5 = close.rolling(5).mean()
        ma10 = close.rolling(10).mean()
        bi = "上涨笔" if ma5.iloc[-1] > ma10.iloc[-1] else "下跌笔"

        # 背驰判定（MACD面积）
        beichi = "无背驰"
        if "macd" in self.df.columns:
            if len(self.df) >= 20:
                current_area = self.df["macd"].iloc[-10:].sum()
                prev_area = self.df["macd"].iloc[-20:-10].sum()
                if close.iloc[-1] > close.iloc[-20] and current_area < prev_area:
                    beichi = "顶背驰"
                elif close.iloc[-1] < close.iloc[-20] and current_area > prev_area:
                    beichi = "底背驰"

        # 买卖信号
        signal = "观望"
        if fenxing == "底分型":
            signal = "买入(底分型)"
        elif fenxing == "顶分型":
            signal = "卖出(顶分型)"

        return {
            "fenxing": fenxing,
            "bi": bi,
            "zhongshu": None,
            "beichi": beichi,
            "signal": signal,
            "czsc_used": False,
        }

    def analyze(self) -> Dict:
        """
        执行完整分析

        Returns:
            缠论分析结果
        """
        if self.use_czsc:
            try:
                return self.analyze_with_czsc()
            except Exception as e:
                print(f"czsc分析异常: {e}")
                return self._analyze_simple()
        else:
            return self._analyze_simple()


def analyze_chanlun(symbol: str, df: pd.DataFrame) -> Dict:
    """
    缠论分析入口函数

    Args:
        symbol: 股票代码
        df: K线数据

    Returns:
        分析结果
    """
    analyzer = ChanlunAnalyzer(df)
    return analyzer.analyze()


if __name__ == "__main__":
    # 测试
    import numpy as np

    np.random.seed(42)
    close = np.cumsum(np.random.randn(100)) + 100
    data = {
        "date": pd.date_range("2024-01-01", periods=100),
        "open": close - np.random.randn(100) * 2,
        "high": close + np.random.randn(100) * 2,
        "low": close - np.random.randn(100) * 2,
        "close": close,
        "volume": np.random.randint(1000000, 10000000, 100),
    }
    df = pd.DataFrame(data)

    # 添加MACD用于背驰判断
    df["ema12"] = df["close"].ewm(span=12).mean()
    df["ema26"] = df["close"].ewm(span=26).mean()
    df["dif"] = df["ema12"] - df["ema26"]
    df["dea"] = df["dif"].ewm(span=9).mean()
    df["macd"] = (df["dif"] - df["dea"]) * 2

    analyzer = ChanlunAnalyzer(df)
    result = analyzer.analyze()

    print("缠论分析结果:")
    for k, v in result.items():
        print(f"  {k}: {v}")
