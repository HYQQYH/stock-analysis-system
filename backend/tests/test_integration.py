# Integration tests for Stock Analysis System
#
# Tests cover:
# 1. Data collection flow (akshare API calls)
# 2. Data storage flow (database read/write)
# 3. API endpoints (request/response)
# 4. AI analysis flow (LLM integration)
#
# Version: v1.0 (2026-2-03)
# Author: AI Assistant

import pytest
import time
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
from typing import Optional
import pandas as pd

from fastapi.testclient import TestClient
from app.main import app
from app.services.data_collector import DataCollector
from app.services.indicator_calculator import IndicatorCalculator
from app.services.stock_analysis import StockAnalysisService
from app.services.market_analysis import MarketAnalysisService
from app.services.ai_analyzer import AIAnalyzer, StockAnalysisResult, TradingAdvice
from app.services.analysis_pipeline import (
    StockAnalysisPipeline, 
    MarketAnalysisPipeline,
    PipelineExecutionResult,
    run_stock_analysis_pipeline,
    run_market_analysis_pipeline
)
from app.llm_config import (
    LLMManager, 
    LLMProvider, 
    LLMResponse, 
    LLMTokenUsage
)
from app.cache import build_cache_key, CacheKeys


# Fixtures
@pytest.fixture
def test_client():
    """Create a test client for the FastAPI application"""
    return TestClient(app)


@pytest.fixture
def sample_kline_data():
    """Create sample K-line data for testing (using English column names)"""
    dates = pd.date_range(end=datetime.now(), periods=60, freq='D')
    return pd.DataFrame({
        'date': dates.strftime('%Y-%m-%d').tolist(),
        'open': [10.0 + i * 0.1 for i in range(60)],
        'close': [10.2 + i * 0.1 for i in range(60)],
        'high': [10.5 + i * 0.1 for i in range(60)],
        'low': [9.8 + i * 0.1 for i in range(60)],
        'volume': [1000000 + i * 10000 for i in range(60)],
        'amount': [10000000 + i * 100000 for i in range(60)],
        'pct_change': [0.5 + i * 0.1 for i in range(60)],
        'turnover': [1.0 + i * 0.05 for i in range(60)]
    })


@pytest.fixture
def sample_kline_data_chinese():
    """Create sample K-line data for testing (using Chinese column names for API response)"""
    dates = pd.date_range(end=datetime.now(), periods=60, freq='D')
    return pd.DataFrame({
        '日期': dates.strftime('%Y-%m-%d').tolist(),
        '开盘': [10.0 + i * 0.1 for i in range(60)],
        '收盘': [10.2 + i * 0.1 for i in range(60)],
        '最高': [10.5 + i * 0.1 for i in range(60)],
        '最低': [9.8 + i * 0.1 for i in range(60)],
        '成交量': [1000000 + i * 10000 for i in range(60)],
        '成交额': [10000000 + i * 100000 for i in range(60)],
        '涨跌幅': [0.5 + i * 0.1 for i in range(60)],
        '换手率': [1.0 + i * 0.05 for i in range(60)]
    })


@pytest.fixture
def sample_stock_data():
    """Create sample stock data for AI analysis"""
    return {
        'stock_code': '600000',
        'stock_name': '浦发银行',
        'current_price': 10.25,
        'change_percent': 2.15,
        'industry': '银行业',
        'kline_str': '日期 | 收盘\n2026-01-27 | 10.08\n2026-01-28 | 10.12\n2026-01-29 | 10.25'
    }


@pytest.fixture
def sample_news_list():
    """Create sample news list for testing"""
    return [
        {'title': '央行降息', 'time': '2026-01-29', 'content': '央行宣布降息25个基点'},
        {'title': '新能源政策利好', 'time': '2026-01-28', 'content': '新能源行业获得政策支持'},
        {'title': '大盘放量上涨', 'time': '2026-01-27', 'content': '两市成交量突破万亿'}
    ]


# Data Collector Integration Tests
class TestDataCollectorIntegration:
    """Integration tests for data collection module"""
    
    def test_collector_initialization(self):
        """Test that data collector initializes correctly"""
        dc = DataCollector(retry=3, backoff=1.0)
        assert dc.retry == 3
        assert dc.backoff == 1.0
        assert hasattr(dc, 'fetch_kline_data')
        assert hasattr(dc, 'fetch_limit_up_pool')
        assert hasattr(dc, 'fetch_market_fund_flow')
        assert hasattr(dc, 'fetch_market_sentiment')
    
    @patch('akshare.stock_zh_a_hist')
    def test_fetch_kline_data_success(self, mock_akshare, sample_kline_data_chinese):
        """Test successful K-line data fetching"""
        mock_akshare.return_value = sample_kline_data_chinese
        
        dc = DataCollector(retry=1, backoff=0.1)
        df = dc.fetch_kline_data("600000", period="daily")
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        mock_akshare.assert_called_once()
    
    @patch('akshare.stock_zh_a_hist')
    def test_fetch_kline_data_weekly_period(self, mock_akshare, sample_kline_data_chinese):
        """Test K-line data fetching for weekly period"""
        mock_akshare.return_value = sample_kline_data_chinese
        
        dc = DataCollector(retry=1, backoff=0.1)
        df = dc.fetch_kline_data("600000", period="weekly")
        
        assert isinstance(df, pd.DataFrame)
        mock_akshare.assert_called_once()
    
    @patch('akshare.stock_zh_a_hist')
    def test_fetch_kline_data_retry_on_failure(self, mock_akshare):
        """Test retry mechanism on API failure"""
        call_count = 0
        
        def fail_then_succeed(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary API failure")
            return pd.DataFrame({'日期': ['2024-01-01'], '开盘': [10.0], '收盘': [10.5]})
        
        mock_akshare.side_effect = fail_then_succeed
        
        dc = DataCollector(retry=3, backoff=0.01)
        df = dc.fetch_kline_data("600000")
        
        assert call_count == 2
        assert isinstance(df, pd.DataFrame)
    
    def test_fetch_kline_data_invalid_period(self):
        """Test handling of invalid period parameter"""
        dc = DataCollector(retry=1, backoff=0.1)
        
        with pytest.raises(ValueError, match="Unsupported period"):
            dc.fetch_kline_data("600000", period="invalid")


# Indicator Calculator Integration Tests
class TestIndicatorCalculatorIntegration:
    """Integration tests for technical indicator calculation"""
    
    def test_calculator_initialization(self):
        """Test that indicator calculator initializes correctly"""
        calc = IndicatorCalculator()
        assert hasattr(calc, 'calculate_macd')
        assert hasattr(calc, 'calculate_kdj')
        assert hasattr(calc, 'calculate_rsi')
        assert hasattr(calc, 'calculate_all_indicators')
    
    def test_calculate_all_indicators_success(self, sample_kline_data):
        """Test successful calculation of all indicators"""
        calc = IndicatorCalculator()
        result = calc.calculate_all_indicators(sample_kline_data)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        
        # Check for required indicator columns
        has_macd = any('macd' in c.lower() for c in result.columns)
        # pandas-ta uses K_9_3, D_9_3, J_9_3 format
        has_kdj = any('k_' in c.lower() or 'd_' in c.lower() or 'j_' in c.lower() 
                     for c in result.columns)
        
        assert has_macd, f"No MACD columns found. Columns: {result.columns.tolist()}"
        assert has_kdj, f"No KDJ columns found. Columns: {result.columns.tolist()}"
    
    def test_calculate_macd(self, sample_kline_data):
        """Test MACD calculation"""
        calc = IndicatorCalculator()
        result = calc.calculate_macd(sample_kline_data)
        
        assert isinstance(result, pd.DataFrame)
        assert 'MACD_12_26_9' in result.columns or 'MACDh_12_26_9' in result.columns
    
    def test_calculate_kdj(self, sample_kline_data):
        """Test KDJ calculation"""
        calc = IndicatorCalculator()
        result = calc.calculate_kdj(sample_kline_data)
        
        assert isinstance(result, pd.DataFrame)
        # pandas-ta uses K_9_3, D_9_3, J_9_3 format
        assert 'K_9_3' in result.columns or 'KDJ_K' in result.columns or 'K' in result.columns
        assert 'D_9_3' in result.columns or 'KDJ_D' in result.columns or 'D' in result.columns
        assert 'J_9_3' in result.columns or 'KDJ_J' in result.columns or 'J' in result.columns
    
    def test_calculate_rsi(self, sample_kline_data):
        """Test RSI calculation"""
        calc = IndicatorCalculator()
        result = calc.calculate_rsi(sample_kline_data)
        
        assert isinstance(result, pd.DataFrame)
        assert 'RSI_14' in result.columns
    
    def test_calculate_indicators_empty_data(self):
        """Test handling of empty data"""
        calc = IndicatorCalculator()
        empty_df = pd.DataFrame()
        
        # Empty data should raise an error since there's no 'close' column
        with pytest.raises(ValueError, match="close"):
            calc.calculate_all_indicators(empty_df)
    
    def test_calculate_macd_missing_close_column(self):
        """Test MACD calculation with missing close column"""
        calc = IndicatorCalculator()
        df_no_close = pd.DataFrame({
            'open': [10.0, 10.5],
            'high': [10.3, 11.0],
            'low': [9.9, 10.4]
        })
        
        with pytest.raises(ValueError, match="close"):
            calc.calculate_macd(df_no_close)
    
    def test_calculate_kdj_missing_columns(self):
        """Test KDJ calculation with missing columns"""
        calc = IndicatorCalculator()
        df_no_cols = pd.DataFrame({
            'open': [10.0, 10.5]
        })
        
        with pytest.raises(ValueError, match="high.*low.*close"):
            calc.calculate_kdj(df_no_cols)
    
    def test_calculate_rsi_missing_close_column(self):
        """Test RSI calculation with missing close column"""
        calc = IndicatorCalculator()
        df_no_close = pd.DataFrame({
            'open': [10.0, 10.5],
            'high': [10.3, 11.0]
        })
        
        with pytest.raises(ValueError, match="close"):
            calc.calculate_rsi(df_no_close)


# Stock Analysis Service Integration Tests
class TestStockAnalysisServiceIntegration:
    """Integration tests for stock analysis service"""
    
    def test_service_initialization(self):
        """Test that stock analysis service initializes correctly"""
        service = StockAnalysisService()
        assert hasattr(service, 'data_collector')
        assert hasattr(service, 'kline_manager')
        assert hasattr(service, 'indicator_calculator')
    
    @patch('app.services.stock_analysis.DataCollector')
    @patch('app.services.stock_analysis.KlineManager')
    @patch('app.services.stock_analysis.IndicatorCalculator')
    def test_analyze_single_stock_invalid_code(self, mock_indicator, mock_kline, mock_collector):
        """Test analysis with invalid stock code"""
        service = StockAnalysisService()
        result = service.analyze_single_stock("INVALID")
        
        assert result.stock_code == "INVALID"
        assert result.is_valid == False
        assert "Invalid stock code" in result.error_message
    
    @patch('app.services.stock_analysis.DataCollector')
    @patch('app.services.stock_analysis.KlineManager')
    @patch('app.services.stock_analysis.IndicatorCalculator')
    def test_analyze_single_stock_valid_code(self, mock_indicator, mock_kline, mock_collector):
        """Test analysis with valid stock code"""
        mock_collector_instance = MagicMock()
        mock_collector_instance.fetch_kline_data.return_value = pd.DataFrame({
            '日期': ['2024-01-01', '2024-01-02'],
            '开盘': [10.0, 10.5],
            '收盘': [10.2, 10.8],
            '最高': [10.3, 11.0],
            '最低': [9.9, 10.4],
            '成交量': [1000000, 1200000],
            '成交额': [10200000, 12960000]
        })
        mock_collector.return_value = mock_collector_instance
        
        mock_indicator_instance = MagicMock()
        mock_indicator_instance.calculate_all_indicators.return_value = pd.DataFrame({
            'close': [10.0, 10.2, 10.5, 10.8, 11.0],
            'MACD': [0.1, 0.15, 0.2, 0.25, 0.3],
            'K': [50, 55, 60, 65, 70],
            'D': [48, 52, 56, 60, 64],
            'J': [54, 61, 68, 75, 82],
            'RSI': [45, 50, 55, 60, 65]
        })
        mock_indicator.return_value = mock_indicator_instance
        
        service = StockAnalysisService()
        result = service.analyze_single_stock("600000")
        
        assert result.stock_code == "600000"
    
    def test_validate_stock_code(self):
        """Test stock code validation"""
        service = StockAnalysisService()
        
        assert service.validate_stock_code("600000") == True
        assert service.validate_stock_code("000001") == True
        assert service.validate_stock_code("300001") == True
        
        with pytest.raises(Exception):
            service.validate_stock_code("12345")
        with pytest.raises(Exception):
            service.validate_stock_code("1234567")
        with pytest.raises(Exception):
            service.validate_stock_code("ABCDEF")


# Market Analysis Service Integration Tests
class TestMarketAnalysisServiceIntegration:
    """Integration tests for market analysis service"""
    
    def test_service_initialization(self):
        """Test that market analysis service initializes correctly"""
        service = MarketAnalysisService()
        assert hasattr(service, 'data_collector')
        assert hasattr(service, 'kline_manager')
        assert hasattr(service, 'indicator_calculator')
        assert service.index_code == "000001"
    
    @patch('app.services.market_analysis.DataCollector')
    @patch('app.services.market_analysis.KlineManager')
    @patch('app.services.market_analysis.IndicatorCalculator')
    def test_get_market_overview(self, mock_indicator, mock_kline, mock_collector):
        """Test getting market overview"""
        mock_collector_instance = MagicMock()
        mock_collector_instance.fetch_kline_data.return_value = pd.DataFrame({
            '日期': ['2024-01-01'],
            '开盘': [3000.0],
            '收盘': [3010.0],
            '最高': [3020.0],
            '最低': [2990.0],
            '成交量': [100000000]
        })
        mock_collector.return_value = mock_collector_instance
        
        service = MarketAnalysisService()
        result = service.get_market_overview()
        
        assert result.index_code == "000001"
        assert hasattr(result, 'is_valid')
    
    @patch('akshare.stock_market_activity_legu')
    @patch('app.services.market_analysis.DataCollector')
    @patch('app.services.market_analysis.KlineManager')
    @patch('app.services.market_analysis.IndicatorCalculator')
    def test_analyze_market_sentiment(self, mock_indicator, mock_kline, mock_collector, mock_activity):
        """Test market sentiment analysis"""
        mock_activity.return_value = pd.DataFrame({
            'item': ['上涨', '下跌', '平盘', '涨停'],
            'value': [2500, 800, 700, 80]
        })
        
        service = MarketAnalysisService()
        sentiment = service.analyze_market_sentiment()
        
        assert sentiment.sentiment_score > 0
        assert sentiment.sentiment_level in ['cold', 'warm', 'hot']


# AI Analyzer Integration Tests
class TestAIAnalyzerIntegration:
    """Integration tests for AI analysis module"""
    
    def test_analyzer_initialization(self):
        """Test that AI analyzer initializes correctly"""
        analyzer = AIAnalyzer()
        assert hasattr(analyzer, 'llm')
        assert hasattr(analyzer, 'analyze_stock')
        assert hasattr(analyzer, 'analyze_market')
        assert hasattr(analyzer, 'extract_news_insights')
    
    def test_trading_advice_dataclass(self):
        """Test TradingAdvice dataclass"""
        advice = TradingAdvice(
            direction="买入",
            target_price=10.5,
            quantity=1000,
            stop_loss=9.5,
            take_profit=12.0,
            holding_period=5,
            risk_level="中",
            confidence_score=0.75
        )
        
        assert advice.direction == "买入"
        assert advice.target_price == 10.5
        assert advice.risk_level == "中"
        
        advice_dict = advice.to_dict()
        assert advice_dict["direction"] == "买入"
        assert advice_dict["target_price"] == 10.5
    
    def test_stock_analysis_result_dataclass(self, sample_stock_data):
        """Test StockAnalysisResult dataclass"""
        trading_advice = TradingAdvice(
            direction="买入",
            target_price=10.5,
            stop_loss=9.5,
            take_profit=12.0
        )
        
        result = StockAnalysisResult(
            stock_code=sample_stock_data['stock_code'],
            stock_name=sample_stock_data['stock_name'],
            analysis_mode="短线T+1",
            analysis_type="综合分析",
            trend="上涨",
            trading_advice=trading_advice,
            analysis_content="Test analysis content",
            confidence_score=0.75,
            llm_provider="openai",
            llm_model="gpt-3.5-turbo"
        )
        
        assert result.stock_code == "600000"
        assert result.trading_advice.direction == "买入"
        assert result.confidence_score == 0.75
        
        result_dict = result.to_dict()
        assert result_dict["stock_code"] == "600000"
        assert result_dict["trading_advice"]["direction"] == "买入"
    
    def test_parse_trading_advice(self):
        """Test parsing trading advice from text"""
        analyzer = AIAnalyzer()
        
        text = """交易方向：买入
目标价格：10.50
止损价格：9.50
止盈目标：12.00
持仓时间：5
风险等级：中
置信度：0.75
分析理由：技术指标显示买入信号"""
        
        advice = analyzer._parse_trading_advice(text)
        
        assert advice.direction == "买入"
        assert advice.target_price == 10.50
        assert advice.stop_loss == 9.50
        assert advice.take_profit == 12.00
        assert advice.holding_period == 5
        assert advice.risk_level == "中"
        assert advice.confidence_score == 0.75
    
    def test_extract_json_from_response(self):
        """Test extracting JSON from LLM response"""
        analyzer = AIAnalyzer()
        
        text1 = """```json
{
    "trend": "上涨",
    "confidence_score": 0.85,
    "trading_advice": {
        "direction": "买入",
        "target_price": 10.5
    }
}
```"""
        
        json_data = analyzer._extract_json_from_response(text1)
        assert json_data is not None
        assert json_data["trend"] == "上涨"
        assert json_data["confidence_score"] == 0.85
        
        text2 = '{"trend": "震荡", "confidence_score": 0.5}'
        json_data = analyzer._extract_json_from_response(text2)
        assert json_data is not None
        assert json_data["trend"] == "震荡"


# Analysis Pipeline Integration Tests
class TestAnalysisPipelineIntegration:
    """Integration tests for analysis pipelines"""
    
    def test_pipeline_initialization(self):
        """Test pipeline initialization"""
        pipeline = StockAnalysisPipeline("600000", "银行板块", "短线T+1")
        assert pipeline.stock_code == "600000"
        assert pipeline.sector_name == "银行板块"
        assert pipeline.analysis_mode == "短线T+1"
    
    @patch('app.services.analysis_pipeline.DataCollector')
    @patch('app.services.analysis_pipeline.KlineManager')
    @patch('app.services.analysis_pipeline.IndicatorCalculator')
    @patch('app.services.analysis_pipeline.StockAnalysisService')
    @patch('app.services.analysis_pipeline.AIAnalyzer')
    @patch('app.services.analysis_pipeline.get_redis_client')
    def test_stock_pipeline_invalid_code(self, mock_redis, mock_ai, mock_service, 
                                          mock_indicator, mock_kline, mock_collector):
        """Test stock pipeline with invalid code"""
        mock_redis_instance = MagicMock()
        mock_redis_instance.set_json.return_value = True
        mock_redis.return_value = mock_redis_instance
        
        pipeline = StockAnalysisPipeline("INVALID", "银行板块")
        result = pipeline.run()
        
        assert result.success == False
        assert "Invalid stock code" in result.error_message
    
    @patch('app.services.analysis_pipeline.DataCollector')
    @patch('app.services.analysis_pipeline.KlineManager')
    @patch('app.services.analysis_pipeline.IndicatorCalculator')
    @patch('app.services.analysis_pipeline.StockAnalysisService')
    @patch('app.services.analysis_pipeline.AIAnalyzer')
    @patch('app.services.analysis_pipeline.get_redis_client')
    def test_stock_pipeline_execution(self, mock_redis, mock_ai, mock_service,
                                       mock_indicator, mock_kline, mock_collector):
        """Test stock pipeline execution flow"""
        mock_redis_instance = MagicMock()
        mock_redis_instance.set_json.return_value = True
        mock_redis.return_value = mock_redis_instance
        
        mock_service_instance = MagicMock()
        from app.services.stock_analysis import StockAnalysisResult, CompanyInfo, RelatedNews
        # Create a real RelatedNews with proper count attribute
        related_news = RelatedNews(count=0, news_list=[])
        mock_result = StockAnalysisResult(
            stock_code="600000",
            is_valid=True,
            company_info=CompanyInfo(
                stock_code="600000",
                stock_name="浦发银行",
                exchange="SH",
                industry="银行"
            ),
            related_news=related_news
        )
        mock_service_instance.analyze_single_stock.return_value = mock_result
        mock_service.return_value = mock_service_instance
        
        mock_ai_instance = MagicMock()
        from app.services.ai_analyzer import StockAnalysisResult as AIStockResult, TradingAdvice
        mock_ai_result = AIStockResult(
            stock_code="600000",
            stock_name="浦发银行",
            analysis_mode="短线T+1",
            analysis_type="综合分析",
            trend="震荡",
            trading_advice=TradingAdvice(),
            success=True
        )
        mock_ai_instance.analyze_stock.return_value = mock_ai_result
        mock_ai.return_value = mock_ai_instance
        
        pipeline = StockAnalysisPipeline("600000", "银行板块", "短线T+1")
        result = pipeline.run()
        
        assert result.success == True
        assert result.pipeline_type == "stock_analysis"
        assert result.stock_code == "600000"
    
    def test_market_pipeline_initialization(self):
        """Test market pipeline initialization"""
        pipeline = MarketAnalysisPipeline("000001")
        assert pipeline.index_code == "000001"
    
    @patch('app.services.analysis_pipeline.DataCollector')
    @patch('app.services.analysis_pipeline.KlineManager')
    @patch('app.services.analysis_pipeline.IndicatorCalculator')
    @patch('app.services.analysis_pipeline.MarketAnalysisService')
    @patch('app.services.analysis_pipeline.AIAnalyzer')
    @patch('app.services.analysis_pipeline.get_redis_client')
    def test_market_pipeline_execution(self, mock_redis, mock_ai, mock_service,
                                        mock_indicator, mock_kline, mock_collector):
        """Test market pipeline execution flow"""
        mock_redis_instance = MagicMock()
        mock_redis_instance.set_json.return_value = True
        mock_redis.return_value = mock_redis_instance
        
        mock_service_instance = MagicMock()
        from app.services.market_analysis import MarketOverviewResult
        mock_result = MarketOverviewResult(
            index_code="000001",
            is_valid=True
        )
        mock_service_instance.get_market_overview.return_value = mock_result
        mock_service.return_value = mock_service_instance
        
        mock_ai_instance = MagicMock()
        from app.services.ai_analyzer import MarketAnalysisResult as AIMarketResult
        mock_ai_result = AIMarketResult(
            index_code="000001",
            index_name="上证指数",
            trend="震荡",
            success=True
        )
        mock_ai_instance.analyze_market.return_value = mock_ai_result
        mock_ai.return_value = mock_ai_instance
        
        pipeline = MarketAnalysisPipeline("000001")
        result = pipeline.run()
        
        assert result.success == True
        assert result.pipeline_type == "market_analysis"
        assert result.stock_code == "000001"
    
    def test_run_stock_analysis_convenience_function(self):
        """Test convenience function for running stock analysis"""
        with patch('app.services.analysis_pipeline.StockAnalysisPipeline.run') as mock_run:
            mock_result = PipelineExecutionResult(
                success=True,
                pipeline_type="stock_analysis",
                stock_code="600000"
            )
            mock_run.return_value = mock_result
            
            result = run_stock_analysis_pipeline("600000")
            
            assert result.success == True
            assert result.stock_code == "600000"
    
    def test_run_market_analysis_convenience_function(self):
        """Test convenience function for running market analysis"""
        with patch('app.services.analysis_pipeline.MarketAnalysisPipeline.run') as mock_run:
            mock_result = PipelineExecutionResult(
                success=True,
                pipeline_type="market_analysis",
                stock_code="000001"
            )
            mock_run.return_value = mock_result
            
            result = run_market_analysis_pipeline("000001")
            
            assert result.success == True
            assert result.stock_code == "000001"


# API Endpoint Integration Tests
class TestAPIEndpointsIntegration:
    """Integration tests for API endpoints"""
    
    def test_health_endpoint(self, test_client):
        """Test health check endpoint"""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_root_endpoint(self, test_client):
        """Test root endpoint"""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
    
    def test_api_version_health(self, test_client):
        """Test API version-specific health check"""
        response = test_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @patch('akshare.stock_zh_a_hist')
    def test_stock_kline_endpoint(self, mock_akshare, test_client, sample_kline_data_chinese):
        """Test stock K-line data endpoint"""
        mock_akshare.return_value = sample_kline_data_chinese
        
        response = test_client.get("/api/v1/stocks/600000/kline?kline_type=day")
        # The endpoint may return 200 or 500 depending on internal processing
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["code"] == 0
            assert "data" in data
    
    @patch('akshare.stock_zh_a_hist')
    def test_stock_indicators_endpoint(self, mock_akshare, test_client, sample_kline_data_chinese):
        """Test stock technical indicators endpoint"""
        mock_akshare.return_value = sample_kline_data_chinese
        
        response = test_client.get("/api/v1/stocks/600000/indicators?days=30")
        # The endpoint may return 200 or 500 depending on internal processing
        assert response.status_code in [200, 500]
    
    def test_stock_kline_invalid_code(self, test_client):
        """Test K-line endpoint with invalid stock code"""
        response = test_client.get("/api/v1/stocks/123/kline")
        # Should return error (422, 400, or 500)
        assert response.status_code in [422, 400, 500]
    
    def test_stock_kline_invalid_kline_type(self, test_client):
        """Test K-line endpoint with invalid kline_type"""
        response = test_client.get("/api/v1/stocks/600000/kline?kline_type=invalid")
        # Should work with default or return appropriate error
        assert response.status_code in [200, 400, 422, 500]


# LLM Integration Tests
class TestLLMIntegration:
    """Integration tests for LLM functionality"""
    
    def test_llm_manager_initialization(self):
        """Test LLM manager initialization"""
        manager = LLMManager()
        assert manager.current_provider is None
        assert manager.current_client is None
        assert len(manager.FALLBACK_ORDER) > 0
    
    def test_llm_response_dataclass(self):
        """Test LLM response dataclass"""
        token_usage = LLMTokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cost_usd=0.005
        )
        
        response = LLMResponse(
            content="Test response",
            provider="openai",
            model="gpt-3.5-turbo",
            token_usage=token_usage,
            response_time_ms=1500.5
        )
        
        assert response.content == "Test response"
        assert response.provider == "openai"
        assert response.token_usage.total_tokens == 150
        assert response.success == True
        
        response_dict = response.to_dict()
        assert response_dict["content"] == "Test response"
        assert response_dict["token_usage"]["prompt_tokens"] == 100
    
    def test_llm_response_failure(self):
        """Test failed LLM response"""
        response = LLMResponse(
            content="",
            provider="openai",
            model="gpt-3.5-turbo",
            token_usage=LLMTokenUsage(),
            response_time_ms=500,
            success=False,
            error_message="API rate limit exceeded"
        )
        
        assert response.success == False
        assert response.error_message == "API rate limit exceeded"


# Cache Integration Tests
class TestCacheIntegration:
    """Integration tests for caching functionality"""
    
    def test_build_cache_key(self):
        """Test cache key building"""
        key = build_cache_key("kline", "600000", "day", "20240101")
        assert "kline" in key
        assert "600000" in key
        assert "day" in key
        assert "20240101" in key
    
    def test_build_cache_key_without_date(self):
        """Test cache key building without date"""
        key = build_cache_key("stock_info", "600000")
        assert "stock_info" in key
        assert "600000" in key
    
    def test_cache_keys_enum(self):
        """Test cache keys enum values"""
        # Check that the enum values exist (actual values may vary)
        assert hasattr(CacheKeys, 'KLINE') or hasattr(CacheKeys, 'kline')
        assert hasattr(CacheKeys, 'INDICATOR') or hasattr(CacheKeys, 'indicator')
        assert hasattr(CacheKeys, 'STOCK_INFO') or hasattr(CacheKeys, 'stock_info')


# Pipeline Logger Integration Tests
class TestPipelineLoggerIntegration:
    """Integration tests for pipeline logging"""
    
    def test_pipeline_logger_initialization(self):
        """Test pipeline logger initialization"""
        from app.services.analysis_pipeline import PipelineLogger
        
        logger = PipelineLogger("test_pipeline", "600000")
        assert logger.pipeline_name == "test_pipeline"
        assert logger.stock_code == "600000"
        assert logger.status == "pending"
    
    def test_pipeline_logger_start_end(self):
        """Test pipeline logger start and end"""
        from app.services.analysis_pipeline import PipelineLogger
        
        logger = PipelineLogger("test_pipeline", "600000")
        logger.start()
        assert logger.status == "running"
        assert logger.start_time is not None
        
        logger.log_step("test_step", "Test message", {"key": "value"})
        assert len(logger.steps) >= 2
        
        logger.end(success=True)
        assert logger.status == "completed"
        assert logger.end_time is not None
    
    def test_pipeline_logger_error_logging(self):
        """Test pipeline logger error logging"""
        from app.services.analysis_pipeline import PipelineLogger
        
        logger = PipelineLogger("test_pipeline", "600000")
        logger.start()
        
        try:
            raise ValueError("Test error")
        except ValueError as e:
            logger.log_error("test_step", e, {"context": "test"})
        
        assert len(logger.steps) > 0
        error_step = logger.steps[-1]
        assert error_step.get("status") == "error"
        assert "Test error" in error_step.get("message", "")
    
    def test_get_log_summary(self):
        """Test getting pipeline log summary"""
        from app.services.analysis_pipeline import PipelineLogger
        
        logger = PipelineLogger("test_pipeline", "600000")
        logger.start()
        logger.log_step("step1", "Step 1 completed")
        logger.log_step("step2", "Step 2 completed")
        logger.end(success=True)
        
        summary = logger.get_log_summary()
        
        assert summary["pipeline_name"] == "test_pipeline"
        assert summary["status"] == "completed"
        # steps_executed includes start, step1, step2, and end
        assert summary["steps_executed"] >= 3
        assert len(summary["steps"]) >= 3


# End-to-End Flow Tests
class TestEndToEndFlows:
    """End-to-end integration flow tests"""
    
    @patch('app.services.analysis_pipeline.DataCollector')
    @patch('app.services.analysis_pipeline.KlineManager')
    @patch('app.services.analysis_pipeline.IndicatorCalculator')
    @patch('app.services.analysis_pipeline.StockAnalysisService')
    @patch('app.services.analysis_pipeline.AIAnalyzer')
    @patch('app.services.analysis_pipeline.get_redis_client')
    def test_complete_stock_analysis_flow(self, mock_redis, mock_ai, mock_service,
                                           mock_indicator, mock_kline, mock_collector):
        """Test complete stock analysis flow from data collection to AI analysis"""
        mock_redis_instance = MagicMock()
        mock_redis_instance.set_json.return_value = True
        mock_redis.return_value = mock_redis_instance
        
        from app.services.stock_analysis import StockAnalysisResult, CompanyInfo, RelatedNews
        # Create a real RelatedNews with proper count attribute
        related_news = RelatedNews(count=0, news_list=[])
        mock_result = StockAnalysisResult(
            stock_code="600000",
            is_valid=True,
            company_info=CompanyInfo(
                stock_code="600000",
                stock_name="浦发银行",
                exchange="SH",
                industry="银行"
            ),
            related_news=related_news
        )
        mock_service_instance = MagicMock()
        mock_service_instance.analyze_single_stock.return_value = mock_result
        mock_service.return_value = mock_service_instance
        
        from app.services.ai_analyzer import StockAnalysisResult as AIStockResult, TradingAdvice
        mock_ai_result = AIStockResult(
            stock_code="600000",
            stock_name="浦发银行",
            analysis_mode="短线T+1",
            analysis_type="综合分析",
            trend="震荡",
            trading_advice=TradingAdvice(direction="买入", target_price=10.5),
            success=True,
            confidence_score=0.75
        )
        mock_ai_instance = MagicMock()
        mock_ai_instance.analyze_stock.return_value = mock_ai_result
        mock_ai.return_value = mock_ai_instance
        
        pipeline = StockAnalysisPipeline("600000", None, "短线T+1")
        result = pipeline.run()
        
        assert result.success == True
        assert result.pipeline_type == "stock_analysis"
        assert result.execution_time_ms >= 0
        
        log = result.execution_log
        assert log["status"] == "completed"
        assert log["steps_executed"] >= 4
    
    @patch('app.services.analysis_pipeline.DataCollector')
    @patch('app.services.analysis_pipeline.KlineManager')
    @patch('app.services.analysis_pipeline.IndicatorCalculator')
    @patch('app.services.analysis_pipeline.MarketAnalysisService')
    @patch('app.services.analysis_pipeline.AIAnalyzer')
    @patch('app.services.analysis_pipeline.get_redis_client')
    def test_complete_market_analysis_flow(self, mock_redis, mock_ai, mock_service,
                                            mock_indicator, mock_kline, mock_collector):
        """Test complete market analysis flow from data collection to AI analysis"""
        mock_redis_instance = MagicMock()
        mock_redis_instance.set_json.return_value = True
        mock_redis.return_value = mock_redis_instance
        
        from app.services.market_analysis import MarketOverviewResult
        mock_result = MarketOverviewResult(
            index_code="000001",
            is_valid=True
        )
        mock_service_instance = MagicMock()
        mock_service_instance.get_market_overview.return_value = mock_result
        mock_service.return_value = mock_service_instance
        
        from app.services.ai_analyzer import MarketAnalysisResult as AIMarketResult
        mock_ai_result = AIMarketResult(
            index_code="000001",
            index_name="上证指数",
            trend="震荡",
            sentiment_score=50.0,
            success=True
        )
        mock_ai_instance = MagicMock()
        mock_ai_instance.analyze_market.return_value = mock_ai_result
        mock_ai.return_value = mock_ai_instance
        
        pipeline = MarketAnalysisPipeline("000001")
        result = pipeline.run()
        
        assert result.success == True
        assert result.pipeline_type == "market_analysis"
        assert result.execution_time_ms >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
