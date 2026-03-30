# -*- coding: utf-8 -*-
import akshare as ak
import sys

sys.stdout.reconfigure(encoding="utf-8")

# 测试指数数据获取
print("Testing index_zh_a_hist...")
df = ak.index_zh_a_hist(
    symbol="000300", period="daily", start_date="20240101", end_date="20250330"
)
print("Columns:", df.columns.tolist())
print("First row:", df.iloc[0].to_dict())
