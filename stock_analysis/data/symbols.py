"""
标的定义模块
"""

# A股大盘指数
INDEX_SYMBOLS = {
    "000001.SH": "上证指数",
    "000300.SH": "沪深300",
    "399006.SZ": "创业板指",
    "399001.SZ": "深证成指",
    "000905.SH": "中证500",
}

# 外围市场
GLOBAL_SYMBOLS = {
    "^DJI": "道琼斯指数",
    "^IXIC": "纳斯达克指数",
    "^GSPC": "标普500",
    "CN00Y": "新加坡A50",
    "NIKKEI": "日经225",
}

# 大宗商品
COMMODITY_SYMBOLS = {
    "CL=F": "WTI原油",
    "GC=F": "纽约黄金",
    "SI=F": "纽约白银",
    "XAUUSD": "现货黄金",
    "XAGUSD": "现货白银",
    "DXY": "美元指数",
}

# 个股
STOCK_SYMBOLS = {
    "600176.SH": "中国巨石",
    "600299.SH": "安迪苏",
    "515000.SH": "证券ETF",
    "600519.SH": "贵州茅台",
    "600036.SH": "招商银行",
}


def get_all_symbols():
    """获取所有监控标的"""
    all_symbols = {}
    all_symbols.update(INDEX_SYMBOLS)
    all_symbols.update(GLOBAL_SYMBOLS)
    all_symbols.update(COMMODITY_SYMBOLS)
    all_symbols.update(STOCK_SYMBOLS)
    return all_symbols


def get_china_symbols():
    """获取A股相关标的"""
    china = {}
    china.update(INDEX_SYMBOLS)
    china.update(STOCK_SYMBOLS)
    return china


def get_global_symbols():
    """获取外围市场标的"""
    return GLOBAL_SYMBOLS


def get_commodity_symbols():
    """获取大宗商品标的"""
    return COMMODITY_SYMBOLS
