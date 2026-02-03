import React from 'react';
import { Card, Row, Col, Table } from 'antd';

function MarketAnalysis() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">大盘分析</h1>
      
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} sm={8}>
          <Card>
            <div className="text-center">
              <div className="text-gray-500">上证指数</div>
              <div className="text-2xl font-bold">--</div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <div className="text-center">
              <div className="text-gray-500">市场情绪</div>
              <div className="text-2xl font-bold">--</div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <div className="text-center">
              <div className="text-gray-500">涨停家数</div>
              <div className="text-2xl font-bold">--</div>
            </div>
          </Card>
        </Col>
      </Row>

      <Card title="资金流向" className="mb-6">
        <Table
          columns={[
            { title: '资金类型', dataIndex: 'type', key: 'type' },
            { title: '净流入(万)', dataIndex: 'netInflow', key: 'netInflow' },
            { title: '净占比', dataIndex: 'ratio', key: 'ratio' },
          ]}
          dataSource={[]}
          pagination={false}
        />
      </Card>
    </div>
  );
}

export default MarketAnalysis;
