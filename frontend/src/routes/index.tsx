import { createBrowserRouter } from 'react-router-dom';
import MainLayout from '../components/Layout';
import Dashboard from '../pages/Dashboard';
import StockAnalysis from '../pages/StockAnalysis';
import MarketAnalysis from '../pages/MarketAnalysis';
import News from '../pages/News';
import LimitUp from '../pages/LimitUp';

const router = createBrowserRouter([
  {
    path: '/',
    element: (
      <MainLayout>
        <Dashboard />
      </MainLayout>
    ),
  },
  {
    path: '/stock-analysis',
    element: (
      <MainLayout>
        <StockAnalysis />
      </MainLayout>
    ),
  },
  {
    path: '/market-analysis',
    element: (
      <MainLayout>
        <MarketAnalysis />
      </MainLayout>
    ),
  },
  {
    path: '/news',
    element: (
      <MainLayout>
        <News />
      </MainLayout>
    ),
  },
  {
    path: '/limit-up',
    element: (
      <MainLayout>
        <LimitUp />
      </MainLayout>
    ),
  },
]);

export default router;
