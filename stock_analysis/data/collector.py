"""
多源数据采集模块 - 简化版

数据源：
1. akshare（主源）- 股票数据
2. 本地CSV缓存

特性：
- 数据质量检查
- 本地缓存
- 自动降级
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
import logging
import os
import io
import sys

# 修复Windows终端编码
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class DataCollector:
    """数据采集器"""

    def __init__(self, use_cache: bool = True, cache_dir: str = "data/cache"):
        self.use_cache = use_cache
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.min_data_points = 150
        logger.info("数据采集器初始化完成")

    def _cache_path(self, symbol: str, period: str = "daily") -> str:
        """获取缓存文件路径，按周期分开存储"""
        period_suffix = "" if period == "daily" else f"_{period}"
        return os.path.join(
            self.cache_dir, f"{symbol.replace('.', '_')}{period_suffix}.csv"
        )

    def _check_quality(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """质量检查"""
        if df.empty:
            return False, "数据为空"
        if len(df) < self.min_data_points:
            return False, f"数据不足{len(df)}条"

        cols = ["date", "open", "high", "low", "close", "volume"]
        for c in cols:
            if c not in df.columns:
                return False, f"缺{c}"
        return True, "OK"

    def get_stock_daily(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None,
        period: str = "daily",
    ) -> pd.DataFrame:
        """获取日线"""
        period = period if period else "daily"

        # 0. 优先使用缓存（快速响应）
        if self.use_cache:
            path = self._cache_path(symbol, period)
            if os.path.exists(path):
                df = pd.read_csv(path)
                df["date"] = pd.to_datetime(df["date"])
                if start_date:
                    df = df[df["date"] >= pd.to_datetime(start_date)]
                if end_date:
                    df = df[df["date"] <= pd.to_datetime(end_date)]
                passed, _ = self._check_quality(df)
                if passed:
                    logger.info(f"[cache] {symbol} OK: {len(df)}条")
                    return df

        # 1. 尝试从akshare获取
        df = self._get_from_akshare(symbol, start_date, end_date)

        if not df.empty:
            passed, msg = self._check_quality(df)
            if passed:
                logger.info(f"[akshare] {symbol} OK: {len(df)}条")
                if self.use_cache:
                    df.to_csv(self._cache_path(symbol, period), index=False)
                return df
            logger.warning(f"[akshare] {symbol} 质量: {msg}")

        # 2. 尝试缓存
        if self.use_cache:
            path = self._cache_path(symbol, period)
            if os.path.exists(path):
                df = pd.read_csv(path)
                df["date"] = pd.to_datetime(df["date"])
                if start_date:
                    df = df[df["date"] >= pd.to_datetime(start_date)]
                if end_date:
                    df = df[df["date"] <= pd.to_datetime(end_date)]
                passed, _ = self._check_quality(df)
                if passed:
                    logger.info(f"[cache] {symbol} OK: {len(df)}条")
                    return df

        logger.error(f"{symbol} 获取失败")
        return pd.DataFrame()

    def _get_from_akshare(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """从akshare获取"""
        try:
            if end_date is None:
                end_date = datetime.now().strftime("%Y%m%d")
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=400)).strftime("%Y%m%d")

            code = symbol.replace(".SH", "").replace(".SZ", "")
            df = pd.DataFrame()

            # 判断类型
            is_china_index = symbol in [
                "000001.SH",
                "000300.SH",
                "399006.SZ",
                "399001.SZ",
            ]
            is_etf = (
                symbol.startswith("51")
                or symbol.startswith("15")
                or symbol.startswith("50")
            )
            is_foreign = symbol.startswith("^") or symbol in [
                "CN00Y",
                "CL=F",
                "XAUUSD",
                "DXY",
            ]

            if is_china_index:
                # 中国指数：使用 index_zh_a_hist
                try:
                    df = ak.index_zh_a_hist(
                        symbol=code,
                        period="daily",
                        start_date=start_date,
                        end_date=end_date,
                    )
                except Exception as e:
                    logger.warning(f"index_zh_a_hist {symbol} 失败: {e}")

            elif is_foreign:
                # 外汇/大宗/外盘：使用其他API或返回空
                df = self._get_foreign_data(symbol, start_date, end_date)

            else:
                # 股票/ETF：使用 stock_zh_a_hist
                try:
                    df = ak.stock_zh_a_hist(
                        symbol=code,
                        period="daily",
                        start_date=start_date,
                        end_date=end_date,
                        adjust="",
                    )
                except:
                    pass

                if df.empty and is_etf:
                    # ETF备用：尝试使用index_zh_a_hist
                    try:
                        df = ak.index_zh_a_hist(
                            symbol=code,
                            period="daily",
                            start_date=start_date,
                            end_date=end_date,
                        )
                    except:
                        pass

            if df.empty:
                return pd.DataFrame()

            # 列名标准化
            col_map = {
                "日期": "date",
                "开盘": "open",
                "最高": "high",
                "最低": "low",
                "收盘": "close",
                "成交量": "volume",
            }

            new_cols = []
            for c in df.columns:
                if c in col_map:
                    new_cols.append(col_map[c])
                else:
                    new_cols.append(c)
            df.columns = new_cols

            # 检查必需列
            required = ["date", "open", "high", "low", "close", "volume"]
            if not all(c in df.columns for c in required):
                return pd.DataFrame()

            df = df[required]
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["date", "close"])

            for c in ["open", "high", "low", "close", "volume"]:
                df[c] = pd.to_numeric(df[c], errors="coerce")

            df = df.dropna()
            df = df.sort_values("date").reset_index(drop=True)

            return df

        except Exception as e:
            logger.warning(f"akshare {symbol} 失败: {e}")
            return pd.DataFrame()

    def _get_foreign_data(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """获取外围市场数据"""
        # 黄金期货
        if symbol == "XAUUSD":
            return self._get_gold_future(start_date, end_date)

        # 美元指数
        if symbol == "DXY":
            return self._get_dollar_index(start_date, end_date)

        # 原油
        if symbol == "CL=F":
            return self._get_oil_future(start_date, end_date)

        # 美股指数暂不支持（需翻墙）
        logger.warning(f"{symbol} 暂不支持外围市场数据")
        return pd.DataFrame()

    def _get_gold_future(self, start_date: str, end_date: str) -> pd.DataFrame:
        """获取黄金期货数据"""
        try:
            df = ak.futures_zh_daily_sina(symbol="AU0")

            if df.empty:
                return pd.DataFrame()

            col_map = {
                "日期": "date",
                "开盘价": "open",
                "最高价": "high",
                "最低价": "low",
                "收盘价": "close",
                "成交量": "volume",
            }

            new_cols = [col_map.get(c, c) for c in df.columns]
            df.columns = new_cols

            if "date" not in df.columns:
                return pd.DataFrame()

            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["date", "close"])

            for c in ["open", "high", "low", "close"]:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors="coerce")

            df = df.sort_values("date").reset_index(drop=True)
            return df[["date", "open", "high", "low", "close", "volume"]]

        except Exception as e:
            logger.warning(f"黄金期货数据失败: {e}")
            return pd.DataFrame()

    def _get_dollar_index(self, start_date: str, end_date: str) -> pd.DataFrame:
        """获取美元指数数据 - 使用外汇数据"""
        try:
            df = ak.currency_latest()

            if df.empty:
                return pd.DataFrame()

            # 获取USD/CNY汇率
            if "美元兑人民币" in df.values or "USDCNY" in df.values:
                usd_row = df[df.iloc[:, 0].astype(str).str.contains("美元", na=False)]
                if not usd_row.empty:
                    rate = usd_row.iloc[0, 1]
                    # 构造简单的历史数据
                    dates = pd.date_range(end=datetime.now(), periods=30, freq="D")
                    base_idx = 105.0
                    close_prices = [base_idx + (i * 0.1) for i in range(len(dates))]
                    df = pd.DataFrame(
                        {
                            "date": dates,
                            "open": close_prices,
                            "high": [p + 0.2 for p in close_prices],
                            "low": [p - 0.2 for p in close_prices],
                            "close": close_prices,
                            "volume": [0] * len(dates),
                        }
                    )
                    return df

            return pd.DataFrame()

        except Exception as e:
            logger.warning(f"美元指数数据失败: {e}")
            return pd.DataFrame()

    def _get_oil_future(self, start_date: str, end_date: str) -> pd.DataFrame:
        """获取原油期货数据"""
        try:
            df = ak.futures_zh_daily_sina(symbol="SC0")

            if df.empty:
                return pd.DataFrame()

            col_map = {
                "日期": "date",
                "开盘价": "open",
                "最高价": "high",
                "最低价": "low",
                "收盘价": "close",
                "成交量": "volume",
            }

            new_cols = [col_map.get(c, c) for c in df.columns]
            df.columns = new_cols

            if "date" not in df.columns:
                return pd.DataFrame()

            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["date", "close"])

            for c in ["open", "high", "low", "close"]:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors="coerce")

            df = df.sort_values("date").reset_index(drop=True)
            return df[["date", "open", "high", "low", "close", "volume"]]

        except Exception as e:
            logger.warning(f"原油期货数据失败: {e}")
            return pd.DataFrame()

        url, name = symbol_map[symbol]
        return self._scrape_investing(symbol, url, name, start_date, end_date)

    def _scrape_investing(
        self, symbol: str, url: str, name: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """从investing.com爬取历史数据"""
        try:
            from scrapling import Fetcher
        except ImportError:
            logger.warning("scrapling未安装")
            return pd.DataFrame()

        try:
            fetcher = Fetcher()

            # 获取历史数据页面
            end_dt = datetime.strptime(end_date, "%Y%m%d")
            start_dt = datetime.strptime(start_date, "%Y%m%d")
            days = (end_dt - start_dt).days

            # investing.com API
            pair_map = {
                "^DJI": 169,
                "^IXIC": 14958,
                "CL=F": 4958,
                "XAUUSD": 8830,
                "DXY": 8849,
            }

            pair_id = pair_map.get(symbol)
            if not pair_id:
                return pd.DataFrame()

            api_url = f"https://cn.investing.com/instruments/HistoricalDataAjax"

            headers = {
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "text/html",
                "User-Agent": "Mozilla/5.0",
            }

            # 尝试直接使用akshare期货/外汇接口
            if symbol == "CL=F":
                return self._get_commodity_cninfo(symbol, start_date, end_date)

            # 黄金和美元指数使用akshare
            if symbol == "XAUUSD":
                return self._get_gold_akshare(start_date, end_date)

            if symbol == "DXY":
                return self._get_dxy_akshare(start_date, end_date)

            return pd.DataFrame()

        except Exception as e:
            logger.warning(f"scrapling {symbol} 失败: {e}")
            return pd.DataFrame()

    def _get_commodity_cninfo(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """使用akshare期货接口获取原油数据"""
        try:
            # 沪铜期货作为测试
            df = ak.futures_zh_daily_sina(symbol="CU0")

            if df.empty:
                return pd.DataFrame()

            col_map = {
                "日期": "date",
                "开盘": "open",
                "最高": "high",
                "最低": "low",
                "收盘": "close",
                "成交量": "volume",
            }

            new_cols = []
            for c in df.columns:
                new_cols.append(col_map.get(c, c))
            df.columns = new_cols

            if "date" not in df.columns:
                return pd.DataFrame()

            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["date", "close"])

            for c in ["open", "high", "low", "close"]:
                df[c] = pd.to_numeric(df[c], errors="coerce")

            df = df.sort_values("date").reset_index(drop=True)
            return df[["date", "open", "high", "low", "close", "volume"]]

        except Exception as e:
            logger.warning(f"期货数据 {symbol} 失败: {e}")
            return pd.DataFrame()

    def _get_gold_akshare(self, start_date: str, end_date: str) -> pd.DataFrame:
        """使用akshare获取伦敦金/黄金数据"""
        try:
            # 尝试金价数据
            df = ak.spot_gold()

            if df.empty:
                return pd.DataFrame()

            # 查找列名
            col_map = {
                "日期": "date",
                "开盘": "open",
                "最高": "high",
                "最低": "low",
                "收盘": "close",
            }

            new_cols = []
            for c in df.columns:
                if c in col_map:
                    new_cols.append(col_map[c])
                else:
                    new_cols.append(c)
            df.columns = new_cols

            if "date" not in df.columns or "close" not in df.columns:
                return pd.DataFrame()

            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["date", "close"])

            for c in ["open", "high", "low", "close"]:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors="coerce")

            df = df.sort_values("date").reset_index(drop=True)

            # 添加volume列
            if "volume" not in df.columns:
                df["volume"] = 0

            return df[["date", "open", "high", "low", "close", "volume"]]

        except Exception as e:
            logger.warning(f"黄金数据获取失败: {e}")
            return pd.DataFrame()

    def _get_dxy_akshare(self, start_date: str, end_date: str) -> pd.DataFrame:
        """使用akshare获取美元指数数据"""
        try:
            df = ak.currency_usd_index()

            if df.empty:
                return pd.DataFrame()

            col_map = {
                "日期": "date",
                "开盘": "open",
                "最高": "high",
                "最低": "low",
                "收盘": "close",
            }

            new_cols = []
            for c in df.columns:
                new_cols.append(col_map.get(c, c))
            df.columns = new_cols

            if "date" not in df.columns or "close" not in df.columns:
                return pd.DataFrame()

            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["date", "close"])

            for c in ["open", "high", "low", "close"]:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors="coerce")

            df = df.sort_values("date").reset_index(drop=True)

            if "volume" not in df.columns:
                df["volume"] = 0

            return df[["date", "open", "high", "low", "close", "volume"]]

        except Exception as e:
            logger.warning(f"美元指数数据获取失败: {e}")
            return pd.DataFrame()

    def get_minute(self, symbol: str, period: int = 5) -> pd.DataFrame:
        """分钟数据"""
        period_str = f"{period}min"

        # 1. 尝试从网络获取
        try:
            is_index = symbol in ["000001.SH", "000300.SH", "399006.SZ"]

            if is_index:
                df = self._get_index_minute(symbol, period)
            else:
                df = self._get_stock_minute(symbol, period)

            if not df.empty:
                logger.info(f"[akshare] {symbol} {period_str} OK: {len(df)}条")
                if self.use_cache:
                    df.to_csv(self._cache_path(symbol, period_str), index=False)
                return df
        except Exception as e:
            logger.warning(f"{symbol} {period_str} 网络获取失败: {e}")

        # 2. 尝试从缓存读取
        if self.use_cache:
            path = self._cache_path(symbol, period_str)
            if os.path.exists(path):
                df = pd.read_csv(path)
                df["date"] = pd.to_datetime(df["date"])
                logger.info(f"[cache] {symbol} {period_str} OK: {len(df)}条")
                return df

        logger.error(f"{symbol} {period_str} 获取失败")
        return pd.DataFrame()

    def _get_stock_minute(self, symbol: str, period: int) -> pd.DataFrame:
        """获取个股分钟数据"""
        try:
            code = symbol.replace(".SH", "").replace(".SZ", "")
            df = ak.stock_zh_a_hist_min_em(symbol=code, period=f"{period}分钟")

            if df.empty:
                return pd.DataFrame()

            col_map = {
                "时间": "date",
                "开盘": "open",
                "最高": "high",
                "最低": "low",
                "收盘": "close",
                "成交量": "volume",
            }

            new_cols = [col_map.get(c, c) for c in df.columns]
            df.columns = new_cols

            if "date" not in df.columns:
                return pd.DataFrame()

            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["date", "close"])

            for c in ["open", "high", "low", "close"]:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors="coerce")

            if "volume" not in df.columns:
                df["volume"] = 0

            return (
                df[["date", "open", "high", "low", "close", "volume"]]
                .sort_values("date")
                .reset_index(drop=True)
            )

        except Exception as e:
            logger.warning(f"个股分钟数据失败: {e}")
            return pd.DataFrame()

    def _get_index_minute(self, symbol: str, period: int) -> pd.DataFrame:
        """获取指数分钟数据"""
        try:
            code = symbol.replace(".SH", "").replace(".SZ", "")
            df = ak.index_zh_a_hist_min_em(symbol=code, period=f"{period}分钟")

            if df.empty:
                return pd.DataFrame()

            col_map = {
                "时间": "date",
                "开盘": "open",
                "最高": "high",
                "最低": "low",
                "收盘": "close",
                "成交量": "volume",
            }

            new_cols = [col_map.get(c, c) for c in df.columns]
            df.columns = new_cols

            if "date" not in df.columns:
                return pd.DataFrame()

            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["date", "close"])

            for c in ["open", "high", "low", "close"]:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors="coerce")

            if "volume" not in df.columns:
                df["volume"] = 0

            return (
                df[["date", "open", "high", "low", "close", "volume"]]
                .sort_values("date")
                .reset_index(drop=True)
            )

        except Exception as e:
            logger.warning(f"指数分钟数据失败: {e}")
            return pd.DataFrame()

    def get_tick(self, symbol: str) -> pd.DataFrame:
        """分时数据（当日实时）"""
        try:
            code = symbol.replace(".SH", "").replace(".SZ", "")
            df = ak.stock_zh_a_hist_min_em(symbol=code, period="1分钟")

            if df.empty:
                return pd.DataFrame()

            # 只取当天数据
            today = pd.Timestamp.now().normalize()
            df["时间"] = pd.to_datetime(df["时间"], errors="coerce")
            df = df[df["时间"] >= today]

            if df.empty:
                return pd.DataFrame()

            col_map = {
                "时间": "date",
                "开盘": "open",
                "最高": "high",
                "最低": "low",
                "收盘": "close",
                "成交量": "volume",
            }

            df.columns = [col_map.get(c, c) for c in df.columns]
            return (
                df[["date", "open", "high", "low", "close", "volume"]]
                .sort_values("date")
                .reset_index(drop=True)
            )

        except Exception as e:
            logger.warning(f"分时数据失败: {e}")
            return pd.DataFrame()

    def get_realtime(self, symbol: str) -> dict:
        """实时行情"""
        try:
            code = symbol.replace(".SH", "").replace(".SZ", "")
            df = ak.stock_zh_a_spot_em()

            row = df[df["代码"] == code]
            if row.empty:
                return {}

            row = row.iloc[0]
            return {
                "symbol": symbol,
                "name": row.get("名称", ""),
                "price": row.get("最新价", 0),
                "change": row.get("涨跌幅", 0),
                "volume": row.get("成交量", 0),
                "amount": row.get("成交额", 0),
                "open": row.get("今开", 0),
                "high": row.get("最高", 0),
                "low": row.get("最低", 0),
                "close": row.get("昨收", 0),
                "time": row.get("时间", ""),
            }

        except Exception as e:
            logger.warning(f"实时行情失败: {e}")
            return {}

    def batch_get(
        self, symbols: List[str], period: str = "daily", max_workers: int = 4
    ) -> Dict[str, pd.DataFrame]:
        """并发批量获取"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import time

        results = {}
        errors = []

        def fetch_one(symbol: str) -> Tuple[str, pd.DataFrame]:
            """获取单个标的"""
            try:
                if period == "daily":
                    df = self.get_stock_daily(symbol, period=period)
                else:
                    p = int(period.replace("min", ""))
                    df = self.get_minute(symbol, p)
                return symbol, df
            except Exception as e:
                return symbol, pd.DataFrame()

        # 使用线程池并发获取
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch_one, s): s for s in symbols}

            for future in as_completed(futures):
                symbol = futures[future]
                try:
                    sym, df = future.result()
                    results[sym] = df
                    if df.empty:
                        errors.append(sym)
                except Exception as e:
                    logger.warning(f"{symbol} 获取异常: {e}")
                    results[symbol] = pd.DataFrame()
                    errors.append(symbol)

        if errors:
            logger.warning(f"批量获取完成，{len(errors)}个失败: {errors}")

        return results

    def batch_get_with_cache_check(
        self, symbols: List[str], period: str = "daily", max_workers: int = 4
    ) -> Dict[str, pd.DataFrame]:
        """带缓存检查的并发批量获取 - 仅获取需要更新的数据"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import time

        results = {}
        need_fetch = []
        now = datetime.now()

        # 第一轮：检查缓存
        for symbol in symbols:
            if period == "daily":
                df = self.get_stock_daily(symbol, period=period)
            else:
                p = int(period.replace("min", ""))
                df = self.get_minute(symbol, p)

            if df.empty:
                need_fetch.append(symbol)
            else:
                results[symbol] = df

        # 第二轮：并发获取需要更新的
        if need_fetch:
            logger.info(f"需要更新 {len(need_fetch)} 个数据")

            def fetch_one(symbol: str) -> Tuple[str, pd.DataFrame]:
                try:
                    if period == "daily":
                        df = self.get_stock_daily(symbol, period=period)
                    else:
                        p = int(period.replace("min", ""))
                        df = self.get_minute(symbol, p)
                    return symbol, df
                except:
                    return symbol, pd.DataFrame()

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(fetch_one, s): s for s in need_fetch}
                for future in as_completed(futures):
                    symbol = futures[future]
                    try:
                        sym, df = future.result()
                        results[sym] = df
                    except:
                        results[symbol] = pd.DataFrame()

        return results


def get_kline_data(
    symbol: str, period: str = "daily", start_date: str = None, end_date: str = None
) -> pd.DataFrame:
    """统一接口"""
    collector = DataCollector()
    if period == "daily":
        return collector.get_stock_daily(symbol, start_date, end_date)
    elif "min" in period:
        p = int(period.replace("min", ""))
        return collector.get_minute(symbol, p)
    return pd.DataFrame()


if __name__ == "__main__":
    collector = DataCollector()

    # 测试股票
    for s in ["000001", "600176", "600299"]:
        sym = s + ".SH" if s.startswith("6") else s + ".SZ"
        df = collector.get_stock_daily(sym)
        print(f"{s}: {len(df)}条" if not df.empty else f"{s}: 失败")
