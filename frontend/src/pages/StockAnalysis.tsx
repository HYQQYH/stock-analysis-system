import React, { useState, useEffect } from 'react';
import { Card, Input, Button, Select, Space, Alert, Result, Tag, Spin, Timeline } from 'antd';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useStockStore, useAnalysisStore, useLoadingStore, useToastStore } from '../store';
import { stockApi, analysisApi, sectorApi, PipelineStep } from '../services/api';
import { HistoryList } from '../components';

const { Option } = Select;
const { Search } = Input;

type AnalysisMode = '基础面技术面综合分析' | '波段交易分析' | '短线T+1分析' | '涨停反包分析' | '投机套利分析' | '公司估值分析';

const ANALYSIS_MODES: AnalysisMode[] = [
  '基础面技术面综合分析',
  '波段交易分析',
  '短线T+1分析',
  '涨停反包分析',
  '投机套利分析',
  '公司估值分析',
];

// Pipeline step display names mapping
const STEP_TITLES: Record<string, string> = {
  validation: '验证股票代码',
  data_collection: '收集股票数据',
  indicator_calculation: '计算技术指标',
  data_caching: '缓存数据',
  ai_analysis: 'AI智能分析',
  database_save: '保存结果',
};

interface AnalysisResultData {
  id: string;
  analysisId: string;
  stockCode: string;
  analysisMode: string;
  analysisTime: string;
  analysisResult: string;
  tradingAdvice: {
    direction: string;
    targetPrice?: number;
    stopLoss?: number;
    takeProfit?: number;
    holdingPeriod?: number;
    riskLevel?: string;
  };
  confidenceScore: number;
  status: string;
}

function StockAnalysis() {
  // Zustand store
  const { 
    currentStock, 
    klineData, 
    klineType, 
    sectorName,
    setCurrentStock, 
    setKlineData, 
    setKlineType,
    setSectorName,
    clearStockData 
  } = useStockStore();
  
  const { addAnalysis, setCurrentAnalysis } = useAnalysisStore();
  const { analysisLoading, setAnalysisLoading } = useLoadingStore();
  const { showToast } = useToastStore();

  // 组件状态
  const [stockCode, setStockCode] = useState('');
  const [inputSectorName, setInputSectorName] = useState('');
  const [sectors, setSectors] = useState<string[]>([]);
  const [sectorsLoading, setSectorsLoading] = useState(true);
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>('短线T+1分析');
  const [result, setResult] = useState<{
    summary: string;
    details: string;
    advice: {
      direction: string;
      target_price?: number;
      stop_loss?: number;
      take_profit?: number;
      holding_period?: number;
      risk_level?: string;
    };
    confidence_score: number;
    llm_model?: string;
    trend?: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  // Pipeline steps for displaying analysis progress
  const [pipelineSteps, setPipelineSteps] = useState<PipelineStep[]>([]);
  // Track if we're currently in analysis
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // 加载板块列表
  useEffect(() => {
    const loadSectors = async () => {
      setSectorsLoading(true);
      try {
        const data = await sectorApi.getSectors();
        
        if (data.sectors && Array.isArray(data.sectors)) {
          setSectors(data.sectors);
        } else {
          setSectors([]);
        }
      } catch (err) {
        console.error('获取板块列表失败:', err);
        setSectors([]);
      } finally {
        setSectorsLoading(false);
      }
    };
    loadSectors();
  }, []);

  // 从持久化恢复状态
  useEffect(() => {
    setKlineType(klineType);
    setSectorName(sectorName);
  }, []);

  // 验证股票代码格式
  const validateStockCode = (code: string): boolean => {
    return /^[0-9]{6}$/.test(code);
  };

  // 查询股票信息
  const handleSearchStock = async (code: string) => {
    if (!validateStockCode(code)) {
      setError('请输入有效的6位股票代码');
      return;
    }

    setError(null);
    setAnalysisLoading(true);

    try {
      const response = await stockApi.getStockInfo(code);
      setCurrentStock(response);
      await handleFetchKline(code);
      showToast('股票信息获取成功', 'success');
    } catch (err) {
      const message = err instanceof Error ? err.message : '获取股票信息失败';
      setError(message);
      showToast(message, 'error');
    } finally {
      setAnalysisLoading(false);
    }
  };

  // 获取K线数据
  const handleFetchKline = async (code: string) => {
    try {
      const response = await stockApi.getKline(code, { type: klineType });
      setKlineData(response);
    } catch (err) {
      console.error('获取K线数据失败:', err);
    }
  };

  // 执行股票分析
  const handleAnalyze = async () => {
    if (!stockCode) {
      setError('请输入股票代码');
      return;
    }

    if (!validateStockCode(stockCode)) {
      setError('股票代码格式不正确');
      return;
    }

    setError(null);
    setResult(null);
    // 设置初始的步骤列表 - 点击开始分析后立即显示
    setPipelineSteps([
      { step: 'validation', message: '验证股票代码', status: 'pending', timestamp: new Date().toISOString() },
      { step: 'data_collection', message: '收集股票数据', status: 'pending', timestamp: '' },
      { step: 'indicator_calculation', message: '计算技术指标', status: 'pending', timestamp: '' },
      { step: 'data_caching', message: '缓存数据', status: 'pending', timestamp: '' },
      { step: 'ai_analysis', message: 'AI智能分析', status: 'pending', timestamp: '' },
      { step: 'database_save', message: '保存结果', status: 'pending', timestamp: '' },
    ]);
    setAnalysisLoading(true);
    setIsAnalyzing(true);

    // 模拟进度更新 - 除了AI分析外的其他步骤都很快
    const simulateProgress = () => {
      setPipelineSteps(prev => {
        const newSteps = [...prev];
        
        // 1. 验证完成 (0.5秒后)
        if (newSteps[0].status === 'pending') {
          newSteps[0] = { ...newSteps[0], status: 'running', timestamp: new Date().toISOString() };
        } else if (newSteps[0].status === 'running') {
          newSteps[0] = { ...newSteps[0], status: 'completed', duration_ms: 200, timestamp: new Date().toISOString() };
          
          // 2. 数据收集开始
          newSteps[1] = { ...newSteps[1], status: 'running', timestamp: new Date().toISOString() };
        } else if (newSteps[1].status === 'running') {
          // 3. 数据收集完成，指标计算开始
          newSteps[1] = { ...newSteps[1], status: 'completed', duration_ms: 1500, timestamp: new Date().toISOString() };
          newSteps[2] = { ...newSteps[2], status: 'running', timestamp: new Date().toISOString() };
        } else if (newSteps[2].status === 'running') {
          // 4. 指标计算完成，缓存开始
          newSteps[2] = { ...newSteps[2], status: 'completed', duration_ms: 300, timestamp: new Date().toISOString() };
          newSteps[3] = { ...newSteps[3], status: 'running', timestamp: new Date().toISOString() };
        } else if (newSteps[3].status === 'running') {
          // 5. 缓存完成，AI分析开始
          newSteps[3] = { ...newSteps[3], status: 'completed', duration_ms: 100, timestamp: new Date().toISOString() };
          newSteps[4] = { ...newSteps[4], status: 'running', timestamp: new Date().toISOString() };
        }
        
        return newSteps;
      });
    };

    // 启动模拟进度更新 (每500ms更新一次)
    const progressInterval = setInterval(simulateProgress, 500);

    const analysisId = `analysis_${Date.now()}`;
    
    // 设置当前分析状态
    setCurrentAnalysis({
      id: analysisId,
      stockCode: stockCode,
      analysisMode,
      analysisTime: new Date().toISOString(),
      summary: '',
      details: '',
      tradingAdvice: { direction: '观望' },
      confidenceScore: 0,
      status: 'pending',
    });

    try {
      // 调用后端分析 API（异步模式）
      const submitResponse = await analysisApi.submitAnalysis({
        stock_code: stockCode,
        analysis_mode: analysisMode,
        kline_type: klineType,
        sector_names: inputSectorName ? [inputSectorName] : [],
        include_news: true,
      });

      console.log('Analysis submitted, ID:', submitResponse.analysis_id);

      // 轮询获取结果
      let attempts = 0;
      const maxAttempts = 120;

      while (attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        const resultResponse = await analysisApi.getAnalysisResult(submitResponse.analysis_id);
        console.log('Poll attempt', attempts, 'status:', resultResponse.status, 'steps:', resultResponse.pipeline_steps?.length);
        
        // 更新 pipeline 步骤 - 确保在完成前先显示步骤
        if (resultResponse.pipeline_steps && resultResponse.pipeline_steps.length > 0) {
          console.log('Setting pipeline steps:', resultResponse.pipeline_steps);
          setPipelineSteps(resultResponse.pipeline_steps);
        }
        
        if (resultResponse.status === 'completed') {
          // 确保至少显示一下步骤，然后再显示结果
          const data = resultResponse;
          
          // 解析分析结果
          const resultData = data.result;
          const analysisResult = {
            summary: resultData?.analysis_result?.substring(0, 200) || '暂无分析结果',
            details: resultData?.analysis_result || '暂无分析结果',
            advice: resultData?.trading_advice || { direction: '观望' },
            confidence_score: resultData?.confidence_score || 0,
            llm_model: resultData?.llm_model,
          };
          
          // 先设置步骤，然后延迟设置结果，确保UI有时间渲染
          setTimeout(() => {
            clearInterval(progressInterval); // 清理进度模拟
            setResult(analysisResult);
            setIsAnalyzing(false);
            
            // 保存到历史记录
            addAnalysis({
              id: data.id || data.analysis_id || submitResponse.analysis_id,
              stockCode: data.stock_code,
              analysisMode,
              analysisTime: data.analysis_time || new Date().toISOString(),
              summary: resultData?.analysis_result?.substring(0, 200) || '暂无分析结果',
              details: resultData?.analysis_result || '暂无分析结果',
              tradingAdvice: resultData?.trading_advice as any,
              confidenceScore: resultData?.confidence_score || 0,
              status: 'completed',
            });
            
            showToast('分析完成', 'success');
          }, 1500); // 延迟1.5秒，让用户看到步骤完成
          
          break;
        } else if (resultResponse.status === 'failed') {
          clearInterval(progressInterval);
          setIsAnalyzing(false);
          throw new Error('分析任务失败');
        }
        
        attempts++;
      }

      if (attempts >= maxAttempts) {
        clearInterval(progressInterval);
        setIsAnalyzing(false);
        throw new Error('分析超时，请稍后重试');
      }
    } catch (err) {
      clearInterval(progressInterval);
      const message = err instanceof Error ? err.message : '分析失败';
      setError(message);
      setIsAnalyzing(false);
      showToast(message, 'error');
    } finally {
      clearInterval(progressInterval);
      setAnalysisLoading(false);
    }
  };

  // 清空查询
  const handleClear = () => {
    setStockCode('');
    setInputSectorName('');
    setResult(null);
    setError(null);
    setPipelineSteps([]);
    setIsAnalyzing(false);
    clearStockData();
    showToast('已清空查询', 'info');
  };

  // 获取置信度颜色
  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return '#52c41a';
    if (score >= 0.6) return '#faad14';
    return '#ff4d4f';
  };

  // 获取交易方向颜色
  const getDirectionColor = (direction: string) => {
    switch (direction) {
      case '买入': return 'green';
      case '卖出': return 'red';
      case '持有': return 'blue';
      default: return 'default';
    }
  };

  // 获取步骤状态颜色
  const getStepStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'green';
      case 'running': return 'blue';
      case 'error': return 'red';
      default: return 'gray';
    }
  };

  // 格式化耗时
  const formatDuration = (ms?: number) => {
    if (!ms) return '';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">股票分析</h1>

      {/* 查询表单 */}
      <Card className="mb-6">
        <div className="flex flex-wrap gap-4 items-end">
          <div>
            <label className="block text-sm mb-1 text-gray-600">股票代码</label>
            <Search
              placeholder="如: 600000"
              value={stockCode}
              onChange={(e) => setStockCode(e.target.value)}
              onSearch={handleSearchStock}
              style={{ width: 200 }}
              allowClear
              enterButton="查询股票"
              loading={analysisLoading}
            />
          </div>

          <div>
            <label className="block text-sm mb-1 text-gray-600">K线类型</label>
            <Select
              value={klineType}
              onChange={setKlineType}
              style={{ width: 120 }}
              disabled={analysisLoading}
            >
              <Option value="day">日K</Option>
              <Option value="week">周K</Option>
              <Option value="month">月K</Option>
            </Select>
          </div>

          <div>
            <label className="block text-sm mb-1 text-gray-600">分析模式</label>
            <Select
              value={analysisMode}
              onChange={setAnalysisMode}
              style={{ width: 160 }}
              disabled={analysisLoading}
            >
              {ANALYSIS_MODES.map((mode) => (
                <Option key={mode} value={mode}>
                  {mode}
                </Option>
              ))}
            </Select>
          </div>

          <div>
            <label className="block text-sm mb-1 text-gray-600">板块名称（可选）</label>
            <Select
              showSearch
              placeholder="搜索或选择板块"
              value={inputSectorName || undefined}
              onChange={setInputSectorName}
              style={{ width: 220 }}
              disabled={analysisLoading || sectorsLoading}
              loading={sectorsLoading}
              allowClear
              filterOption={(input, option) => {
                const optionText = typeof option?.children === 'string' ? option.children : '';
                return optionText.toLowerCase().includes(input.toLowerCase());
              }}
            >
              {sectors.map((sector) => (
                <Option key={sector} value={sector}>
                  {sector}
                </Option>
              ))}
            </Select>
          </div>

          <Space>
            <Button
              type="primary"
              onClick={handleAnalyze}
              loading={analysisLoading}
              disabled={!stockCode || !validateStockCode(stockCode)}
            >
              开始分析
            </Button>
            <Button onClick={handleClear} disabled={analysisLoading}>
              清空
            </Button>
          </Space>
        </div>
      </Card>

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

      {/* 股票信息展示 */}
      {currentStock && (
        <Card className="mb-6">
          <div className="flex items-center gap-4">
            <div className="text-2xl font-bold">{currentStock.code}</div>
            <div className="text-xl">{currentStock.name}</div>
            {currentStock.industry && (
              <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm">
                {currentStock.industry}
              </span>
            )}
          </div>
        </Card>
      )}

      {/* K线数据预览 */}
      {klineData.length > 0 && (
        <Card title="K线数据预览" className="mb-6">
          <div className="text-sm text-gray-500 mb-2">
            共 {klineData.length} 条数据 (
            {klineData[0]?.date} 至 {klineData[klineData.length - 1]?.date})
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="bg-gray-100">
                  <th className="px-4 py-2 text-left">日期</th>
                  <th className="px-4 py-2 text-right">开盘</th>
                  <th className="px-4 py-2 text-right">最高</th>
                  <th className="px-4 py-2 text-right">最低</th>
                  <th className="px-4 py-2 text-right">收盘</th>
                  <th className="px-4 py-2 text-right">成交量</th>
                </tr>
              </thead>
              <tbody>
                {klineData.slice(0, 10).map((item, index) => (
                  <tr key={index} className="border-b">
                    <td className="px-4 py-2">{item.date}</td>
                    <td className="px-4 py-2 text-right">{item.open.toFixed(2)}</td>
                    <td className="px-4 py-2 text-right">{item.high.toFixed(2)}</td>
                    <td className="px-4 py-2 text-right">{item.low.toFixed(2)}</td>
                    <td className="px-4 py-2 text-right">{item.close.toFixed(2)}</td>
                    <td className="px-4 py-2 text-right">{(item.volume / 10000).toFixed(2)}万</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {klineData.length > 10 && (
              <div className="text-center py-2 text-gray-500">
                还有 {klineData.length - 10} 条数据...
              </div>
            )}
          </div>
        </Card>
      )}

      {/* 分析进度步骤展示 - 类似ChatGPT风格 */}
      {isAnalyzing && pipelineSteps.length > 0 && (
        <Card 
          title={
            <div className="flex items-center gap-2">
              <Spin size="small" />
              <span>AI分析进度</span>
            </div>
          } 
          className="mb-6"
        >
          <Timeline
            items={pipelineSteps.map((step, index) => ({
              color: getStepStatusColor(step.status),
              children: (
                <div className="flex items-center justify-between">
                  <div>
                    <span className={`font-medium ${
                      step.status === 'completed' ? 'text-green-600' :
                      step.status === 'running' ? 'text-blue-600' :
                      step.status === 'error' ? 'text-red-600' : 'text-gray-400'
                    }`}>
                      {STEP_TITLES[step.step] || step.message}
                    </span>
                    {step.status === 'running' && (
                      <span className="ml-2 text-blue-500 text-sm">处理中...</span>
                    )}
                  </div>
                  {step.duration_ms && step.status === 'completed' && (
                    <span className="text-gray-400 text-sm ml-4">
                      {formatDuration(step.duration_ms)}
                    </span>
                  )}
                </div>
              ),
            }))}
          />
        </Card>
      )}

      {/* 分析结果 - 完成后隐藏步骤 */}
      {result && !isAnalyzing && (
        <Card title="AI分析结果" className="mb-6">
          {/* 置信度和元信息 */}
          <div className="mb-4 flex flex-wrap items-center gap-4">
            <span className="text-gray-600">置信度：</span>
            <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full transition-all duration-300"
                style={{ 
                  width: `${result.confidence_score * 100}%`,
                  backgroundColor: getConfidenceColor(result.confidence_score)
                }}
              />
            </div>
            <span className="font-medium" style={{ color: getConfidenceColor(result.confidence_score) }}>
              {(result.confidence_score * 100).toFixed(0)}%
            </span>
            {result.llm_model && (
              <Tag color="purple">AI模型: {result.llm_model}</Tag>
            )}
            {result.trend && (
              <Tag color={result.trend === '上涨' ? 'green' : result.trend === '下跌' ? 'red' : 'orange'}>
                趋势: {result.trend}
              </Tag>
            )}
          </div>

          {/* 交易建议 */}
          <Card size="small" className="mb-4 bg-gray-50">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div>
                <div className="text-gray-500 text-sm">交易方向</div>
                <Tag color={getDirectionColor(result.advice?.direction)} className="text-base mt-1">
                  {result.advice?.direction || '暂无建议'}
                </Tag>
              </div>
              {result.advice?.target_price && (
                <div>
                  <div className="text-gray-500 text-sm">目标价</div>
                  <div className="font-bold text-green-600 text-lg">{result.advice.target_price}</div>
                </div>
              )}
              {result.advice?.stop_loss && (
                <div>
                  <div className="text-gray-500 text-sm">止损价</div>
                  <div className="font-bold text-red-600 text-lg">{result.advice.stop_loss}</div>
                </div>
              )}
              {result.advice?.take_profit && (
                <div>
                  <div className="text-gray-500 text-sm">止盈目标</div>
                  <div className="font-bold text-green-600 text-lg">{result.advice.take_profit}</div>
                </div>
              )}
              {result.advice?.holding_period && (
                <div>
                  <div className="text-gray-500 text-sm">持仓周期</div>
                  <div className="font-bold text-lg">{result.advice.holding_period}天</div>
                </div>
              )}
              {result.advice?.risk_level && (
                <div>
                  <div className="text-gray-500 text-sm">风险等级</div>
                  <Tag color={result.advice.risk_level === '低' ? 'green' : result.advice.risk_level === '中' ? 'orange' : 'red'}>
                    {result.advice.risk_level}
                  </Tag>
                </div>
              )}
            </div>
          </Card>

          {/* Markdown 分析详情 */}
          <div className="prose max-w-none">
            <Card title="详细分析报告" size="small" className="bg-white">
              <div className="markdown-body ai-analysis-content">
                <ReactMarkdown 
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({node, ...props}) => <h1 className="text-2xl font-bold mt-6 mb-4 text-gray-800" {...props} />,
                    h2: ({node, ...props}) => <h2 className="text-xl font-bold mt-5 mb-3 text-gray-800" {...props} />,
                    h3: ({node, ...props}) => <h3 className="text-lg font-bold mt-4 mb-2 text-gray-800" {...props} />,
                    p: ({node, ...props}) => <p className="my-3 text-gray-700 leading-relaxed" {...props} />,
                    ul: ({node, ...props}) => <ul className="list-disc list-inside my-3 text-gray-700" {...props} />,
                    ol: ({node, ...props}) => <ol className="list-decimal list-inside my-3 text-gray-700" {...props} />,
                    li: ({node, ...props}) => <li className="my-1" {...props} />,
                    blockquote: ({node, ...props}) => <blockquote className="border-l-4 border-blue-400 pl-4 my-4 text-gray-600 italic" {...props} />,
                    code: ({node, ...props}) => <code className="bg-gray-100 px-2 py-1 rounded text-sm font-mono text-gray-800" {...props} />,
                    pre: ({node, ...props}) => <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto my-4" {...props} />,
                    table: ({node, ...props}) => <div className="overflow-x-auto my-4"><table className="min-w-full border border-gray-200" {...props} /></div>,
                    th: ({node, ...props}) => <th className="border border-gray-300 px-4 py-2 bg-gray-50 font-semibold text-left" {...props} />,
                    td: ({node, ...props}) => <td className="border border-gray-300 px-4 py-2" {...props} />,
                    strong: ({node, ...props}) => <strong className="font-bold text-gray-900" {...props} />,
                    em: ({node, ...props}) => <em className="italic text-gray-700" {...props} />,
                    a: ({node, ...props}) => <a className="text-blue-600 hover:underline" {...props} />,
                    hr: ({node}) => <hr className="my-6 border-gray-300" />,
                  }}
                >
                  {result.details}
                </ReactMarkdown>
              </div>
            </Card>
          </div>
        </Card>
      )}

      {/* 历史分析记录列表 */}
      <HistoryList stockCode={stockCode || undefined} />

      {/* 初始状态提示 */}
      {!currentStock && !result && !analysisLoading && !isAnalyzing && (
        <Result
          status="info"
          title="股票分析"
          subTitle="输入股票代码，选择K线类型和分析模式，点击开始分析获取AI分析报告"
        />
      )}
    </div>
  );
}

export default StockAnalysis;
