import React from 'react';
import { Link } from 'react-router-dom';
import { Card, Row, Col, Statistic } from 'antd';

function Dashboard() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">股票分析系统</h1>
      
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Link to="/stock-analysis">
            <Card hoverable className="h-32 flex items-center justify-center">
              <Statistic title="股票分析" value="个股/大盘分析" />
            </Card>
          </Link>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Link to="/market-analysis">
            <Card hoverable className="h-32 flex items-center justify-center">
              <Statistic title="大盘分析" value="市场情绪/资金流向" />
            </Card>
          </Link>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Link to="/news">
            <Card hoverable className="h-32 flex items-center justify-center">
              <Statistic title="新闻资讯" value="财经新闻/投资机会" />
            </Card>
          </Link>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Link to="/limit-up">
            <Card hoverable className="h-32 flex items-center justify-center">
              <Statistic title="涨停股池" value="每日涨停股票" />
            </Card>
          </Link>
        </Col>
      </Row>

      <div className="mt-8">
        <Card title="系统功能">
          <ul className="space-y-2 text-gray-600">
            <li>• 股票技术指标分析（MACD、KDJ、RSI）</li>
            <li>• AI 智能分析报告生成</li>
            <li>• 大盘资金流向分析</li>
            <li>• 市场活跃度监控</li>
            <li>• 涨停板股票池</li>
            <li>• 财经新闻投资机会挖掘</li>
          </ul>
        </Card>
      </div>
    </div>
  );
}

export default Dashboard;
