import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface KlineData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  amount?: number;
}

export interface StockInfo {
  code: string;
  name: string;
  industry?: string;
  region?: string;
  market?: string;
}

export interface IndicatorData {
  macd?: {
    dif: number[];
    dea: number[];
    macd: number[];
  };
  kdj?: {
    k: number[];
    d: number[];
    j: number[];
  };
  rsi?: number[];
}

export interface StockState {
  // 当前查询的股票信息
  currentStock: StockInfo | null;
  klineData: KlineData[];
  indicators: IndicatorData | null;
  klineType: 'day' | 'week' | 'month';
  sectorName: string;
  
  // Actions
  setCurrentStock: (stock: StockInfo | null) => void;
  setKlineData: (data: KlineData[]) => void;
  setIndicators: (data: IndicatorData | null) => void;
  setKlineType: (type: 'day' | 'week' | 'month') => void;
  setSectorName: (name: string) => void;
  clearStockData: () => void;
}

export const useStockStore = create<StockState>()(
  persist(
    (set) => ({
      // 初始状态
      currentStock: null,
      klineData: [],
      indicators: null,
      klineType: 'day',
      sectorName: '',
      
      // Actions
      setCurrentStock: (stock) => set({ currentStock: stock }),
      setKlineData: (data) => set({ klineData: data }),
      setIndicators: (data) => set({ indicators: data }),
      setKlineType: (type) => set({ klineType: type }),
      setSectorName: (name) => set({ sectorName: name }),
      clearStockData: () => set({
        currentStock: null,
        klineData: [],
        indicators: null,
      }),
    }),
    {
      name: 'stock-storage',
      partialize: (state) => ({
        klineType: state.klineType,
        sectorName: state.sectorName,
      }),
    }
  )
);
