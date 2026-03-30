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

## 项目部署

### 方式一：本地源码部署

#### 1. 克隆项目
```bash
git clone https://github.com/mickey3721/stock_analysis_system.git
cd stock_analysis_system
```

#### 2. 后端部署
```bash
# 创建虚拟环境
cd stock_analysis
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动后端
python -m uvicorn api.main:app --host 0.0.0.0 --port 8899
```

#### 3. 前端部署
```bash
# 安装依赖
cd frontend
npm install

# 开发模式
npm run dev

# 生产构建
npm run build
```

---

### 方式二：Docker镜像部署

#### 1. 后端Dockerfile
```dockerfile
# stock_analysis/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8899

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8899"]
```

#### 2. 前端Dockerfile
```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

#### 3. Docker Compose一键部署
```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./stock_analysis
    ports:
      - "8899:8899"
    volumes:
      - ./stock_analysis/data:/app/data
    environment:
      - PYTHONUNBUFFERED=1

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
```

#### 4. 部署命令
```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 5. 访问地址
- 前端: http://localhost:3000
- 后端API: http://localhost:8899

---

## 启动方式（开发模式）

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
