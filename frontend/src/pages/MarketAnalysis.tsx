import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Select, DatePicker, Space, Alert, Spin, message, Button, Progress, Steps } from 'antd';
import { KLineChart, IndicatorCard, MarketDashboard, TechnicalAnalysisCard, MarketAnalysisHistory } from '../components';
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

// 大盘AI分析结果类型
interface MarketAnalysisData {
  index_code: string;
  index_name: string;
  kline_type: string;
  days: number;
  analysis_time: string;
  trend: string;
  support_levels: number[];
  resistance_levels: number[];
  sentiment_score: number;
  confidence_score: number;
  llm_provider: string;
  llm_model: string;
  token_usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  analysis_content: string;
  success: boolean;
  error_message: string | null;
}

function MarketAnalysis() {
  const { indexKline, setIndexKline } = useMarketStore();
  const { marketLoading, setMarketLoading } = useLoadingStore();

  const [klineType, setKlineType] = useState<KlineType>('day');
  const [analysisDays, setAnalysisDays] = useState<number>(30);
  const [dateRange, setDateRange] = useState<[string, string] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState<boolean>(false);
  
  // AI分析当前步骤 (0: 获取数据, 1: 计算指标, 2: AI分析, 3: 生成报告)
  const [analysisStep, setAnalysisStep] = useState<number>(0);

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

  // AI分析结果状态
  const [analysisResult, setAnalysisResult] = useState<MarketAnalysisData | null>(null);

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
          amount: item.amount,
        }));
        setIndexKline(klineData);

        // 计算大盘指数数据（最新一天，数据已按日期升序排列，latest在最后）
        const latest = response.data[response.data.length - 1];
        const previous = response.data[response.data.length - 2] || latest;
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

  // 获取AI市场分析结果 - 带步骤模拟
  const fetchMarketAnalysis = async () => {
    setAnalysisLoading(true);
    setAnalysisStep(0); // 重置到第一步
    setError(null);
    
    // 模拟步骤1: 获取数据 (1秒)
    await new Promise(resolve => setTimeout(resolve, 1000));
    setAnalysisStep(1);
    
    // 模拟步骤2: 计算指标 (1秒)
    await new Promise(resolve => setTimeout(resolve, 1000));
    setAnalysisStep(2);
    
    try {
      // 步骤3: AI分析 (实际API调用)
      const response = await marketApi.getMarketAnalysis({
        kline_type: klineType,
        days: analysisDays
      });
      
      console.log('AI分析响应:', response);
      
      // 步骤4: 生成报告
      setAnalysisStep(3);
      await new Promise(resolve => setTimeout(resolve, 500));
      
      if (response && response.success) {
        setAnalysisResult(response);
      } else {
        message.warning(response?.error_message || 'AI分析暂时不可用');
        setAnalysisResult(null);
      }
    } catch (err) {
      console.error('获取AI分析失败:', err);
      message.error('获取AI分析失败');
      setAnalysisResult(null);
    } finally {
      setAnalysisLoading(false);
      setAnalysisStep(0); // 重置步骤
    }
  };

  // 执行AI分析
  const handleAnalyze = () => {
    fetchMarketAnalysis();
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

      {/* 技术指标 - AI分析结果 */}
      <Card title="技术指标分析" className="mb-6">
        {/* 分析控制栏 */}
        <div className="flex flex-wrap gap-4 items-center mb-4">
          <span className="text-gray-500">分析周期：</span>
          <Select
            value={analysisDays}
            onChange={setAnalysisDays}
            style={{ width: 120 }}
            options={[
              { value: 7, label: '7天' },
              { value: 15, label: '15天' },
              { value: 30, label: '30天' },
              { value: 60, label: '60天' },
              { value: 90, label: '90天' },
            ]}
          />
          <Button 
            type="primary" 
            onClick={handleAnalyze}
            loading={analysisLoading}
            icon={<span className="mr-1">📊</span>}
            disabled={analysisLoading}
          >
            {analysisLoading ? 'AI分析中...' : '开始AI分析'}
          </Button>
        </div>
        
        {/* AI分析进度展示 */}
        {analysisLoading && (
          <div className="mb-6">
            <div className="flex items-center justify-center mb-4">
              <Spin size="large" />
              <span className="ml-4 text-lg text-gray-600">AI正在分析大盘走势，请稍候...</span>
            </div>
            <div className="mb-4">
              <Steps
                current={analysisStep}
                status="process"
                items={[
                  { title: '获取数据', description: '正在获取K线数据...' },
                  { title: '计算指标', description: '正在计算技术指标...' },
                  { title: 'AI分析', description: '正在调用AI模型分析...' },
                  { title: '生成报告', description: '正在生成分析报告...' },
                ]}
              />
            </div>
            <Progress 
              percent={Math.min((analysisStep + 1) * 25, 100)} 
              status="active" 
              strokeColor={{ from: '#108ee9', to: '#87d068' }}
              format={() => 'AI分析进行中...'}
            />
          </div>
        )}
        
        {/* AI分析结果展示 */}
        {!analysisLoading && analysisResult && (
          <TechnicalAnalysisCard
            analysisContent={analysisResult.analysis_content}
            trend={analysisResult.trend}
            supportLevels={analysisResult.support_levels}
            resistanceLevels={analysisResult.resistance_levels}
            sentimentScore={analysisResult.sentiment_score}
            confidenceScore={analysisResult.confidence_score}
            loading={analysisLoading}
            analysisTime={analysisResult.analysis_time}
          />
        )}
        
        {/* 初始状态 - 未进行分析 */}
        {!analysisLoading && !analysisResult && (
          <div className="text-center py-10">
            <div className="text-gray-400 mb-4">
              点击"开始AI分析"按钮，获取上证指数的技术分析报告
            </div>
            <Button type="default" onClick={handleAnalyze} loading={analysisLoading}>
              开始AI分析
            </Button>
          </div>
        )}
      </Card>

      {/* 大盘分析历史记录 */}
      <MarketAnalysisHistory />
    </div>
  );
}

export default MarketAnalysis;
