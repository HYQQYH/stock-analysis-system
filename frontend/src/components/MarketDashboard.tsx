import React from 'react';
import { Card, Row, Col, Statistic, Table, Progress, Tag } from 'antd';

interface MarketDashboardProps {
  indexData?: {
    close: number;
    change: number;
    changePct: number;
    volume: number;
    amount: number;
  };
  sentimentData?: {
    sentimentScore: number;
    bullBearRatio: number;
    riseCount: number;
    fallCount: number;
    limitUpCount: number;
    limitDownCount: number;
  };
  fundFlowData?: Array<{
    type: string;
    netInflow: number;
    ratio: number;
  }>;
  recentLimitUp?: Array<{
    code: string;
    name: string;
    changePct: number;
    industry: string;
  }>;
}

export function MarketDashboard({
  indexData,
  sentimentData,
  fundFlowData,
  recentLimitUp,
}: MarketDashboardProps) {
  const getChangeColor = (change: number) => {
    if (change > 0) return '#ef4444';
    if (change < 0) return '#22c55e';
    return '#6b7280';
  };

  const change = indexData?.change ?? 0;
  const changePct = indexData?.changePct ?? 0;
  const volume = indexData?.volume ?? 0;

  return (
    <div className="space-y-4">
      {/* 大盘指数卡片 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small" className="shadow-sm">
            <Statistic
              title="上证指数"
              value={indexData?.close || 0}
              precision={2}
              valueStyle={{ color: getChangeColor(change) }}
              suffix={
                <span className="text-sm ml-2">
                  ({change > 0 ? '+' : ''}
                  {change.toFixed(2)}
                  , {changePct > 0 ? '+' : ''}
                  {changePct.toFixed(2)}%)
                </span>
              }
            />
            <div className="mt-2 text-sm text-gray-500">
              成交量: {(volume / 100000000).toFixed(2)}亿
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card size="small" className="shadow-sm">
            <div className="text-gray-500 text-sm mb-1">市场情绪</div>
            {sentimentData ? (
              <>
                <div className="text-2xl font-bold" style={{ color: sentimentData.sentimentScore > 50 ? '#ef4444' : '#22c55e' }}>
                  {sentimentData.sentimentScore.toFixed(0)}
                </div>
                <Progress
                  percent={sentimentData.sentimentScore}
                  showInfo={false}
                  strokeColor={sentimentData.sentimentScore > 50 ? '#ef4444' : '#22c55e'}
                  size="small"
                />
              </>
            ) : (
              <div className="text-gray-400">--</div>
            )}
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card size="small" className="shadow-sm">
            <div className="grid grid-cols-2 gap-2">
              <div>
                <div className="text-gray-500 text-xs">上涨家数</div>
                <div className="text-red-500 font-bold">{sentimentData?.riseCount || 0}</div>
              </div>
              <div>
                <div className="text-gray-500 text-xs">下跌家数</div>
                <div className="text-green-500 font-bold">{sentimentData?.fallCount || 0}</div>
              </div>
              <div>
                <div className="text-gray-500 text-xs">涨停</div>
                <div className="text-red-500 font-bold">{sentimentData?.limitUpCount || 0}</div>
              </div>
              <div>
                <div className="text-gray-500 text-xs">跌停</div>
                <div className="text-green-500 font-bold">{sentimentData?.limitDownCount || 0}</div>
              </div>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card size="small" className="shadow-sm">
            <div className="text-gray-500 text-sm mb-1">多空比例</div>
            {sentimentData ? (
              <div className="text-2xl font-bold">
                {sentimentData.bullBearRatio.toFixed(2)}
              </div>
            ) : (
              <div className="text-gray-400">--</div>
            )}
            <div className="text-xs text-gray-400 mt-1">
              多头/空头
            </div>
          </Card>
        </Col>
      </Row>

      {/* 资金流向 */}
      {fundFlowData && fundFlowData.length > 0 && (
        <Card title="资金流向" size="small" className="shadow-sm">
          <Row gutter={[16, 16]}>
            {fundFlowData.map((item, index) => (
              <Col xs={24} sm={12} md={8} lg={6} key={index}>
                <div className="bg-gray-50 rounded p-3">
                  <div className="text-gray-500 text-sm">{item.type}</div>
                  <div
                    className={`font-bold ${
                      item.netInflow > 0 ? 'text-red-500' : item.netInflow < 0 ? 'text-green-500' : 'text-gray-500'
                    }`}
                  >
                    {item.netInflow > 0 ? '+' : ''}
                    {(item.netInflow / 10000).toFixed(2)}万
                  </div>
                  <div className="text-xs text-gray-400">{item.ratio.toFixed(2)}%</div>
                </div>
              </Col>
            ))}
          </Row>
        </Card>
      )}

      {/* 近期涨停 */}
      {recentLimitUp && recentLimitUp.length > 0 && (
        <Card title="近期涨停" size="small" className="shadow-sm">
          <Table
            size="small"
            pagination={false}
            columns={[
              {
                title: '股票',
                dataIndex: 'code',
                key: 'code',
                render: (code: string, record: any) => (
                  <span>
                    <span className="font-medium">{code}</span>
                    <span className="text-gray-500 ml-1">{record.name}</span>
                  </span>
                ),
              },
              {
                title: '涨幅',
                dataIndex: 'changePct',
                key: 'changePct',
                render: (v: number) => (
                  <Tag color="red">{v > 0 ? '+' : ''}{v.toFixed(2)}%</Tag>
                ),
              },
              {
                title: '行业',
                dataIndex: 'industry',
                key: 'industry',
                render: (v: string) => v ? <Tag>{v}</Tag> : '-',
              },
            ]}
            dataSource={recentLimitUp}
            rowKey="code"
          />
        </Card>
      )}
    </div>
  );
}

export default MarketDashboard;
