import { useQuery, useQueryClient } from '@tanstack/react-query';
import { newsApi } from '../services/api';

// ==================== 类型定义 ====================

export interface NewsItem {
  id: string;
  title: string;
  content: string;
  source: string;
  publishTime: string;
  relatedStocks?: string[];
  investmentAdvice?: string;
}

export interface NewsParams {
  limit?: number;
  page?: number;
}

// ==================== 新闻相关 Hooks ====================

/**
 * 获取最新财经新闻列表
 */
export function useLatestNews(params?: NewsParams) {
  return useQuery({
    queryKey: ['news', 'latest', params],
    queryFn: () => newsApi.getLatest(params),
    staleTime: 10 * 60 * 1000, // 新闻10分钟内不更新
  });
}

/**
 * 获取新闻详情
 */
export function useNewsDetail(id: string) {
  return useQuery({
    queryKey: ['news', 'detail', id],
    queryFn: () => newsApi.getNewsDetail(id),
    enabled: !!id,
  });
}

/**
 * 刷新新闻列表
 */
export function useRefreshNews() {
  const queryClient = useQueryClient();

  return () => {
    queryClient.invalidateQueries({ queryKey: ['news'] });
  };
}

/**
 * 预加载新闻数据
 */
export function usePrefetchNews(params?: NewsParams) {
  const queryClient = useQueryClient();

  return () => {
    queryClient.prefetchQuery({
      queryKey: ['news', 'latest', params],
      queryFn: () => newsApi.getLatest(params),
    });
  };
}
