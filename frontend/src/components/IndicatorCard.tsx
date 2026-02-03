import React from 'react';
import { Card, Progress, Tag } from 'antd';

interface IndicatorData {
  macd?: {
    dif: number[];
    dea: number[];
    macd: number[];
  };
  kdj?: {
    k: number[];
    d: number[];
    j: number[];
  };
  rsi?: number[];
}

interface IndicatorCardProps {
  data: IndicatorData;
  latestPrice?: number;
}

export function IndicatorCard({ data, latestPrice }: IndicatorCardProps) {
  const getMacdSignal = () => {
    if (!data.macd || data.macd.dif.length === 0) return null;
    const dif = data.macd.dif[data.macd.dif.length - 1];
    const dea = data.macd.dea[data.macd.dea.length - 1];
    const macd = data.macd.macd[data.macd.macd.length - 1];
    
    let signal = '中性';
    let color = 'default';
    if (dif > dea && macd > 0) {
      signal = '金叉/多头';
      color = 'green';
    } else if (dif < dea && macd < 0) {
      signal = '死叉/空头';
      color = 'red';
    }
    
    return { dif, dea, macd, signal, color };
  };

  const getKdjSignal = () => {
    if (!data.kdj || data.kdj.k.length === 0) return null;
    const k = data.kdj.k[data.kdj.k.length - 1];
    const d = data.kdj.d[data.kdj.d.length - 1];
    const j = data.kdj.j[data.kdj.j.length - 1];
    
    let signal = '中性';
    let color = 'default';
    if (k > 80 || j > 100) {
      signal = '超买';
      color = 'red';
    } else if (k < 20 || j < 0) {
      signal = '超卖';
      color = 'green';
    } else if (k > d) {
      signal = '多头';
      color = 'green';
    } else {
      signal = '空头';
      color = 'red';
    }
    
    return { k, d, j, signal, color };
  };

  const getRsiSignal = () => {
    if (!data.rsi || data.rsi.length === 0) return null;
    const rsi = data.rsi[data.rsi.length - 1];
    
    let signal = '中性';
    let color = 'default';
    if (rsi > 70) {
      signal = '超买';
      color = 'red';
    } else if (rsi < 30) {
      signal = '超卖';
      color = 'green';
    } else if (rsi > 50) {
      signal = '偏多';
      color = 'green';
    } else {
      signal = '偏空';
      color = 'red';
    }
    
    return { rsi, signal, color };
  };

  const macdSignal = getMacdSignal();
  const kdjSignal = getKdjSignal();
  const rsiSignal = getRsiSignal();

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* MACD 卡片 */}
      <Card title="MACD" size="small" className="shadow-sm">
        {macdSignal ? (
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-gray-500">信号</span>
              <Tag color={macdSignal.color}>{macdSignal.signal}</Tag>
            </div>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span>DIF</span>
                <span className={macdSignal.dif >= 0 ? 'text-red-500' : 'text-green-500'}>
                  {macdSignal.dif.toFixed(4)}
                </span>
              </div>
              <div className="flex justify-between">
                <span>DEA</span>
                <span>{macdSignal.dea.toFixed(4)}</span>
              </div>
              <div className="flex justify-between">
                <span>MACD</span>
                <span className={macdSignal.macd >= 0 ? 'text-red-500' : 'text-green-500'}>
                  {macdSignal.macd.toFixed(4)}
                </span>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-gray-400 text-center py-4">暂无数据</div>
        )}
      </Card>

      {/* KDJ 卡片 */}
      <Card title="KDJ" size="small" className="shadow-sm">
        {kdjSignal ? (
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-gray-500">信号</span>
              <Tag color={kdjSignal.color}>{kdjSignal.signal}</Tag>
            </div>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span>K</span>
                <Progress
                  percent={Math.min(kdjSignal.k, 100)}
                  size="small"
                  status={kdjSignal.k > 80 ? 'exception' : kdjSignal.k < 20 ? 'success' : 'active'}
                  showInfo={false}
                />
                <span>{kdjSignal.k.toFixed(1)}</span>
              </div>
              <div className="flex justify-between">
                <span>D</span>
                <span>{kdjSignal.d.toFixed(1)}</span>
              </div>
              <div className="flex justify-between">
                <span>J</span>
                <span className={kdjSignal.j > 100 ? 'text-red-500' : kdjSignal.j < 0 ? 'text-green-500' : ''}>
                  {kdjSignal.j.toFixed(1)}
                </span>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-gray-400 text-center py-4">暂无数据</div>
        )}
      </Card>

      {/* RSI 卡片 */}
      <Card title="RSI(14)" size="small" className="shadow-sm">
        {rsiSignal ? (
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-gray-500">信号</span>
              <Tag color={rsiSignal.color}>{rsiSignal.signal}</Tag>
            </div>
            <div className="text-center py-2">
              <Progress
                type="dashboard"
                percent={Math.round(rsiSignal.rsi)}
                status={rsiSignal.rsi > 70 ? 'exception' : rsiSignal.rsi < 30 ? 'success' : 'normal'}
                format={(percent) => `${percent}%`}
              />
            </div>
          </div>
        ) : (
          <div className="text-gray-400 text-center py-4">暂无数据</div>
        )}
      </Card>
    </div>
  );
}

export default IndicatorCard;
