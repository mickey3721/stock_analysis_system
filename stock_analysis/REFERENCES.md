# 参考资料文档

## 一、核心参考项目

### 1. czsc - 缠中说禅技术分析工具
- **GitHub**: https://github.com/waditu/czsc
- **PyPI**: czsc
- **说明**: 最专业的缠论Python库，提供完整的缠论分析功能
- **功能**: 分型、笔、线段、中枢、背驰、买卖点等

### 2. czsc_skills - 缠论技能
- **GitHub**: https://github.com/zengbin93/czsc_skills
- **说明**: 缠论技能实战应用，基于czsc的策略实现

---

## 二、技术指标参考

### 1. 徐小明多空通道
- **来源**: 通达信公式、同花顺指标
- **核心**:
  - 短线通道: EMA(H,25) / EMA(L,25)
  - 长线通道: EMA(H,89) / EMA(L,89)
- **信号**: 红/绿/紫/蓝四色多空判定

### 2. 九转序列（TD序列）
- **来源**: 徐小明、迪马克TD序列
- **算法**:
  - 买序列: 收盘价 >= 前第4根收盘价 → 计数+1
  - 卖序列: 收盘价 <= 前第4根收盘价 → 计数+1
- **信号**: 序列9为高概率反转点

### 3. MACD定量结构
- **来源**: 徐小明定量结构
- **核心**:
  - 钝化: 价格创新高但DIF未新高（120周期窗口）
  - 75%结构: 钝化 + DIF转向
  - 100%结构: 75% + 金叉/死叉确认

---

## 三、数据源参考

### 1. akshare
- **文档**: https://akshare.akfamily.xyz/
- **说明**: 免费A股数据接口
- **常用API**:
  - `stock_zh_a_hist` - 个股历史数据
  - `index_zh_a_hist` - 指数历史数据
  - `futures_zh_daily_sina` - 期货历史数据
  - `currency_latest` - 外汇实时数据

### 2. akshare指数数据
- **API**: `index_zh_a_hist(symbol="000300", period="daily")`
- **支持**: 上证指数、沪深300、创业板指、中证500等
- **字段**: 日期/开盘/收盘/最高/最低/成交量/成交额/振幅/涨跌幅/涨跌额/换手率

### 3. akshare期货数据
- **API**: `futures_zh_daily_sina(symbol="AU0")` - 黄金期货
- **API**: `futures_zh_daily_sina(symbol="SC0")` - 原油期货
- **API**: `futures_zh_daily_sina(symbol="CU0")` - 铜期货

### 4. tushare
- **文档**: https://tushare.pro/
- **说明**: 专业金融数据接口（需注册获取token）

### 5. scrapling
- **文档**: https://scrapling.readthedocs.io/
- **说明**: 自适应网页爬取库

### 6. yfinance (备用)
- **说明**: Yahoo Finance数据源，需翻墙
- **状态**: 当前网络环境下不可用，保留作为备用

---

## 四、量化策略参考

### 1. 多周期EMA交叉策略
- **来源**: FMZ量化
- **参数**: 5/21/89 或 12/26/50

### 2. 布林带趋势通道
- **公式**:
  - 上轨: MA + 2×STD
  - 下轨: MA - 2×STD
  - 中轨: MA

---

## 五、数据库设计参考

### 1. SQLite
- 轻量级，适合个人使用
- 无需单独安装

### 2. PostgreSQL（推荐生产环境）
- 支持JSON类型
- 并发能力强

---

## 六、Web框架参考

### 1. Flask + Dash
- Dash: 快速数据可视化
- Flask: 轻量级Web服务

### 2. FastAPI
- 现代Python异步框架
- 自动API文档

---

## 七、风控策略参考

### 1. 止损策略
- 固定止损: -7%
- ATR止损: 2.5×ATR

### 2. 止盈策略
- 固定止盈: +15%
- 跟踪止盈: 回落5%止盈

### 3. 回撤控制
- 最大回撤: -15%
- 熔断清仓
- 冷却期: 5天

---

## 八、项目目录结构

```
stock_analysis/
├── README.md                 # 项目说明
├── REFERENCES.md             # 本文件
├── config.py                 # 配置文件
├── requirements.txt          # 依赖
├── data/
│   ├── collector.py         # 数据采集（多源）
│   ├── storage.py           # SQLite存储
│   └── symbols.py           # 标的定义
├── indicators/
│   ├── ma.py                # 均线系统（EMA）
│   ├── trend_channel.py     # 徐小明多空通道
│   ├── sequence.py          # 九转序列
│   ├── macd_quant.py       # MACD定量结构
│   ├── chanlun.py          # 缠论分析（czsc）
│   └── support.py           # 支撑阻力
├── analysis/
│   └── analyzer.py          # 综合分析
├── risk/
│   ├── stop_loss.py        # 止损
│   ├── take_profit.py      # 止盈
│   ├── drawdown.py         # 回撤控制
│   └── position.py          # 仓位管理
└── main.py                  # 入口
```

---

## 九、依赖版本

```
akshare>=1.12.0
pandas>=2.0.0
numpy>=1.24.0
ta-lib>=0.4.28
flask>=2.3.0
dash>=2.14.0
plotly>=5.18.0
apscheduler>=3.10.0
sqlalchemy>=2.0.0
czsc>=0.10.0
scrapling>=0.4.0
```

---

## 十、注意事项

1. Python版本需 >= 3.10（czsc要求）
2. ta-lib需要单独安装C库
3. scrapling用于备用网页爬取
4. 缠论分析优先使用czsc库
5. 数据采集建议使用akshare免费接口
