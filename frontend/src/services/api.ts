import axios, { AxiosError } from 'axios';

// 创建 axios 实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
});

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const message = (error.response?.data as { message?: string })?.message || error.message;
    return Promise.reject(new Error(message));
  }
);

// API 辅助函数
async function get<T>(url: string, params?: Record<string, unknown>): Promise<T> {
  const response = await api.get<{ data: T }>(url, { params });
  return response.data.data;
}

async function post<T>(url: string, data?: Record<string, unknown>): Promise<T> {
  const response = await api.post<{ data: T }>(url, data);
  return response.data.data;
}

async function del(url: string): Promise<void> {
  await api.delete(url);
}

// 股票相关 API
export const stockApi = {
  getStockInfo: (code: string) => 
    get<{ code: string; name: string; industry?: string }>(`/stocks/${code}/info`),
  
  getKline: (code: string, params: { type: string; startDate?: string; endDate?: string }) => 
    get<Array<{ date: string; open: number; high: number; low: number; close: number; volume: number; amount: number }>>(`/stocks/${code}/kline`, params),
  
  getIndicators: (code: string, params: { type: string; indicators?: string }) => 
    get<{
      macd?: { dif: number[]; dea: number[]; macd: number[] };
      kdj?: { k: number[]; d: number[]; j: number[] };
      rsi?: number[];
    }>(`/stocks/${code}/indicators`, params),
};

// 大盘相关 API
export const marketApi = {
  getIndex: (params: { type: string; startDate?: string; endDate?: string }) => 
    get<Array<{ date: string; open: number; high: number; low: number; close: number; volume: number }>>('/market/index', params),
  
  getSentiment: (date?: string) => 
    get<{ sentimentScore: number; bullBearRatio: number; riseCount: number; fallCount: number }>('/market/sentiment', { date }),
  
  getFundFlow: (params: { startDate?: string; endDate?: string }) => 
    get<Array<{ date: string; mainNetInflow: number; superLargeNetInflow: number; largeNetInflow: number }>>('/market/fund-flow', params),
  
  getLimitUp: (date?: string) => 
    get<Array<{ code: string; name: string; changePct: number; price: number; amount: number; turnoverRate: number; continuousLimit: number; industry: string }>>('/market/limit-up', { date }),
};

// 分析相关 API
export const analysisApi = {
  submitAnalysis: (data: { stock_code: string; analysis_mode: string; kline_type: string; sector_names?: string[]; include_news?: boolean }) => 
    post<{ analysis_id: string; status: string }>('/analysis', data),
  
  // 注意：后端返回的是 AnalysisDetail 结构，分析结果在 result.analysis_result 中
  getAnalysisResult: (analysisId: string) => 
    get<{
      id: string; analysis_id: string; stock_code: string; analysis_mode: string; status: string;
      analysis_time: string;
      result: {
        analysis_result: string;
        trading_advice: { direction: string; target_price?: number; stop_loss?: number; take_profit?: number; holding_period?: number; risk_level?: string };
        confidence_score: number;
        llm_model?: string;
      };
    }>(`/analysis/${analysisId}`),
  
  // 后端返回格式: { code: 200, message: "success", data: { total: N, page: 1, page_size: 10, data: [...] } }
  getHistory: (params?: { page?: number; pageSize?: number; stockCode?: string }) => 
    get<{ total: number; page: number; page_size: number; data: Array<{ id: string; stock_code: string; analysis_mode: string; status: string; analysis_time: string; confidence_score: number; created_at: string }> }>('/analysis/history', params),
  
  deleteAnalysis: (id: string) => del(`/analysis/${id}`),
};

// 新闻相关 API
export const newsApi = {
  getLatest: (params?: { limit?: number; page?: number }) => 
    get<Array<{ id: string; title: string; content: string; source: string; publishTime: string; relatedStocks?: string[] }>>('/news/latest', params),
  
  getNewsDetail: (id: string) => 
    get<{ id: string; title: string; content: string; source: string; publishTime: string; investmentAdvice?: string }>(`/news/${id}`),
};

export default api;
