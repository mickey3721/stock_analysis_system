"""
技术指标模块
"""

from .ma import calculate_ma
from .trend_channel import calculate_trend_channel, get_channel_signal
from .sequence import calculate_sequence, get_sequence_signal
from .macd_quant import calculate_macd_quant, get_macd_structure
from .chanlun import ChanlunAnalyzer
from .support import calculate_support_resistance
