/**
 * 历史分析记录组件
 * 用于展示和管理股票分析历史记录
 */
import React, { useEffect, useState } from 'react';
import { Card, Table, Tag, Button, Space, Tooltip, Modal, Empty, Spin, Pagination } from 'antd';
import { EyeOutlined, DeleteOutlined, ReloadOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useAnalysisStore, useToastStore, useLoadingStore } from '../store';
import { analysisApi } from '../services/api';
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';

// 配置 dayjs 插件
dayjs.extend(utc);
dayjs.extend(timezone);

interface HistoryListProps {
  stockCode?: string;
  onViewDetail?: (record: any) => void;
  refreshKey?: number;
}

interface HistoryItem {
  id: string;
  analysis_id: string;
  stock_code: string;
  analysis_mode: string;
  status: string;
  analysis_time: string | null;
  confidence_score: number | null;
  created_at: string;
}

function HistoryList({ stockCode, onViewDetail, refreshKey }: HistoryListProps) {
  const { history, removeAnalysis } = useAnalysisStore();
  const { showToast } = useToastStore();

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [loading, setLoading] = useState(false);
  const [historyData, setHistoryData] = useState<HistoryItem[]>([]);
  const [total, setTotal] = useState(0);

  // 从后端获取历史记录
  const fetchHistory = async () => {
    setLoading(true);
    try {
      const response = await analysisApi.getHistory({
        page,
        pageSize,
        stockCode: stockCode,
      });
      
      // 转换为 HistoryItem 格式
      const items: HistoryItem[] = (response.data || []).map((item: any) => ({
        id: item.id || item.analysis_id,
        analysis_id: item.analysis_id || item.id,
        stock_code: item.stock_code,
        analysis_mode: item.analysis_mode,
        status: item.status,
        analysis_time: item.analysis_time,
        confidence_score: item.confidence_score,
        created_at: item.created_at || item.analysis_time,
      }));
      
      setHistoryData(items);
      setTotal(response.total || items.length);
    } catch (err) {
      console.error('获取历史记录失败:', err);
      // 如果后端调用失败，使用本地存储的历史记录
      const localHistory = stockCode
        ? history.filter(h => h.stockCode === stockCode)
        : history;
      
      const items: HistoryItem[] = localHistory.map((h) => ({
        id: h.id,
        analysis_id: h.id,
        stock_code: h.stockCode,
        analysis_mode: h.analysisMode,
        status: h.status,
        analysis_time: h.analysisTime,
        confidence_score: h.confidenceScore,
        created_at: h.analysisTime,
      }));
      
      setHistoryData(items);
      setTotal(items.length);
    } finally {
      setLoading(false);
    }
  };

  // 刷新历史记录
  const handleRefresh = () => {
    fetchHistory();
    showToast('已刷新历史记录', 'success');
  };

  // 查看详情
  const handleViewDetail = async (record: HistoryItem) => {
    try {
      setLoading(true);
      const response = await analysisApi.getAnalysisResult(record.analysis_id);
      
      if (onViewDetail) {
        onViewDetail(response);
      } else {
        // 默认行为：显示在 Modal 中
        Modal.info({
          title: `分析详情 - ${record.stock_code}`,
          width: 900,
          content: (
            <div className="analysis-detail-modal">
              {/* 元信息标签 */}
              <div className="mb-4">
                <Space>
                  <Tag color="blue">{record.analysis_mode}</Tag>
                  <Tag color={record.status === 'completed' ? 'green' : record.status === 'failed' ? 'red' : 'orange'}>
                    {record.status === 'completed' ? '已完成' : record.status === 'failed' ? '失败' : '进行中'}
                  </Tag>
                  {record.confidence_score !== null && (
                    <Tag color={record.confidence_score >= 0.7 ? 'green' : record.confidence_score >= 0.5 ? 'orange' : 'red'}>
                      置信度: {(record.confidence_score * 100).toFixed(0)}%
                    </Tag>
                  )}
                  {response.result?.llm_model && (
                    <Tag color="purple">AI: {response.result.llm_model}</Tag>
                  )}
                </Space>
              </div>
              
              {/* 交易建议卡片 */}
              {response.result && response.result.trading_advice && (
                <Card size="small" className="mb-4 bg-blue-50 border-blue-200">
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                    <div>
                      <div className="text-gray-500 text-xs">交易方向</div>
                      <Tag color={
                        response.result.trading_advice.direction === '买入' ? 'green' :
                        response.result.trading_advice.direction === '卖出' ? 'red' :
                        response.result.trading_advice.direction === '持有' ? 'blue' : 'default'
                      } className="text-sm mt-1">
                        {response.result.trading_advice.direction || '暂无'}
                      </Tag>
                    </div>
                    {response.result.trading_advice.target_price && (
                      <div>
                        <div className="text-gray-500 text-xs">目标价</div>
                        <div className="font-bold text-green-600 text-sm">
                          {response.result.trading_advice.target_price}
                        </div>
                      </div>
                    )}
                    {response.result.trading_advice.stop_loss && (
                      <div>
                        <div className="text-gray-500 text-xs">止损价</div>
                        <div className="font-bold text-red-600 text-sm">
                          {response.result.trading_advice.stop_loss}
                        </div>
                      </div>
                    )}
                    {response.result.trading_advice.take_profit && (
                      <div>
                        <div className="text-gray-500 text-xs">止盈目标</div>
                        <div className="font-bold text-green-600 text-sm">
                          {response.result.trading_advice.take_profit}
                        </div>
                      </div>
                    )}
                    {response.result.trading_advice.holding_period && (
                      <div>
                        <div className="text-gray-500 text-xs">持仓周期</div>
                        <div className="font-bold text-sm">
                          {response.result.trading_advice.holding_period}天
                        </div>
                      </div>
                    )}
                    {response.result.trading_advice.risk_level && (
                      <div>
                        <div className="text-gray-500 text-xs">风险等级</div>
                        <Tag color={
                          response.result.trading_advice.risk_level === '低' ? 'green' :
                          response.result.trading_advice.risk_level === '中' ? 'orange' : 'red'
                        } className="text-sm mt-1">
                          {response.result.trading_advice.risk_level}
                        </Tag>
                      </div>
                    )}
                  </div>
                </Card>
              )}
              
              {/* Markdown 分析结果 */}
              {response.result && response.result.analysis_result && (
                <Card size="small" title="详细分析报告" className="bg-white">
                  <div className="markdown-content">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        h1: ({ children }) => <h1 className="text-xl font-bold mt-4 mb-3 text-gray-800">{children}</h1>,
                        h2: ({ children }) => <h2 className="text-lg font-bold mt-3 mb-2 text-gray-800">{children}</h2>,
                        h3: ({ children }) => <h3 className="text-base font-bold mt-2 mb-2 text-gray-800">{children}</h3>,
                        p: ({ children }) => <p className="my-2 text-gray-700 leading-relaxed">{children}</p>,
                        ul: ({ children }) => <ul className="list-disc list-inside my-2 ml-4 text-gray-700">{children}</ul>,
                        ol: ({ children }) => <ol className="list-decimal list-inside my-2 ml-4 text-gray-700">{children}</ol>,
                        li: ({ children }) => <li className="my-1">{children}</li>,
                        blockquote: ({ children }) => (
                          <blockquote className="border-l-4 border-blue-400 pl-4 my-3 text-gray-600 italic bg-gray-50 py-2 rounded-r">
                            {children}
                          </blockquote>
                        ),
                        code: ({ children }) => (
                          <code className="bg-gray-100 px-2 py-0.5 rounded text-sm font-mono text-gray-800">{children}</code>
                        ),
                        pre: ({ children }) => (
                          <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto my-3 text-sm">
                            {children}
                          </pre>
                        ),
                        table: ({ children }) => (
                          <div className="overflow-x-auto my-3">
                            <table className="min-w-full border border-gray-200 text-sm">{children}</table>
                          </div>
                        ),
                        th: ({ children }) => (
                          <th className="border border-gray-300 px-3 py-2 bg-gray-50 font-semibold text-left">{children}</th>
                        ),
                        td: ({ children }) => (
                          <td className="border border-gray-300 px-3 py-2">{children}</td>
                        ),
                        strong: ({ children }) => <strong className="font-bold text-gray-900">{children}</strong>,
                        em: ({ children }) => <em className="italic text-gray-700">{children}</em>,
                        a: ({ children, href }) => <a className="text-blue-600 hover:underline" href={href}>{children}</a>,
                        hr: () => <hr className="my-4 border-gray-300" />,
                      }}
                    >
                      {response.result.analysis_result}
                    </ReactMarkdown>
                  </div>
                </Card>
              )}
            </div>
          ),
          styles: { content: { maxHeight: '70vh', overflowY: 'auto' } },
        });
      }
    } catch (err) {
      showToast('获取分析详情失败', 'error');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // 删除历史记录
  const handleDelete = (record: HistoryItem) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除股票 ${record.stock_code} 的分析记录吗？`,
      okText: '确认',
      cancelText: '取消',
      onOk: async () => {
        try {
          await analysisApi.deleteAnalysis(record.analysis_id);
          removeAnalysis(record.id);
          fetchHistory();
          showToast('删除成功', 'success');
        } catch (err) {
          // 如果后端删除失败，只删除本地
          removeAnalysis(record.id);
          showToast('已从本地删除', 'success');
        }
      },
    });
  };

  // 初始加载和刷新
  useEffect(() => {
    fetchHistory();
  }, [page, pageSize, stockCode, refreshKey]);

  // 表格列定义
  const columns = [
    {
      title: '股票代码',
      dataIndex: 'stock_code',
      key: 'stock_code',
      width: 100,
    },
    {
      title: '分析模式',
      dataIndex: 'analysis_mode',
      key: 'analysis_mode',
      width: 140,
      render: (mode: string) => (
        <Tag color="blue">{mode}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const colors: Record<string, string> = {
          completed: 'success',
          failed: 'error',
          pending: 'processing',
          running: 'processing',
          timeout: 'warning',
        };
        const labels: Record<string, string> = {
          completed: '已完成',
          failed: '失败',
          pending: '等待中',
          running: '分析中',
          timeout: '超时',
        };
        return (
          <Tag color={colors[status] || 'default'}>
            {labels[status] || status}
          </Tag>
        );
      },
    },
    {
      title: '置信度',
      dataIndex: 'confidence_score',
      key: 'confidence_score',
      width: 100,
      render: (score: number | null) => {
        if (score === null) return '-';
        const color = score >= 0.7 ? '#52c41a' : score >= 0.5 ? '#faad14' : '#ff4d4f';
        return (
          <span style={{ color, fontWeight: 'bold' }}>
            {(score * 100).toFixed(0)}%
          </span>
        );
      },
    },
    {
      title: '分析时间',
      dataIndex: 'analysis_time',
      key: 'analysis_time',
      width: 160,
      render: (time: string | null) => {
        if (!time) return '-';
        // 转换为本地时区显示 (假设后端返回的是UTC时间)
        return dayjs.utc(time).local().format('YYYY-MM-DD HH:mm:ss');
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_: any, record: HistoryItem) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handleViewDetail(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  // 渲染空状态
  if (!loading && historyData.length === 0) {
    return (
      <Card title="历史分析记录" className="mb-6">
        <Empty description="暂无历史分析记录" />
      </Card>
    );
  }

  return (
    <Card
      title="历史分析记录"
      extra={
        <Tooltip title="刷新">
          <Button
            type="text"
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
            loading={loading}
          />
        </Tooltip>
      }
      className="mb-6"
    >
      <Spin spinning={loading}>
        <Table
          dataSource={historyData}
          columns={columns}
          rowKey="id"
          pagination={false}
          size="small"
          scroll={{ x: 800 }}
        />
        
        {total > pageSize && (
          <div className="mt-4 flex justify-center">
            <Pagination
              current={page}
              pageSize={pageSize}
              total={total}
              onChange={(p, ps) => {
                setPage(p);
                setPageSize(ps);
              }}
              showSizeChanger
              showTotal={(total) => `共 ${total} 条记录`}
            />
          </div>
        )}
      </Spin>
    </Card>
  );
}

export default HistoryList;
