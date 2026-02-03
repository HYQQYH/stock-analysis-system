import React, { useState } from 'react';
import { Card, List, Tag, Input, Button, Empty, Spin, Pagination } from 'antd';

const { Search } = Input;

interface NewsItem {
  id: string;
  title: string;
  content?: string;
  source: string;
  publishTime: string;
  relatedStocks?: string[];
  investmentAdvice?: string;
}

interface NewsListProps {
  news: NewsItem[];
  loading?: boolean;
  onSearch?: (keyword: string) => void;
  onDetail?: (id: string) => void;
  onPageChange?: (page: number, pageSize: number) => void;
  total?: number;
  currentPage?: number;
  pageSize?: number;
  showPagination?: boolean;
}

export function NewsList({
  news,
  loading = false,
  onSearch,
  onDetail,
  onPageChange,
  total = 0,
  currentPage = 1,
  pageSize = 10,
  showPagination = false,
}: NewsListProps) {
  const [keyword, setKeyword] = useState('');

  const handleSearch = (value: string) => {
    setKeyword(value);
    onSearch?.(value);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <Spin size="large" tip="加载中..." />
      </div>
    );
  }

  return (
    <Card
      title="财经新闻"
      size="small"
      className="shadow-sm"
      extra={
        onSearch && (
          <Search
            placeholder="搜索新闻"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onSearch={handleSearch}
            style={{ width: 200 }}
            allowClear
          />
        )
      }
    >
      {news.length === 0 ? (
        <Empty description="暂无新闻" />
      ) : (
        <>
          <List
            itemLayout="vertical"
            dataSource={news}
            renderItem={(item) => (
              <List.Item
                className="cursor-pointer hover:bg-gray-50 px-2 py-1 -mx-2 rounded transition-colors"
                onClick={() => onDetail?.(item.id)}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="font-medium text-base mb-2 hover:text-blue-600 transition-colors">
                      {item.title}
                    </div>
                    <div className="text-gray-500 text-sm mb-2">
                      <span>{item.source}</span>
                      <span className="mx-2">|</span>
                      <span>{new Date(item.publishTime).toLocaleDateString('zh-CN')}</span>
                    </div>
                    {item.relatedStocks && item.relatedStocks.length > 0 && (
                      <div className="mb-2">
                        {item.relatedStocks.map((stock) => (
                          <Tag key={stock} color="blue" className="mr-1">
                            {stock}
                          </Tag>
                        ))}
                      </div>
                    )}
                    {item.investmentAdvice && (
                      <div className="text-green-600 text-sm bg-green-50 p-2 rounded mt-2">
                        <span className="font-medium">AI 建议: </span>
                        {item.investmentAdvice}
                      </div>
                    )}
                  </div>
                </div>
              </List.Item>
            )}
          />
          
          {showPagination && onPageChange && (
            <div className="mt-4 flex justify-end">
              <Pagination
                current={currentPage}
                pageSize={pageSize}
                total={total}
                onChange={onPageChange}
                showSizeChanger
                showQuickJumper
              />
            </div>
          )}
        </>
      )}
    </Card>
  );
}

export default NewsList;
