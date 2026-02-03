import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { stockApi } from '../services/api';

// ==================== 类型定义 ====================

export interface KlineData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  amount: number;
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

export interface StockInfo {
  code: string;
  name: string;
  industry?: string;
}

// ==================== 股票相关 Hooks ====================

/**
 * 获取股票基本信息
 */
export function useStockInfo(code: string) {
  return useQuery({
    queryKey: ['stock', 'info', code],
    queryFn: () => stockApi.getStockInfo(code),
    enabled: !!code && code.length === 6,
    staleTime: 10 * 60 * 1000, // 10分钟内不重新请求
  });
}

/**
 * 获取股票K线数据
 */
export function useKlineData(
  code: string,
  params: { type: string; startDate?: string; endDate?: string }
) {
  return useQuery({
    queryKey: ['stock', 'kline', code, params],
    queryFn: () => stockApi.getKline(code, params),
    enabled: !!code && code.length === 6 && !!params.type,
    staleTime: 5 * 60 * 1000, // 5分钟内不重新请求
  });
}

/**
 * 获取股票技术指标
 */
export function useIndicatorData(
  code: string,
  params: { type: string; indicators?: string }
) {
  return useQuery({
    queryKey: ['stock', 'indicators', code, params],
    queryFn: () => stockApi.getIndicators(code, params),
    enabled: !!code && code.length === 6 && !!params.type,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 预加载股票数据（用于数据预加载场景）
 */
export function usePrefetchStockData(code: string, klineType: string) {
  const queryClient = useQueryClient();

  return () => {
    queryClient.prefetchQuery({
      queryKey: ['stock', 'info', code],
      queryFn: () => stockApi.getStockInfo(code),
    });

    queryClient.prefetchQuery({
      queryKey: ['stock', 'kline', code, { type: klineType }],
      queryFn: () => stockApi.getKline(code, { type: klineType }),
    });

    queryClient.prefetchQuery({
      queryKey: ['stock', 'indicators', code, { type: klineType }],
      queryFn: () => stockApi.getIndicators(code, { type: klineType }),
    });
  };
}
