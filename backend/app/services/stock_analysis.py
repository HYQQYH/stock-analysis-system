"""
Stock Analysis Business Logic Module

This module provides comprehensive stock analysis functionality including:
- Single stock analysis with K-line data, technical indicators, company info, and news
- Stock analysis with sector comparison data
- Data validation and error handling
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import pandas as pd
import akshare as ak

from app.services.data_collector import DataCollector
from app.services.kline_manager import KlineManager
from app.services.indicator_calculator import IndicatorCalculator

logger = logging.getLogger(__name__)


class StockAnalysisError(Exception):
    """Base exception for stock analysis errors"""
    def __init__(self, message: str, stock_code: str = None, error_type: str = "analysis_error"):
        self.message = message
        self.stock_code = stock_code
        self.error_type = error_type
        super().__init__(self.message)


class InvalidStockCodeError(StockAnalysisError):
    """Exception raised for invalid stock code format"""
    def __init__(self, stock_code: str):
        super().__init__(
            message=f"Invalid stock code format: {stock_code}. Stock code must be 6 digits.",
            stock_code=stock_code,
            error_type="invalid_stock_code"
        )


class DataNotFoundError(StockAnalysisError):
    """Exception raised when data is not found"""
    def __init__(self, stock_code: str, data_type: str):
        super().__init__(
            message=f"{data_type} data not found for stock: {stock_code}",
            stock_code=stock_code,
            error_type="data_not_found"
        )


class DataCollectionError(StockAnalysisError):
    """Exception raised when data collection fails"""
    def __init__(self, stock_code: str, data_type: str, original_error: Exception):
        super().__init__(
            message=f"Failed to collect {data_type} data for stock {stock_code}: {str(original_error)}",
            stock_code=stock_code,
            error_type="data_collection_error"
        )


@dataclass
class CompanyInfo:
    """Company basic information"""
    stock_code: str
    stock_name: Optional[str] = None
    exchange: Optional[str] = None
    industry: Optional[str] = None
    main_business: Optional[str] = None
    company_intro: Optional[str] = None
    market_cap: Optional[float] = None
    obtained_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class StockKlineData:
    """Stock K-line data container"""
    daily: Optional[pd.DataFrame] = None
    weekly: Optional[pd.DataFrame] = None
    monthly: Optional[pd.DataFrame] = None


@dataclass
class TechnicalIndicators:
    """Technical indicators container"""
    macd: Optional[pd.DataFrame] = None
    kdj: Optional[pd.DataFrame] = None
    rsi: Optional[pd.DataFrame] = None
    full_indicators: Optional[pd.DataFrame] = None


@dataclass
class RelatedNews:
    """Related news container"""
    news_list: List[Dict[str, Any]] = field(default_factory=list)
    count: int = 0


@dataclass
class SectorData:
    """Sector K-line data container"""
    sector_name: str
    kline_data: Optional[pd.DataFrame] = None
    indicators: Optional[pd.DataFrame] = None


@dataclass
class StockAnalysisResult:
    """
    Complete stock analysis result container
    
    Attributes:
        stock_code: Stock code
        company_info: Company basic information
        kline_data: K-line data (daily, weekly, monthly)
        indicators: Technical indicators
        related_news: Related news articles
        analysis_time: Time of analysis
        is_valid: Whether the analysis was successful
        error_message: Error message if analysis failed
    """
    stock_code: str
    company_info: Optional[CompanyInfo] = None
    kline_data: Optional[StockKlineData] = None
    indicators: Optional[TechnicalIndicators] = None
    related_news: Optional[RelatedNews] = None
    sector_data: Optional[SectorData] = None
    analysis_time: datetime = field(default_factory=datetime.utcnow)
    is_valid: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        result = {
            "stock_code": self.stock_code,
            "analysis_time": self.analysis_time.isoformat(),
            "is_valid": self.is_valid,
        }
        
        if self.company_info:
            result["company_info"] = {
                "stock_code": self.company_info.stock_code,
                "stock_name": self.company_info.stock_name,
                "exchange": self.company_info.exchange,
                "industry": self.company_info.industry,
                "main_business": self.company_info.main_business,
                "company_intro": self.company_info.company_intro,
            }
        
        if self.kline_data:
            result["kline_data"] = {}
            if self.kline_data.daily is not None:
                result["kline_data"]["daily"] = self._df_to_records(self.kline_data.daily)
            if self.kline_data.weekly is not None:
                result["kline_data"]["weekly"] = self._df_to_records(self.kline_data.weekly)
            if self.kline_data.monthly is not None:
                result["kline_data"]["monthly"] = self._df_to_records(self.kline_data.monthly)
        
        if self.indicators and self.indicators.full_indicators is not None:
            result["indicators"] = self._df_to_records(self.indicators.full_indicators)
        
        if self.related_news:
            result["related_news"] = {
                "count": self.related_news.count,
                "articles": self.related_news.news_list
            }
        
        if self.sector_data:
            result["sector_data"] = {
                "sector_name": self.sector_data.sector_name,
                "kline_data": self._df_to_records(self.sector_data.kline_data) if self.sector_data.kline_data is not None else None,
            }
        
        if not self.is_valid and self.error_message:
            result["error_message"] = self.error_message
            
        return result
    
    def _df_to_records(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Convert DataFrame to records list"""
        if df is None or df.empty:
            return []
        # Convert to serializable format
        return df.astype(object).where(pd.notnull(df), None).to_dict(orient="records")


class StockAnalysisService:
    """
    Stock Analysis Service
    
    Provides comprehensive stock analysis capabilities including:
    - K-line data fetching and caching
    - Technical indicator calculation
    - Company information retrieval
    - News fetching
    - Sector data analysis
    """
    
    def __init__(self):
        """Initialize the stock analysis service"""
        self.data_collector = DataCollector()
        self.kline_manager = KlineManager()
        self.indicator_calculator = IndicatorCalculator()
        
        logger.info("StockAnalysisService initialized")
    
    def validate_stock_code(self, stock_code: str) -> bool:
        """
        Validate stock code format
        
        Args:
            stock_code: Stock code to validate
            
        Returns:
            True if valid, raises InvalidStockCodeError otherwise
        """
        if not stock_code:
            raise InvalidStockCodeError(stock_code)
        
        if len(stock_code) != 6:
            raise InvalidStockCodeError(stock_code)
        
        if not stock_code.isdigit():
            raise InvalidStockCodeError(stock_code)
        
        return True
    
    def get_exchange_from_code(self, stock_code: str) -> str:
        """
        Determine exchange from stock code
        
        Args:
            stock_code: Stock code
            
        Returns:
            Exchange code ('SH' or 'SZ')
        """
        if stock_code.startswith('6'):
            return 'SH'
        elif stock_code.startswith(('0', '3')):
            return 'SZ'
        else:
            raise InvalidStockCodeError(stock_code)
    
    def analyze_single_stock(self, stock_code: str) -> StockAnalysisResult:
        """
        Analyze a single stock - get complete data package
        
        This method retrieves and整合:
        1. K-line data (daily, weekly, monthly)
        2. Technical indicators (MACD, KDJ, RSI)
        3. Company basic information
        4. Related financial news
        
        Args:
            stock_code: Stock code (6 digits, e.g., '600000')
            
        Returns:
            StockAnalysisResult containing all analysis data
            
        Raises:
            InvalidStockCodeError: If stock code format is invalid
            DataNotFoundError: If data cannot be retrieved
        """
        logger.info(f"Starting single stock analysis for code: {stock_code}")
        
        # Validate stock code
        try:
            self.validate_stock_code(stock_code)
        except InvalidStockCodeError as e:
            logger.error(f"Invalid stock code: {stock_code}")
            return StockAnalysisResult(
                stock_code=stock_code,
                is_valid=False,
                error_message=e.message
            )
        
        result = StockAnalysisResult(stock_code=stock_code)
        
        try:
            # Step 1: Get company information
            logger.info(f"Fetching company info for {stock_code}")
            try:
                company_info = self._fetch_company_info(stock_code)
                result.company_info = company_info
            except Exception as e:
                logger.warning(f"Failed to fetch company info for {stock_code}: {e}")
                result.company_info = None
            
            # Step 2: Get K-line data (daily, weekly, monthly)
            logger.info(f"Fetching K-line data for {stock_code}")
            try:
                kline_data = self._fetch_kline_data(stock_code)
                result.kline_data = kline_data
            except Exception as e:
                logger.warning(f"Failed to fetch K-line data for {stock_code}: {e}")
                result.kline_data = None
            
            # Step 3: Calculate technical indicators
            logger.info(f"Calculating technical indicators for {stock_code}")
            try:
                if result.kline_data and result.kline_data.daily is not None:
                    indicators = self._calculate_indicators(result.kline_data.daily)
                    result.indicators = indicators
                else:
                    result.indicators = None
            except Exception as e:
                logger.warning(f"Failed to calculate indicators for {stock_code}: {e}")
                result.indicators = None
            
            # Step 4: Get related news
            logger.info(f"Fetching related news for {stock_code}")
            try:
                news = self._fetch_stock_news(stock_code)
                result.related_news = news
            except Exception as e:
                logger.warning(f"Failed to fetch news for {stock_code}: {e}")
                result.related_news = None
            
            logger.info(f"Completed single stock analysis for {stock_code}")
            return result
            
        except Exception as e:
            logger.error(f"Error during stock analysis for {stock_code}: {e}")
            result.is_valid = False
            result.error_message = str(e)
            return result
    
    def analyze_with_sector(
        self,
        stock_code: str,
        sector_name: Optional[str] = None
    ) -> StockAnalysisResult:
        """
        Analyze a stock with optional sector comparison data
        
        This method extends analyze_single_stock by adding sector data
        for relative performance analysis.
        
        Args:
            stock_code: Stock code (6 digits)
            sector_name: Optional sector name for comparison (e.g., '银行板块')
            
        Returns:
            StockAnalysisResult with sector data included
        """
        logger.info(f"Starting stock analysis with sector for code: {stock_code}, sector: {sector_name}")
        
        # First, get the complete single stock analysis
        result = self.analyze_single_stock(stock_code)
        
        # If single stock analysis failed, return early
        if not result.is_valid:
            return result
        
        # If sector name is provided, fetch sector data
        if sector_name:
            logger.info(f"Fetching sector data for: {sector_name}")
            try:
                sector_data = self._fetch_sector_data(sector_name)
                result.sector_data = sector_data
            except Exception as e:
                logger.warning(f"Failed to fetch sector data for {sector_name}: {e}")
                result.sector_data = None
        
        logger.info(f"Completed stock analysis with sector for {stock_code}")
        return result
    
    def _fetch_company_info(self, stock_code: str) -> Optional[CompanyInfo]:
        """
        Fetch company basic information
        
        Args:
            stock_code: Stock code
            
        Returns:
            CompanyInfo object or None if not available
        """
        try:
            # Use akshare to get company information
            exchange = self.get_exchange_from_code(stock_code)
            full_code = f"{exchange}{stock_code}"
            
            # Try to get company info using akshare
            try:
                df = ak.stock_individual_basic_info_xq(symbol=full_code)
                if df is not None and not df.empty:
                    # Convert DataFrame to dictionary
                    info_dict = df.set_index('item')['value'].to_dict() if 'item' in df.columns else {}
                    
                    return CompanyInfo(
                        stock_code=stock_code,
                        stock_name=info_dict.get('org_short_name_cn'),
                        exchange=exchange,
                        industry=info_dict.get('industry'),
                        main_business=info_dict.get('main_operation_business'),
                        company_intro=info_dict.get('org_short_name_cn'),
                    )
            except Exception as e:
                logger.debug(f"akshare company info failed: {e}")
            
            # Return basic info if full info not available
            return CompanyInfo(stock_code=stock_code, exchange=exchange)
            
        except Exception as e:
            logger.warning(f"Error fetching company info: {e}")
            return None
    
    def _fetch_kline_data(self, stock_code: str) -> Optional[StockKlineData]:
        """
        Fetch K-line data for all timeframes
        
        Args:
            stock_code: Stock code
            
        Returns:
            StockKlineData object with daily, weekly, monthly DataFrames
        """
        kline_data = StockKlineData()
        
        # Determine date range for data
        end_date = datetime.now().strftime('%Y%m%d')
        
        # Daily K-line (last 30 days for short-term analysis)
        start_date_daily = datetime.now().strftime('%Y%m%d')  # Use current date as start
        # Calculate a reasonable start date (30 days ago)
        from datetime import timedelta
        start_date_daily = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        try:
            df_daily = self.data_collector.fetch_kline_data(
                stock_code, period="daily", start=start_date_daily, end=end_date
            )
            if df_daily is not None and not df_daily.empty:
                # Normalize column names
                df_daily = self._normalize_kline_columns(df_daily)
                kline_data.daily = df_daily
                
                # Cache the data
                try:
                    self.kline_manager.cache_kline_data(stock_code, "day", df_daily)
                except Exception as e:
                    logger.warning(f"Failed to cache daily kline data: {e}")
                    
        except Exception as e:
            logger.warning(f"Failed to fetch daily K-line data: {e}")
        
        # Weekly K-line (last 26 weeks)
        try:
            df_weekly = self.data_collector.fetch_kline_data(
                stock_code, period="weekly"
            )
            if df_weekly is not None and not df_weekly.empty:
                df_weekly = self._normalize_kline_columns(df_weekly)
                kline_data.weekly = df_weekly
        except Exception as e:
            logger.warning(f"Failed to fetch weekly K-line data: {e}")
        
        # Monthly K-line (last 12 months)
        try:
            df_monthly = self.data_collector.fetch_kline_data(
                stock_code, period="monthly"
            )
            if df_monthly is not None and not df_monthly.empty:
                df_monthly = self._normalize_kline_columns(df_monthly)
                kline_data.monthly = df_monthly
        except Exception as e:
            logger.warning(f"Failed to fetch monthly K-line data: {e}")
        
        return kline_data
    
    def _normalize_kline_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize K-line DataFrame column names
        
        Args:
            df: Raw DataFrame from akshare
            
        Returns:
            DataFrame with standardized column names
        """
        if df is None or df.empty:
            return df
        
        df = df.copy()
        
        # Column name mapping (common names from akshare)
        column_mapping = {}
        for col in df.columns:
            col_lower = col.lower()
            if col_lower in ['日期', 'date', 'trade_date']:
                column_mapping[col] = 'trade_date'
            elif col_lower in ['开盘', 'open', 'open_price']:
                column_mapping[col] = 'open_price'
            elif col_lower in ['收盘', 'close', 'close_price']:
                column_mapping[col] = 'close_price'
            elif col_lower in ['最高', 'high', 'high_price']:
                column_mapping[col] = 'high_price'
            elif col_lower in ['最低', 'low', 'low_price']:
                column_mapping[col] = 'low_price'
            elif col_lower in ['成交量', 'volume', 'vol']:
                column_mapping[col] = 'volume'
            elif col_lower in ['成交额', 'amount', 'turnover']:
                column_mapping[col] = 'amount'
            elif col_lower in ['涨跌幅', 'pct_chg', 'percentage_change']:
                column_mapping[col] = 'percentage_change'
            elif col_lower in ['换手率', 'turnover_rate']:
                column_mapping[col] = 'turnover_rate'
        
        # Apply mapping
        if column_mapping:
            df = df.rename(columns=column_mapping)
        
        # Ensure required columns exist
        required_cols = ['trade_date', 'open_price', 'close_price', 'high_price', 'low_price']
        for col in required_cols:
            if col not in df.columns:
                df[col] = None
        
        # Add standard column names for indicator calculation compatibility
        # These are needed by indicator_calculator.py which uses 'close', 'high', 'low'
        if 'close_price' in df.columns and 'close' not in df.columns:
            df['close'] = df['close_price']
        if 'high_price' in df.columns and 'high' not in df.columns:
            df['high'] = df['high_price']
        if 'low_price' in df.columns and 'low' not in df.columns:
            df['low'] = df['low_price']
        if 'open_price' in df.columns and 'open' not in df.columns:
            df['open'] = df['open_price']
        if 'volume' in df.columns and 'vol' not in df.columns:
            df['vol'] = df['volume']
        
        return df
    
    def _calculate_indicators(self, kline_df: pd.DataFrame) -> Optional[TechnicalIndicators]:
        """
        Calculate technical indicators for K-line data
        
        Args:
            kline_df: K-line DataFrame with OHLCV data
            
        Returns:
            TechnicalIndicators object with calculated indicators
        """
        if kline_df is None or kline_df.empty:
            return None
        
        indicators = TechnicalIndicators()
        try:
            # Calculate all indicators at once
            full_indicators = self.indicator_calculator.calculate_all_indicators(kline_df)
            indicators.full_indicators = full_indicators
            
            # Also calculate individual indicators for easier access
            try:
                indicators.macd = self.indicator_calculator.calculate_macd(kline_df)
            except Exception as e:
                logger.warning(f"Failed to calculate MACD: {e}")
            
            try:
                indicators.kdj = self.indicator_calculator.calculate_kdj(kline_df)
            except Exception as e:
                logger.warning(f"Failed to calculate KDJ: {e}")

            try:
                indicators.rsi = self.indicator_calculator.calculate_rsi(kline_df)
            except Exception as e:
                logger.warning(f"Failed to calculate RSI: {e}")
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return None
    
    def _fetch_stock_news(self, stock_code: str) -> Optional[RelatedNews]:
        """
        Fetch related news for a stock
        
        Args:
            stock_code: Stock code
            
        Returns:
            RelatedNews object with news articles
        """
        news = RelatedNews()
        
        try:
            # Try to get news from Eastmoney using akshare
            try:
                df_news = ak.stock_news_em(symbol=stock_code)
                if df_news is not None and not df_news.empty:
                    # Process the news DataFrame
                    if isinstance(df_news, pd.DataFrame):
                        # Get the first 5 news items
                        news_items = []
                        for _, row in df_news.head(5).iterrows():
                            news_item = {
                                "title": str(row.iloc[0]) if len(row) > 0 else "",
                                "url": str(row.iloc[1]) if len(row) > 1 else "",
                                "publish_time": str(row.iloc[2]) if len(row) > 2 else "",
                            }
                            news_items.append(news_item)
                        
                        news.news_list = news_items
                        news.count = len(news_items)
            except Exception as e:
                logger.debug(f"akshare stock news failed: {e}")
            
            return news
            
        except Exception as e:
            logger.warning(f"Error fetching stock news: {e}")
            return None
    
    def _fetch_sector_data(self, sector_name: str) -> Optional[SectorData]:
        """
        Fetch sector K-line data for comparison
        
        Args:
            sector_name: Sector name (e.g., '银行板块', '科技概念')
            
        Returns:
            SectorData object with K-line data
        """
        sector_data = SectorData(sector_name=sector_name)
        
        try:
            # Try to get sector index data using akshare
            try:
                df_sector = ak.stock_board_concept_index_ths(
                    symbol=sector_name,
                    start_date="20260101",
                    end_date=datetime.now().strftime('%Y%m%d')
                )
                
                if df_sector is not None and not df_sector.empty:
                    # Normalize sector columns
                    df_sector = df_sector.copy()
                    sector_data.kline_data = df_sector
                    
                    # Calculate sector indicators
                    if not df_sector.empty and 'close' in df_sector.columns:
                        try:
                            sector_data.indicators = self.indicator_calculator.calculate_all_indicators(df_sector)
                        except Exception as e:
                            logger.warning(f"Failed to calculate sector indicators: {e}")
                            
            except Exception as e:
                logger.debug(f"akshare sector data failed: {e}")
            
            return sector_data
            
        except Exception as e:
            logger.warning(f"Error fetching sector data: {e}")
            return None


# Convenience function for quick analysis
def analyze_stock(stock_code: str, sector_name: str = None) -> Dict[str, Any]:
    """
    Convenience function for quick stock analysis
    
    Args:
        stock_code: Stock code (6 digits)
        sector_name: Optional sector name for comparison
        
    Returns:
        Dictionary containing analysis results
    """
    service = StockAnalysisService()
    
    if sector_name:
        result = service.analyze_with_sector(stock_code, sector_name)
    else:
        result = service.analyze_single_stock(stock_code)
    
    return result.to_dict()
