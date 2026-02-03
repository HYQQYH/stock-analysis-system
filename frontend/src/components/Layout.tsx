import React from 'react';
import { Layout, Menu } from 'antd';
import { Link, useLocation } from 'react-router-dom';

const { Header, Content } = Layout;

function MainLayout({ children }: { children: React.ReactNode }) {
  const location = useLocation();

  const menuItems = [
    { key: '/', label: <Link to="/">首页</Link> },
    { key: '/stock-analysis', label: <Link to="/stock-analysis">股票分析</Link> },
    { key: '/market-analysis', label: <Link to="/market-analysis">大盘分析</Link> },
    { key: '/news', label: <Link to="/news">新闻资讯</Link> },
    { key: '/limit-up', label: <Link to="/limit-up">涨停股池</Link> },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', alignItems: 'center' }}>
        <div className="font-bold text-xl mr-8">📈 股票分析系统</div>
        <Menu
          mode="horizontal"
          selectedKeys={[location.pathname]}
          items={menuItems}
          style={{ flex: 1, borderBottom: 'none' }}
        />
      </Header>
      <Content>{children}</Content>
    </Layout>
  );
}

export default MainLayout;
