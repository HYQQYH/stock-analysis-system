import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import { analysisApi } from '../services/api';

// ==================== 类型定义 ====================

export interface TradingAdvice {
  direction: string;
  targetPrice?: number;
  stopLoss?: number;
  takeProfit?: number;
  holdingPeriod?: number;
  riskLevel?: string;
}

export interface AnalysisResult {
  id: string;
  stockCode: string;
  analysisMode: string;
  analysisTime: string;
  analysisResult: string;
  tradingAdvice: TradingAdvice;
  confidenceScore: number;
  status: string;
}

export interface SubmitAnalysisParams {
  stockCode: string;
  klineType: string;
  sectorNames?: string[];
  includeNews?: boolean;
}

export interface HistoryParams {
  page?: number;
  pageSize?: number;
  stockCode?: string;
}

// ==================== 分析相关 Hooks ====================

/**
 * 提交分析任务（异步模式）
 */
export function useSubmitAnalysis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SubmitAnalysisParams) => analysisApi.submitAnalysis(data),
    onSuccess: () => {
      // 分析历史可能已更新
      queryClient.invalidateQueries({ queryKey: ['analysis', 'history'] });
    },
  });
}

/**
 * 获取分析结果（支持轮询）
 */
export function useAnalysisResult(
  analysisId: string,
  options?: Omit<UseQueryOptions<AnalysisResult>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: ['analysis', 'result', analysisId],
    queryFn: () => analysisApi.getAnalysisResult(analysisId),
    enabled: !!analysisId,
    refetchInterval: (query) => {
      // 如果状态是 pending，每2秒轮询一次
      if (query.state.data?.status === 'pending') {
        return 2000;
      }
      return false;
    },
    ...options,
  });
}

/**
 * 获取分析历史记录
 */
export function useAnalysisHistory(params?: HistoryParams) {
  return useQuery({
    queryKey: ['analysis', 'history', params],
    queryFn: () => analysisApi.getHistory(params),
    staleTime: 2 * 60 * 1000, // 2分钟内不重新请求
  });
}

/**
 * 删除分析记录
 */
export function useDeleteAnalysis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => analysisApi.deleteAnalysis(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analysis', 'history'] });
    },
  });
}

/**
 * 手动刷新分析历史
 */
export function useRefreshAnalysisHistory() {
  const queryClient = useQueryClient();

  return () => {
    queryClient.invalidateQueries({ queryKey: ['analysis', 'history'] });
  };
}

/**
 * 预加载分析历史
 */
export function usePrefetchAnalysisHistory(params?: HistoryParams) {
  const queryClient = useQueryClient();

  return () => {
    queryClient.prefetchQuery({
      queryKey: ['analysis', 'history', params],
      queryFn: () => analysisApi.getHistory(params),
    });
  };
}
