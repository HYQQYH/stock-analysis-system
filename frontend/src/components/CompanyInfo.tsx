import React from 'react';
import { Card, Descriptions, Tag } from 'antd';

interface CompanyInfoData {
  code: string;
  name: string;
  shortName?: string;
  industry?: string;
  region?: string;
  mainBusiness?: string;
  companyIntro?: string;
  market?: string;
  listingDate?: string;
}

interface CompanyInfoProps {
  data: CompanyInfoData;
}

export function CompanyInfo({ data }: CompanyInfoProps) {
  return (
    <Card title={`${data.name} (${data.code})`} size="small" className="shadow-sm">
      <Descriptions column={{ xs: 1, sm: 2, md: 3 }} size="small" bordered>
        <Descriptions.Item label="公司简称">{data.shortName || '-'}</Descriptions.Item>
        <Descriptions.Item label="所属行业">
          {data.industry ? <Tag color="blue">{data.industry}</Tag> : '-'}
        </Descriptions.Item>
        <Descriptions.Item label="所在地区">{data.region || '-'}</Descriptions.Item>
        <Descriptions.Item label="市场类型">{data.market || '-'}</Descriptions.Item>
        <Descriptions.Item label="上市日期">{data.listingDate || '-'}</Descriptions.Item>
      </Descriptions>
      
      {data.mainBusiness && (
        <div className="mt-4">
          <div className="text-gray-500 text-sm mb-1">主营业务</div>
          <div className="text-gray-700">{data.mainBusiness}</div>
        </div>
      )}
      
      {data.companyIntro && (
        <div className="mt-4">
          <div className="text-gray-500 text-sm mb-1">公司简介</div>
          <div className="text-gray-700 text-sm">{data.companyIntro}</div>
        </div>
      )}
    </Card>
  );
}

export default CompanyInfo;
