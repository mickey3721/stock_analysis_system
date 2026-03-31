<template>
  <div class="home">
    <div class="home-header">
      <h1>股票智能分析系统</h1>
      <van-button 
        size="small" 
        type="primary" 
        :loading="refreshing"
        @click="handleRefresh"
        class="refresh-btn"
      >
        {{ refreshing ? '刷新中...' : '刷新数据' }}
      </van-button>
    </div>
    
    <div class="home-content">
      <!-- 左侧：股票选择区 -->
      <div class="stock-list-section">
        <div class="section-title">📈 股票列表</div>
        
        <van-loading v-if="loading" type="spinner" class="loading" />
        <van-empty v-else-if="error" :description="error" />
        <van-empty v-else-if="stocks.length === 0" description="暂无数据" />
        
        <div v-else>
          <van-cell-group v-for="(list, cat) in groupedStocks" :key="cat" :title="cat">
            <van-cell 
              v-for="s in list" 
              :key="s.symbol" 
              :title="s.name" 
              :label="s.symbol"
              :class="{ active: selectedSymbol === s.symbol }"
              is-link 
              clickable
              @click="selectStock(s.symbol)"
            />
          </van-cell-group>
        </div>
      </div>
      
      <!-- 右侧：综合报告区 -->
      <div class="report-section">
        <div class="section-title">📊 综合分析报告</div>
        
        <div v-if="reportLoading" class="loading">加载中...</div>
        <div v-else-if="reportError" class="error">{{ reportError }}</div>
        <div v-else-if="report" class="report-content">
          <!-- 大盘指数 -->
          <div class="report-block">
            <div class="block-title">🔔 大盘状态</div>
            <div class="index-grid">
              <div v-for="idx in marketIndexes" :key="idx.symbol" class="index-card">
                <div class="idx-name">{{ idx.name }}</div>
                <div class="idx-price" :class="idx.change >= 0 ? 'up' : 'down'">{{ idx.price }}</div>
                <div class="idx-change" :class="idx.change >= 0 ? 'up' : 'down'">
                  {{ idx.change >= 0 ? '▲' : '▼' }} {{ idx.change }}%
                </div>
              </div>
            </div>
          </div>
          
          <!-- 选中标的分析 -->
          <div class="report-block">
            <div class="block-title">{{ report.name }} ({{ report.symbol }})</div>
            
            <!-- 价格信息 -->
            <div class="price-info">
              <div class="current-price" :class="report.change_pct >= 0 ? 'up' : 'down'">
                {{ report.close }}
              </div>
              <div class="price-change" :class="report.change_pct >= 0 ? 'up' : 'down'">
                {{ report.change_pct >= 0 ? '+' : '' }}{{ report.change_pct }}%
              </div>
            </div>
            
            <!-- 信号 -->
            <div class="signal-box">
              <div class="signal-label">综合信号</div>
              <div class="signal-value" :class="getSignalClass(report.signal)">
                {{ report.signal }}
              </div>
              <div class="confidence">置信度: {{ report.confidence }}%</div>
            </div>
            
            <!-- EMA均线 -->
            <div class="ma-grid">
              <div v-if="report.ma5" class="ma-item">
                <span class="ma-label">EMA5</span>
                <span class="ma-value">{{ report.ma5.toFixed(2) }}</span>
              </div>
              <div v-if="report.ma26" class="ma-item">
                <span class="ma-label">EMA26</span>
                <span class="ma-value">{{ report.ma26.toFixed(2) }}</span>
              </div>
              <div v-if="report.ma89" class="ma-item">
                <span class="ma-label">EMA89</span>
                <span class="ma-value">{{ report.ma89.toFixed(2) }}</span>
              </div>
              <div v-if="report.ma144" class="ma-item">
                <span class="ma-label">EMA144</span>
                <span class="ma-value">{{ report.ma144.toFixed(2) }}</span>
              </div>
            </div>
            
            <!-- 技术指标 -->
            <div class="indicator-section">
              <div class="indicator-title">📐 技术指标</div>
              <div class="indicator-row">
                <span>多空通道:</span>
                <span>{{ report.channel_signal || '-' }}</span>
              </div>
              <div class="indicator-row">
                <span>九转序列:</span>
                <span>{{ report.seq_desc || '-' }}</span>
              </div>
              <div class="indicator-row">
                <span>MACD:</span>
                <span>{{ report.macd_desc || '-' }}</span>
              </div>
            </div>
            
            <!-- 缠论 -->
            <div class="indicator-section">
              <div class="indicator-title">⏱ 缠论分析</div>
              <div class="indicator-row">
                <span>分型:</span>
                <span>{{ report.fenxing || '-' }}</span>
              </div>
              <div class="indicator-row">
                <span>笔方向:</span>
                <span>{{ report.bi_status || '-' }}</span>
              </div>
              <div class="indicator-row">
                <span>背驰:</span>
                <span>{{ report.beichi || '-' }}</span>
              </div>
            </div>
            
            <!-- 支撑阻力 -->
            <div class="levels-section">
              <div class="levels-row">
                <span class="level-label">支撑位:</span>
                <div class="level-tags">
                  <span v-for="(s, i) in report.support_levels" :key="i" class="level-tag support">
                    {{ s.type }}: {{ s.level.toFixed(2) }}
                  </span>
                </div>
              </div>
              <div class="levels-row">
                <span class="level-label">阻力位:</span>
                <div class="level-tags">
                  <span v-for="(r, i) in report.resistance_levels" :key="i" class="level-tag resistance">
                    {{ r.type }}: {{ r.level.toFixed(2) }}
                  </span>
                </div>
              </div>
            </div>
            
            <!-- 操作建议 -->
            <div class="action-section">
              <div class="action-title">🎯 操作建议</div>
              <div class="action-content">
                <span :class="['action-tag', getSignalClass(report.signal)]">
                  {{ report.signal }}
                </span>
                <span class="action-reason">{{ getActionReason(report) }}</span>
              </div>
            </div>
            
            <!-- 周期切换 -->
            <div class="chart-tabs">
              <span 
                v-for="p in chartPeriods" 
                :key="p.value"
                :class="['tab', chartPeriod === p.value ? 'active' : '']"
                @click="changeChartPeriod(p.value)"
              >
                {{ p.label }}
              </span>
            </div>
            
            <!-- K线/分时图 -->
            <div class="chart-container">
              <v-chart :option="chartOption" autoresize style="height: 380px" />
            </div>
          </div>
        </div>
        <div v-else class="empty-report">
          <p>点击左侧股票查看详细分析报告</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { CellGroup, Cell, Loading, Empty, Button, showToast } from 'vant'
import * as echarts from 'echarts'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { CandlestickChart, LineChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, DataZoomComponent, LegendComponent } from 'echarts/components'
import api from '../api/stock'

use([CanvasRenderer, CandlestickChart, LineChart, BarChart, GridComponent, TooltipComponent, DataZoomComponent, LegendComponent])

const stocks = ref([])
const loading = ref(true)
const error = ref('')
const selectedSymbol = ref('')
const report = ref(null)
const reportLoading = ref(false)
const reportError = ref('')
const marketIndexes = ref([])
const refreshing = ref(false)

// Chart
const isIndexOrFuture = computed(() => {
  return ['000001.SH', '000300.SH', '399006.SZ', '399001.SZ', 'XAUUSD', 'CL=F'].includes(selectedSymbol.value)
})

const chartPeriods = computed(() => {
  if (isIndexOrFuture.value) {
    return [
      { label: '分时', value: 'intraday' },
      { label: '日线', value: 'daily' },
    ]
  }
  return [
    { label: '分时', value: 'intraday' },
    { label: '日线', value: 'daily' },
    { label: '60分', value: '60min' },
    { label: '30分', value: '30min' },
    { label: '15分', value: '15min' },
    { label: '5分', value: '5min' },
  ]
})

const chartPeriod = ref('daily')
const chartData = ref([])
const intradayData = ref({ times: [], prices: [], volumes: [] })

const changeChartPeriod = async (period) => {
  chartPeriod.value = period
  await loadChartData()
}

const loadChartData = async () => {
  if (!selectedSymbol.value) return
  
  try {
    if (chartPeriod.value === 'intraday') {
      const res = await api.getIntraday(selectedSymbol.value)
      if (res.data) {
        intradayData.value = res.data
      }
    } else {
      const res = await api.getKline(selectedSymbol.value, chartPeriod.value)
      if (res.data && res.data.dates) {
        chartData.value = res.data.dates.map((d, i) => ({
          date: d,
          open: res.data.opens[i],
          high: res.data.highs[i],
          low: res.data.lows[i],
          close: res.data.closes[i],
          volume: res.data.volumes[i]
        }))
      }
    }
  } catch (e) {
    console.error('Chart data error:', e)
  }
}

const intradayOption = computed(() => {
  if (!intradayData.value.times?.length) return {}
  
  const times = intradayData.value.times
  const prices = intradayData.value.prices
  const volumes = intradayData.value.volumes
  
  const avgPrices = []
  let sum = 0
  for (let i = 0; i < prices.length; i++) {
    sum += prices[i]
    avgPrices.push((sum / (i + 1)).toFixed(2))
  }
  
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    legend: { data: ['价格', '均价', '成交量'], top: 0, textStyle: { color: '#e2e8f0' } },
    grid: [
      { left: '8%', right: '8%', height: '60%' },
      { left: '8%', right: '8%', top: '80%', height: '12%' }
    ],
    xAxis: [
      { type: 'category', data: times, boundaryGap: false, axisLine: { lineStyle: { color: '#555' } }, axisLabel: { color: '#aaa' } },
      { type: 'category', data: times, boundaryGap: false, gridIndex: 1, axisLine: { lineStyle: { color: '#555' } }, axisLabel: { show: false } }
    ],
    yAxis: [
      { scale: true, splitArea: { show: true, areaStyle: { color: ['#1a1f35', '#141828'] } }, axisLine: { lineStyle: { color: '#555' } }, axisLabel: { color: '#e2e8f0' }, splitLine: { lineStyle: { color: '#333' } } },
      { scale: true, gridIndex: 1, splitNumber: 2, axisLine: { lineStyle: { color: '#555' } }, axisLabel: { color: '#aaa' }, splitLine: { show: false } }
    ],
    backgroundColor: '#1a1f35',
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 60, end: 100 }
    ],
    series: [
      {
        name: '价格', type: 'line', data: prices, smooth: true, symbol: 'none',
        lineStyle: { width: 2, color: '#00ff00' },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(0, 255, 0, 0.3)' },
          { offset: 1, color: 'rgba(0, 255, 0, 0.05)' }
        ])}
      },
      {
        name: '均价', type: 'line', data: avgPrices, smooth: true, symbol: 'none',
        lineStyle: { width: 2, color: '#ff9900' }
      },
      {
        name: '成交量', type: 'bar', xAxisIndex: 1, yAxisIndex: 1,
        data: volumes.map((v, i) => ({ value: v, itemStyle: { color: i > 0 && prices[i] >= prices[i-1] ? '#22c55e' : '#ef4444' } })),
        symbol: 'none'
      }
    ]
  }
})

const klineOption = computed(() => {
  if (chartPeriod.value === 'intraday') return intradayOption.value
  if (!chartData.value.length) return {}
  
  const dates = chartData.value.map(d => d.date)
  const ohlc = chartData.value.map(d => [d.open, d.close, d.low, d.high])
  const ma5 = calculateEMA(5)
  const ma26 = calculateEMA(26)
  const ma89 = calculateEMA(89)
  const channel = calculateChannel(25)
  
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    legend: { data: ['K线', 'EMA5', 'EMA26', 'EMA89', '通道'], top: 0, textStyle: { color: '#e2e8f0' } },
    grid: [
      { left: '8%', right: '8%', height: '58%' },
      { left: '8%', right: '8%', top: '80%', height: '12%' }
    ],
    xAxis: [
      { type: 'category', data: dates, boundaryGap: true, axisLine: { lineStyle: { color: '#555' } }, axisLabel: { color: '#aaa' } },
      { type: 'category', data: dates, boundaryGap: true, gridIndex: 1, axisLine: { lineStyle: { color: '#555' } }, axisLabel: { show: false } }
    ],
    yAxis: [
      { scale: true, splitArea: { show: true, areaStyle: { color: ['#1a1f35', '#141828'] } }, axisLine: { lineStyle: { color: '#555' } }, axisLabel: { color: '#e2e8f0' }, splitLine: { lineStyle: { color: '#333' } } },
      { scale: true, gridIndex: 1, splitNumber: 2, axisLine: { lineStyle: { color: '#555' } }, axisLabel: { color: '#aaa' }, splitLine: { show: false } }
    ],
    backgroundColor: '#1a1f35',
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 50, end: 100 }
    ],
    series: [
      { name: '通道', type: 'line', data: channel.upper, smooth: true, symbol: 'none', lineStyle: { width: 0, color: 'transparent' },
        areaStyle: { color: 'rgba(25, 118, 210, 0.2)' }, z: 1 },
      { name: '通道', type: 'line', data: channel.lower, smooth: true, symbol: 'none', lineStyle: { width: 1, color: '#4a90d9', type: 'dashed' }, z: 2 },
      { name: 'K线', type: 'candlestick', data: ohlc,
        itemStyle: { color: '#ef4444', color0: '#22c55e', borderColor: '#ef4444', borderColor0: '#22c55e' }, z: 10 },
      { name: 'EMA5', type: 'line', data: ma5, smooth: true, symbol: 'none', lineStyle: { width: 2, color: '#00ff00' }, z: 15 },
      { name: 'EMA26', type: 'line', data: ma26, smooth: true, symbol: 'none', lineStyle: { width: 2, color: '#ff9900' }, z: 15 },
      { name: 'EMA89', type: 'line', data: ma89, smooth: true, symbol: 'none', lineStyle: { width: 2, color: '#ff00ff' }, z: 15 },
      { name: '成交量', type: 'bar', xAxisIndex: 1, yAxisIndex: 1,
        data: chartData.value.map(d => ({ value: d.volume, itemStyle: { color: d.close >= d.open ? '#22c55e' : '#ef4444' } })), symbol: 'none' }
    ]
  }
})

const chartOption = computed(() => {
  if (chartPeriod.value === 'intraday') return intradayOption.value
  return klineOption.value
})

function calculateEMA(dayCount) {
  const result = []
  const closes = chartData.value.map(d => d.close)
  const alpha = 2 / (dayCount + 1)
  let ema = null
  for (let i = 0; i < chartData.value.length; i++) {
    if (i < dayCount - 1) { result.push(null); continue }
    if (ema === null) ema = closes[i - dayCount + 1]
    ema = alpha * closes[i] + (1 - alpha) * ema
    result.push(parseFloat(ema.toFixed(2)))
  }
  return result
}

function calculateChannel(dayCount) {
  const upper = [], lower = []
  const highs = chartData.value.map(d => d.high)
  const lows = chartData.value.map(d => d.low)
  const alpha = 2 / (dayCount + 1)
  
  for (let i = 0; i < chartData.value.length; i++) {
    if (i < dayCount - 1) { upper.push('-'); lower.push('-'); continue }
    let emaH = highs[i], emaL = lows[i]
    for (let j = 0; j < dayCount && i - j >= 0; j++) {
      emaH = alpha * highs[i - j] + (1 - alpha) * emaH
      emaL = alpha * lows[i - j] + (1 - alpha) * emaL
    }
    upper.push(emaH.toFixed(2))
    lower.push(emaL.toFixed(2))
  }
  return { upper, lower }
}

const groupedStocks = computed(() => {
  const g = {}
  stocks.value.forEach(s => {
    if (!g[s.category]) g[s.category] = []
    g[s.category].push(s)
  })
  return g
})

const loadStocks = async () => {
  try {
    const res = await api.getStocks()
    stocks.value = res.data || []
    
    if (stocks.value.length > 0 && !selectedSymbol.value) {
      selectStock(stocks.value[0].symbol)
    }
  } catch (e) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

const selectStock = async (symbol) => {
  selectedSymbol.value = symbol
  await loadReport(symbol)
}

const loadReport = async (symbol) => {
  reportLoading.value = true
  reportError.value = ''
  report.value = null
  
  try {
    const res = await api.analyzeStock(symbol, 'daily')
    if (res.data) {
      report.value = res.data
    }
    
    if (['000001.SH', '000300.SH', '399006.SZ'].includes(symbol)) {
      await loadMarketIndexes()
    }
    
    // Load chart data
    await loadChartData()
  } catch (e) {
    reportError.value = e.message
  } finally {
    reportLoading.value = false
  }
}

const loadMarketIndexes = async () => {
  try {
    const indexes = [
      { symbol: '000001.SH', name: '上证指数' },
      { symbol: '000300.SH', name: '沪深300' },
      { symbol: '399006.SZ', name: '创业板指' }
    ]
    
    const results = []
    for (const idx of indexes) {
      try {
        const res = await api.analyzeStock(idx.symbol, 'daily')
        if (res.data) {
          results.push({
            symbol: idx.symbol,
            name: idx.name,
            price: res.data.close,
            change: res.data.change_pct
          })
        }
      } catch (e) {
        // skip
      }
    }
    marketIndexes.value = results
  } catch (e) {
    // skip
  }
}

const handleRefresh = async () => {
  if (!selectedSymbol.value) {
    showToast('请先选择股票')
    return
  }
  
  refreshing.value = true
  
  try {
    // 刷新当前选中的股票数据
    const res = await api.refreshSymbol(selectedSymbol.value, 'daily')
    if (res.data && res.data.success) {
      showToast('数据已刷新')
      // 重新加载报告
      await loadReport(selectedSymbol.value)
    } else {
      showToast(res.data?.message || '刷新失败')
    }
  } catch (e) {
    showToast('刷新失败')
  } finally {
    refreshing.value = false
  }
}

const getSignalClass = (signal) => {
  if (signal === '买入') return 'buy'
  if (signal === '卖出') return 'sell'
  return 'hold'
}

const getActionReason = (report) => {
  if (report.signal === '买入' && report.confidence >= 80) {
    return '多级别共振信号明确，建议关注'
  }
  if (report.signal === '卖出') {
    return '注意风险，建议减仓'
  }
  if (report.beichi === '背驰') {
    return '出现背驰信号，关注转折点'
  }
  if (report.fenxing === '顶分型') {
    return '注意回调风险'
  }
  if (report.fenxing === '底分型') {
    return '关注反弹机会'
  }
  return '等待更明确信号'
}

onMounted(() => {
  loadStocks()
})
</script>

<style>
.home {
  min-height: 100vh;
  background: #0d0f1a;
  color: #e2e8f0;
}

.home-header {
  background: linear-gradient(135deg, #1a1f35, #141828);
  padding: 16px 20px;
  border-bottom: 1px solid #252a42;
  text-align: center;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.home-header h1 {
  font-size: 18px;
  font-weight: 700;
  color: #e2e8f0;
  margin: 0;
}

.refresh-btn {
  font-size: 12px;
}

.home-content {
  display: flex;
  min-height: calc(100vh - 60px);
}

.stock-list-section {
  width: 280px;
  min-width: 280px;
  background: #141828;
  border-right: 1px solid #252a42;
  overflow-y: auto;
  height: calc(100vh - 60px);
}

.report-section {
  flex: 1;
  background: #0d0f1a;
  overflow-y: auto;
  height: calc(100vh - 60px);
  padding: 12px;
}

.section-title {
  font-size: 14px;
  font-weight: 700;
  color: #4f8fce;
  padding: 12px 16px;
  border-bottom: 1px solid #252a42;
  background: #141828;
}

.loading {
  padding: 40px;
  text-align: center;
}

.error {
  color: #ef4444;
  padding: 20px;
  text-align: center;
}

/* Stock list styles */
.stock-list-section :deep(.van-cell-group) {
  background: transparent;
}

.stock-list-section :deep(.van-cell-group__title) {
  background: #1a1f35;
  color: #8899aa;
  font-size: 12px;
  padding: 8px 12px;
}

.stock-list-section :deep(.van-cell) {
  background: #141828;
  color: #e2e8f0;
  border-bottom: 1px solid #1f2638;
}

.stock-list-section :deep(.van-cell__title) {
  color: #e2e8f0;
}

.stock-list-section :deep(.van-cell__label) {
  color: #6b7280;
}

.stock-list-section :deep(.van-cell.active) {
  background: #1f2937;
  border-left: 3px solid #4f8fce;
}

/* Report styles */
.report-content {
  padding: 0;
}

.report-block {
  background: #141828;
  border: 1px solid #252a42;
  border-radius: 10px;
  margin-bottom: 12px;
  overflow: hidden;
}

.block-title {
  font-size: 14px;
  font-weight: 700;
  color: #f0b429;
  padding: 12px 14px;
  background: #1a1f35;
  border-bottom: 1px solid #252a42;
}

/* Index grid */
.index-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  padding: 12px;
}

.index-card {
  background: #1a1f35;
  border-radius: 8px;
  padding: 10px;
  text-align: center;
}

.idx-name {
  font-size: 11px;
  color: #8899aa;
  margin-bottom: 4px;
}

.idx-price {
  font-size: 16px;
  font-weight: 700;
}

.idx-change {
  font-size: 12px;
  font-weight: 600;
  margin-top: 2px;
}

.up { color: #ef4444; }
.down { color: #22c55e; }

/* Price info */
.price-info {
  display: flex;
  align-items: baseline;
  padding: 16px;
  gap: 12px;
  border-bottom: 1px solid #252a42;
}

.current-price {
  font-size: 28px;
  font-weight: 700;
}

.price-change {
  font-size: 16px;
  font-weight: 600;
}

/* Signal box */
.signal-box {
  text-align: center;
  padding: 14px;
  background: #1a1f35;
  border-bottom: 1px solid #252a42;
}

.signal-label {
  font-size: 12px;
  color: #8899aa;
}

.signal-value {
  font-size: 20px;
  font-weight: 700;
  margin: 6px 0;
}

.signal-value.buy { color: #ef4444; }
.signal-value.sell { color: #22c55e; }
.signal-value.hold { color: #f0b429; }

.confidence {
  font-size: 12px;
  color: #6b7280;
}

/* MA grid */
.ma-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  padding: 12px;
  border-bottom: 1px solid #252a42;
}

.ma-item {
  background: #1a1f35;
  border-radius: 6px;
  padding: 8px;
  text-align: center;
}

.ma-label {
  display: block;
  font-size: 10px;
  color: #6b7280;
  margin-bottom: 2px;
}

.ma-value {
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
}

/* Indicators */
.indicator-section {
  padding: 12px;
  border-bottom: 1px solid #252a42;
}

.indicator-title {
  font-size: 12px;
  font-weight: 700;
  color: #00d4aa;
  margin-bottom: 8px;
}

.indicator-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  padding: 4px 0;
  color: #a0aec0;
}

.indicator-row span:last-child {
  color: #e2e8f0;
  font-weight: 500;
}

/* Levels */
.levels-section {
  padding: 12px;
  border-bottom: 1px solid #252a42;
}

.levels-row {
  margin-bottom: 8px;
}

.level-label {
  font-size: 12px;
  color: #8899aa;
  display: block;
  margin-bottom: 4px;
}

.level-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.level-tag {
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
}

.level-tag.support {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.level-tag.resistance {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

/* Action */
.action-section {
  padding: 14px;
  background: #1a1f35;
}

.action-title {
  font-size: 12px;
  font-weight: 700;
  color: #f0b429;
  margin-bottom: 10px;
}

.action-content {
  display: flex;
  align-items: center;
  gap: 10px;
}

.action-tag {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 700;
}

.action-tag.buy {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.action-tag.sell {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.action-tag.hold {
  background: rgba(240, 180, 41, 0.15);
  color: #f0b429;
}

.action-reason {
  font-size: 12px;
  color: #a0aec0;
}

/* Chart tabs */
.chart-tabs {
  display: flex;
  background: #1a1f35;
  padding: 8px;
  gap: 4px;
  border-bottom: 1px solid #252a42;
}

.chart-tabs .tab {
  flex-shrink: 0;
  text-align: center;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 11px;
  background: #141828;
  color: #6b7280;
}

.chart-tabs .tab.active {
  background: #4f8fce;
  color: #fff;
}

.chart-container {
  background: #1e2538;
  padding: 10px;
}

.empty-report {
  text-align: center;
  padding: 60px 20px;
  color: #6b7280;
}

/* Responsive */
@media (max-width: 768px) {
  .home-content {
    flex-direction: column;
  }
  
  .stock-list-section {
    width: 100%;
    min-width: 100%;
    height: auto;
    max-height: 40vh;
    border-right: none;
    border-bottom: 1px solid #252a42;
  }
  
  .report-section {
    height: auto;
  }
  
  .index-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .ma-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
