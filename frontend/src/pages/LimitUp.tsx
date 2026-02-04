import React, { useState, useEffect } from 'react';
import { Card, Table, Tag, DatePicker, message } from 'antd';
import { marketApi } from '../services/api';

const DatePickerAntd = DatePicker;

interface LimitUpData {
  trade_date: string;
  total_count: number;
  stocks: Array<{
    stock_code: string;
    stock_name: string;
    change_pct: number;
    latest_price: number;
    turnover_amount: number;
    circulation_market_value: number;
    total_market_value: number;
    turnover_rate: number;
    limit_up_funds: number;
    first_limit_time: string | null;
    last_limit_time: string | null;
    burst_count: number;
    limit_up_stats: string | null;
    continuous_limit_count: number;
    industry: string | null;
  }>;
}

function LimitUp() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<LimitUpData | null>(null);

  // 获取涨停股池数据
  const fetchLimitUpData = async (date?: string) => {
    setLoading(true);
    try {
      const response = await marketApi.getLimitUp(date) as unknown as LimitUpData;
      setData(response);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '获取涨停股池数据失败';
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // 日期选择
  const handleDateChange = (_date: any, dateString: string | string[]) => {
    fetchLimitUpData(dateString as string);
  };

  useEffect(() => {
    fetchLimitUpData();
  }, []);

  const columns = [
    {
      title: '股票代码',
      dataIndex: 'stock_code',
      key: 'stock_code',
      render: (code: string) => <span className="font-medium">{code}</span>,
    },
    {
      title: '股票名称',
      dataIndex: 'stock_name',
      key: 'stock_name',
    },
    {
      title: '涨跌幅',
      dataIndex: 'change_pct',
      key: 'change_pct',
      render: (v: number) => (
        <Tag color="red">{v != null ? (v > 0 ? '+' : '') + v.toFixed(2) + '%' : '-'}</Tag>
      ),
    },
    {
      title: '最新价',
      dataIndex: 'latest_price',
      key: 'latest_price',
      render: (v: number) => v?.toFixed(2) ?? '-',
    },
    {
      title: '成交额(万)',
      dataIndex: 'turnover_amount',
      key: 'turnover_amount',
      render: (v: number) => v != null ? (v / 10000).toFixed(2) : '-',
    },
    {
      title: '换手率',
      dataIndex: 'turnover_rate',
      key: 'turnover_rate',
      render: (v: number) => v != null ? v.toFixed(2) + '%' : '-',
    },
    {
      title: '连板数',
      dataIndex: 'continuous_limit_count',
      key: 'continuous_limit_count',
      render: (v: number) => v ?? '-',
    },
    {
      title: '行业',
      dataIndex: 'industry',
      key: 'industry',
      render: (v: string) => v ? <Tag>{v}</Tag> : '-',
    },
  ];

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">涨停股池</h1>
      
      <Card className="mb-4">
        <div className="flex items-center gap-4">
          <span className="text-gray-500">选择日期：</span>
          <DatePickerAntd 
            onChange={handleDateChange}
            placeholder="选择日期"
          />
          <span className="text-gray-500">
            {data?.trade_date ? `数据日期: ${data.trade_date}` : ''}
          </span>
          <span className="text-gray-500">
            {data?.total_count ? `共 ${data.total_count} 只涨停股票` : ''}
          </span>
        </div>
      </Card>
      
      <Card>
        <Table
          columns={columns}
          dataSource={data?.stocks || []}
          rowKey="stock_code"
          loading={loading}
          pagination={{ pageSize: 20 }}
          locale={{ emptyText: '暂无涨停股票数据' }}
        />
      </Card>
    </div>
  );
}

export default LimitUp;
