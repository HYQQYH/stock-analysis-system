import React from 'react';
import { Card, Table, Tag } from 'antd';

function LimitUp() {
  const columns = [
    { title: '股票代码', dataIndex: 'code', key: 'code' },
    { title: '股票名称', dataIndex: 'name', key: 'name' },
    { title: '涨跌幅', dataIndex: 'changePct', key: 'changePct', render: (v: number) => <Tag color="red">{v}%</Tag> },
    { title: '最新价', dataIndex: 'price', key: 'price' },
    { title: '成交额(万)', dataIndex: 'amount', key: 'amount' },
    { title: '换手率', dataIndex: 'turnover', key: 'turnover', render: (v: number) => `${v}%` },
    { title: '连板数', dataIndex: 'continuous', key: 'continuous' },
    { title: '行业', dataIndex: 'industry', key: 'industry' },
  ];

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">涨停股池</h1>
      
      <Card>
        <Table
          columns={columns}
          dataSource={[]}
          rowKey="id"
          pagination={{ pageSize: 20 }}
        />
      </Card>
    </div>
  );
}

export default LimitUp;
