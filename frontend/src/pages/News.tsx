import React, { useState, useEffect } from 'react';
import { Card, Modal, Empty, Spin, Tag } from 'antd';
import { NewsList } from '../components';
import { useNewsStore, useLoadingStore, useToastStore } from '../store';
import { newsApi } from '../services/api';

interface NewsDetailData {
  id: string;
  title: string;
  content: string;
  source: string;
  publishTime: string;
  investmentAdvice?: string;
}

function News() {
  const { newsList, setNewsList } = useNewsStore();
  const { newsLoading, setNewsLoading } = useLoadingStore();
  const { showToast } = useToastStore();

  const [keyword, setKeyword] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [total, setTotal] = useState(0);
  const [detailVisible, setDetailVisible] = useState(false);
  const [currentDetail, setCurrentDetail] = useState<NewsDetailData | null>(null);

  // 获取新闻列表
  const fetchNews = async (searchKeyword?: string, pageNum = 1, size = 10) => {
    setNewsLoading(true);
    try {
      const params: { limit?: number; page?: number } = { limit: size, page: pageNum };
      if (searchKeyword) {
        params.page = pageNum;
      }
      const response = await newsApi.getLatest(params);
      
      const newsItems = Array.isArray(response) ? response : [];
      setNewsList(newsItems);
      setTotal(newsItems.length * 10); // 模拟总数
    } catch (err) {
      const message = err instanceof Error ? err.message : '获取新闻失败';
      showToast(message, 'error');
      // 使用模拟数据
      const mockNews = [
        { id: '1', title: 'A股市场今日大涨 沪指突破3400点', source: '财经网', publishTime: new Date().toISOString(), content: '今日A股市场表现强势...', relatedStocks: ['600000', '000001'] },
        { id: '2', title: '银行板块持续走强 主力资金净流入', source: '证券时报', publishTime: new Date().toISOString(), content: '银行板块今日表现活跃...', relatedStocks: ['601398', '601939'] },
        { id: '3', title: '科技股午后拉升 半导体板块涨幅居前', source: '上海证券报', publishTime: new Date().toISOString(), content: '午后科技股集体发力...', relatedStocks: ['688981', '300433'] },
        { id: '4', title: '新能源车销量创新高 产业链有望受益', source: '中国证券报', publishTime: new Date().toISOString(), content: '新能源汽车销量持续增长...', relatedStocks: ['002594', '300750'] },
        { id: '5', title: '医药板块回调 机构称估值已具备吸引力', source: '证券日报', publishTime: new Date().toISOString(), content: '医药板块今日出现调整...', relatedStocks: ['600276', '000566'] },
      ];
      setNewsList(mockNews);
      setTotal(100);
    } finally {
      setNewsLoading(false);
    }
  };

  // 搜索新闻
  const handleSearch = (value: string) => {
    setKeyword(value);
    setPage(1);
    fetchNews(value, 1, pageSize);
  };

  // 分页变化
  const handlePageChange = (newPage: number, newPageSize?: number) => {
    setPage(newPage);
    if (newPageSize) {
      setPageSize(newPageSize);
      fetchNews(keyword, newPage, newPageSize);
    } else {
      fetchNews(keyword, newPage, pageSize);
    }
  };

  // 查看新闻详情
  const handleViewDetail = async (id: string) => {
    try {
      const response = await newsApi.getNewsDetail(id);
      setCurrentDetail(response);
      setDetailVisible(true);
    } catch (err) {
      // 使用模拟详情
      const newsItem = newsList.find(n => n.id === id);
      if (newsItem) {
        setCurrentDetail({
          id: newsItem.id,
          title: newsItem.title,
          content: newsItem.content || '暂无详细内容',
          source: newsItem.source,
          publishTime: newsItem.publishTime,
          investmentAdvice: '建议关注相关板块的投资机会，注意风险控制。',
        });
        setDetailVisible(true);
      }
    }
  };

  useEffect(() => {
    fetchNews();
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">新闻资讯</h1>

      {/* 新闻列表 */}
      <NewsList
        news={newsList}
        loading={newsLoading}
        onSearch={handleSearch}
        onDetail={handleViewDetail}
        onPageChange={handlePageChange}
        total={total}
        currentPage={page}
        pageSize={pageSize}
        showPagination
      />

      {/* 新闻详情弹窗 */}
      <Modal
        title={currentDetail?.title}
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={null}
        width={800}
      >
        {currentDetail && (
          <div>
            <div className="flex items-center gap-4 mb-4 text-sm text-gray-500">
              <span>来源: {currentDetail.source}</span>
              <span>发布时间: {new Date(currentDetail.publishTime).toLocaleString('zh-CN')}</span>
            </div>
            
            {currentDetail.relatedStocks && currentDetail.relatedStocks.length > 0 && (
              <div className="mb-4">
                <span className="text-gray-500 mr-2">相关股票:</span>
                {currentDetail.relatedStocks.map((stock: string) => (
                  <Tag key={stock} color="blue">{stock}</Tag>
                ))}
              </div>
            )}
            
            <div className="prose max-w-none mb-4">
              <pre className="whitespace-pre-wrap text-gray-700">
                {currentDetail.content}
              </pre>
            </div>
            
            {currentDetail.investmentAdvice && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="text-green-700 font-medium mb-2">AI 投资建议</div>
                <div className="text-green-600">{currentDetail.investmentAdvice}</div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}

export default News;
