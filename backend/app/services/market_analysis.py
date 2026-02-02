"""
Market Analysis Business Logic Module

This module provides comprehensive market analysis functionality including:
- Market overview with index data, fund flow, market activity, and limit-up stocks
- Market sentiment analysis
- Data integration and validation
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


class MarketAnalysisError(Exception):
    """Base exception for market analysis errors"""
    def __init__(self, message: str, error_type: str = "market_analysis_error"):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)


class DataNotFoundError(MarketAnalysisError):
    """Exception raised when market data is not found"""
    def __init__(self, data_type: str):
        super().__init__(
            message=f"{data_type} data not found",
            error_type="data_not_found"
        )


class DataCollectionError(MarketAnalysisError):
    """Exception raised when data collection fails"""
    def __init__(self, data_type: str, original_error: Exception):
        super().__init__(
            message=f"Failed to collect {data_type}: {str(original_error)}",
            error_type="data_collection_error"
        )


@dataclass
class IndexData:
    """Index K-line data container"""
    kline_data: Optional[pd.DataFrame] = None
    indicators: Optional[pd.DataFrame] = None


@dataclass
class FundFlowData:
    """Market fund flow data container"""
    raw_data: Optional[pd.DataFrame] = None
    processed_data: Optional[Dict[str, Any]] = None


@dataclass
class MarketActivityData:
    """Market activity data container"""
    raw_data: Optional[pd.DataFrame] = None
    processed_data: Optional[Dict[str, Any]] = None


@dataclass
class LimitUpPoolData:
    """Limit-up stock pool container"""
    raw_data: Optional[pd.DataFrame] = None
    processed_data: Optional[Dict[str, Any]] = None


@dataclass
class MarketSentimentResult:
    """Market sentiment analysis result"""
    sentiment_score: Optional[float] = None
    sentiment_level: Optional[str] = None  # "cold", "warm", "hot"
    bull_bear_ratio: Optional[float] = None
    rise_fall_count: Optional[Dict[str, int]] = None
    volume_ratio: Optional[float] = None
    analysis_time: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "sentiment_score": self.sentiment_score,
            "sentiment_level": self.sentiment_level,
            "bull_bear_ratio": self.bull_bear_ratio,
            "rise_fall_count": self.rise_fall_count,
            "volume_ratio": self.volume_ratio,
            "analysis_time": self.analysis_time.isoformat()
        }


@dataclass
class MarketOverviewResult:
    """
    Complete market overview result container
    
    Attributes:
        index_code: Index code (default: 000001 for Shanghai)
        index_data: Index K-line data and indicators
        fund_flow_data: Market fund flow data
        market_activity: Market activity data
        limit_up_pool: Limit-up stock pool data
        sentiment: Market sentiment analysis result
        analysis_time: Time of analysis
        is_valid: Whether the analysis was successful
        error_message: Error message if analysis failed
    """
    index_code: str = "000001"
    index_data: Optional[IndexData] = None
    fund_flow_data: Optional[FundFlowData] = None
    market_activity: Optional[MarketActivityData] = None
    limit_up_pool: Optional[LimitUpPoolData] = None
    sentiment: Optional[MarketSentimentResult] = None
    analysis_time: datetime = field(default_factory=datetime.utcnow)
    is_valid: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        result = {
            "index_code": self.index_code,
            "analysis_time": self.analysis_time.isoformat(),
            "is_valid": self.is_valid,
        }
        
        if self.index_data and self.index_data.kline_data is not None:
            result["index_kline"] = self._df_to_records(self.index_data.kline_data)
        
        if self.fund_flow_data and self.fund_flow_data.processed_data is not None:
            result["fund_flow"] = self.fund_flow_data.processed_data
        
        if self.market_activity and self.market_activity.processed_data is not None:
            result["market_activity"] = self.market_activity.processed_data
        
        if self.limit_up_pool and self.limit_up_pool.processed_data is not None:
            result["limit_up_pool"] = self.limit_up_pool.processed_data
        
        if self.sentiment:
            result["sentiment"] = self.sentiment.to_dict()
        
        if not self.is_valid and self.error_message:
            result["error_message"] = self.error_message
            
        return result
    
    def _df_to_records(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Convert DataFrame to records list"""
        if df is None or df.empty:
            return []
        return df.astype(object).where(pd.notnull(df), None).to_dict(orient="records")


class MarketAnalysisService:
    """
    Market Analysis Service
    
    Provides comprehensive market analysis capabilities including:
    - Index data fetching and analysis
    - Fund flow data analysis
    - Market activity metrics
    - Limit-up stock pool analysis
    - Market sentiment calculation
    """
    
    def __init__(self):
        """Initialize the market analysis service"""
        self.data_collector = DataCollector()
        self.kline_manager = KlineManager()
        self.indicator_calculator = IndicatorCalculator()
        self.index_code = "000001"  # Shanghai Composite Index
        
        logger.info("MarketAnalysisService initialized")
    
    def get_market_overview(self) -> MarketOverviewResult:
        """
        Get comprehensive market overview data
        
        This method retrieves and integrates:
        1. Shanghai Composite Index K-line data and technical indicators
        2. Market fund flow data
        3. Market activity data
        4. Limit-up stock pool data
        5. Market sentiment analysis
        
        Returns:
            MarketOverviewResult containing all market data
        """
        logger.info("Starting market overview analysis")
        
        result = MarketOverviewResult(index_code=self.index_code)
        
        try:
            # Step 1: Get index K-line data
            logger.info("Fetching index K-line data for %s", self.index_code)
            try:
                index_data = self._fetch_index_data()
                result.index_data = index_data
            except Exception as e:
                logger.warning("Failed to fetch index data: %s", e)
                result.index_data = None
            
            # Step 2: Get fund flow data
            logger.info("Fetching market fund flow data")
            try:
                fund_flow_data = self._fetch_fund_flow_data()
                result.fund_flow_data = fund_flow_data
            except Exception as e:
                logger.warning("Failed to fetch fund flow data: %s", e)
                result.fund_flow_data = None
            
            # Step 3: Get market activity data
            logger.info("Fetching market activity data")
            try:
                activity_data = self._fetch_market_activity()
                result.market_activity = activity_data
            except Exception as e:
                logger.warning("Failed to fetch market activity data: %s", e)
                result.market_activity = None
            
            # Step 4: Get limit-up stock pool
            logger.info("Fetching limit-up stock pool")
            try:
                limit_up_data = self._fetch_limit_up_pool()
                result.limit_up_pool = limit_up_data
            except Exception as e:
                logger.warning("Failed to fetch limit-up pool data: %s", e)
                result.limit_up_pool = None
            
            # Step 5: Analyze market sentiment
            logger.info("Analyzing market sentiment")
            try:
                sentiment = self.analyze_market_sentiment()
                result.sentiment = sentiment
            except Exception as e:
                logger.warning("Failed to analyze market sentiment: %s", e)
                result.sentiment = None
            
            logger.info("Completed market overview analysis")
            return result
            
        except Exception as e:
            logger.error("Error during market overview analysis: %s", e)
            result.is_valid = False
            result.error_message = str(e)
            return result
    
    def analyze_market_sentiment(self) -> MarketSentimentResult:
        """
        Analyze market sentiment based on available data
        
        Calculates:
        - Sentiment score (0-100)
        - Sentiment level (cold/warm/hot)
        - Bull-bear ratio
        - Rise-fall count
        - Volume ratio
        
        Returns:
            MarketSentimentResult with analysis
        """
        logger.info("Analyzing market sentiment")
        
        sentiment = MarketSentimentResult()
        
        try:
            # Get market activity data for calculation
            activity_data = self._fetch_market_activity()
            
            if activity_data and activity_data.processed_data:
                activity = activity_data.processed_data
                
                rise_count = activity.get("rise_count", 0)
                fall_count = activity.get("fall_count", 0)
                flat_count = activity.get("flat_count", 0)
                
                total = rise_count + fall_count + flat_count
                
                if total > 0:
                    # Calculate sentiment score (percentage of rising stocks)
                    sentiment.sentiment_score = round((rise_count / total) * 100, 2)
                    
                    # Calculate bull-bear ratio
                    sentiment.bull_bear_ratio = round(rise_count / (fall_count + 1), 2)
                    
                    # Set sentiment level
                    if sentiment.sentiment_score >= 70:
                        sentiment.sentiment_level = "hot"
                    elif sentiment.sentiment_score >= 40:
                        sentiment.sentiment_level = "warm"
                    else:
                        sentiment.sentiment_level = "cold"
                    
                    # Rise-fall count
                    sentiment.rise_fall_count = {
                        "rise": rise_count,
                        "fall": fall_count,
                        "flat": flat_count
                    }
                    
                    # Volume ratio (if available)
                    sentiment.volume_ratio = activity.get("volume_ratio")
            
            # Get fund flow data for additional sentiment
            fund_flow = self._fetch_fund_flow_data()
            if fund_flow and fund_flow.processed_data:
                # If main net inflow is positive, slightly increase sentiment
                main_net_inflow = fund_flow.processed_data.get("main_net_inflow", 0)
                if main_net_inflow > 0 and sentiment.sentiment_score:
                    sentiment.sentiment_score = min(100, sentiment.sentiment_score + 5)
            
            logger.info("Market sentiment analysis completed: score=%s, level=%s",
                       sentiment.sentiment_score, sentiment.sentiment_level)
            
            return sentiment
            
        except Exception as e:
            logger.error("Error analyzing market sentiment: %s", e)
            # Return default sentiment on error
            sentiment.sentiment_score = 50.0
            sentiment.sentiment_level = "warm"
            return sentiment
    
    def _fetch_index_data(self) -> Optional[IndexData]:
        """
        Fetch Shanghai Composite Index K-line data
        
        Returns:
            IndexData with K-line data and calculated indicators
        """
        index_data = IndexData()
        
        try:
            # Get daily K-line data for the index
            df = self.data_collector.fetch_kline_data(self.index_code, period="daily")
            
            if df is not None and not df.empty:
                # Normalize column names
                df = self._normalize_kline_columns(df)
                index_data.kline_data = df
                
                # Calculate technical indicators
                try:
                    indicators = self.indicator_calculator.calculate_all_indicators(df)
                    index_data.indicators = indicators
                except Exception as e:
                    logger.warning("Failed to calculate index indicators: %s", e)
            
            return index_data
            
        except Exception as e:
            logger.error("Error fetching index data: %s", e)
            return None
    
    def _fetch_fund_flow_data(self) -> Optional[FundFlowData]:
        """
        Fetch market fund flow data
        
        Returns:
            FundFlowData with processed fund flow information
        """
        fund_flow = FundFlowData()
        
        try:
            df = self.data_collector.fetch_market_fund_flow()
            
            if df is not None and not df.empty:
                fund_flow.raw_data = df
                
                # Process the first row (most recent data)
                latest = df.iloc[0] if len(df) > 0 else None
                
                if latest is not None:
                    # Extract key metrics
                    processed = {
                        "trade_date": str(latest.get('日期', '')) if '日期' in latest else '',
                        "sh_close_price": float(latest.get('上证-收盘价', 0)) if '上证-收盘价' in latest else 0,
                        "sh_change_pct": float(latest.get('上证-涨跌幅', 0)) if '上证-涨跌幅' in latest else 0,
                        "sz_close_price": float(latest.get('深证-收盘价', 0)) if '深证-收盘价' in latest else 0,
                        "sz_change_pct": float(latest.get('深证-涨跌幅', 0)) if '深证-涨跌幅' in latest else 0,
                        "main_net_inflow": float(latest.get('主力净流入-净额', 0)) if '主力净流入-净额' in latest else 0,
                        "main_net_inflow_ratio": float(latest.get('主力净流入-净占比', 0)) if '主力净流入-净占比' in latest else 0,
                        "super_large_net_inflow": float(latest.get('超大单净流入-净额', 0)) if '超大单净流入-净额' in latest else 0,
                        "large_net_inflow": float(latest.get('大单净流入-净额', 0)) if '大单净流入-净额' in latest else 0,
                        "medium_net_inflow": float(latest.get('中单净流入-净额', 0)) if '中单净流入-净额' in latest else 0,
                        "small_net_inflow": float(latest.get('小单净流入-净额', 0)) if '小单净流入-净额' in latest else 0,
                    }
                    fund_flow.processed_data = processed
            
            return fund_flow
            
        except Exception as e:
            logger.error("Error fetching fund flow data: %s", e)
            return None
    
    def _fetch_market_activity(self) -> Optional[MarketActivityData]:
        """
        Fetch market activity data
        
        Returns:
            MarketActivityData with processed activity metrics
        """
        activity = MarketActivityData()
        
        try:
            # Try to get market activity from akshare
            try:
                df = ak.stock_market_activity_legu()
                if df is not None and not df.empty:
                    activity.raw_data = df
                    
                    # Convert to dictionary format
                    if 'item' in df.columns and 'value' in df.columns:
                        value_dict = df.set_index('item')['value'].to_dict()
                        
                        processed = {
                            "trade_date": value_dict.get('统计日期', ''),
                            "rise_count": int(value_dict.get('上涨', 0)),
                            "fall_count": int(value_dict.get('下跌', 0)),
                            "flat_count": int(value_dict.get('平盘', 0)),
                            "limit_up_count": int(value_dict.get('涨停', 0)),
                            "real_limit_up_count": int(value_dict.get('真实涨停', 0)),
                            "limit_down_count": int(value_dict.get('跌停', 0)),
                            "real_limit_down_count": int(value_dict.get('真实跌停', 0)),
                            "activity_level": value_dict.get('活跃度', ''),
                        }
                        activity.processed_data = processed
            except Exception as e:
                logger.debug(f"akshare market activity failed: {e}")
                # Fallback: estimate from fund flow
                fund_flow = self._fetch_fund_flow_data()
                if fund_flow and fund_flow.processed_data:
                    # Estimate activity based on market performance
                    sh_change = fund_flow.processed_data.get("sh_change_pct", 0)
                    processed = {
                        "trade_date": datetime.now().strftime('%Y-%m-%d'),
                        "activity_level": "normal",
                        "estimated_trend": "up" if sh_change > 0 else "down",
                    }
                    activity.processed_data = processed
            
            return activity
            
        except Exception as e:
            logger.error("Error fetching market activity data: %s", e)
            return None
    
    def _fetch_limit_up_pool(self) -> Optional[LimitUpPoolData]:
        """
        Fetch limit-up stock pool data
        
        Returns:
            LimitUpPoolData with processed pool information
        """
        limit_up = LimitUpPoolData()
        
        try:
            df = self.data_collector.fetch_limit_up_pool()
            
            if df is not None and not df.empty:
                limit_up.raw_data = df
                
                # Calculate statistics
                total_count = len(df)
                
                # Industry distribution
                industry_col = None
                for col in df.columns:
                    if '行业' in str(col):
                        industry_col = col
                        break
                
                industry_distribution = {}
                if industry_col:
                    industry_distribution = df[industry_col].value_counts().head(10).to_dict()
                
                # Continuous limit statistics
                continuous_col = None
                for col in df.columns:
                    if '连板' in str(col):
                        continuous_col = col
                        break
                
                continuous_stats = {}
                if continuous_col:
                    continuous_stats = df[continuous_col].value_counts().sort_index().to_dict()
                
                # Average turnover rate
                turnover_col = None
                for col in df.columns:
                    if '换手率' in str(col):
                        turnover_col = col
                        break
                
                avg_turnover = 0
                if turnover_col:
                    try:
                        avg_turnover = float(df[turnover_col].mean())
                    except:
                        pass
                
                processed = {
                    "trade_date": datetime.now().strftime('%Y-%m-%d'),
                    "total_count": total_count,
                    "industry_distribution": industry_distribution,
                    "continuous_limit_stats": continuous_stats,
                    "avg_turnover_rate": round(avg_turnover, 2),
                }
                limit_up.processed_data = processed
            
            return limit_up
            
        except Exception as e:
            logger.error("Error fetching limit-up pool data: %s", e)
            return None
    
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
        
        # Column name mapping
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
        
        return df


# Convenience function for quick market analysis
def get_market_overview() -> Dict[str, Any]:
    """
    Convenience function for quick market overview
    
    Returns:
        Dictionary containing market overview results
    """
    service = MarketAnalysisService()
    result = service.get_market_overview()
    return result.to_dict()


def analyze_sentiment() -> Dict[str, Any]:
    """
    Convenience function for market sentiment analysis
    
    Returns:
        Dictionary containing sentiment analysis results
    """
    service = MarketAnalysisService()
    result = service.analyze_market_sentiment()
    return result.to_dict()
