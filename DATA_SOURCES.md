# 数据获取模块总结

## 数据源概览

| # | 数据源 | 用途 | 数据类型 | Token需求 | 状态 |
|---|--------|------|----------|-----------|------|
| 1 | 腾讯/同花顺 | 日K线(含盘中) | 历史K线、实时 | ❌ | ✅ |
| 2 | Sina | 分钟K线 | 分钟K线 | ❌ | ✅ |
| 3 | Baostock | 历史日K备用 | 历史K线 | ❌ | ✅ |
| 4 | TickFlow | 历史日K备用 | 历史K线 | ❌ | ✅ |
| 5 | Snowball-实时 | 实时行情 | 实时行情 | ❌ | ✅ |
| 6 | Snowball-K线 | K线数据 | K线、分钟线 | ✅ | ✅ |
| 7 | 东方财富-实时 | 实时行情 | 实时行情 | ❌ | ⚠️ |

**可用数据源: 6/7**

---

## 数据源详情

### 1. 腾讯/同花顺 (web.ifzq.gtimg.cn)
- **方法**: `_get_from_tencent()`
- **用途**: 日K线数据（含盘中实时）
- **周期**: day, week, month
- **特点**: 
  - 包含当日盘中实时数据
  - 列顺序: 日期,开盘,最低,最高,收盘,成交量（注意：最低/最高顺序）

### 2. Sina (money.finance.sina.com.cn)
- **方法**: `_get_minute_from_sina()`
- **用途**: 分钟K线数据
- **周期**: 5/15/30/60 分钟
- **特点**: 稳定的分钟线数据源

### 3. Baostock
- **方法**: `_get_from_baostock()`
- **用途**: 历史日K线备用
- **特点**: 稳定可靠，适合批量获取

### 4. TickFlow (free-api.tickflow.org)
- **方法**: `_get_from_tickflow()`
- **用途**: 历史日K线备用
- **API**: `https://free-api.tickflow.org/v1/klines`
- **特点**: 免费无需注册，提供历史日K线

### 5. Snowball 实时 (stock.xueqiu.com)
- **方法**: `_get_from_snowball()`
- **用途**: 批量实时行情
- **API**: `quotec(symbols)` - 无需Token
- **字段**: current, open, high, low, volume, percent, chg 等

### 6. Snowball K线
- **方法**: `_get_kline_from_snowball()`
- **用途**: K线数据（需要Token）
- **周期**: day, week, month, 60m, 30m, 5m
- **Token**: 环境变量 `XUEQIU_TOKEN`
- **配置**: `.env.snowball` 文件

### 7. 东方财富实时 (push2.eastmoney.com)
- **方法**: `_get_realtime_from_eastmoney()`
- **用途**: 实时行情
- **状态**: ⚠️ 连接不稳定，作为备用

---

## 数据质量修复记录

### 1. 高低价列顺序问题
- **来源**: 腾讯API
- **问题**: 返回列顺序为 `日期,开盘,最低,最高,收盘,成交量`
- **修复**: `_get_from_tencent()` 中正确映射 low/high 字段

### 2. 东方财富实时高低价字段
- **来源**: push2.eastmoney.com
- **问题**: 字段 f15=最高价, f16=最低价
- **修复**: 在 `_get_realtime_from_eastmoney()` 中正确使用

---

## 配置说明

### 环境变量
```bash
# 雪球Token (.env.snowball)
XUEQIU_TOKEN=u=941774936183264; xq_a_token=ee5d330e6b3b85416dfd3c86696c78d742b37ced

# TickFlow API Key (可选)
TICKFLOW_API_KEY=tk_e0a77fadba2d447d98a8cb9a549a4c2b
```

### Docker配置
```yaml
# docker-compose.yml
services:
  backend:
    env_file:
      - .env.snowball
```

---

## 健康检查

数据采集器初始化时会自动测试所有数据源：

```
[数据源测试] tencent: 可用
[数据源测试] baostock: 可用
[数据源测试] sina: 可用
[数据源测试] tickflow: 可用
[数据源测试] snowball: 可用
```

---

## 下一步优化建议

1. **东方财富实时接口**: 排查连接问题或切换备用方案
2. **Snowball Token**: 有效期约1个月，需定期更新
3. **缓存策略**: 优化数据缓存过期时间
4. **回归测试**: 全量标的测试验证数据质量
