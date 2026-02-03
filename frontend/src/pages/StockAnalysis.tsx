import React, { useState, useEffect } from 'react';
import { Card, Input, Button, Select, Space, Alert, Result } from 'antd';
import { useStockStore, useAnalysisStore, useLoadingStore, useToastStore } from '../store';
import { stockApi, analysisApi } from '../services/api';

const { Option } = Select;
const { Search } = Input;

type AnalysisMode = '基础面技术面综合' | '波段交易' | '短线T+1' | '涨停反包' | '投机套利' | '公司估值';

const ANALYSIS_MODES: AnalysisMode[] = [
  '基础面技术面综合',
  '波段交易',
  '短线T+1',
  '涨停反包',
  '投机套利',
  '公司估值',
];

interface AnalysisResultData {
  id: string;
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
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>('短线T+1');
  const [result, setResult] = useState<{
    summary: string;
    details: string;
    advice: {
      direction: string;
      targetPrice?: number;
      stopLoss?: number;
      takeProfit?: number;
      holdingPeriod?: number;
      riskLevel?: string;
    };
    confidenceScore: number;
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
        stockCode,
        klineType,
        sectorNames: inputSectorName ? [inputSectorName] : [],
        includeNews: true,
      });

      // 轮询获取结果
      let attempts = 0;
      const maxAttempts = 60;

      while (attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 500));
        
        const resultResponse = await analysisApi.getAnalysisResult(submitResponse.analysisId);
        
        if (resultResponse.status === 'completed') {
          const data = resultResponse;
          
          const analysisResult = {
            summary: data.analysisResult,
            details: data.analysisResult,
            advice: data.tradingAdvice,
            confidenceScore: data.confidenceScore,
          };
          
          setResult(analysisResult);
          
          // 保存到历史记录
          addAnalysis({
            id: data.id,
            stockCode: data.stockCode,
            analysisMode,
            analysisTime: data.analysisTime,
            summary: data.analysisResult.substring(0, 200),
            details: data.analysisResult,
            tradingAdvice: data.tradingAdvice as any,
            confidenceScore: data.confidenceScore,
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
        <Card title="分析结果" className="mb-6">
          {/* 置信度 */}
          <div className="mb-4 flex items-center gap-4">
            <span className="text-gray-600">置信度：</span>
            <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full ${result.confidenceScore > 0.7 ? 'bg-green-500' : result.confidenceScore > 0.4 ? 'bg-yellow-500' : 'bg-red-500'}`}
                style={{ width: `${result.confidenceScore * 100}%` }}
              />
            </div>
            <span className="font-medium">{(result.confidenceScore * 100).toFixed(0)}%</span>
          </div>

          {/* 交易建议 */}
          <Card size="small" className="mb-4 bg-gray-50">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div className="text-gray-500 text-sm">交易方向</div>
                <div className={`font-bold ${
                  result.advice.direction === '买入' ? 'text-green-600' : 
                  result.advice.direction === '卖出' ? 'text-red-600' : 'text-gray-600'
                }`}>
                  {result.advice.direction}
                </div>
              </div>
              {result.advice.targetPrice && (
                <div>
                  <div className="text-gray-500 text-sm">目标价</div>
                  <div className="font-bold text-green-600">{result.advice.targetPrice}</div>
                </div>
              )}
              {result.advice.stopLoss && (
                <div>
                  <div className="text-gray-500 text-sm">止损价</div>
                  <div className="font-bold text-red-600">{result.advice.stopLoss}</div>
                </div>
              )}
              {result.advice.holdingPeriod && (
                <div>
                  <div className="text-gray-500 text-sm">持仓周期</div>
                  <div className="font-bold">{result.advice.holdingPeriod}天</div>
                </div>
              )}
            </div>
          </Card>

          {/* 分析详情 */}
          <div className="prose max-w-none">
            <pre className="whitespace-pre-wrap text-gray-700 font-sans">
              {result.details}
            </pre>
          </div>
        </Card>
      )}

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
