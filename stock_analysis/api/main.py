# -*- coding: utf-8 -*-
"""
股票智能分析系统 - FastAPI后端
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import logging
import akshare as ak

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

from data.collector import DataCollector
from analysis.analyzer import StockAnalyzer
from config import SYMBOLS

app = FastAPI(title="股票智能分析API", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

collector = DataCollector()


class StockInfo(BaseModel):
    symbol: str
    name: str
    category: str


class KLineData(BaseModel):
    dates: List[str]
    opens: List[float]
    highs: List[float]
    lows: List[float]
    closes: List[float]
    volumes: List[float]


class LevelInfo(BaseModel):
    level: float
    type: str


class AnalysisResult(BaseModel):
    symbol: str
    name: str
    close: float
    change_pct: float
    ma5: Optional[float] = None
    ma26: Optional[float] = None
    ma89: Optional[float] = None
    ma144: Optional[float] = None
    channel_signal: str
    seq_desc: str
    macd_desc: str
    fenxing: str
    bi_status: str
    beichi: str
    signal: str
    confidence: int
    support_levels: List[LevelInfo] = []
    resistance_levels: List[LevelInfo] = []


@app.get("/")
def root():
    return {"message": "股票智能分析API", "version": "1.0.0"}


@app.get("/stocks", response_model=List[StockInfo])
def get_stocks():
    """获取股票列表"""
    stocks = []
    for category, symbols in SYMBOLS.items():
        for code, name in symbols.items():
            stocks.append(StockInfo(symbol=code, name=name, category=category))
    return stocks


@app.get("/kline/{symbol}", response_model=KLineData)
def get_kline(symbol: str, period: str = Query("daily")):
    """获取K线数据"""
    try:
        if period == "daily":
            df = collector.get_stock_daily(symbol, period="daily")
        else:
            p = int(period.replace("min", ""))
            df = collector.get_minute(symbol, p)

        if df.empty:
            return KLineData(
                dates=[], opens=[], highs=[], lows=[], closes=[], volumes=[]
            )

        return KLineData(
            dates=df["date"].dt.strftime("%Y-%m-%d").tolist(),
            opens=df["open"].tolist(),
            highs=df["high"].tolist(),
            lows=df["low"].tolist(),
            closes=df["close"].tolist(),
            volumes=df["volume"].tolist(),
        )
    except Exception as e:
        return KLineData(dates=[], opens=[], highs=[], lows=[], closes=[], volumes=[])


@app.get("/analyze/{symbol}", response_model=AnalysisResult)
def analyze_stock(symbol: str, period: str = Query("daily")):
    """分析股票"""
    try:
        # 获取数据
        if period == "daily":
            df = collector.get_stock_daily(symbol, period="daily")
        else:
            p = int(period.replace("min", ""))
            df = collector.get_minute(symbol, p)

        if df.empty:
            return None

        # 分析
        analyzer = StockAnalyzer(df, symbol=symbol)
        result = analyzer.analyze()

        # 获取股票名称
        name = symbol
        for category, symbols in SYMBOLS.items():
            if symbol in symbols:
                name = symbols[symbol]
                break

        # 计算涨跌幅
        if len(df) >= 2:
            change_pct = (
                (df["close"].iloc[-1] - df["close"].iloc[-2]) / df["close"].iloc[-2]
            ) * 100
        else:
            change_pct = 0

        def to_float(v):
            if v is None:
                return None
            try:
                return float(v)
            except:
                return None

        def to_list(levels):
            if not levels:
                return []
            result = []
            for item in levels:
                if isinstance(item, dict) and "level" in item:
                    result.append(
                        {
                            "level": to_float(item.get("level")),
                            "type": item.get("type", ""),
                        }
                    )
                elif isinstance(item, dict):
                    result.append(item)
            return result

        return AnalysisResult(
            symbol=symbol,
            name=name,
            close=to_float(result.get("close")),
            change_pct=round(to_float(change_pct), 2),
            ma5=to_float(result.get("ma5")),
            ma26=to_float(result.get("ma26")),
            ma89=to_float(result.get("ma89")),
            ma144=to_float(result.get("ma144")),
            channel_signal=result.get("channel_signal", ""),
            seq_desc=result.get("seq_desc", ""),
            macd_desc=result.get("macd_desc", ""),
            fenxing=result.get("fenxing", ""),
            bi_status=result.get("bi_direction", ""),
            beichi=result.get("beichi", ""),
            signal=result.get("signal", ""),
            confidence=int(result.get("confidence", 0)),
            support_levels=to_list(result.get("support_levels", [])),
            resistance_levels=to_list(result.get("resistance_levels", [])),
        )
    except Exception as e:
        print(f"分析失败: {e}")
        return None


@app.get("/realtime/{symbol}")
def get_realtime(symbol: str):
    """获取实时行情"""
    try:
        return collector.get_realtime(symbol)
    except Exception as e:
        return {}


@app.get("/intraday/{symbol}")
def get_intraday(symbol: str):
    """获取分时图数据"""
    import akshare as ak_module

    try:
        code = symbol.replace(".SH", "").replace(".SZ", "")

        # 获取分时数据
        df = ak_module.stock_zh_a_hist_min_em(symbol=code, period="1", adjust="qfq")

        if df is not None and len(df) > 0:
            df = df.tail(240)
            times = df.iloc[:, 0].tolist()
            prices = [float(x) for x in df.iloc[:, 2].tolist()]
            volumes = [float(x) for x in df.iloc[:, 5].tolist()]

            return {
                "symbol": symbol,
                "times": times,
                "prices": prices,
                "volumes": volumes,
            }

        return {"symbol": symbol, "times": [], "prices": [], "volumes": []}
    except Exception as e:
        logger.warning(f"分时数据失败: {e}")
        return {"symbol": symbol, "times": [], "prices": [], "volumes": []}
    except Exception as e:
        print(f"DEBUG ERROR: {traceback.format_exc()}", flush=True)
        return {"symbol": symbol, "times": [], "prices": [], "volumes": []}
    except Exception as e:
        return {"symbol": symbol, "times": [], "prices": [], "volumes": []}
    except Exception as e:
        print(f"[DEBUG] 外部异常: {traceback.format_exc()}")
        return {"symbol": symbol, "times": [], "prices": [], "volumes": []}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
