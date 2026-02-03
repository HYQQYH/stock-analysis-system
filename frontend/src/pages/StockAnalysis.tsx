import React, { useState, useEffect } from 'react';
import { Card, Input, Button, Select, Space, Alert, Result, Tag, Spin, Collapse } from 'antd';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useStockStore, useAnalysisStore, useLoadingStore, useToastStore } from '../store';
import { stockApi, analysisApi } from '../services/api';
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
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>('短线T+1分析');
  // 注意：后端返回snake_case字段名
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
    setAnalysisLoading(true);

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

      // 轮询获取结果
      let attempts = 0;
      const maxAttempts = 120; // 增加超时时间

      while (attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        const resultResponse = await analysisApi.getAnalysisResult(submitResponse.analysis_id);
        
        if (resultResponse.status === 'completed') {
          const data = resultResponse;
          
          // 解析分析结果 - 后端返回的数据嵌套在 result 中
          const resultData = data.result;
          const analysisResult = {
            summary: resultData?.analysis_result?.substring(0, 200) || '暂无分析结果',
            details: resultData?.analysis_result || '暂无分析结果',
            advice: resultData?.trading_advice || { direction: '观望' },
            confidence_score: resultData?.confidence_score || 0,
            llm_model: resultData?.llm_model,
          };
          
          setResult(analysisResult);
          
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
          break;
        } else if (resultResponse.status === 'failed') {
          throw new Error('分析任务失败');
        }
        
        attempts++;
      }

      if (attempts >= maxAttempts) {
        throw new Error('分析超时，请稍后重试');
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : '分析失败';
      setError(message);
      showToast(message, 'error');
    } finally {
      setAnalysisLoading(false);
    }
  };

  // 清空查询
  const handleClear = () => {
    setStockCode('');
    setInputSectorName('');
    setResult(null);
    setError(null);
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
            <Input
              placeholder="如: 银行板块"
              value={inputSectorName}
              onChange={(e) => setInputSectorName(e.target.value)}
              style={{ width: 200 }}
              disabled={analysisLoading}
            />
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

      {/* 分析结果 */}
      {result && (
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
      {!currentStock && !result && !analysisLoading && (
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
