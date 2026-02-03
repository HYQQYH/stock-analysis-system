import { useQuery, useQueryClient } from '@tanstack/react-query';
import { marketApi } from '../services/api';

// ==================== 类型定义 ====================

export interface MarketIndexData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface MarketSentiment {
  sentimentScore: number;
  bullBearRatio: number;
  riseCount: number;
  fallCount: number;
}

export interface FundFlowData {
  date: string;
  mainNetInflow: number;
  superLargeNetInflow: number;
  largeNetInflow: number;
}

export interface LimitUpStock {
  code: string;
  name: string;
  changePct: number;
  price: number;
  amount: number;
  turnoverRate: number;
  continuousLimit: number;
  industry: string;
}

// ==================== 大盘相关 Hooks ====================

/**
 * 获取上证指数K线数据
 */
export function useMarketIndex(params: { type: string; startDate?: string; endDate?: string }) {
  return useQuery({
    queryKey: ['market', 'index', params],
    queryFn: () => marketApi.getIndex(params),
    enabled: !!params.type,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 获取大盘情绪数据
 */
export function useMarketSentiment(date?: string) {
  return useQuery({
    queryKey: ['market', 'sentiment', date],
    queryFn: () => marketApi.getSentiment(date),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 获取大盘资金流向
 */
export function useFundFlow(params: { startDate?: string; endDate?: string }) {
  return useQuery({
    queryKey: ['market', 'fund-flow', params],
    queryFn: () => marketApi.getFundFlow(params),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 获取涨停股池
 */
export function useLimitUp(date?: string) {
  return useQuery({
    queryKey: ['market', 'limit-up', date],
    queryFn: () => marketApi.getLimitUp(date),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 获取完整的大盘数据（组合查询）
 */
export function useMarketOverview(klineType: string = 'day') {
  const indexQuery = useMarketIndex({ type: klineType });
  const sentimentQuery = useMarketSentiment();
  const fundFlowQuery = useFundFlow({});
  const limitUpQuery = useLimitUp();

  return {
    index: indexQuery,
    sentiment: sentimentQuery,
    fundFlow: fundFlowQuery,
    limitUp: limitUpQuery,
    isLoading:
      indexQuery.isLoading ||
      sentimentQuery.isLoading ||
      fundFlowQuery.isLoading ||
      limitUpQuery.isLoading,
    isError:
      indexQuery.isError ||
      sentimentQuery.isError ||
      fundFlowQuery.isError ||
      limitUpQuery.isError,
  };
}

/**
 * 预加载大盘数据
 */
export function usePrefetchMarketData(klineType: string = 'day') {
  const queryClient = useQueryClient();

  return () => {
    queryClient.prefetchQuery({
      queryKey: ['market', 'index', { type: klineType }],
      queryFn: () => marketApi.getIndex({ type: klineType }),
    });

    queryClient.prefetchQuery({
      queryKey: ['market', 'sentiment', undefined],
      queryFn: () => marketApi.getSentiment(),
    });

    queryClient.prefetchQuery({
      queryKey: ['market', 'fund-flow', {}],
      queryFn: () => marketApi.getFundFlow({}),
    });
  };
}

/**
 * 刷新大盘所有数据
 */
export function useRefreshMarketData() {
  const queryClient = useQueryClient();

  return () => {
    queryClient.invalidateQueries({ queryKey: ['market'] });
  };
}
