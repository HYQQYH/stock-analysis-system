import React from 'react';
import { Card, Progress, Tag, Button, Collapse } from 'antd';

interface TradingAdvice {
  direction: '买入' | '卖出' | '持有' | '观望';
  targetPrice?: number;
  stopLoss?: number;
  takeProfit?: number;
  holdingPeriod?: number;
  riskLevel?: '低' | '中' | '高';
  quantity?: number;
}

interface AnalysisReportProps {
  summary: string;
  details: string;
  advice: TradingAdvice;
  confidenceScore: number;
  llmModel?: string;
  analysisTime?: string;
  onRetry?: () => void;
}

export function AnalysisReport({
  summary,
  details,
  advice,
  confidenceScore,
  llmModel,
  analysisTime,
  onRetry,
}: AnalysisReportProps) {
  const getDirectionColor = (direction: string) => {
    switch (direction) {
      case '买入': return 'green';
      case '卖出': return 'red';
      case '持有': return 'orange';
      default: return 'default';
    }
  };

  const getRiskColor = (risk?: string) => {
    switch (risk) {
      case '低': return 'success';
      case '中': return 'warning';
      case '高': return 'error';
      default: return 'default';
    }
  };

  return (
    <Card
      title="AI 分析报告"
      size="small"
      className="shadow-sm"
      extra={
        onRetry && (
          <Button type="link" onClick={onRetry}>
            重新分析
          </Button>
        )
      }
    >
      {/* 置信度 */}
      <div className="flex items-center gap-4 mb-4">
        <span className="text-gray-500">置信度</span>
        <Progress
          percent={Math.round(confidenceScore * 100)}
          status={confidenceScore > 0.7 ? 'success' : confidenceScore > 0.4 ? 'normal' : 'exception'}
          strokeColor={confidenceScore > 0.7 ? '#52c41a' : confidenceScore > 0.4 ? '#1890ff' : '#ff4d4f'}
          style={{ flex: 1, maxWidth: 200 }}
        />
        {llmModel && (
          <span className="text-gray-400 text-xs">via {llmModel}</span>
        )}
      </div>

      {/* 交易建议 */}
      <Card size="small" className="mb-4 bg-gray-50">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div className="text-gray-500 text-sm">交易方向</div>
            <Tag color={getDirectionColor(advice.direction)} className="text-base">
              {advice.direction}
            </Tag>
          </div>
          {advice.targetPrice && (
            <div>
              <div className="text-gray-500 text-sm">目标价</div>
              <div className="text-green-600 font-bold text-lg">{advice.targetPrice.toFixed(2)}</div>
            </div>
          )}
          {advice.stopLoss && (
            <div>
              <div className="text-gray-500 text-sm">止损价</div>
              <div className="text-red-600 font-bold text-lg">{advice.stopLoss.toFixed(2)}</div>
            </div>
          )}
          {advice.holdingPeriod && (
            <div>
              <div className="text-gray-500 text-sm">持仓周期</div>
              <div className="font-bold text-lg">{advice.holdingPeriod}天</div>
            </div>
          )}
        </div>
        {advice.riskLevel && (
          <div className="mt-3 flex items-center gap-2">
            <span className="text-gray-500 text-sm">风险等级</span>
            <Tag color={getRiskColor(advice.riskLevel)}>{advice.riskLevel}</Tag>
          </div>
        )}
      </Card>

      {/* 分析摘要 */}
      <div className="mb-4">
        <div className="text-gray-500 text-sm mb-2">摘要</div>
        <div className="text-gray-700">{summary}</div>
      </div>

      {/* 详细分析 */}
      <Collapse
        size="small"
        items={[
          {
            key: 'details',
            label: '详细分析',
            children: (
              <pre className="whitespace-pre-wrap text-gray-700 text-sm font-sans bg-gray-50 p-3 rounded">
                {details}
              </pre>
            ),
          },
        ]}
      />

      {analysisTime && (
        <div className="mt-4 text-right text-gray-400 text-xs">
          分析时间: {new Date(analysisTime).toLocaleString('zh-CN')}
        </div>
      )}
    </Card>
  );
}

export default AnalysisReport;
