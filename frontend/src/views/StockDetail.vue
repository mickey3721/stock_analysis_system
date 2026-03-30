<template>
  <div class="stock-detail">
    <div class="header">
      <span class="back" @click="goBack">&larr;</span>
      <h2>{{ stockName }}</h2>
      <span class="refresh" @click="loadData">&#x21bb;</span>
    </div>
    
    <!-- 周期切换 -->
    <div class="period-tabs">
      <span 
        v-for="p in periods" 
        :key="p.value"
        :class="['tab', period === p.value ? 'active' : '']"
        @click="changePeriod(p.value)"
      >
        {{ p.label }}
      </span>
    </div>
    <div v-if="isIndexOrFuture" class="index-tip">指数/期货仅支持分时/日线</div>
    
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    
    <div v-else-if="analysis">
      <!-- 价格信息 -->
      <div class="price-card">
        <div class="price">{{ analysis.close }}</div>
        <div class="change" :class="analysis.change_pct >= 0 ? 'up' : 'down'">
          {{ analysis.change_pct >= 0 ? '+' : '' }}{{ analysis.change_pct }}%
        </div>
      </div>
      
      <!-- 综合信号 -->
      <div class="signal-card">
        <div class="signal-label">综合信号</div>
        <div class="signal-value" :class="analysis.signal === '买入' ? 'buy' : (analysis.signal === '卖出' ? 'sell' : 'hold')">
          {{ analysis.signal }}
        </div>
        <div class="confidence">置信度: {{ analysis.confidence }}%</div>
      </div>
      
      <!-- 均线 (EMA) -->
      <div class="ma-list">
        <span v-if="analysis.ma5">EMA5: {{ analysis.ma5.toFixed(2) }}</span>
        <span v-if="analysis.ma26">EMA26: {{ analysis.ma26.toFixed(2) }}</span>
        <span v-if="analysis.ma89">EMA89: {{ analysis.ma89.toFixed(2) }}</span>
        <span v-if="analysis.ma144">EMA144: {{ analysis.ma144.toFixed(2) }}</span>
      </div>
      
      <!-- 技术指标 -->
      <div class="info-card">
        <h3>技术指标</h3>
        <div class="info-row">
          <span>多空通道:</span>
          <span>{{ analysis.channel_signal }}</span>
        </div>
        <div class="info-row">
          <span>九转序列:</span>
          <span>{{ analysis.seq_desc }}</span>
        </div>
        <div class="info-row">
          <span>MACD:</span>
          <span>{{ analysis.macd_desc }}</span>
        </div>
      </div>
      
      <!-- 缠论 -->
      <div class="info-card">
        <h3>缠论分析</h3>
        <div class="info-row">
          <span>分型:</span>
          <span>{{ analysis.fenxing }}</span>
        </div>
        <div class="info-row">
          <span>笔方向:</span>
          <span>{{ analysis.bi_status }}</span>
        </div>
        <div class="info-row">
          <span>背驰:</span>
          <span>{{ analysis.beichi }}</span>
        </div>
      </div>
      
      <!-- 支撑阻力 -->
      <div class="info-card">
        <h3>支撑位</h3>
        <div class="levels">
          <span v-for="(s, i) in analysis.support_levels" :key="i" class="level support">
            {{ s.type }}: {{ s.level.toFixed(2) }}
          </span>
        </div>
      </div>
      <div class="info-card">
        <h3>阻力位</h3>
        <div class="levels">
          <span v-for="(r, i) in analysis.resistance_levels" :key="i" class="level resistance">
            {{ r.type }}: {{ r.level.toFixed(2) }}
          </span>
        </div>
      </div>
      
      <!-- K线图/分时图 -->
      <div class="chart-container">
        <h3>{{ period === 'intraday' ? '分时走势' : 'K线走势' }}</h3>
        <v-chart :option="chartOption" autoresize style="height: 350px" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as echarts from 'echarts'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { CandlestickChart, LineChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, DataZoomComponent, LegendComponent } from 'echarts/components'
import api from '../api/stock'

use([CanvasRenderer, CandlestickChart, LineChart, BarChart, GridComponent, TooltipComponent, DataZoomComponent, LegendComponent])

const route = useRoute()
const router = useRouter()
const symbol = route.params.symbol

const isIndexOrFuture = computed(() => {
  return ['000001.SH', '000300.SH', '399006.SZ', '399001.SZ', 'XAUUSD', 'CL=F'].includes(symbol)
})

const periods = computed(() => {
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

const period = ref('daily')
const loading = ref(true)
const error = ref('')
const analysis = ref(null)
const klineData = ref([])
const intradayData = ref({ times: [], prices: [], volumes: [] })
const stockName = ref('')

const loadData = async () => {
  loading.value = true
  error.value = ''
  try {
    if (period.value === 'intraday') {
      // 加载分时数据
      const [analysisRes, intradayRes] = await Promise.all([
        api.analyzeStock(symbol, 'daily'),
        api.getIntraday(symbol)
      ])
      
      if (analysisRes.data) {
        analysis.value = analysisRes.data
        stockName.value = analysisRes.data.name
      }
      
      if (intradayRes.data) {
        intradayData.value = intradayRes.data
      }
    } else {
      // 加载K线数据
      const [analysisRes, klineRes] = await Promise.all([
        api.analyzeStock(symbol, period.value),
        api.getKline(symbol, period.value)
      ])
      
      if (analysisRes.data) {
        analysis.value = analysisRes.data
        stockName.value = analysisRes.data.name
      }
      
      if (klineRes.data && klineRes.data.dates) {
        klineData.value = klineRes.data.dates.map((d, i) => ({
          date: d,
          open: klineRes.data.opens[i],
          high: klineRes.data.highs[i],
          low: klineRes.data.lows[i],
          close: klineRes.data.closes[i],
          volume: klineRes.data.volumes[i]
        }))
      }
    }
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

const changePeriod = (p) => {
  period.value = p
  loadData()
}

const intradayOption = computed(() => {
  if (!intradayData.value.times.length) return {}
  
  const times = intradayData.value.times
  const prices = intradayData.value.prices
  const volumes = intradayData.value.volumes
  
  // 计算均价线
  const avgPrices = []
  let sum = 0
  for (let i = 0; i < prices.length; i++) {
    sum += prices[i]
    avgPrices.push((sum / (i + 1)).toFixed(2))
  }
  
  return {
    tooltip: { 
      trigger: 'axis', 
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['价格', '均价', '成交量'],
      top: 0
    },
    grid: [
      { left: '10%', right: '10%', height: '55%' },
      { left: '10%', right: '10%', top: '72%', height: '15%' }
    ],
    xAxis: [
      { type: 'category', data: times, boundaryGap: false },
      { type: 'category', data: times, boundaryGap: false, gridIndex: 1 }
    ],
    yAxis: [
      { scale: true, splitArea: { show: true } },
      { scale: true, gridIndex: 1, splitNumber: 2 }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 60, end: 100 },
      { type: 'slider', xAxisIndex: [0, 1], start: 60, end: 100 }
    ],
    series: [
      {
        name: '价格',
        type: 'line',
        data: prices,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2, color: '#1976d2' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(25, 118, 210, 0.3)' },
            { offset: 1, color: 'rgba(25, 118, 210, 0.05)' }
          ])
        }
      },
      {
        name: '均价',
        type: 'line',
        data: avgPrices,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 1, color: '#ff9800' }
      },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumes.map((v, i) => ({
          value: v,
          itemStyle: {
            color: i > 0 && prices[i] >= prices[i-1] ? '#22c55e' : '#ef4444'
          }
        })),
        symbol: 'none'
      }
    ]
  }
})

const chartOption = computed(() => {
  if (period.value === 'intraday') {
    return intradayOption.value
  }
  
  if (!klineData.value.length) return {}
  
  const dates = klineData.value.map(d => d.date)
  const ohlc = klineData.value.map(d => [d.open, d.close, d.low, d.high])
  
  const ma5 = calculateMA(5)
  const ma26 = calculateMA(26)
  const ma89 = calculateMA(89)
  
  // 徐小明短线通道 (25日): 上轨=EMA(H,25), 下轨=EMA(L,25)
  const channel = calculateChannel(25)
  
  return {
    tooltip: { 
      trigger: 'axis', 
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['K线', 'EMA5', 'EMA26', 'EMA89', '通道上轨', '通道下轨', '成交量'],
      top: 0
    },
    grid: [
      { left: '8%', right: '8%', height: '55%' },
      { left: '8%', right: '8%', top: '78%', height: '10%' }
    ],
    xAxis: [
      { type: 'category', data: dates, boundaryGap: true },
      { type: 'category', data: dates, boundaryGap: true, gridIndex: 1 }
    ],
    yAxis: [
      { scale: true, splitArea: { show: true } },
      { scale: true, gridIndex: 1, splitNumber: 2 }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 50, end: 100 },
      { type: 'slider', xAxisIndex: [0, 1], start: 50, end: 100 }
    ],
    series: [
      // 趋势通道 - 上轨
      {
        name: '通道上轨',
        type: 'line',
        data: channel.upper,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 1, color: '#1976d2' }
      },
      // 趋势通道 - 下轨
      {
        name: '通道下轨',
        type: 'line',
        data: channel.lower,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 1, color: '#1976d2' }
      },
      // 趋势通道填充区域
      {
        name: '通道',
        type: 'line',
        data: channel.upper,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 0, color: 'transparent' },
        areaStyle: {
          color: 'rgba(25, 118, 210, 0.1)'
        },
        z: 1
      },
      {
        name: 'EMA5',
        type: 'line',
        data: ma5,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2, color: '#8B4513' },
        z: 5
      },
      {
        name: 'EMA26',
        type: 'line',
        data: ma26,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2, color: '#ff6600' },
        z: 5
      },
      {
        name: 'EMA89',
        type: 'line',
        data: ma89,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2, color: '#ff00ff' },
        z: 5
      },
      {
        name: 'K线',
        type: 'candlestick',
        data: ohlc,
        itemStyle: { 
          color: '#ef4444', 
          color0: '#22c55e', 
          borderColor: '#ef4444', 
          borderColor0: '#22c55e' 
        },
        z: 10
      },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: klineData.value.map(d => ({
          value: d.volume,
          itemStyle: {
            color: d.close >= d.open ? '#22c55e' : '#ef4444'
          }
        })),
        symbol: 'none'
      }
    ]
  }
})

// EMA计算 (指数移动平均)
function calculateEMA(dayCount) {
  const result = []
  const closes = klineData.value.map(d => d.close)
  const alpha = 2 / (dayCount + 1)
  
  // 使用pandas相同的EMA计算方式
  // EMA_today = alpha * price_today + (1 - alpha) * EMA_yesterday
  let ema = null
  
  for (let i = 0; i < klineData.value.length; i++) {
    if (i < dayCount - 1) {
      result.push(null)
      continue
    }
    
    // 初始化EMA为第一个价格
    if (ema === null) {
      ema = closes[i - dayCount + 1]
    }
    
    // 迭代计算EMA
    ema = alpha * closes[i] + (1 - alpha) * ema
    result.push(parseFloat(ema.toFixed(2)))
  }
  return result
}

// 保持兼容性的别名
const calculateMA = calculateEMA

// 徐小明趋势通道: 上轨=EMA(H,25), 下轨=EMA(L,25)
function calculateChannel(dayCount) {
  const upper = []
  const lower = []
  const closes = klineData.value.map(d => d.close)
  const highs = klineData.value.map(d => d.high)
  const lows = klineData.value.map(d => d.low)
  
  for (let i = 0; i < klineData.value.length; i++) {
    if (i < dayCount - 1) {
      upper.push('-')
      lower.push('-')
      continue
    }
    
    // 计算EMA(最高价, dayCount) 作为上轨
    let emaHigh = highs[i]
    const alpha = 2 / (dayCount + 1)
    for (let j = 0; j < dayCount && i - j >= 0; j++) {
      emaHigh = alpha * highs[i - j] + (1 - alpha) * emaHigh
    }
    
    // 计算EMA(最低价, dayCount) 作为下轨
    let emaLow = lows[i]
    for (let j = 0; j < dayCount && i - j >= 0; j++) {
      emaLow = alpha * lows[i - j] + (1 - alpha) * emaLow
    }
    
    upper.push(emaHigh.toFixed(2))
    lower.push(emaLow.toFixed(2))
  }
  
  return { upper, lower }
}

onMounted(() => {
  loadData()
})

const goBack = () => router.back()
</script>

<style scoped>
.stock-detail { padding-bottom: 20px; }
.header {
  background: #1976d2;
  color: white;
  padding: 12px 16px;
  display: flex;
  align-items: center;
}
.header .back {
  font-size: 20px;
  margin-right: 12px;
  cursor: pointer;
}
.header h2 { margin: 0; font-size: 16px; flex: 1; }
.header .refresh {
  font-size: 20px;
  cursor: pointer;
}

.period-tabs {
  display: flex;
  background: #fff;
  padding: 8px;
  gap: 4px;
  border-bottom: 1px solid #eee;
  overflow-x: auto;
}
.period-tabs .tab {
  flex-shrink: 0;
  text-align: center;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 12px;
  background: #f5f5f5;
  color: #666;
}
.period-tabs .tab.active {
  background: #1976d2;
  color: #fff;
}

.index-tip {
  background: #fff3cd;
  color: #856404;
  padding: 6px 12px;
  font-size: 12px;
  text-align: center;
  border-bottom: 1px solid #ffeaa7;
}

.loading, .error { padding: 20px; text-align: center; }
.error { color: red; }

.price-card {
  background: #fff;
  padding: 12px;
  text-align: center;
  border-bottom: 1px solid #eee;
}
.price-card .price {
  font-size: 24px;
  font-weight: bold;
}
.price-card .change {
  font-size: 14px;
  margin-top: 4px;
}
.change.up { color: #ef4444; }
.change.down { color: #22c55e; }

.signal-card {
  background: #fff;
  padding: 12px;
  text-align: center;
  border-bottom: 1px solid #eee;
}
.signal-label { font-size: 12px; color: #666; }
.signal-value {
  font-size: 18px;
  font-weight: bold;
  margin: 4px 0;
}
.signal-value.buy { color: #ef4444; }
.signal-value.sell { color: #22c55e; }
.signal-value.hold { color: #999; }
.confidence { font-size: 12px; color: #666; }

.ma-list {
  background: #fff;
  padding: 8px 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  border-bottom: 1px solid #eee;
}
.ma-list span {
  font-size: 12px;
  color: #333;
}

.info-card {
  background: #fff;
  padding: 10px 12px;
  margin-top: 8px;
}
.info-card h3 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #333;
}
.info-row {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  border-bottom: 1px solid #f5f5f5;
  font-size: 12px;
}
.info-row:last-child { border: none; }

.levels {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.level {
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 12px;
}
.level.support {
  background: #fce7e7;
  color: #ef4444;
}
.level.resistance {
  background: #e7f5e7;
  color: #22c55e;
}

.chart-container {
  margin-top: 8px;
  background: #fff;
  padding: 10px;
}
.chart-container h3 {
  margin: 0 0 8px 0;
  font-size: 14px;
}
</style>
