import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Select, DatePicker, Space, Alert, Spin } from 'antd';
import { KLineChart, IndicatorCard, MarketDashboard } from '../components';
import { useMarketStore, useLoadingStore, useToastStore, useStockStore } from '../store';
import { marketApi } from '../services/api';

const { Option } = Select;
const { RangePicker } = DatePicker;

type KlineType = 'day' | 'week' | 'month';

function MarketAnalysis() {
  const { 
    indexKline, 
    indexIndicators,
    setIndexKline, 
    setIndexIndicators 
  } = useMarketStore();
  const { marketLoading, setMarketLoading } = useLoadingStore();
  const { showToast } = useToastStore();

  const [klineType, setKlineType] = useState<KlineType>('day');
  const [dateRange, setDateRange] = useState<[string, string] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [marketData, setMarketData] = useState<{
    indexData?: { close: number; change: number; changePct: number; volume: number; amount: number };
    sentimentData?: { sentimentScore: number; bullBearRatio: number; riseCount: number; fallCount: number; limitUpCount: number; limitDownCount: number };
  }>({});

  // 获取大盘K线数据
  const fetchIndexKline = async () => {
    setMarketLoading(true);
    setError(null);
    try {
      const params: { type: string; startDate?: string; endDate?: string } = { type: klineType };
      if (dateRange) {
        params.startDate = dateRange[0];
        params.endDate = dateRange[1];
      }
      const response = await marketApi.getIndex(params);
      setIndexKline(response);
    } catch (err) {
      const message = err instanceof Error ? err.message : '获取大盘数据失败';
      setError(message);
      showToast(message, 'error');
    } finally {
      setMarketLoading(false);
    }
  };

  // 获取技术指标
  const fetchIndicators = async () => {
    try {
      // 这里可以添加获取大盘指标的方法
    } catch (err) {
      console.error('获取技术指标失败:', err);
    }
  };

  // 获取市场数据
  const fetchMarketData = async () => {
    try {
      const [sentimentRes] = await Promise.all([
        marketApi.getSentiment().catch(() => null),
      ]);
      
      // 模拟一些基础数据
      const indexData = {
        close: 3054.28,
        change: 15.47,
        changePct: 0.51,
        volume: 25678912345,
        amount: 356789123456,
      };
      
      const sentimentData = sentimentRes ? {
        sentimentScore: sentimentRes.sentimentScore,
        bullBearRatio: sentimentRes.bullBearRatio,
        riseCount: sentimentRes.riseCount,
        fallCount: sentimentRes.fallCount,
        limitUpCount: 45,
        limitDownCount: 5,
      } : {
        sentimentScore: 58,
        bullBearRatio: 1.25,
        riseCount: 1523,
        fallCount: 823,
        limitUpCount: 45,
        limitDownCount: 5,
      };

      setMarketData({ indexData, sentimentData });
    } catch (err) {
      console.error('获取市场数据失败:', err);
    }
  };

  useEffect(() => {
    fetchMarketData();
    fetchIndexKline();
    fetchIndicators();
  }, [klineType]);

  const fundFlowData = [
    { type: '主力净流入', netInflow: 125.8, ratio: 35.2 },
    { type: '超大单净流入', netInflow: 89.3, ratio: 25.1 },
    { type: '大单净流入', netInflow: 36.5, ratio: 10.1 },
    { type: '中单净流入', netInflow: -28.4, ratio: -8.2 },
    { type: '小单净流入', netInflow: -122.2, ratio: -34.5 },
  ];

  const limitUpData = [
    { code: '600000', name: '浦发银行', changePct: 10.05, industry: '银行' },
    { code: '000001', name: '平安银行', changePct: 9.98, industry: '银行' },
    { code: '600036', name: '招商银行', changePct: 8.75, industry: '银行' },
    { code: '601398', name: '工商银行', changePct: 6.32, industry: '银行' },
    { code: '601939', name: '建设银行', changePct: 5.89, industry: '银行' },
  ];

  if (marketLoading && indexKline.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spin size="large" tip="加载大盘数据..." />
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">大盘分析</h1>

      {/* 错误提示 */}
      {error && (
        <Alert
          message="错误"
          description={error}
          type="error"
          showIcon
          className="mb-6"
          closable
          onClose={() => setError(null)}
        />
      )}

      {/* 大盘数据看板 */}
      <MarketDashboard
        indexData={marketData.indexData}
        sentimentData={marketData.sentimentData}
        fundFlowData={fundFlowData}
        recentLimitUp={limitUpData}
      />

      {/* 控制栏 */}
      <Card className="mb-6 mt-6">
        <div className="flex flex-wrap gap-4 items-center">
          <div>
            <span className="text-gray-500 mr-2">K线类型</span>
            <Select
              value={klineType}
              onChange={setKlineType}
              style={{ width: 100 }}
            >
              <Option value="day">日K</Option>
              <Option value="week">周K</Option>
              <Option value="month">月K</Option>
            </Select>
          </div>
          
          <div>
            <span className="text-gray-500 mr-2">时间范围</span>
            <RangePicker 
              onChange={(dates, dateStrings) => {
                if (dates && dates[0] && dates[1]) {
                  setDateRange([dateStrings[0], dateStrings[1]]);
                } else {
                  setDateRange(null);
                }
              }}
            />
          </div>

          <Space>
            <button
              onClick={fetchIndexKline}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              刷新数据
            </button>
          </Space>
        </div>
      </Card>

      {/* 上证指数K线图 */}
      <Card title="上证指数 K线图" className="mb-6">
        {indexKline.length > 0 ? (
          <KLineChart data={indexKline} height={500} title="上证指数" />
        ) : (
          <div className="text-center py-20 text-gray-400">
            暂无K线数据
          </div>
        )}
      </Card>

      {/* 技术指标 */}
      {indexIndicators && (
        <Card title="技术指标分析" className="mb-6">
          <IndicatorCard data={indexIndicators} />
        </Card>
      )}

      {/* 资金流向 */}
      <Card title="资金流向分析" className="mb-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {fundFlowData.map((item, index) => (
            <div key={index} className="bg-gray-50 rounded-lg p-4 text-center">
              <div className="text-gray-500 text-sm mb-1">{item.type}</div>
              <div className={`text-xl font-bold ${
                item.netInflow > 0 ? 'text-red-500' : 
                item.netInflow < 0 ? 'text-green-500' : 'text-gray-500'
              }`}>
                {item.netInflow > 0 ? '+' : ''}{item.netInflow}亿
              </div>
              <div className="text-gray-400 text-xs">{item.ratio}%</div>
            </div>
          ))}
        </div>
      </Card>

      {/* 市场活跃度 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} md={8}>
          <Card title="涨跌统计" size="small">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <div className="text-red-500 text-3xl font-bold">
                  {marketData.sentimentData?.riseCount || 0}
                </div>
                <div className="text-gray-500">上涨家数</div>
              </div>
              <div className="text-center">
                <div className="text-green-500 text-3xl font-bold">
                  {marketData.sentimentData?.fallCount || 0}
                </div>
                <div className="text-gray-500">下跌家数</div>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card title="涨跌停统计" size="small">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <div className="text-red-500 text-3xl font-bold">
                  {marketData.sentimentData?.limitUpCount || 0}
                </div>
                <div className="text-gray-500">涨停家数</div>
              </div>
              <div className="text-center">
                <div className="text-green-500 text-3xl font-bold">
                  {marketData.sentimentData?.limitDownCount || 0}
                </div>
                <div className="text-gray-500">跌停家数</div>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card title="多空情绪" size="small">
            <div className="text-center">
              <div className="text-3xl font-bold" style={{ 
                color: (marketData.sentimentData?.bullBearRatio || 0) > 1 ? '#ef4444' : '#22c55e'
              }}>
                {(marketData.sentimentData?.bullBearRatio || 0).toFixed(2)}
              </div>
              <div className="text-gray-500">多空比</div>
              <div className="text-sm text-gray-400 mt-2">
                {(marketData.sentimentData?.sentimentScore || 0).toFixed(0)}分
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
}

export default MarketAnalysis;
