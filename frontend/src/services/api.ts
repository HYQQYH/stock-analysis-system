import axios, { AxiosError } from 'axios';

// 创建 axios 实例 - AI分析需要较长时间，设置为5分钟
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 300000, // 5分钟 = 300秒
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
  
  // 大盘AI分析接口
  getMarketAnalysis: (params: { kline_type: string; days?: number }) => 
    get<{
      index_code: string;
      index_name: string;
      kline_type: string;
      days: number;
      analysis_time: string;
      trend: string;
      support_levels: number[];
      resistance_levels: number[];
      sentiment_score: number;
      confidence_score: number;
      llm_provider: string;
      llm_model: string;
      token_usage: {
        prompt_tokens: number;
        completion_tokens: number;
        total_tokens: number;
      };
      analysis_content: string;
      success: boolean;
      error_message: string | null;
    }>('/market/analysis', params),
  
  // 大盘分析历史接口
  getMarketAnalysisHistory: (params?: { page?: number; pageSize?: number }) => 
    get<{
      total: number;
      page: number;
      page_size: number;
      data: Array<{
        analysis_id: string;
        stock_code: string;
        analysis_mode: string;
        status: string;
        analysis_time: string;
        confidence_score: number | null;
        created_at: string;
        kline_type: string;
      }>;
    }>('/market/analysis/history', params),
  
  // 获取大盘分析详情
  getMarketAnalysisResult: (analysisId: string) => 
    get<{
      analysis_id: string;
      stock_code: string;
      analysis_mode: string;
      kline_type: string;
      status: string;
      analysis_time: string;
      confidence_score: number | null;
      llm_model: string | null;
      analysis_result: string | null;
      trading_advice: {
        direction: string;
        target_price?: number;
        stop_loss?: number;
        take_profit?: number;
        holding_period?: number;
        risk_level?: string;
      } | null;
      error_message: string | null;
      created_at: string;
      updated_at: string;
    }>(`/market/analysis/${analysisId}`),
  
  // 删除大盘分析记录
  deleteMarketAnalysis: (analysisId: string) => 
    del(`/market/analysis/${analysisId}`),
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
      error_message?: string | null;
      created_at: string;
      updated_at: string;
    }>(`/analysis/${analysisId}`),
  
  // 后端返回格式: { code: 200, message: "success", data: { total: N, page: 1, page_size: 10, data: [...] } }
  getHistory: (params?: { page?: number; pageSize?: number; stockCode?: string; analysisType?: string }) => 
    get<{ total: number; page: number; page_size: number; data: Array<{ analysis_id: string; stock_code: string; analysis_mode: string; status: string; analysis_time: string; confidence_score: number | null; created_at: string }> }>('/analysis/history', params),
  
  deleteAnalysis: (id: string) => del(`/analysis/${id}`),
};

// 新闻相关 API
export const newsApi = {
  getLatest: (params?: { limit?: number; page?: number }) => 
    get<Array<{ id: string; title: string; content: string; source: string; publishTime: string; relatedStocks?: string[] }>>('/news/latest', params),
  
  getNewsDetail: (id: string) => 
    get<{ id: string; title: string; content: string; source: string; publishTime: string; investmentAdvice?: string }>(`/news/${id}`),
};

// Asserts相关 API
export interface FileItem {
  name: string;
  path: string;
  is_dir: boolean;
  size: number;
}

export interface AssertsStructure {
  summary_dates: string[];
  output_files: string[];
}

export interface FileContent {
  name: string;
  path: string;
  content: string;
  content_type: string;
  size: number;
}

export const assertsApi = {
  // 获取asserts目录结构
  getStructure: () => get<AssertsStructure>('/asserts/structure'),
  
  // 获取指定文件夹下的文件列表
  getFiles: (folder?: string) => 
    get<FileItem[]>('/asserts/files', folder ? { folder } : undefined),
  
  // 获取文件内容
  getContent: (path: string) => get<FileContent>('/asserts/content', { path }),
  
  // 下载文件
  download: (path: string) => {
    const url = `${api.defaults.baseURL}/asserts/download?path=${encodeURIComponent(path)}`;
    window.open(url, '_blank');
  }
};

export default api;
