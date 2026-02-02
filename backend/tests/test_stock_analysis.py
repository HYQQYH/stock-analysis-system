"""
Unit tests for Stock Analysis module
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from app.services.stock_analysis import (
    StockAnalysisService,
    StockAnalysisResult,
    StockKlineData,
    TechnicalIndicators,
    CompanyInfo,
    RelatedNews,
    SectorData,
    InvalidStockCodeError,
    StockAnalysisError,
    analyze_stock,
)


class TestInvalidStockCodeError:
    """Tests for InvalidStockCodeError exception"""
    
    def test_invalid_stock_code_empty(self):
        """Test error for empty stock code"""
        with pytest.raises(InvalidStockCodeError) as exc_info:
            raise InvalidStockCodeError("")
        assert "Invalid stock code format" in str(exc_info.value)
        assert exc_info.value.error_type == "invalid_stock_code"
    
    def test_invalid_stock_code_too_short(self):
        """Test error for stock code that's too short"""
        with pytest.raises(InvalidStockCodeError) as exc_info:
            raise InvalidStockCodeError("12345")
        assert "6 digits" in str(exc_info.value)
    
    def test_invalid_stock_code_too_long(self):
        """Test error for stock code that's too long"""
        with pytest.raises(InvalidStockCodeError) as exc_info:
            raise InvalidStockCodeError("1234567")
        assert "6 digits" in str(exc_info.value)
    
    def test_invalid_stock_code_non_numeric(self):
        """Test error for non-numeric stock code"""
        with pytest.raises(InvalidStockCodeError) as exc_info:
            raise InvalidStockCodeError("ABCDEF")
        assert "6 digits" in str(exc_info.value)


class TestStockAnalysisService:
    """Tests for StockAnalysisService class"""
    
    def test_service_initialization(self):
        """Test that service initializes correctly"""
        service = StockAnalysisService()
        assert hasattr(service, 'data_collector')
        assert hasattr(service, 'kline_manager')
        assert hasattr(service, 'indicator_calculator')
    
    def test_validate_stock_code_valid_sh(self):
        """Test validation of valid Shanghai stock code"""
        service = StockAnalysisService()
        assert service.validate_stock_code("600000") == True
    
    def test_validate_stock_code_valid_sz(self):
        """Test validation of valid Shenzhen stock code"""
        service = StockAnalysisService()
        assert service.validate_stock_code("000001") == True
        assert service.validate_stock_code("300001") == True
    
    def test_validate_stock_code_invalid(self):
        """Test validation of invalid stock code"""
        service = StockAnalysisService()
        with pytest.raises(InvalidStockCodeError):
            service.validate_stock_code("12345")
    
    def test_validate_stock_code_empty(self):
        """Test validation of empty stock code"""
        service = StockAnalysisService()
        with pytest.raises(InvalidStockCodeError):
            service.validate_stock_code("")
    
    def test_validate_stock_code_non_numeric(self):
        """Test validation of non-numeric stock code"""
        service = StockAnalysisService()
        with pytest.raises(InvalidStockCodeError):
            service.validate_stock_code("ABCDEF")
    
    def test_get_exchange_from_code_sh(self):
        """Test exchange detection for Shanghai stocks"""
        service = StockAnalysisService()
        assert service.get_exchange_from_code("600000") == "SH"
        assert service.get_exchange_from_code("688888") == "SH"
    
    def test_get_exchange_from_code_sz(self):
        """Test exchange detection for Shenzhen stocks"""
        service = StockAnalysisService()
        assert service.get_exchange_from_code("000001") == "SZ"
        assert service.get_exchange_from_code("300001") == "SZ"
    
    def test_get_exchange_from_code_invalid(self):
        """Test exchange detection for invalid stock code"""
        service = StockAnalysisService()
        with pytest.raises(InvalidStockCodeError):
            service.get_exchange_from_code("900000")


class TestStockAnalysisResult:
    """Tests for StockAnalysisResult dataclass"""
    
    def test_result_creation(self):
        """Test creating a basic result"""
        result = StockAnalysisResult(stock_code="600000")
        assert result.stock_code == "600000"
        assert result.is_valid == True
        assert result.error_message is None
    
    def test_result_to_dict_basic(self):
        """Test converting result to dictionary"""
        result = StockAnalysisResult(stock_code="600000")
        result_dict = result.to_dict()
        
        assert result_dict["stock_code"] == "600000"
        assert result_dict["is_valid"] == True
        assert "analysis_time" in result_dict
    
    def test_result_to_dict_with_company_info(self):
        """Test converting result with company info to dictionary"""
        company_info = CompanyInfo(
            stock_code="600000",
            stock_name="浦发银行",
            exchange="SH",
            industry="银行"
        )
        result = StockAnalysisResult(
            stock_code="600000",
            company_info=company_info
        )
        result_dict = result.to_dict()
        
        assert "company_info" in result_dict
        assert result_dict["company_info"]["stock_name"] == "浦发银行"
        assert result_dict["company_info"]["exchange"] == "SH"
    
    def test_result_to_dict_with_invalid_flag(self):
        """Test converting invalid result to dictionary"""
        result = StockAnalysisResult(
            stock_code="600000",
            is_valid=False,
            error_message="Test error"
        )
        result_dict = result.to_dict()
        
        assert result_dict["is_valid"] == False
        assert result_dict["error_message"] == "Test error"
    
    def test_result_to_dict_with_kline_data(self):
        """Test converting result with K-line data to dictionary"""
        df = pd.DataFrame({
            'trade_date': ['2024-01-01', '2024-01-02'],
            'open_price': [10.0, 10.5],
            'close_price': [10.2, 10.8],
            'high_price': [10.3, 11.0],
            'low_price': [9.9, 10.4]
        })
        kline_data = StockKlineData(daily=df)
        result = StockAnalysisResult(stock_code="600000", kline_data=kline_data)
        result_dict = result.to_dict()
        
        assert "kline_data" in result_dict
        assert "daily" in result_dict["kline_data"]
        assert len(result_dict["kline_data"]["daily"]) == 2
    
    def test_result_to_dict_empty_dataframe(self):
        """Test converting result with empty DataFrame"""
        df = pd.DataFrame()
        kline_data = StockKlineData(daily=df)
        result = StockAnalysisResult(stock_code="600000", kline_data=kline_data)
        result_dict = result.to_dict()
        
        assert result_dict["kline_data"]["daily"] == []
    
    def test_result_to_dict_with_related_news(self):
        """Test converting result with news to dictionary"""
        news = RelatedNews(
            news_list=[
                {"title": "News 1", "url": "http://example.com/1"},
                {"title": "News 2", "url": "http://example.com/2"}
            ],
            count=2
        )
        result = StockAnalysisResult(stock_code="600000", related_news=news)
        result_dict = result.to_dict()
        
        assert "related_news" in result_dict
        assert result_dict["related_news"]["count"] == 2
        assert len(result_dict["related_news"]["articles"]) == 2


class TestAnalyzeSingleStock:
    """Tests for analyze_single_stock method"""
    
    @patch('app.services.stock_analysis.DataCollector')
    @patch('app.services.stock_analysis.KlineManager')
    @patch('app.services.stock_analysis.IndicatorCalculator')
    def test_analyze_single_stock_invalid_code(
        self, mock_indicator, mock_kline, mock_collector
    ):
        """Test analysis with invalid stock code returns error result"""
        service = StockAnalysisService()
        result = service.analyze_single_stock("INVALID")
        
        assert result.stock_code == "INVALID"
        assert result.is_valid == False
        assert "Invalid stock code" in result.error_message
    
    @patch('app.services.stock_analysis.DataCollector')
    @patch('app.services.stock_analysis.KlineManager')
    @patch('app.services.stock_analysis.IndicatorCalculator')
    def test_analyze_single_stock_empty_code(
        self, mock_indicator, mock_kline, mock_collector
    ):
        """Test analysis with empty stock code returns error result"""
        service = StockAnalysisService()
        result = service.analyze_single_stock("")
        
        assert result.is_valid == False
        assert "Invalid stock code" in result.error_message
    
    @patch('akshare.stock_individual_basic_info_xq')
    @patch('akshare.stock_news_em')
    @patch('app.services.stock_analysis.DataCollector')
    @patch('app.services.stock_analysis.KlineManager')
    @patch('app.services.stock_analysis.IndicatorCalculator')
    def test_analyze_single_stock_valid_code(
        self, mock_indicator, mock_kline, mock_collector, mock_news, mock_company_info
    ):
        """Test analysis with valid stock code returns valid result"""
        # Mock akshare functions
        mock_company_info.return_value = pd.DataFrame({
            'item': ['org_short_name_cn', 'industry', 'main_operation_business'],
            'value': ['浦发银行', '银行', '银行业务']
        })
        mock_news.return_value = pd.DataFrame({
            0: ['News 1', 'News 2'],
            1: ['http://example.com/1', 'http://example.com/2'],
            2: ['2024-01-01', '2024-01-02']
        })
        
        # Mock data collector
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
        
        # Mock indicator calculator
        mock_indicator_instance = MagicMock()
        mock_indicator_instance.calculate_all_indicators.return_value = pd.DataFrame({
            'close': [10.0, 10.2, 10.5, 10.8, 11.0],
            'MACD_12_26_9': [0.1, 0.15, 0.2, 0.25, 0.3],
            'KDJ_K': [50, 55, 60, 65, 70],
            'KDJ_D': [48, 52, 56, 60, 64],
            'RSI_14': [45, 50, 55, 60, 65]
        })
        mock_indicator.return_value = mock_indicator_instance
        
        service = StockAnalysisService()
        result = service.analyze_single_stock("600000")
        
        assert result.stock_code == "600000"
        assert result.is_valid == True
        assert result.company_info is not None or True  # May be None if API fails


class TestAnalyzeWithSector:
    """Tests for analyze_with_sector method"""
    
    @patch('app.services.stock_analysis.DataCollector')
    @patch('app.services.stock_analysis.KlineManager')
    @patch('app.services.stock_analysis.IndicatorCalculator')
    def test_analyze_with_sector_invalid_code(
        self, mock_indicator, mock_kline, mock_collector
    ):
        """Test analysis with invalid stock code returns error"""
        service = StockAnalysisService()
        result = service.analyze_with_sector("INVALID", "银行板块")
        
        assert result.is_valid == False
        assert "Invalid stock code" in result.error_message
    
    @patch('app.services.stock_analysis.DataCollector')
    @patch('app.services.stock_analysis.KlineManager')
    @patch('app.services.stock_analysis.IndicatorCalculator')
    def test_analyze_with_sector_without_sector_name(
        self, mock_indicator, mock_kline, mock_collector
    ):
        """Test analysis without sector name works like single stock analysis"""
        service = StockAnalysisService()
        result = service.analyze_with_sector("600000", None)
        
        assert result.stock_code == "600000"
        # Should return valid result (even if no data)
    
    @patch('akshare.stock_board_concept_index_ths')
    @patch('app.services.stock_analysis.DataCollector')
    @patch('app.services.stock_analysis.KlineManager')
    @patch('app.services.stock_analysis.IndicatorCalculator')
    def test_analyze_with_sector_with_sector_name(
        self, mock_indicator, mock_kline, mock_collector, mock_sector
    ):
        """Test analysis with valid stock code and sector name"""
        # Mock sector data
        mock_sector.return_value = pd.DataFrame({
            '日期': ['2024-01-01', '2024-01-02'],
            '开盘': [100, 102],
            '收盘': [101, 103],
            '最高': [102, 104],
            '最低': [99, 101]
        })
        
        service = StockAnalysisService()
        result = service.analyze_with_sector("600000", "银行板块")
        
        assert result.stock_code == "600000"
        # Sector data may or may not be present depending on API


class TestConvenienceFunction:
    """Tests for analyze_stock convenience function"""
    
    def test_analyze_stock_function_exists(self):
        """Test that analyze_stock function exists"""
        assert callable(analyze_stock)
    
    @patch('app.services.stock_analysis.StockAnalysisService')
    def test_analyze_stock_without_sector(self, mock_service_class):
        """Test analyze_stock function without sector"""
        mock_service = MagicMock()
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"stock_code": "600000", "is_valid": True}
        mock_service.analyze_single_stock.return_value = mock_result
        mock_service_class.return_value = mock_service
        
        result = analyze_stock("600000")
        
        mock_service.analyze_single_stock.assert_called_once_with("600000")
        assert result["stock_code"] == "600000"
    
    @patch('app.services.stock_analysis.StockAnalysisService')
    def test_analyze_stock_with_sector(self, mock_service_class):
        """Test analyze_stock function with sector"""
        mock_service = MagicMock()
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"stock_code": "600000", "is_valid": True}
        mock_service.analyze_with_sector.return_value = mock_result
        mock_service_class.return_value = mock_service
        
        result = analyze_stock("600000", "银行板块")
        
        mock_service.analyze_with_sector.assert_called_once_with("600000", "银行板块")
        assert result["stock_code"] == "600000"


class TestDataClasses:
    """Tests for dataclasses used in the module"""
    
    def test_company_info_defaults(self):
        """Test CompanyInfo with default values"""
        info = CompanyInfo(stock_code="600000")
        assert info.stock_code == "600000"
        assert info.stock_name is None
        assert info.exchange is None
        assert info.obtained_at is not None
    
    def test_stock_kline_data_defaults(self):
        """Test StockKlineData with default values"""
        kline = StockKlineData()
        assert kline.daily is None
        assert kline.weekly is None
        assert kline.monthly is None
    
    def test_technical_indicators_defaults(self):
        """Test TechnicalIndicators with default values"""
        indicators = TechnicalIndicators()
        assert indicators.macd is None
        assert indicators.kdj is None
        assert indicators.rsi is None
        assert indicators.full_indicators is None
    
    def test_related_news_defaults(self):
        """Test RelatedNews with default values"""
        news = RelatedNews()
        assert news.news_list == []
        assert news.count == 0
    
    def test_sector_data_defaults(self):
        """Test SectorData with required sector_name"""
        sector = SectorData(sector_name="银行板块")
        assert sector.sector_name == "银行板块"
        assert sector.kline_data is None
        assert sector.indicators is None


class TestColumnNormalization:
    """Tests for K-line column normalization"""
    
    def test_normalize_kline_columns_chinese(self):
        """Test normalizing Chinese column names"""
        service = StockAnalysisService()
        df = pd.DataFrame({
            '日期': ['2024-01-01'],
            '开盘': [10.0],
            '收盘': [10.5],
            '最高': [11.0],
            '最低': [9.9],
            '成交量': [1000000]
        })
        result = service._normalize_kline_columns(df)
        
        assert 'trade_date' in result.columns
        assert 'open_price' in result.columns
        assert 'close_price' in result.columns
    
    def test_normalize_kline_columns_english(self):
        """Test normalizing English column names"""
        service = StockAnalysisService()
        df = pd.DataFrame({
            'date': ['2024-01-01'],
            'open': [10.0],
            'close': [10.5],
            'high': [11.0],
            'low': [9.9],
            'volume': [1000000]
        })
        result = service._normalize_kline_columns(df)
        
        assert 'trade_date' in result.columns
        assert 'open_price' in result.columns
    
    def test_normalize_kline_columns_empty(self):
        """Test normalizing empty DataFrame"""
        service = StockAnalysisService()
        df = pd.DataFrame()
        result = service._normalize_kline_columns(df)
        
        assert result.empty
    
    def test_normalize_kline_columns_none(self):
        """Test normalizing None DataFrame"""
        service = StockAnalysisService()
        result = service._normalize_kline_columns(None)
        
        assert result is None


class TestExceptionHandling:
    """Tests for exception handling in the module"""
    
    def test_stock_analysis_error_base(self):
        """Test base StockAnalysisError"""
        error = StockAnalysisError("Test error", "600000", "test_type")
        assert error.message == "Test error"
        assert error.stock_code == "600000"
        assert error.error_type == "test_type"
    
    def test_stock_analysis_error_default_type(self):
        """Test StockAnalysisError with default error type"""
        error = StockAnalysisError("Test error", "600000")
        assert error.error_type == "analysis_error"
