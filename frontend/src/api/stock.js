import axios from 'axios'

const API_BASE = '/api'

const api = {
  // 获取股票列表
  getStocks() {
    return axios.get(`${API_BASE}/stocks`)
  },

  // 获取K线数据
  getKline(symbol, period = 'daily') {
    return axios.get(`${API_BASE}/kline/${symbol}`, { params: { period } })
  },

  // 分析股票
  analyzeStock(symbol, period = 'daily') {
    return axios.get(`${API_BASE}/analyze/${symbol}`, { params: { period } })
  },

  // 实时行情
  getRealtime(symbol) {
    return axios.get(`${API_BASE}/realtime/${symbol}`)
  },

  // 分时图数据
  getIntraday(symbol) {
    return axios.get(`${API_BASE}/intraday/${symbol}`)
  },
}

export default api
