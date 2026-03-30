# 股票智能分析系统

A-share stock intelligent analysis system with 徐小明交易系统 + 缠论

## 功能特性

### 1. 均线系统
- EMA 5/26/89/144 均线
- 多头排列/空头排列判断

### 2. 徐小明系统
- **多空通道**: 短线25日/长线89日EMA通道
- **九转序列**: TD序列规则，与前4根K线比较
- **MACD定量结构**: 120周期钝化观察，75%/100%结构判定

### 3. 缠论系统
- 基于czsc库的分型/笔识别
- 背驰判定（力度对比）
- 买卖点信号

### 4. 风控模块
- 止损: -7%
- 止盈: +15%或回落5%止盈
- 回撤熔断: -15%

## 技术栈

- **后端**: Python + FastAPI + akshare + czsc
- **前端**: Vue3 + Vant + ECharts
- **数据**: akshare + 本地CSV缓存

## 启动方式

### 后端
```bash
cd stock_analysis
python -m uvicorn api.main:app --host 127.0.0.1 --port 8899
```

### 前端
```bash
cd frontend
npm run dev
```

## API接口

| 接口 | 说明 |
|------|------|
| GET /stocks | 股票列表 |
| GET /kline/{symbol} | K线数据 |
| GET /analyze/{symbol} | 综合分析 |
| GET /realtime/{symbol} | 实时行情 |

## 核心文件

```
stock_analysis/
├── api/main.py              # FastAPI主程序
├── analysis/analyzer.py     # 综合分析器
├── indicators/
│   ├── ma.py               # 均线
│   ├── trend_channel.py    # 多空通道
│   ├── sequence.py         # 九转序列
│   ├── macd_quant.py       # MACD定量
│   ├── chanlun.py          # 缠论
│   └── support.py          # 支撑阻力
└── data/collector.py       # 数据采集
```

## 更新日志

### 2024-03-30
- 修复CZSC枚举比较方式，使用.value属性
- 优化多空通道信号描述
- 优化九转序列中文描述
- 优化MACD定量结构检测逻辑
- 修复前端代理配置

### 2024-03-29
- 初始版本完成
- 均线/通道/九转/MACD/缠论指标实现
- FastAPI后端 + Vue3前端
