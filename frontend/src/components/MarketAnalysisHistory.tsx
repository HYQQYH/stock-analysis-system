import React, { useState, useEffect } from 'react';
import { Card, Table, Tag, Button, Space, Modal, Spin, Empty, Pagination, message, Tooltip } from 'antd';
import { EyeOutlined, DeleteOutlined, ReloadOutlined } from '@ant-design/icons';
import MarkdownRenderer from './MarkdownRenderer';
import { analysisApi } from '../services/api';

// API返回的历史记录类型
interface MarketAnalysisHistoryItem {
  analysis_id: string;
  stock_code: string;
  analysis_mode: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'timeout';
  analysis_time: string;
  confidence_score: number | null;
  created_at: string;
}

// 完整分析结果类型
interface AnalysisDetail {
  id: string;
  analysis_id: string;
  stock_code: string;
  analysis_mode: string;
  status: string;
  analysis_time: string;
  result: {
    analysis_result: string;
    trading_advice: {
      direction: string;
      target_price?: number;
      stop_loss?: number;
      take_profit?: number;
      holding_period?: number;
      risk_level?: string;
    } | null;
    confidence_score: number | null;
    llm_model?: string;
  } | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

const MarketAnalysisHistory: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<MarketAnalysisHistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [currentDetail, setCurrentDetail] = useState<AnalysisDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // 获取大盘分析历史记录
  const fetchHistory = async () => {
    setLoading(true);
    try {
      const response = await analysisApi.getHistory({
        page,
        pageSize,
        stockCode: '000001', // 上证指数代码
        analysisType: 'index' // 大盘分析类型
      }) as {
        total: number;
        page: number;
        page_size: number;
        data: MarketAnalysisHistoryItem[];
      };

      setHistory(response.data || []);
      setTotal(response.total || 0);
    } catch (err) {
      console.error('获取大盘分析历史失败:', err);
      message.error('获取历史记录失败');
      // 使用空数组作为降级
      setHistory([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [page, pageSize]);

  // 查看详情
  const handleViewDetail = async (analysisId: string) => {
    setDetailModalVisible(true);
    setDetailLoading(true);
    setCurrentDetail(null);

    try {
      const response = await analysisApi.getAnalysisResult(analysisId) as AnalysisDetail;
      setCurrentDetail(response);
    } catch (err) {
      console.error('获取分析详情失败:', err);
      message.error('获取详情失败');
      setDetailModalVisible(false);
    } finally {
      setDetailLoading(false);
    }
  };

  // 删除记录
  const handleDelete = async (analysisId: string) => {
    try {
      await analysisApi.deleteAnalysis(analysisId);
      message.success('删除成功');
      fetchHistory();
    } catch (err) {
      console.error('删除失败:', err);
      message.error('删除失败');
    }
  };

  // 状态标签颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'processing';
      case 'pending': return 'warning';
      case 'failed':
      case 'timeout': return 'error';
      default: return 'default';
    }
  };

  // 状态文本
  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed': return '完成';
      case 'running': return '分析中';
      case 'pending': return '等待中';
      case 'failed': return '失败';
      case 'timeout': return '超时';
      default: return status;
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '分析时间',
      dataIndex: 'analysis_time',
      key: 'analysis_time',
      render: (time: string) => {
        if (!time) return '--';
        const date = new Date(time);
        return date.toLocaleString('zh-CN');
      },
    },
    {
      title: '分析类型',
      dataIndex: 'analysis_mode',
      key: 'analysis_mode',
      render: (mode: string) => mode || '大盘分析',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>
          {getStatusText(status)}
        </Tag>
      ),
    },
    {
      title: '置信度',
      dataIndex: 'confidence_score',
      key: 'confidence_score',
      render: (score: number | null) => {
        if (score === null) return '--';
        const percentage = Math.round(score * 100);
        return (
          <Tag color={percentage >= 70 ? 'green' : percentage >= 50 ? 'orange' : 'red'}>
            {percentage}%
          </Tag>
        );
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time: string) => {
        if (!time) return '--';
        const date = new Date(time);
        return date.toLocaleString('zh-CN');
      },
    },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, record: MarketAnalysisHistoryItem) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="link"
              icon={<EyeOutlined />}
              onClick={() => handleViewDetail(record.analysis_id)}
              disabled={record.status !== 'completed'}
            >
              查看
            </Button>
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record.analysis_id)}
            >
              删除
            </Button>
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <Card
      title="📊 大盘分析历史"
      className="mb-6"
      extra={
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchHistory}
            loading={loading}
          >
            刷新
          </Button>
        </Space>
      }
    >
      {loading && history.length === 0 ? (
        <div className="text-center py-10">
          <Spin tip="加载中..." />
        </div>
      ) : history.length === 0 ? (
        <Empty
          description="暂无大盘分析记录"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        >
          <Button type="primary" onClick={() => window.location.reload()}>
            刷新页面
          </Button>
        </Empty>
      ) : (
        <>
          <Table
            columns={columns}
            dataSource={history}
            rowKey="analysis_id"
            pagination={false}
            loading={loading}
            size="small"
          />
          <div className="mt-4 flex justify-end">
            <Pagination
              current={page}
              pageSize={pageSize}
              total={total}
              onChange={(p) => setPage(p)}
              showSizeChanger={false}
              showTotal={(total) => `共 ${total} 条记录`}
            />
          </div>
        </>
      )}

      {/* 详情弹窗 */}
      <Modal
        title="大盘分析详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={900}
      >
        {detailLoading ? (
          <div className="text-center py-20">
            <Spin tip="加载分析结果..." />
          </div>
        ) : currentDetail ? (
          <div>
            <div className="mb-4 flex flex-wrap gap-4">
              <div>
                <span className="text-gray-500">分析ID：</span>
                <span className="font-mono text-sm">{currentDetail.analysis_id}</span>
              </div>
              <div>
                <span className="text-gray-500">状态：</span>
                <Tag color={getStatusColor(currentDetail.status)}>
                  {getStatusText(currentDetail.status)}
                </Tag>
              </div>
              <div>
                <span className="text-gray-500">分析时间：</span>
                <span>
                  {currentDetail.analysis_time
                    ? new Date(currentDetail.analysis_time).toLocaleString('zh-CN')
                    : '--'}
                </span>
              </div>
              {currentDetail.result?.confidence_score && (
                <div>
                  <span className="text-gray-500">置信度：</span>
                  <Tag color="blue">
                    {Math.round(currentDetail.result.confidence_score * 100)}%
                  </Tag>
                </div>
              )}
              {currentDetail.result?.llm_model && (
                <div>
                  <span className="text-gray-500">AI模型：</span>
                  <span>{currentDetail.result.llm_model}</span>
                </div>
              )}
            </div>

            {/* 交易建议 */}
            {currentDetail.result?.trading_advice && (
              <Card title="📈 交易建议" size="small" className="mb-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <div className="text-gray-500 text-sm">方向</div>
                    <div
                      className={`text-xl font-bold ${
                        currentDetail.result.trading_advice.direction === '买入'
                          ? 'text-red-500'
                          : currentDetail.result.trading_advice.direction === '卖出'
                          ? 'text-green-500'
                          : ''
                      }`}
                    >
                      {currentDetail.result.trading_advice.direction || '--'}
                    </div>
                  </div>
                  {currentDetail.result.trading_advice.target_price && (
                    <div>
                      <div className="text-gray-500 text-sm">目标价</div>
                      <div className="text-xl font-bold text-red-500">
                        {currentDetail.result.trading_advice.target_price}
                      </div>
                    </div>
                  )}
                  {currentDetail.result.trading_advice.stop_loss && (
                    <div>
                      <div className="text-gray-500 text-sm">止损价</div>
                      <div className="text-xl font-bold text-green-500">
                        {currentDetail.result.trading_advice.stop_loss}
                      </div>
                    </div>
                  )}
                  {currentDetail.result.trading_advice.risk_level && (
                    <div>
                      <div className="text-gray-500 text-sm">风险等级</div>
                      <Tag
                        color={
                          currentDetail.result.trading_advice.risk_level === '低'
                            ? 'green'
                            : currentDetail.result.trading_advice.risk_level === '中'
                            ? 'orange'
                            : 'red'
                        }
                      >
                        {currentDetail.result.trading_advice.risk_level}
                      </Tag>
                    </div>
                  )}
                </div>
              </Card>
            )}

            {/* 分析内容（Markdown格式） */}
            {currentDetail.result?.analysis_result && (
              <Card title="📋 详细分析" size="small">
                <MarkdownRenderer content={currentDetail.result.analysis_result} />
              </Card>
            )}

            {/* 错误信息 */}
            {currentDetail.error_message && (
              <Card title="❌ 错误信息" size="small" className="mt-4">
                <div className="text-red-500">{currentDetail.error_message}</div>
              </Card>
            )}
          </div>
        ) : (
          <Empty description="暂无分析详情" />
        )}
      </Modal>
    </Card>
  );
};

export default MarketAnalysisHistory;
