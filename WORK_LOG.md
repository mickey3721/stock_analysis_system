# 工作日志

## 2026-03-31

### 功能优化

#### pysnowball 雪球数据源集成
- **GitHub**: https://github.com/uname-yang/pysnowball
- **PyPI**: `pip install pysnowball>=0.1.0`

- **无需Token的API**:
  | API | 功能 | URL |
  |-----|------|-----|
  | `quotec(symbols)` | 实时行情 | `https://stock.xueqiu.com/v5/stock/realtime/quotec.json` |

- **需要Token的API** (K线等):
  - `kline()` - K线数据
  - `quote_detail()` - 详细行情
  - `pankou()` - 分笔数据
  - `capital_flow()` - 资金流向
  - `margin()` - 融资融券
  - `report()` - 机构评级

- **Token获取方法**:
  1. Edge浏览器登录 https://xueqiu.com
  2. F12打开开发者工具 → Network
  3. 刷新页面，找任意xueqiu.com请求
  4. Headers → Request Headers → Cookie

- **Token配置**:
  - 保存到 `.env.snowball` 文件
  - docker-compose.yml 使用 `env_file: .env.snowball`
  - 环境变量: `XUEQIU_TOKEN`

- **实现内容**:
  1. 添加 `pysnowball>=0.1.0` 到 `requirements.txt`
  2. 实现 `_get_from_snowball()` 方法：获取实时行情
  3. 实现 `_get_kline_from_snowball()` 方法：获取K线数据（需要Token）
  4. 实现 `_test_snowball_source()` 方法：健康检查
  5. 添加到数据源监控列表

- **K线周期支持**:
  | 周期 | 代码 | 状态 |
  |------|------|------|
  | 日K | `day` | ✅ |
  | 周K | `week` | ✅ |
  | 月K | `month` | ✅ |
  | 60分钟 | `60m` | ✅ |
  | 30分钟 | `30m` | ✅ |
  | 5分钟 | `5m` | ✅ |

- **测试结果**:
  - ✅ 健康检查通过
  - ✅ 实时行情获取正常（含high/low）
  - ✅ K线数据获取正常（含分钟线）
  - ✅ quote_detail获取详细行情
  - ✅ capital_flow资金流向数据
  - ✅ margin融资融券数据

---

#### TickFlow 数据源集成
- **目标**: 添加TickFlow作为新的备用数据源
- **文档**: https://docs.tickflow.org/zh-Hans/sdk/python-quickstart
- **SDK**: `pip install "tickflow[all]">=0.1.0"`

- **实现内容**:
  1. 添加 `tickflow[all]` 到 `requirements.txt`
  2. 实现 `_get_from_tickflow()` 方法：使用TickFlow免费API获取历史日K线
  3. 更新 `_test_data_source()` 方法：添加TickFlow健康检查
  4. 直接使用HTTP请求（避免SDK的SSL问题）

- **TickFlow API**:
  - 免费服务: https://free-api.tickflow.org/v1/klines
  - 免费API: 无需注册，提供历史日K线数据
  - 实时行情/分钟K线: 需要完整服务（tickflow.org注册）

- **数据格式**:
  ```json
  {
    "data": {
      "timestamp": [1774800000000],
      "open": [3884.277],
      "high": [3924.29],
      "low": [3872.776],
      "close": [3923.287],
      "volume": [595589479]
    }
  }
  ```

- **测试结果**:
  - ✅ 健康检查通过
  - ✅ 获取 贵州茅台(600519.SH) 21条日K线数据

---

## 2024-03-31

### 功能优化

#### 数据刷新逻辑优化
- **目标**: 根据交易时段智能刷新数据
  - 交易时段（9:30-11:30, 13:00-15:00）: 返回当前最新数据
  - 非交易时段: 返回最近历史数据（前一交易日）

- **修改内容**:
  1. 新增 `_get_latest_trading_day()` 方法：获取最近交易日
  2. 重写 `_is_cache_valid()` 方法：
     - 日线：检查缓存数据日期是否 >= 最近交易日
     - 分钟线：交易时段要求当天数据，非交易时段接受历史数据
  3. 修改 `_get_from_akshare()` 方法：
     - 非交易时段使用 `_get_latest_date()` 获取正确的结束日期
  4. 添加交易时段日志输出

- **交易时段判断逻辑**:
  - 工作日 9:30-11:30 (570-690分钟)
  - 工作日 13:00-15:00 (780-900分钟)
  - 周末自动判定为非交易时段

- **文件修改**:
  | 文件 | 修改内容 |
  |------|---------|
  | `data/collector.py` | 交易时段智能刷新逻辑 |
  | `docker-compose.yml` | 添加健康检查、网络配置、数据卷 |
  | `frontend/nginx.conf` | 添加Gzip压缩、静态资源缓存 |

- **docker-compose.yml 改进**:
  - 添加健康检查 (healthcheck)
  - 添加Docker网络 (stock-network)
  - 添加数据卷持久化 (backend-cache)
  - 设置时区 (Asia/Shanghai)
  - 前端依赖后端健康状态启动

### 问题修复

#### akshare接口不可用问题
- **原因**: 容器内无法访问东方财富历史数据接口 (push2his.eastmoney.com)
- **解决**: 
  1. 新增 `_get_from_sina()` 方法：使用新浪财经API作为备用数据源
  2. 修改网络配置：使用 `network_mode: host` 提高网络连通性
  3. 新增 `_update_today_data()` 方法：使用东方财富实时接口更新当日数据

- **数据源优先级**:
  1. akshare（主源，如果可用）
  2. 新浪财经API（备用）
  3. 东方财富实时API（交易时段更新当日数据）

---

## 2024-03-30

### 问题修复

#### 1. 缠论数据显示英文而非中文
- **现象**: 前端显示 `bottom`, `down`, `none`
- **原因**: CZSC枚举比较方式错误
- **解决**: CZSC枚举正确用法是使用 `.value` 属性比较
  - `Mark.G.value` = "顶分型"
  - `Mark.D.value` = "底分型"
  - `Direction.Up.value` = "向上"
  - `Direction.Down.value` = "向下"

#### 2. 前端API配置错误
- **原因**: 前端指向旧端口(8888/8900)
- **解决**: 
  - `api/stock.js`: 改为使用相对路径 `/api`
  - `vite.config.js`: 添加 `rewrite` 去掉 `/api` 前缀，代理到 `127.0.0.1:8899`

### 优化

#### 1. 多空通道信号描述优化
- **之前**: "观望" (单一描述)
- **现在**: 根据长短通道状态组合显示
  - 强势突破、突破回踩、跌破反弹、震荡上行等

#### 2. 九转序列描述优化
- **之前**: "高位1形成中"
- **现在**: 更直观的描述
  - 买9=机会窗口
  - 卖9=风险窗口  
  - 买6=分批布局
  - 反弹5=蓄势中

#### 3. MACD定量结构优化
- **之前**: "无结构" (数据不足120周期时)
- **现在**: 自动调整lookback周期
  - 数据>=120期: 120周期钝化
  - 数据>=60期: 60周期钝化
  - 数据<60期: 30周期钝化
  - 无结构时显示: 多头运行中/空头运行中

### 文件修改

| 文件 | 修改内容 |
|------|---------|
| `indicators/chanlun.py` | CZSC枚举比较方式 |
| `indicators/trend_channel.py` | 信号描述优化 |
| `indicators/sequence.py` | 九转序列描述优化 |
| `indicators/macd_quant.py` | MACD自动调整lookback |
| `frontend/vite.config.js` | 代理配置修正 |
| `frontend/src/api/stock.js` | 改为相对路径 |
| `start_backend.bat` | 更新端口为8899 |

---

## 2024-03-29

### 初始版本

- ✅ 数据采集模块 (akshare + CSV缓存)
- ✅ 均线系统 (EMA 5/26/89/144)
- ✅ 徐小明系统 (趋势通道25/89, 九转序列, MACD 120周期)
- ✅ 缠论系统 (分型/笔/背驰分析，基于czsc)
- ✅ 风控模块
- ✅ 多周期支持 (daily/60min/30min/15min/5min)
- ✅ 断点续传机制
- ✅ FastAPI后端
- ✅ Vue3前端项目
