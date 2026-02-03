import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type AnalysisMode = 
  | '基础面技术面综合分析'
  | '波段交易分析'
  | '短线T+1分析'
  | '涨停反包分析'
  | '投机套利分析'
  | '公司估值分析';

export interface TradingAdvice {
  direction: '买入' | '卖出' | '持有' | '观望';
  targetPrice?: number;
  stopLoss?: number;
  takeProfit?: number;
  holdingPeriod?: number;
  riskLevel?: '低' | '中' | '高';
  quantity?: number;
}

export interface AnalysisResult {
  id: string;
  stockCode: string;
  stockName?: string;
  analysisMode: AnalysisMode;
  analysisTime: string;
  summary: string;
  details: string;
  tradingAdvice: TradingAdvice;
  confidenceScore: number;
  llmModel?: string;
  status: 'pending' | 'completed' | 'failed';
  errorMessage?: string;
}

interface AnalysisState {
  // 分析历史记录
  history: AnalysisResult[];
  // 当前正在进行的分析
  currentAnalysis: AnalysisResult | null;
  
  // Actions
  addAnalysis: (result: AnalysisResult) => void;
  updateAnalysis: (id: string, updates: Partial<AnalysisResult>) => void;
  removeAnalysis: (id: string) => void;
  clearHistory: () => void;
  setCurrentAnalysis: (analysis: AnalysisResult | null) => void;
  
  // Getters
  getHistoryByStock: (stockCode: string) => AnalysisResult[];
}

export const useAnalysisStore = create<AnalysisState>()(
  persist(
    (set, get) => ({
      // 初始状态
      history: [],
      currentAnalysis: null,
      
      // Actions
      addAnalysis: (result) => set((state) => ({
        history: [result, ...state.history].slice(0, 100), // 保留最近100条
      })),
      
      updateAnalysis: (id, updates) => set((state) => ({
        history: state.history.map((item) =>
          item.id === id ? { ...item, ...updates } : item
        ),
        currentAnalysis: state.currentAnalysis?.id === id
          ? { ...state.currentAnalysis, ...updates }
          : state.currentAnalysis,
      })),
      
      removeAnalysis: (id) => set((state) => ({
        history: state.history.filter((item) => item.id !== id),
        currentAnalysis: state.currentAnalysis?.id === id ? null : state.currentAnalysis,
      })),
      
      clearHistory: () => set({ history: [] }),
      
      setCurrentAnalysis: (analysis) => set({ currentAnalysis: analysis }),
      
      // Getters
      getHistoryByStock: (stockCode) => {
        return get().history.filter((item) => item.stockCode === stockCode);
      },
    }),
    {
      name: 'analysis-storage',
    }
  )
);
