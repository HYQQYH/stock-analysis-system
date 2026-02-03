import React, { useState } from 'react';
import { Card, Input, Button, Select, message } from 'antd';

const { Option } = Select;

function StockAnalysis() {
  const [stockCode, setStockCode] = useState('');
  const [sectorName, setSectorName] = useState('');
  const [klineType, setKlineType] = useState('day');
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    if (!stockCode) {
      message.warning('请输入股票代码');
      return;
    }
    setLoading(true);
    // TODO: 调用后端 API
    setTimeout(() => setLoading(false), 1000);
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">股票分析</h1>
      
      <Card className="mb-6">
        <div className="flex flex-wrap gap-4 items-end">
          <div>
            <label className="block text-sm mb-1">股票代码</label>
            <Input
              placeholder="如: 600000"
              value={stockCode}
              onChange={(e) => setStockCode(e.target.value)}
              style={{ width: 200 }}
            />
          </div>
          <div>
            <label className="block text-sm mb-1">K线类型</label>
            <Select value={klineType} onChange={setKlineType} style={{ width: 120 }}>
              <Option value="day">日K</Option>
              <Option value="week">周K</Option>
              <Option value="month">月K</Option>
            </Select>
          </div>
          <div>
            <label className="block text-sm mb-1">板块名称（可选）</label>
            <Input
              placeholder="如: 银行板块"
              value={sectorName}
              onChange={(e) => setSectorName(e.target.value)}
              style={{ width: 200 }}
            />
          </div>
          <Button type="primary" loading={loading} onClick={handleAnalyze}>
            开始分析
          </Button>
        </div>
      </Card>

      <Card title="分析结果">
        <p className="text-gray-500">输入股票代码后点击分析按钮查看结果</p>
      </Card>
    </div>
  );
}

export default StockAnalysis;
