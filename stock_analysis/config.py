"""
股票智能分析系统 - 配置文件
"""

# 监控标的
SYMBOLS = {
    "A股大盘": {
        "000001.SH": "上证指数",
        "000300.SH": "沪深300",
        "399006.SZ": "创业板指",
    },
    "大宗商品": {
        "XAUUSD": "黄金期货",
        "CL=F": "原油期货",
    },
    "个股": {
        "600176.SH": "中国巨石",
        "600299.SH": "安迪苏",
        "515000.SH": "证券ETF",
    },
}

# 均线参数
MA_PARAMS = [5, 26, 89, 144]

# 多空通道参数
CHANNEL_PARAMS = {
    "short": 25,  # 短线通道
    "long": 89,  # 长线通道
}

# MACD参数
MACD_PARAMS = {"fast": 12, "slow": 26, "signal": 9}

# 风控配置
RISK_CONFIG = {
    "stop_loss": {"type": "fixed", "pct": 0.07},
    "take_profit": {
        "type": "trailing",
        "fixed_pct": 0.15,
        "trailing_pct": 0.05,
        "start_pct": 0.10,
    },
    "drawdown": {"max_drawdown": 0.15, "cooling_days": 5},
    "position": {"max_stocks": 3, "max_single": 0.30},
}

# 分析周期
PERIODS = ["daily", "120min", "60min", "30min", "15min", "5min"]

# 周期参数配置
PERIOD_CONFIG = {
    "daily": {
        "name": "日线",
        "ma": [5, 26, 89, 144],
        "channel": {"short": 25, "long": 89},
    },
    "120min": {
        "name": "120分钟",
        "ma": [5, 26, 89],
        "channel": {"short": 25, "long": 89},
    },
    "60min": {
        "name": "60分钟",
        "ma": [5, 26, 89],
        "channel": {"short": 25, "long": 55},
    },
    "30min": {
        "name": "30分钟",
        "ma": [5, 26, 55],
        "channel": {"short": 13, "long": 34},
    },
    "15min": {
        "name": "15分钟",
        "ma": [5, 13, 34],
        "channel": {"short": 13, "long": 26},
    },
    "5min": {
        "name": "5分钟",
        "ma": [5, 13, 34],
        "channel": {"short": 9, "long": 21},
    },
}

# 数据库配置
DATABASE = {"path": "data/stock.db"}

# 数据更新配置
UPDATE_CONFIG = {
    "daily": "16:00",  # 收盘后更新日线
    "120min": "11:00",  # 盘中更新
    "60min": "11:00",
    "30min": "11:00",
    "15min": "09:50",
    "5min": "09:40",
}

# 并发配置
CONCURRENCY = {
    "max_workers": 4,  # 最大并发数
    "timeout": 30,  # 单个请求超时秒数
    "retry": 2,  # 失败重试次数
    "retry_delay": 1,  # 重试间隔秒数
}

# 缓存策略
CACHE_STRATEGY = {
    "daily": {"max_age_hours": 4, "stale_while_revalidate": True},
    "120min": {"max_age_hours": 1, "stale_while_revalidate": True},
    "60min": {"max_age_hours": 1, "stale_while_revalidate": True},
    "30min": {"max_age_hours": 0.5, "stale_while_revalidate": True},
    "15min": {"max_age_hours": 0.25, "stale_while_revalidate": True},
    "5min": {"max_age_hours": 0.1, "stale_while_revalidate": True},
}
