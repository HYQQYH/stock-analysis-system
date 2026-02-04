import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Card, Tag, Spin } from 'antd';

interface MarkdownRendererProps {
  content: string;
  loading?: boolean;
  title?: string;
  className?: string;
}

/**
 * Markdown 渲染组件 - 用于优雅地展示 AI 分析结果
 * 
 * 支持的特性：
 * - 标题 (h1-h6)
 * - 粗体、斜体、删除线
 * - 列表 (有序/无序)
 * - 表格
 * - 代码块
 * - 链接
 * - 引用块
 */
export function MarkdownRenderer({ 
  content, 
  loading = false, 
  title,
  className = '' 
}: MarkdownRendererProps) {
  if (loading) {
    return (
      <Card className={className}>
        <div className="flex items-center justify-center py-10">
          <Spin size="large" tip="AI分析中，请稍候..." />
        </div>
      </Card>
    );
  }

  if (!content || content.trim() === '') {
    return (
      <Card className={className} title={title}>
        <div className="text-center py-10 text-gray-400">
          暂无分析内容
        </div>
      </Card>
    );
  }

  return (
    <Card 
      className={className}
      title={title || 'AI 分析报告'}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // 自定义标题样式
          h1: ({ children }) => (
            <h1 className="text-2xl font-bold text-gray-800 mb-4 mt-6 first:mt-0">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-xl font-bold text-gray-800 mb-3 mt-5">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-lg font-semibold text-gray-700 mb-2 mt-4">
              {children}
            </h3>
          ),
          // 自定义段落样式
          p: ({ children }) => (
            <p className="text-gray-600 leading-relaxed mb-3">
              {children}
            </p>
          ),
          // 自定义列表样式
          ul: ({ children }) => (
            <ul className="list-disc list-inside mb-4 space-y-1">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal list-inside mb-4 space-y-1">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="text-gray-600">
              {children}
            </li>
          ),
          // 自定义引用块样式
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-blue-500 bg-blue-50 pl-4 py-2 my-4 rounded-r">
              {children}
            </blockquote>
          ),
          // 自定义表格样式
          table: ({ children }) => (
            <div className="overflow-x-auto my-4">
              <table className="min-w-full border border-gray-200">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-gray-50">
              {children}
            </thead>
          ),
          tbody: ({ children }) => (
            <tbody className="divide-y divide-gray-200">
              {children}
            </tbody>
          ),
          th: ({ children }) => (
            <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-4 py-2 text-sm text-gray-600">
              {children}
            </td>
          ),
          // 自定义代码块样式
          code: ({ className: codeClass, children }) => {
            const isInline = !codeClass;
            if (isInline) {
              return (
                <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm text-pink-600 font-mono">
                  {children}
                </code>
              );
            }
            return (
              <code className={`${codeClass} block bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto my-4 text-sm font-mono`}>
                {children}
              </code>
            );
          },
          pre: ({ children }) => (
            <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto my-4">
              {children}
            </pre>
          ),
          // 自定义链接样式
          a: ({ href, children }) => (
            <a 
              href={href} 
              className="text-blue-600 hover:text-blue-800 underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              {children}
            </a>
          ),
          // 自定义强调样式
          strong: ({ children }) => (
            <strong className="font-bold text-gray-800">
              {children}
            </strong>
          ),
          em: ({ children }) => (
            <em className="italic text-gray-600">
              {children}
            </em>
          ),
          // 自定义分割线
          hr: () => (
            <hr className="my-6 border-gray-200" />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </Card>
  );
}

/**
 * 技术指标分析结果展示组件
 * 专门用于展示大盘技术分析结果
 */
interface TechnicalAnalysisCardProps {
  analysisContent: string;
  trend?: string;
  supportLevels?: number[];
  resistanceLevels?: number[];
  sentimentScore?: number;
  confidenceScore?: number;
  loading?: boolean;
  analysisTime?: string;
}

export function TechnicalAnalysisCard({
  analysisContent,
  trend,
  supportLevels = [],
  resistanceLevels = [],
  sentimentScore,
  confidenceScore,
  loading,
  analysisTime,
}: TechnicalAnalysisCardProps) {
  const hasIndicators = trend || supportLevels.length > 0 || resistanceLevels.length > 0 || sentimentScore !== undefined;
  
  return (
    <div className="space-y-4">
      {/* 关键指标摘要 */}
      {hasIndicators && (
        <Card size="small" className="mb-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {trend && (
              <div>
                <div className="text-gray-500 text-xs mb-1">趋势判断</div>
                <Tag color={trend === '上涨' ? 'red' : trend === '下跌' ? 'green' : 'orange'}>
                  {trend}
                </Tag>
              </div>
            )}
            {supportLevels.length > 0 && (
              <div>
                <div className="text-gray-500 text-xs mb-1">支撑位</div>
                <div className="text-green-600 font-semibold">
                  {supportLevels.map(l => l.toFixed(0)).join(' / ')}
                </div>
              </div>
            )}
            {resistanceLevels.length > 0 && (
              <div>
                <div className="text-gray-500 text-xs mb-1">压力位</div>
                <div className="text-red-600 font-semibold">
                  {resistanceLevels.map(l => l.toFixed(0)).join(' / ')}
                </div>
              </div>
            )}
            {sentimentScore !== undefined && (
              <div>
                <div className="text-gray-500 text-xs mb-1">情绪得分</div>
                <div className="font-semibold">
                  {sentimentScore.toFixed(0)}分
                </div>
              </div>
            )}
          </div>
          {confidenceScore !== undefined && (
            <div className="mt-3 pt-3 border-t border-gray-100">
              <div className="text-gray-500 text-xs">
                AI 置信度: {confidenceScore.toFixed(1)}%
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Markdown 分析内容 */}
      <MarkdownRenderer 
        content={analysisContent} 
        loading={loading}
        title="技术分析报告"
      />
      
      {/* 分析时间 */}
      {analysisTime && (
        <div className="text-xs text-gray-400 text-right">
          分析时间: {new Date(analysisTime).toLocaleString('zh-CN')}
        </div>
      )}
    </div>
  );
}

export default MarkdownRenderer;
