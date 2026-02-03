import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { KlineData, IndicatorData } from './stockStore';

interface MarketState {
  // 上证指数数据
  indexKline: KlineData[];
  indexIndicators: IndicatorData | null;
  
  // 大盘情绪数据
  sentimentScore: number;
  bullBearRatio: number;
  
  // 设置方法
  setIndexKline: (data: KlineData[]) => void;
  setIndexIndicators: (data: IndicatorData | null) => void;
  setSentimentData: (score: number, ratio: number) => void;
  clearMarketData: () => void;
}

export const useMarketStore = create<MarketState>()(
  persist(
    (set) => ({
      indexKline: [],
      indexIndicators: null,
      sentimentScore: 50,
      bullBearRatio: 1,
      
      setIndexKline: (data) => set({ indexKline: data }),
      setIndexIndicators: (data) => set({ indexIndicators: data }),
      setSentimentData: (score, ratio) => set({ 
        sentimentScore: score, 
        bullBearRatio: ratio 
      }),
      clearMarketData: () => set({ 
        indexKline: [], 
        indexIndicators: null 
      }),
    }),
    {
      name: 'market-storage',
    }
  )
);

// 导出类型以保持 API 兼容性
export type { KlineData, IndicatorData };
