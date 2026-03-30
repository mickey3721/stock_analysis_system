"""
数据存储模块 - SQLite数据库操作
"""

import sqlite3
import pandas as pd
from datetime import datetime
from typing import Optional, List
import json
import os


class Database:
    """数据库操作类"""

    def __init__(self, db_path: str = "data/stock.db"):
        self.db_path = db_path
        self._ensure_dir()
        self._init_db()

    def _ensure_dir(self):
        """确保目录存在"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _get_conn(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """初始化数据库表"""
        conn = self._get_conn()
        cursor = conn.cursor()

        # K线数据表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                trade_date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                amount REAL,
                period TEXT DEFAULT 'daily',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, trade_date, period)
            )
        """)

        # 综合分析结果表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_result (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                period TEXT NOT NULL,
                trade_date TEXT,
                ma5 REAL, ma26 REAL, ma89 REAL, ma144 REAL,
                short_upper REAL, short_lower REAL,
                long_upper REAL, long_lower REAL,
                short_status TEXT, long_status TEXT,
                channel_signal TEXT,
                seq9_buy TEXT, seq9_sell TEXT,
                dif REAL, dea REAL, macd REAL,
                macd_structure TEXT,
                support_levels TEXT,
                resistance_levels TEXT,
                signal TEXT,
                confidence REAL,
                analysis_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, period, trade_date)
            )
        """)

        # 交易记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                action TEXT,
                price REAL,
                quantity INTEGER,
                amount REAL,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 持仓记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE,
                quantity INTEGER,
                avg_cost REAL,
                current_price REAL,
                market_value REAL,
                profit_loss REAL,
                profit_pct REAL,
                stop_loss_price REAL,
                take_profit_price REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 风控日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS risk_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                symbol TEXT,
                action TEXT,
                price REAL,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 任务跟踪表 - 用于断点续传
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_tracker (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                period TEXT DEFAULT 'daily',
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(task_name, symbol, period)
            )
        """)

        conn.commit()
        conn.close()

    def save_kline(self, df: pd.DataFrame, symbol: str, period: str = "daily"):
        """保存K线数据"""
        if df.empty:
            return

        conn = self._get_conn()
        df = df.copy()
        df["symbol"] = symbol
        df["period"] = period

        for _, row in df.iterrows():
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO kline
                (symbol, trade_date, open, high, low, close, volume, amount, period)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    symbol,
                    str(row["date"])[:10],
                    row.get("open"),
                    row.get("high"),
                    row.get("low"),
                    row.get("close"),
                    row.get("volume"),
                    row.get("amount"),
                    period,
                ),
            )

        conn.commit()
        conn.close()

    def get_kline(
        self, symbol: str, period: str = "daily", limit: int = 300
    ) -> pd.DataFrame:
        """获取K线数据"""
        conn = self._get_conn()
        df = pd.read_sql(
            f"""
            SELECT * FROM kline
            WHERE symbol = ? AND period = ?
            ORDER BY trade_date DESC
            LIMIT ?
        """,
            conn,
            params=(symbol, period, limit),
        )
        conn.close()
        return df

    def save_analysis(self, data: dict):
        """保存分析结果"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO analysis_result
            (symbol, period, trade_date, ma5, ma26, ma89, ma144,
             short_upper, short_lower, long_upper, long_lower,
             short_status, long_status, channel_signal,
             seq9_buy, seq9_sell, dif, dea, macd, macd_structure,
             support_levels, resistance_levels, signal, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                data.get("symbol"),
                data.get("period"),
                data.get("trade_date"),
                data.get("ma5"),
                data.get("ma26"),
                data.get("ma89"),
                data.get("ma144"),
                data.get("short_upper"),
                data.get("short_lower"),
                data.get("long_upper"),
                data.get("long_lower"),
                data.get("short_status"),
                data.get("long_status"),
                data.get("channel_signal"),
                data.get("seq9_buy"),
                data.get("seq9_sell"),
                data.get("dif"),
                data.get("dea"),
                data.get("macd"),
                data.get("macd_structure"),
                json.dumps(data.get("support_levels", [])),
                json.dumps(data.get("resistance_levels", [])),
                data.get("signal"),
                data.get("confidence"),
            ),
        )

        conn.commit()
        conn.close()

    def get_analysis(self, symbol: str, period: str = "daily") -> dict:
        """获取最新分析结果"""
        conn = self._get_conn()
        df = pd.read_sql(
            f"""
            SELECT * FROM analysis_result
            WHERE symbol = ? AND period = ?
            ORDER BY trade_date DESC
            LIMIT 1
        """,
            conn,
            params=(symbol, period),
        )
        conn.close()

        if df.empty:
            return {}
        return df.iloc[0].to_dict()

    def save_trade(self, trade: dict):
        """保存交易记录"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO trades (symbol, action, price, quantity, amount, reason)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                trade.get("symbol"),
                trade.get("action"),
                trade.get("price"),
                trade.get("quantity"),
                trade.get("amount"),
                trade.get("reason"),
            ),
        )

        conn.commit()
        conn.close()

    def save_position(self, position: dict):
        """保存持仓"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO positions
            (symbol, quantity, avg_cost, current_price, market_value,
             profit_loss, profit_pct, stop_loss_price, take_profit_price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                position.get("symbol"),
                position.get("quantity"),
                position.get("avg_cost"),
                position.get("current_price"),
                position.get("market_value"),
                position.get("profit_loss"),
                position.get("profit_pct"),
                position.get("stop_loss_price"),
                position.get("take_profit_price"),
            ),
        )

        conn.commit()
        conn.close()

    def get_positions(self) -> pd.DataFrame:
        """获取所有持仓"""
        conn = self._get_conn()
        df = pd.read_sql("SELECT * FROM positions", conn)
        conn.close()
        return df

    def log_risk_event(self, event: dict):
        """记录风控日志"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO risk_logs (event_type, symbol, action, price, reason)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                event.get("event_type"),
                event.get("symbol"),
                event.get("action"),
                event.get("price"),
                event.get("reason"),
            ),
        )

        conn.commit()
        conn.close()

    def init_task(self, task_name: str, symbols: List[str], periods: List[str] = None):
        """初始化任务追踪"""
        if periods is None:
            periods = ["daily"]

        conn = self._get_conn()
        cursor = conn.cursor()

        for symbol in symbols:
            for period in periods:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO task_tracker (task_name, symbol, period, status)
                    VALUES (?, ?, ?, 'pending')
                """,
                    (task_name, symbol, period),
                )

        conn.commit()
        conn.close()

    def update_task_status(self, task_name: str, symbol: str, period: str, status: str):
        """更新任务状态"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE task_tracker 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE task_name = ? AND symbol = ? AND period = ?
        """,
            (status, task_name, symbol, period),
        )

        conn.commit()
        conn.close()

    def get_pending_tasks(self, task_name: str) -> List[dict]:
        """获取待处理任务"""
        conn = self._get_conn()
        df = pd.read_sql(
            """
            SELECT symbol, period FROM task_tracker
            WHERE task_name = ? AND status = 'pending'
            ORDER BY updated_at
        """,
            conn,
            params=(task_name,),
        )
        conn.close()
        return df.to_dict("records")

    def get_task_progress(self, task_name: str) -> dict:
        """获取任务进度"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT status, COUNT(*) as count FROM task_tracker
            WHERE task_name = ?
            GROUP BY status
        """,
            (task_name,),
        )

        results = cursor.fetchall()
        conn.close()

        total = sum(r[1] for r in results)
        completed = sum(r[1] for r in results if r[0] == "completed")

        return {"total": total, "completed": completed, "pending": total - completed}

    def clear_task(self, task_name: str):
        """清除任务记录"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM task_tracker WHERE task_name = ?", (task_name,))
        conn.commit()
        conn.close()


# 全局数据库实例
db = Database()
