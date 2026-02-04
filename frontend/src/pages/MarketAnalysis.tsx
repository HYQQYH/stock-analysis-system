import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Select, DatePicker, Space, Alert, Spin, message } from 'antd';
import { KLineChart, IndicatorCard, MarketDashboard } from '../components';
import { useMarketStore, useLoadingStore } from '../store';
import { marketApi } from '../services/api';

const { Option } = Select;
const { RangePicker } = DatePicker;

type KlineType = 'day' | 'week' | 'month';

// 后端API返回的数据类型
interface MarketIndexData {
  index_code: string;
  index_name: string;
  kline_type: string;
  data: Array<{
    trade_date: string;
    open_price: number;
    high_price: number;
    low_price: number;
    close_price: number;
    volume: number;
    amount: number;
  }>;
}

interface SentimentData {
  trade_date: string;
  index_code: string;
  sentiment_score: number;
  bull_bear_ratio: number;
  rise_fall_count: {
    rise: number;
    fall: number;
    flat: number;
  };
  volume_ratio: number | null;
}

interface FundFlowData {
  trade_date: string;
  sh_close_price: number;
  sh_change_pct: number;
  sz_close_price: number;
  sz_change_pct: number;
  main_net_inflow: number;
  main_net_inflow_ratio: number;
  super_large_net_inflow: number;
  super_large_net_inflow_ratio: number;
  large_net_inflow: number;
  large_net_inflow_ratio: number;
  medium_net_inflow: number;
  medium_net_inflow_ratio: number;
  small_net_inflow: number;
  small_net_inflow_ratio: number;
}

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

function MarketAnalysis() {
  const { indexKline, setIndexKline } = useMarketStore();
  const { marketLoading, setMarketLoading } = useLoadingStore();

  const [klineType, setKlineType] = useState<KlineType>('day');
  const [dateRange, setDateRange] = useState<[string, string] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [marketData, setMarketData] = useState<{
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
      const response = await marketApi.getIndex(params) as unknown as MarketIndexData;
      
      if (response && response.data && response.data.length > 0) {
        // 转换为K线图需要的格式
        const klineData = response.data.map((item) => ({
          date: item.trade_date,
          open: item.open_price,
          high: item.high_price,
          low: item.low_price,
          close: item.close_price,
          volume: item.volume,
          amount: item.amount ?? undefined,
        }));
        setIndexKline(klineData);

        // 计算大盘指数数据（最新一天）
        const latest = response.data[0];
        const previous = response.data[1] || latest;
        const change = latest.close_price - previous.close_price;
        const changePct = previous.close_price > 0 ? (change / previous.close_price) * 100 : 0;

        setMarketData(prev => ({
          ...prev,
          indexData: {
            close: latest.close_price,
            change: change,
            changePct: changePct,
            volume: latest.volume,
            amount: latest.amount,
          },
        }));
      }
    } catch (err) {
      const messageText = err instanceof Error ? err.message : '获取大盘数据失败';
      setError(messageText);
      message.error(messageText);
    } finally {
      setMarketLoading(false);
    }
  };

  // 获取市场数据（情绪、资金流向、涨停）
  const fetchMarketData = async () => {
    try {
      // 并行获取所有数据
      const [sentimentRes, fundFlowRes, limitUpRes] = await Promise.all([
        marketApi.getSentiment().catch(() => null) as Promise<SentimentData | null>,
        marketApi.getFundFlow({}).catch(() => null) as Promise<FundFlowData | null>,
        marketApi.getLimitUp().catch(() => null) as Promise<LimitUpData | null>,
      ]);

      // 处理情绪数据
      if (sentimentRes) {
        setMarketData(prev => ({
          ...prev,
          sentimentData: {
            sentimentScore: sentimentRes.sentiment_score,
            bullBearRatio: sentimentRes.bull_bear_ratio,
            riseCount: sentimentRes.rise_fall_count?.rise || 0,
            fallCount: sentimentRes.rise_fall_count?.fall || 0,
            limitUpCount: 0,
            limitDownCount: 0,
          },
        }));
      }

      // 处理资金流向数据
      if (fundFlowRes) {
        const fundFlowList = [
          { type: '主力净流入', netInflow: fundFlowRes.main_net_inflow, ratio: fundFlowRes.main_net_inflow_ratio },
          { type: '超大单净流入', netInflow: fundFlowRes.super_large_net_inflow, ratio: fundFlowRes.super_large_net_inflow_ratio },
          { type: '大单净流入', netInflow: fundFlowRes.large_net_inflow, ratio: fundFlowRes.large_net_inflow_ratio },
          { type: '中单净流入', netInflow: fundFlowRes.medium_net_inflow, ratio: fundFlowRes.medium_net_inflow_ratio },
          { type: '小单净流入', netInflow: fundFlowRes.small_net_inflow, ratio: fundFlowRes.small_net_inflow_ratio },
        ];
        setMarketData(prev => ({
          ...prev,
          fundFlowData: fundFlowList,
        }));
      }

      // 处理涨停数据
      if (limitUpRes && limitUpRes.stocks) {
        const limitUpList = limitUpRes.stocks.slice(0, 10).map(stock => ({
          code: stock.stock_code,
          name: stock.stock_name,
          changePct: stock.change_pct,
          industry: stock.industry || '未知',
        }));
        setMarketData(prev => ({
          ...prev,
          recentLimitUp: limitUpList,
        }));
      }
    } catch (err) {
      console.error('获取市场数据失败:', err);
    }
  };

  // 获取技术指标
  const fetchIndicators = async () => {
    try {
      // 大盘技术指标暂时使用默认数据
    } catch (err) {
      console.error('获取技术指标失败:', err);
    }
  };

  useEffect(() => {
    fetchMarketData();
    fetchIndexKline();
    fetchIndicators();
  }, [klineType]);

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
        fundFlowData={marketData.fundFlowData}
        recentLimitUp={marketData.recentLimitUp}
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
      <Card title="技术指标分析" className="mb-6">
        <div className="text-center py-10 text-gray-400">
          技术指标分析功能开发中
        </div>
      </Card>

      {/* 资金流向 */}
      {marketData.fundFlowData && marketData.fundFlowData.length > 0 && (
        <Card title="资金流向分析" className="mb-6">
          <Row gutter={[16, 16]}>
            {marketData.fundFlowData.map((item, index) => (
              <Col xs={24} sm={12} md={8} lg={6} key={index}>
                <div className="bg-gray-50 rounded-lg p-4 text-center">
                  <div className="text-gray-500 text-sm mb-1">{item.type}</div>
                  <div className={`text-xl font-bold ${
                    (item.netInflow ?? 0) > 0 ? 'text-red-500' : 
                    (item.netInflow ?? 0) < 0 ? 'text-green-500' : 'text-gray-500'
                  }`}>
                    {(item.netInflow ?? 0) > 0 ? '+' : ''}
                    {Number((item.netInflow ?? 0) / 10000).toFixed(2)}万
                  </div>
                  <div className="text-gray-400 text-xs">
                    {Number(item.ratio ?? 0).toFixed(2)}%
                  </div>
                </div>
              </Col>
            ))}
          </Row>
        </Card>
      )}

      {/* 市场活跃度 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} md={8}>
          <Card title="涨跌统计" size="small">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <div className="text-red-500 text-3xl font-bold">
                  {marketData.sentimentData?.riseCount ?? '--'}
                </div>
                <div className="text-gray-500">上涨家数</div>
              </div>
              <div className="text-center">
                <div className="text-green-500 text-3xl font-bold">
                  {marketData.sentimentData?.fallCount ?? '--'}
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
                  {marketData.sentimentData?.limitUpCount ?? '--'}
                </div>
                <div className="text-gray-500">涨停家数</div>
              </div>
              <div className="text-center">
                <div className="text-green-500 text-3xl font-bold">
                  {marketData.sentimentData?.limitDownCount ?? '--'}
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
                color: (marketData.sentimentData?.bullBearRatio ?? 0) > 1 ? '#ef4444' : '#22c55e'
              }}>
                {Number(marketData.sentimentData?.bullBearRatio ?? 0).toFixed(2)}
              </div>
              <div className="text-gray-500">多空比</div>
              <div className="text-sm text-gray-400 mt-2">
                {Number(marketData.sentimentData?.sentimentScore ?? 0).toFixed(0)}分
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
}

export default MarketAnalysis;
