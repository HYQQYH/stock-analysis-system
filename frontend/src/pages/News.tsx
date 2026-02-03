import React, { useState } from 'react';
import { Card, List, Input, Button, Tag } from 'antd';

function News() {
  const [searchKeyword, setSearchKeyword] = useState('');

  const mockNews = [
    {
      id: 1,
      title: 'A股市场今日大涨 沪指突破3400点',
      source: '财经网',
      time: '2024-01-20',
      tags: ['大盘', 'A股'],
    },
    {
      id: 2,
      title: '银行板块持续走强 主力资金净流入',
      source: '证券时报',
      time: '2024-01-20',
      tags: ['银行', '资金流向'],
    },
  ];

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">新闻资讯</h1>
      
      <Card className="mb-6">
        <div className="flex gap-4">
          <Input
            placeholder="搜索新闻关键词"
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            style={{ width: 300 }}
          />
          <Button type="primary">搜索</Button>
        </div>
      </Card>

      <Card title="最新财经新闻">
        <List
          itemLayout="vertical"
          dataSource={mockNews}
          renderItem={(item) => (
            <List.Item>
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-lg font-medium mb-2">{item.title}</h3>
                  <div className="text-gray-500 text-sm">
                    来源: {item.source} | 时间: {item.time}
                  </div>
                  <div className="mt-2">
                    {item.tags.map((tag) => (
                      <Tag key={tag}>{tag}</Tag>
                    ))}
                  </div>
                </div>
              </div>
            </List.Item>
          )}
        />
      </Card>
    </div>
  );
}

export default News;
