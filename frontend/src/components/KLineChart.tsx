import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';

interface KlineData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  amount: number;
}

interface KLineChartProps {
  data: KlineData[];
  title?: string;
  height?: number | string;
}

export function KLineChart({ data, title = 'K线图', height = 500 }: KLineChartProps) {
  const options = useMemo(() => {
    if (!data || data.length === 0) {
      return {
        title: { text: title },
        tooltip: { trigger: 'axis' },
        xAxis: { data: [] },
        yAxis: {},
        series: [],
      };
    }

    const dates = data.map((item) => item.date);
    const values = data.map((item) => [item.open, item.close, item.low, item.high]);
    const volumes = data.map((item, index) => ({
      value: item.volume,
      itemStyle: {
        color: item.close >= item.open ? '#ef4444' : '#22c55e',
      },
    }));

    return {
      title: { text: title, left: 'center' },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
        formatter: (params: any) => {
          if (Array.isArray(params) && params.length >= 2) {
            const klineParam = params.find((p: any) => p.seriesName === 'K线');
            const volumeParam = params.find((p: any) => p.seriesName === '成交量');
            if (klineParam) {
              const dataIndex = klineParam.dataIndex;
              const item = data[dataIndex];
              return `
                <div style="padding: 8px;">
                  <div><strong>${item.date}</strong></div>
                  <div>开盘: ${item.open.toFixed(2)}</div>
                  <div>收盘: ${item.close.toFixed(2)}</div>
                  <div>最高: ${item.high.toFixed(2)}</div>
                  <div>最低: ${item.low.toFixed(2)}</div>
                  <div>成交量: ${(item.volume / 10000).toFixed(2)}万</div>
                </div>
              `;
            }
          }
          return '';
        },
      },
      grid: [
        { left: '10%', right: '10%', height: '60%' },
        { left: '10%', right: '10%', top: '70%', height: '20%' },
      ],
      xAxis: [
        {
          type: 'category',
          data: dates,
          scale: true,
          boundaryGap: false,
          axisLine: { onZero: false },
          splitLine: { show: false },
          min: 'dataMin',
          max: 'dataMax',
        },
        {
          type: 'category',
          data: dates,
          gridIndex: 1,
          scale: true,
          boundaryGap: false,
          axisLine: { onZero: false },
          splitLine: { show: false },
          min: 'dataMin',
          max: 'dataMax',
        },
      ],
      yAxis: [
        {
          scale: true,
          splitArea: { show: true },
        },
        {
          scale: true,
          gridIndex: 1,
          splitNumber: 2,
          axisLabel: { show: false },
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { show: false },
        },
      ],
      dataZoom: [
        { type: 'inside', xAxisIndex: [0, 1], start: 50, end: 100 },
        { type: 'slider', xAxisIndex: [0, 1], start: 50, end: 100 },
      ],
      series: [
        {
          name: 'K线',
          type: 'candlestick',
          data: values,
          itemStyle: {
            color: '#ef4444',
            color0: '#22c55e',
            borderColor: '#ef4444',
            borderColor0: '#22c55e',
          },
        },
        {
          name: '成交量',
          type: 'bar',
          data: volumes,
          xAxisIndex: 1,
          yAxisIndex: 1,
        },
      ],
    };
  }, [data, title]);

  return <ReactECharts option={options} style={{ height }} />;
}

export default KLineChart;
