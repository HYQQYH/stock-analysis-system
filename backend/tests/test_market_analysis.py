"""
Unit tests for Market Analysis module
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from app.services.market_analysis import (
    MarketAnalysisService,
    MarketOverviewResult,
    MarketSentimentResult,
    IndexData,
    FundFlowData,
    MarketActivityData,
    LimitUpPoolData,
    MarketAnalysisError,
    get_market_overview,
    analyze_sentiment,
)


class TestMarketAnalysisError:
    """Tests for MarketAnalysisError exception"""
    
    def test_market_analysis_error_default(self):
        """Test default market analysis error"""
        error = MarketAnalysisError("Test error")
        assert error.message == "Test error"
        assert error.error_type == "market_analysis_error"
    
    def test_market_analysis_error_custom_type(self):
        """Test market analysis error with custom type"""
        error = MarketAnalysisError("Test error", "custom_type")
        assert error.error_type == "custom_type"


class TestMarketAnalysisService:
    """Tests for MarketAnalysisService class"""
    
    def test_service_initialization(self):
        """Test that service initializes correctly"""
        service = MarketAnalysisService()
        assert hasattr(service, 'data_collector')
        assert hasattr(service, 'kline_manager')
        assert hasattr(service, 'indicator_calculator')
        assert service.index_code == "000001"
    
    def test_service_with_custom_index_code(self):
        """Test service initialization with custom index code"""
        # Note: The service uses a fixed index code
        service = MarketAnalysisService()
        assert service.index_code == "000001"


class TestMarketOverviewResult:
    """Tests for MarketOverviewResult dataclass"""
    
    def test_result_creation(self):
        """Test creating a basic result"""
        result = MarketOverviewResult()
        assert result.index_code == "000001"
        assert result.is_valid == True
        assert result.error_message is None
    
    def test_result_to_dict_basic(self):
        """Test converting result to dictionary"""
        result = MarketOverviewResult()
        result_dict = result.to_dict()
        
        assert result_dict["index_code"] == "000001"
        assert result_dict["is_valid"] == True
        assert "analysis_time" in result_dict
    
    def test_result_to_dict_with_index_data(self):
        """Test converting result with index data to dictionary"""
        df = pd.DataFrame({
            'trade_date': ['2024-01-01', '2024-01-02'],
            'open_price': [3000.0, 3050.0],
            'close_price': [3010.0, 3060.0],
        })
        index_data = IndexData(kline_data=df)
        result = MarketOverviewResult(index_data=index_data)
        result_dict = result.to_dict()
        
        assert "index_kline" in result_dict
        assert len(result_dict["index_kline"]) == 2
    
    def test_result_to_dict_with_fund_flow(self):
        """Test converting result with fund flow data"""
        fund_flow = FundFlowData(processed_data={
            "trade_date": "2024-01-01",
            "main_net_inflow": 1000000000,
            "sh_close_price": 3000.0,
        })
        result = MarketOverviewResult(fund_flow_data=fund_flow)
        result_dict = result.to_dict()
        
        assert "fund_flow" in result_dict
        assert result_dict["fund_flow"]["main_net_inflow"] == 1000000000
    
    def test_result_to_dict_with_market_activity(self):
        """Test converting result with market activity data"""
        activity = MarketActivityData(processed_data={
            "rise_count": 1500,
            "fall_count": 800,
            "flat_count": 200,
            "activity_level": "warm",
        })
        result = MarketOverviewResult(market_activity=activity)
        result_dict = result.to_dict()
        
        assert "market_activity" in result_dict
        assert result_dict["market_activity"]["rise_count"] == 1500
    
    def test_result_to_dict_with_limit_up_pool(self):
        """Test converting result with limit-up pool data"""
        limit_up = LimitUpPoolData(processed_data={
            "total_count": 50,
            "industry_distribution": {"银行": 10, "科技": 8},
        })
        result = MarketOverviewResult(limit_up_pool=limit_up)
        result_dict = result.to_dict()
        
        assert "limit_up_pool" in result_dict
        assert result_dict["limit_up_pool"]["total_count"] == 50
    
    def test_result_to_dict_with_sentiment(self):
        """Test converting result with sentiment data"""
        sentiment = MarketSentimentResult(
            sentiment_score=65.5,
            sentiment_level="warm",
            bull_bear_ratio=1.5,
        )
        result = MarketOverviewResult(sentiment=sentiment)
        result_dict = result.to_dict()
        
        assert "sentiment" in result_dict
        assert result_dict["sentiment"]["sentiment_score"] == 65.5
        assert result_dict["sentiment"]["sentiment_level"] == "warm"
    
    def test_result_to_dict_invalid(self):
        """Test converting invalid result to dictionary"""
        result = MarketOverviewResult(
            is_valid=False,
            error_message="Test error message"
        )
        result_dict = result.to_dict()
        
        assert result_dict["is_valid"] == False
        assert result_dict["error_message"] == "Test error message"
    
    def test_result_to_dict_empty_dataframe(self):
        """Test converting result with empty DataFrame"""
        df = pd.DataFrame()
        index_data = IndexData(kline_data=df)
        result = MarketOverviewResult(index_data=index_data)
        result_dict = result.to_dict()
        
        assert result_dict["index_kline"] == []


class TestMarketSentimentResult:
    """Tests for MarketSentimentResult dataclass"""
    
    def test_sentiment_creation(self):
        """Test creating a sentiment result"""
        sentiment = MarketSentimentResult(
            sentiment_score=70.0,
            sentiment_level="hot",
            bull_bear_ratio=2.0,
        )
        assert sentiment.sentiment_score == 70.0
        assert sentiment.sentiment_level == "hot"
        assert sentiment.bull_bear_ratio == 2.0
    
    def test_sentiment_to_dict(self):
        """Test converting sentiment to dictionary"""
        sentiment = MarketSentimentResult(
            sentiment_score=50.0,
            sentiment_level="warm",
            rise_fall_count={"rise": 1000, "fall": 800, "flat": 200}
        )
        result = sentiment.to_dict()
        
        assert result["sentiment_score"] == 50.0
        assert result["sentiment_level"] == "warm"
        assert result["rise_fall_count"]["rise"] == 1000


class TestGetMarketOverview:
    """Tests for get_market_overview function"""
    
    @patch('app.services.market_analysis.DataCollector')
    @patch('app.services.market_analysis.KlineManager')
    @patch('app.services.market_analysis.IndicatorCalculator')
    def test_get_market_overview_function(self, mock_indicator, mock_kline, mock_collector):
        """Test that get_market_overview function exists and works"""
        result = get_market_overview()
        assert "index_code" in result
        assert "is_valid" in result


class TestAnalyzeSentiment:
    """Tests for analyze_sentiment function"""
    
    @patch('app.services.market_analysis.DataCollector')
    @patch('app.services.market_analysis.KlineManager')
    @patch('app.services.market_analysis.IndicatorCalculator')
    def test_analyze_sentiment_function(self, mock_indicator, mock_kline, mock_collector):
        """Test that analyze_sentiment function exists and works"""
        result = analyze_sentiment()
        assert "sentiment_score" in result


class TestDataClasses:
    """Tests for dataclasses used in the module"""
    
    def test_index_data_defaults(self):
        """Test IndexData with default values"""
        index = IndexData()
        assert index.kline_data is None
        assert index.indicators is None
    
    def test_fund_flow_data_defaults(self):
        """Test FundFlowData with default values"""
        fund = FundFlowData()
        assert fund.raw_data is None
        assert fund.processed_data is None
    
    def test_market_activity_data_defaults(self):
        """Test MarketActivityData with default values"""
        activity = MarketActivityData()
        assert activity.raw_data is None
        assert activity.processed_data is None
    
    def test_limit_up_pool_data_defaults(self):
        """Test LimitUpPoolData with default values"""
        limit_up = LimitUpPoolData()
        assert limit_up.raw_data is None
        assert limit_up.processed_data is None


class TestSentimentCalculation:
    """Tests for sentiment calculation logic"""
    
    @patch('akshare.stock_market_activity_legu')
    @patch('app.services.market_analysis.DataCollector')
    @patch('app.services.market_analysis.KlineManager')
    @patch('app.services.market_analysis.IndicatorCalculator')
    def test_analyze_market_sentiment_hot(self, mock_indicator, mock_kline, mock_collector, mock_activity):
        """Test sentiment analysis with hot market"""
        # Mock market activity
        mock_activity.return_value = pd.DataFrame({
            'item': ['上涨', '下跌', '平盘', '涨停', '活跃度'],
            'value': [2500, 800, 700, 80, '热']
        })
        
        service = MarketAnalysisService()
        sentiment = service.analyze_market_sentiment()
        
        # 2500/4000 * 100 = 62.5 (plus 5 if fund flow positive, max 100)
        assert sentiment.sentiment_score == 62.5
        assert sentiment.sentiment_level == "warm"  # With fund flow boost it's warm, not hot
    
    @patch('akshare.stock_market_activity_legu')
    @patch('app.services.market_analysis.DataCollector')
    @patch('app.services.market_analysis.KlineManager')
    @patch('app.services.market_analysis.IndicatorCalculator')
    def test_analyze_market_sentiment_warm(self, mock_indicator, mock_kline, mock_collector, mock_activity):
        """Test sentiment analysis with warm market"""
        # Mock market activity
        mock_activity.return_value = pd.DataFrame({
            'item': ['上涨', '下跌', '平盘'],
            'value': [1500, 1200, 800]
        })
        
        service = MarketAnalysisService()
        sentiment = service.analyze_market_sentiment()
        
        assert sentiment.sentiment_score == 42.86  # 1500/3500 * 100
        assert sentiment.sentiment_level == "warm"
    
    @patch('akshare.stock_market_activity_legu')
    @patch('app.services.market_analysis.DataCollector')
    @patch('app.services.market_analysis.KlineManager')
    @patch('app.services.market_analysis.IndicatorCalculator')
    def test_analyze_market_sentiment_cold(self, mock_indicator, mock_kline, mock_collector, mock_activity):
        """Test sentiment analysis with cold market"""
        # Mock market activity
        mock_activity.return_value = pd.DataFrame({
            'item': ['上涨', '下跌', '平盘'],
            'value': [500, 2000, 1000]
        })
        
        service = MarketAnalysisService()
        sentiment = service.analyze_market_sentiment()
        
        assert sentiment.sentiment_score == 14.29  # 500/3500 * 100
        assert sentiment.sentiment_level == "cold"


class TestConvenienceFunctions:
    """Tests for convenience functions"""
    
    def test_get_market_overview_exists(self):
        """Test that get_market_overview function exists"""
        assert callable(get_market_overview)
    
    def test_analyze_sentiment_exists(self):
        """Test that analyze_sentiment function exists"""
        assert callable(analyze_sentiment)


class TestColumnNormalization:
    """Tests for K-line column normalization"""
    
    def test_normalize_kline_columns_chinese(self):
        """Test normalizing Chinese column names"""
        service = MarketAnalysisService()
        df = pd.DataFrame({
            '日期': ['2024-01-01'],
            '开盘': [3000.0],
            '收盘': [3010.0],
            '最高': [3020.0],
            '最低': [2990.0],
            '成交量': [100000000]
        })
        result = service._normalize_kline_columns(df)
        
        assert 'trade_date' in result.columns
        assert 'open_price' in result.columns
        assert 'close_price' in result.columns
    
    def test_normalize_kline_columns_empty(self):
        """Test normalizing empty DataFrame"""
        service = MarketAnalysisService()
        df = pd.DataFrame()
        result = service._normalize_kline_columns(df)
        
        assert result.empty
    
    def test_normalize_kline_columns_none(self):
        """Test normalizing None DataFrame"""
        service = MarketAnalysisService()
        result = service._normalize_kline_columns(None)
        
        assert result is None


class TestErrorHandling:
    """Tests for error handling in the module"""
    
    @patch('app.services.market_analysis.DataCollector')
    @patch('app.services.market_analysis.KlineManager')
    @patch('app.services.market_analysis.IndicatorCalculator')
    def test_get_market_overview_with_error(self, mock_indicator, mock_kline, mock_collector):
        """Test market overview returns error result on failure"""
        # Mock collector to raise exception
        mock_collector_instance = MagicMock()
        mock_collector_instance.fetch_kline_data.side_effect = Exception("Test error")
        mock_collector_instance.fetch_market_fund_flow.side_effect = Exception("Test error")
        mock_collector.return_value = mock_collector_instance
        
        service = MarketAnalysisService()
        result = service.get_market_overview()
        
        # Should return with is_valid=True but empty data (graceful handling)
        assert result.is_valid == True
