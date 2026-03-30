# -*- coding: utf-8 -*-
import sys

sys.stdout.reconfigure(encoding="utf-8")
import akshare as ak

# 测试分钟数据获取
print("Testing 5min data...")
df = ak.stock_zh_a_hist_min_em(symbol="000001", period="5分钟")
print("Columns:", df.columns.tolist())
print("Shape:", df.shape)
print(df.head(3))
