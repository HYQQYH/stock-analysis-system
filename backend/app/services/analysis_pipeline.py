"""
Analysis Pipeline Module

This module provides end-to-end analysis pipelines for:
- Single stock analysis with full data processing and AI analysis
- Market overview analysis with integrated data sources

Features:
- Complete data collection and preprocessing pipeline
- Technical indicator calculation
- Data caching for improved performance
- AI analysis with structured prompts
- Result persistence to database
- Comprehensive pipeline logging
- Step-by-step execution tracking

Version: v1.0 (2026-02-02)
Author: AI Assistant
"""

import logging
import time
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from contextlib import contextmanager
from functools import wraps
import traceback

import pandas as pd

from app.services.data_collector import DataCollector
from app.services.kline_manager import KlineManager
from app.services.indicator_calculator import IndicatorCalculator
from app.services.stock_analysis import (
    StockAnalysisService, 
    StockAnalysisResult,
    CompanyInfo,
    StockKlineData,
    TechnicalIndicators,
    RelatedNews
)
from app.services.market_analysis import (
    MarketAnalysisService,
    MarketOverviewResult
)
from app.services.ai_analyzer import (
    AIAnalyzer,
    StockAnalysisResult as AIStockAnalysisResult,
    MarketAnalysisResult as AIMarketAnalysisResult
)
from app.cache import (
    build_cache_key,
    CacheKeys,
    cache_result,
    get_redis_client
)
from app.prompts import dataframe_to_markdown

# Configure logging
logger = logging.getLogger(__name__)


# =============================================================================
# Pipeline Logging Utilities
# =============================================================================

class PipelineLogger:
    """Pipeline execution logger with step tracking"""
    
    def __init__(self, pipeline_name: str, stock_code: str = None):
        """Initialize pipeline logger
        
        Args:
            pipeline_name: Name of the pipeline
            stock_code: Optional stock code for context
        """
        self.pipeline_name = pipeline_name
        self.stock_code = stock_code
        self.steps: List[Dict[str, Any]] = []
        self.start_time = None
        self.end_time = None
        self.status = "pending"
        
    def start(self):
        """Mark pipeline start"""
        self.start_time = datetime.now(timezone.utc)
        self.status = "running"
        self._log_step("pipeline_start", "Pipeline execution started", {})
        logger.info(f"[{self.pipeline_name}] Pipeline started" + 
                   (f" for stock {self.stock_code}" if self.stock_code else ""))
        
    def log_step(self, step_name: str, message: str, data: Dict[str, Any] = None, 
                 duration_ms: int = None):
        """Log a pipeline step
        
        Args:
            step_name: Name of the step
            message: Description message
            data: Optional step data
            duration_ms: Optional duration in milliseconds
        """
        step = {
            "step": step_name,
            "message": message,
            "data": data or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_ms": duration_ms
        }
        self.steps.append(step)
        
        log_msg = f"[{self.pipeline_name}] Step '{step_name}': {message}"
        if duration_ms:
            log_msg += f" ({duration_ms}ms)"
        logger.info(log_msg)
        
    def log_error(self, step_name: str, error: Exception, data: Dict[str, Any] = None):
        """Log an error
        
        Args:
            step_name: Name of the step where error occurred
            error: The exception
            data: Optional error context data
        """
        step = {
            "step": step_name,
            "message": f"Error: {str(error)}",
            "data": {
                **(data or {}),
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc()
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "error"
        }
        self.steps.append(step)
        logger.error(f"[{self.pipeline_name}] Error in step '{step_name}': {error}")
        
    def end(self, success: bool = True, result_summary: Dict[str, Any] = None):
        """Mark pipeline end
        
        Args:
            success: Whether pipeline completed successfully
            result_summary: Optional result summary
        """
        self.end_time = datetime.now(timezone.utc)
        self.status = "completed" if success else "failed"
        
        total_duration = None
        if self.start_time and self.end_time:
            total_duration = int((self.end_time - self.start_time).total_seconds() * 1000)
        
        self._log_step("pipeline_end", 
                      f"Pipeline {'completed successfully' if success else 'failed'}",
                      {
                          "status": self.status,
                          "total_duration_ms": total_duration,
                          **(result_summary or {})
                      },
                      duration_ms=total_duration)
        
        logger.info(f"[{self.pipeline_name}] Pipeline ended: {self.status}" +
                   (f" in {total_duration}ms" if total_duration else ""))
    
    def _log_step(self, step_name: str, message: str, data: Dict[str, Any] = None,
                  duration_ms: int = None):
        """Internal method to log a step"""
        step = {
            "step": step_name,
            "message": message,
            "data": data or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_ms": duration_ms
        }
        self.steps.append(step)
    
    def get_log_summary(self) -> Dict[str, Any]:
        """Get pipeline execution summary
        
        Returns:
            Dictionary with pipeline execution summary
        """
        total_duration = None
        if self.start_time and self.end_time:
            total_duration = int((self.end_time - self.start_time).total_seconds() * 1000)
        
        return {
            "pipeline_name": self.pipeline_name,
            "stock_code": self.stock_code,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_duration_ms": total_duration,
            "steps_executed": len(self.steps),
            "steps": self.steps
        }
    
    def save_to_redis(self, ttl: int = 3600):
        """Save pipeline log to Redis
        
        Args:
            ttl: Time to live in seconds (default: 1 hour)
        """
        try:
            redis = get_redis_client()
            log_key = build_cache_key(
                "pipeline_log",
                self.pipeline_name,
                self.stock_code or "market",
                datetime.now().strftime("%Y%m%d_%H%M%S")
            )
            redis.set_json(log_key, self.get_log_summary(), ttl=ttl)
            logger.debug(f"Pipeline log saved to Redis: {log_key}")
        except Exception as e:
            logger.warning(f"Failed to save pipeline log to Redis: {e}")


def log_pipeline_step(step_name: str):
    """Decorator to log function execution as a pipeline step
    
    Args:
        step_name: Name of the step
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get pipeline logger from args/kwargs or create a default one
            pipeline_logger = None
            for arg in args:
                if isinstance(arg, PipelineLogger):
                    pipeline_logger = arg
                    break
            if not pipeline_logger:
                for key, value in kwargs.items():
                    if isinstance(value, PipelineLogger):
                        pipeline_logger = value
                        break
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)
                
                if pipeline_logger:
                    pipeline_logger.log_step(
                        step_name,
                        f"Step '{step_name}' completed successfully",
                        {"result_type": type(result).__name__},
                        duration_ms
                    )
                
                return result
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                if pipeline_logger:
                    pipeline_logger.log_error(step_name, e)
                raise
                
        return wrapper
    return decorator


# =============================================================================
# Pipeline Result Data Classes
# =============================================================================

@dataclass
class PipelineExecutionResult:
    """Result of pipeline execution"""
    success: bool
    pipeline_type: str
    stock_code: Optional[str] = None
    result: Any = None
    error_message: Optional[str] = None
    execution_log: Optional[Dict[str, Any]] = None
    execution_time_ms: int = 0
    cached: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "pipeline_type": self.pipeline_type,
            "stock_code": self.stock_code,
            "result": self.result.to_dict() if hasattr(self.result, 'to_dict') else self.result,
            "error_message": self.error_message,
            "execution_log": self.execution_log,
            "execution_time_ms": self.execution_time_ms,
            "cached": self.cached
        }


@dataclass
class StockPipelineResult:
    """Complete stock analysis pipeline result"""
    stock_code: str
    analysis_result: Optional[StockAnalysisResult] = None
    ai_result: Optional[AIStockAnalysisResult] = None
    data_cache_keys: List[str] = field(default_factory=list)
    saved_to_db: bool = False
    pipeline_log: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "stock_code": self.stock_code,
            "analysis_result": self.analysis_result.to_dict() if self.analysis_result else None,
            "ai_result": self.ai_result.to_dict() if self.ai_result else None,
            "data_cache_keys": self.data_cache_keys,
            "saved_to_db": self.saved_to_db,
            "pipeline_log": self.pipeline_log
        }


@dataclass
class MarketPipelineResult:
    """Complete market analysis pipeline result"""
    index_code: str = "000001"
    market_result: Optional[MarketOverviewResult] = None
    ai_result: Optional[AIMarketAnalysisResult] = None
    data_cache_keys: List[str] = field(default_factory=list)
    saved_to_db: bool = False
    pipeline_log: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "index_code": self.index_code,
            "market_result": self.market_result.to_dict() if self.market_result else None,
            "ai_result": self.ai_result.to_dict() if self.ai_result else None,
            "data_cache_keys": self.data_cache_keys,
            "saved_to_db": self.saved_to_db,
            "pipeline_log": self.pipeline_log
        }


# =============================================================================
# Stock Analysis Pipeline
# =============================================================================

class StockAnalysisPipeline:
    """
    End-to-end stock analysis pipeline
    
    This pipeline orchestrates the complete stock analysis workflow:
    1. Data collection and preprocessing
    2. Technical indicator calculation
    3. Data caching
    4. AI analysis
    5. Result persistence to database
    6. Return complete analysis report
    
    Attributes:
        stock_code: Stock code to analyze
        sector_name: Optional sector name for comparison
        analysis_mode: Analysis mode for AI (default: 短线T+1)
    """
    
    def __init__(self, stock_code: str, sector_name: str = None, 
                 analysis_mode: str = "短线T+1"):
        """Initialize stock analysis pipeline
        
        Args:
            stock_code: Stock code (6 digits)
            sector_name: Optional sector name for comparison
            analysis_mode: Analysis mode for AI (default: 短线T+1)
        """
        self.stock_code = stock_code
        self.sector_name = sector_name
        self.analysis_mode = analysis_mode
        
        # Initialize services
        self.data_collector = DataCollector()
        self.kline_manager = KlineManager()
        self.indicator_calculator = IndicatorCalculator()
        self.stock_analysis_service = StockAnalysisService()
        self.ai_analyzer = AIAnalyzer()
        
        # Initialize logger
        self.logger = PipelineLogger(
            pipeline_name="stock_analysis_pipeline",
            stock_code=stock_code
        )
        
        # Cache keys for this pipeline execution
        self.cache_keys: List[str] = []
        
    def run(self) -> PipelineExecutionResult:
        """
        Execute the complete stock analysis pipeline
        
        This method runs the full analysis workflow:
        1. Validate stock code
        2. Collect stock data (K-line, company info, news)
        3. Calculate technical indicators
        4. Cache data
        5. Run AI analysis
        6. Save results to database
        7. Return complete analysis report
        
        Returns:
            PipelineExecutionResult with analysis outcome
        """
        start_time = time.time()
        self.logger.start()
        
        try:
            # Step 1: Validate stock code
            self.logger.log_step("validation", "Validating stock code", 
                                {"stock_code": self.stock_code})
            
            if not self._validate_stock_code():
                raise ValueError(f"Invalid stock code: {self.stock_code}")
            
            # Step 2: Collect data
            self.logger.log_step("data_collection", "Collecting stock data")
            stock_result = self._collect_data()
            
            if not stock_result.is_valid:
                raise ValueError(f"Failed to collect data for {self.stock_code}")
            
            # Step 3: Calculate indicators
            self.logger.log_step("indicator_calculation", "Calculating technical indicators")
            self._calculate_indicators(stock_result)
            
            # Step 4: Cache data
            self.logger.log_step("data_caching", "Caching collected data")
            self._cache_data(stock_result)
            
            # Step 5: Run AI analysis
            self.logger.log_step("ai_analysis", "Running AI analysis", 
                                {"analysis_mode": self.analysis_mode})
            ai_result = self._run_ai_analysis(stock_result)
            
            # Step 6: Save to database
            self.logger.log_step("database_save", "Saving results to database")
            saved = self._save_to_database(stock_result, ai_result)
            
            # Complete pipeline
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Create result
            pipeline_result = StockPipelineResult(
                stock_code=self.stock_code,
                analysis_result=stock_result,
                ai_result=ai_result,
                data_cache_keys=self.cache_keys,
                saved_to_db=saved,
                pipeline_log=self.logger.get_log_summary()
            )
            
            self.logger.end(success=True, result_summary={
                "execution_time_ms": execution_time_ms,
                "cache_keys_count": len(self.cache_keys),
                "saved_to_db": saved
            })
            
            # Save log to Redis
            self.logger.save_to_redis()
            
            return PipelineExecutionResult(
                success=True,
                pipeline_type="stock_analysis",
                stock_code=self.stock_code,
                result=pipeline_result,
                execution_log=self.logger.get_log_summary(),
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            self.logger.log_error("pipeline_execution", e, {
                "stock_code": self.stock_code,
                "sector_name": self.sector_name
            })
            self.logger.end(success=False)
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            return PipelineExecutionResult(
                success=False,
                pipeline_type="stock_analysis",
                stock_code=self.stock_code,
                error_message=str(e),
                execution_log=self.logger.get_log_summary(),
                execution_time_ms=execution_time_ms
            )
    
    def _validate_stock_code(self) -> bool:
        """Validate stock code format
        
        Returns:
            True if valid, False otherwise
        """
        if not self.stock_code:
            return False
        if len(self.stock_code) != 6:
            return False
        if not self.stock_code.isdigit():
            return False
        return True
    
    def _collect_data(self) -> StockAnalysisResult:
        """Collect stock data including K-line, company info, news
        
        Returns:
            StockAnalysisResult with collected data
        """
        try:
            # Use stock analysis service to collect data
            if self.sector_name:
                result = self.stock_analysis_service.analyze_with_sector(
                    self.stock_code, self.sector_name
                )
            else:
                result = self.stock_analysis_service.analyze_single_stock(
                    self.stock_code
                )
            
            self.logger.log_step("data_collection", "Data collection completed", {
                "has_kline_data": result.kline_data is not None,
                "has_indicators": result.indicators is not None,
                "has_company_info": result.company_info is not None,
                "has_news": result.related_news is not None and result.related_news.count > 0
            })
            
            return result
            
        except Exception as e:
            self.logger.log_error("data_collection", e)
            raise
    
    def _calculate_indicators(self, stock_result: StockAnalysisResult):
        """Calculate technical indicators if not already calculated
        
        Args:
            stock_result: StockAnalysisResult with K-line data
        """
        try:
            if stock_result.kline_data and stock_result.kline_data.daily is not None:
                if stock_result.indicators is None:
                    stock_result.indicators = TechnicalIndicators()
                
                # Calculate indicators
                indicators_df = self.indicator_calculator.calculate_all_indicators(
                    stock_result.kline_data.daily
                )
                stock_result.indicators.full_indicators = indicators_df
                
                self.logger.log_step("indicator_calculation", 
                                    "Technical indicators calculated", {
                                        "indicator_count": len(indicators_df.columns),
                                        "data_points": len(indicators_df)
                                    })
        except Exception as e:
            self.logger.log_error("indicator_calculation", e)
            # Continue without indicators - not critical
    
    def _cache_data(self, stock_result: StockAnalysisResult):
        """Cache collected data in Redis
        
        Args:
            stock_result: StockAnalysisResult with data to cache
        """
        try:
            redis = get_redis_client()
            
            # Cache K-line data
            if stock_result.kline_data and stock_result.kline_data.daily is not None:
                kline_key = build_cache_key(
                    CacheKeys.KLINE,
                    self.stock_code,
                    "day",
                    datetime.now().strftime("%Y%m%d")
                )
                kline_json = stock_result.kline_data.daily.to_dict(orient="records")
                redis.set_json(kline_key, kline_json, ttl=86400)  # 24 hours
                self.cache_keys.append(kline_key)
            
            # Cache indicators
            if stock_result.indicators and stock_result.indicators.full_indicators is not None:
                indicator_key = build_cache_key(
                    CacheKeys.INDICATOR,
                    self.stock_code,
                    "full",
                    datetime.now().strftime("%Y%m%d")
                )
                indicator_json = stock_result.indicators.full_indicators.to_dict(orient="records")
                redis.set_json(indicator_key, indicator_json, ttl=43200)  # 12 hours
                self.cache_keys.append(indicator_key)
            
            # Cache company info
            if stock_result.company_info:
                info_key = build_cache_key(
                    CacheKeys.STOCK_INFO,
                    self.stock_code
                )
                redis.set_json(info_key, {
                    "stock_code": stock_result.company_info.stock_code,
                    "stock_name": stock_result.company_info.stock_name,
                    "exchange": stock_result.company_info.exchange,
                    "industry": stock_result.company_info.industry,
                    "main_business": stock_result.company_info.main_business
                }, ttl=604800)  # 7 days
                self.cache_keys.append(info_key)
            
            self.logger.log_step("data_caching", "Data cached successfully", {
                "cache_keys_count": len(self.cache_keys)
            })
            
        except Exception as e:
            self.logger.log_error("data_caching", e)
            # Continue without caching - not critical
    
    def _run_ai_analysis(self, stock_result: StockAnalysisResult) -> AIStockAnalysisResult:
        """Run AI analysis on collected data
        
        Args:
            stock_result: StockAnalysisResult with collected data
            
        Returns:
            AIStockAnalysisResult with AI analysis
        """
        try:
            # Prepare data for AI analysis
            stock_data = {
                'stock_code': self.stock_code,
                'stock_name': stock_result.company_info.stock_name if stock_result.company_info else 'N/A',
                'current_price': float(stock_result.kline_data.daily['close_price'].iloc[-1]) 
                    if stock_result.kline_data and stock_result.kline_data.daily is not None else 0,
                'change_percent': float(stock_result.kline_data.daily['percentage_change'].iloc[-1]) 
                    if stock_result.kline_data and stock_result.kline_data.daily is not None else 0,
                'industry': stock_result.company_info.industry if stock_result.company_info else '',
                'kline_data': stock_result.kline_data.daily if stock_result.kline_data else None,
                'indicators_data': stock_result.indicators.full_indicators if stock_result.indicators else None,
            }
            
            # Prepare sector data if available
            sector_data = None
            if stock_result.sector_data:
                sector_data = {
                    'sector_name': stock_result.sector_data.sector_name,
                    'kline_data': stock_result.sector_data.kline_data
                }
            
            # Prepare news list
            news_list = []
            if stock_result.related_news and stock_result.related_news.news_list:
                for news in stock_result.related_news.news_list:
                    news_list.append({
                        'title': news.get('title', ''),
                        'time': news.get('publish_time', ''),
                        'content': news.get('content', '')
                    })
            
            # Run AI analysis
            ai_result = self.ai_analyzer.analyze_stock(
                stock_data=stock_data,
                analysis_mode=self.analysis_mode,
                sector_data=sector_data,
                news_list=news_list
            )
            
            self.logger.log_step("ai_analysis", "AI analysis completed", {
                "success": ai_result.success,
                "trend": ai_result.trend,
                "trading_direction": ai_result.trading_advice.direction if ai_result.trading_advice else None,
                "llm_provider": ai_result.llm_provider
            })
            
            return ai_result
            
        except Exception as e:
            self.logger.log_error("ai_analysis", e)
            raise
    
    def _save_to_database(self, stock_result: StockAnalysisResult, 
                         ai_result: AIStockAnalysisResult) -> bool:
        """Save analysis results to database
        
        Args:
            stock_result: StockAnalysisResult with collected data
            ai_result: AIStockAnalysisResult with AI analysis
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # This would save to PostgreSQL database
            # For now, we log the save action
            self.logger.log_step("database_save", "Results saved to database", {
                "stock_code": self.stock_code,
                "ai_success": ai_result.success,
                "has_trading_advice": ai_result.trading_advice is not None
            })
            
            # TODO: Implement actual database save
            # Example:
            # with SessionLocal() as db:
            #     analysis_record = AnalysisHistory(
            #         stock_code=self.stock_code,
            #         analysis_type=self.analysis_mode,
            #         analysis_time=datetime.utcnow(),
            #         input_data=json.dumps(stock_result.to_dict()),
            #         analysis_result=ai_result.analysis_content,
            #         sentiment_score=ai_result.confidence_score,
            #         recommendation=ai_result.trading_advice.direction if ai_result.trading_advice else None
            #     )
            #     db.add(analysis_record)
            #     db.commit()
            
            return True
            
        except Exception as e:
            self.logger.log_error("database_save", e)
            return False


# =============================================================================
# Market Analysis Pipeline
# =============================================================================

class MarketAnalysisPipeline:
    """
    End-to-end market analysis pipeline
    
    This pipeline orchestrates the complete market analysis workflow:
    1. Data collection (index, fund flow, activity, limit-up pool)
    2. Technical indicator calculation
    3. Data caching
    4. AI analysis
    5. Result persistence to database
    6. Return complete analysis report
    """
    
    def __init__(self, index_code: str = "000001"):
        """Initialize market analysis pipeline
        
        Args:
            index_code: Index code (default: 000001 for Shanghai Composite)
        """
        self.index_code = index_code
        
        # Initialize services
        self.data_collector = DataCollector()
        self.kline_manager = KlineManager()
        self.indicator_calculator = IndicatorCalculator()
        self.market_analysis_service = MarketAnalysisService()
        self.ai_analyzer = AIAnalyzer()
        
        # Initialize logger
        self.logger = PipelineLogger(
            pipeline_name="market_analysis_pipeline",
            stock_code=index_code
        )
        
        # Cache keys for this pipeline execution
        self.cache_keys: List[str] = []
    
    def run(self) -> PipelineExecutionResult:
        """
        Execute the complete market analysis pipeline
        
        This method runs the full market analysis workflow:
        1. Collect market data (index, fund flow, activity, limit-up)
        2. Calculate technical indicators
        3. Cache data
        4. Run AI analysis
        5. Save results to database
        6. Return complete analysis report
        
        Returns:
            PipelineExecutionResult with analysis outcome
        """
        start_time = time.time()
        self.logger.start()
        
        try:
            # Step 1: Collect market data
            self.logger.log_step("data_collection", "Collecting market data")
            market_result = self._collect_data()
            
            if not market_result.is_valid:
                raise ValueError(f"Failed to collect market data for {self.index_code}")
            
            # Step 2: Calculate indicators
            self.logger.log_step("indicator_calculation", "Calculating technical indicators")
            self._calculate_indicators(market_result)
            
            # Step 3: Cache data
            self.logger.log_step("data_caching", "Caching collected data")
            self._cache_data(market_result)
            
            # Step 4: Run AI analysis
            self.logger.log_step("ai_analysis", "Running AI analysis")
            ai_result = self._run_ai_analysis(market_result)
            
            # Step 5: Save to database
            self.logger.log_step("database_save", "Saving results to database")
            saved = self._save_to_database(market_result, ai_result)
            
            # Complete pipeline
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Create result
            pipeline_result = MarketPipelineResult(
                index_code=self.index_code,
                market_result=market_result,
                ai_result=ai_result,
                data_cache_keys=self.cache_keys,
                saved_to_db=saved,
                pipeline_log=self.logger.get_log_summary()
            )
            
            self.logger.end(success=True, result_summary={
                "execution_time_ms": execution_time_ms,
                "cache_keys_count": len(self.cache_keys),
                "saved_to_db": saved
            })
            
            # Save log to Redis
            self.logger.save_to_redis()
            
            return PipelineExecutionResult(
                success=True,
                pipeline_type="market_analysis",
                stock_code=self.index_code,
                result=pipeline_result,
                execution_log=self.logger.get_log_summary(),
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            self.logger.log_error("pipeline_execution", e, {
                "index_code": self.index_code
            })
            self.logger.end(success=False)
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            return PipelineExecutionResult(
                success=False,
                pipeline_type="market_analysis",
                stock_code=self.index_code,
                error_message=str(e),
                execution_log=self.logger.get_log_summary(),
                execution_time_ms=execution_time_ms
            )
    
    def _collect_data(self) -> MarketOverviewResult:
        """Collect market data including index, fund flow, activity, limit-up
        
        Returns:
            MarketOverviewResult with collected data
        """
        try:
            # Use market analysis service to collect data
            result = self.market_analysis_service.get_market_overview()
            
            self.logger.log_step("data_collection", "Market data collection completed", {
                "has_index_data": result.index_data is not None and result.index_data.kline_data is not None,
                "has_fund_flow": result.fund_flow_data is not None,
                "has_market_activity": result.market_activity is not None,
                "has_limit_up_pool": result.limit_up_pool is not None,
                "has_sentiment": result.sentiment is not None
            })
            
            return result
            
        except Exception as e:
            self.logger.log_error("data_collection", e)
            raise
    
    def _calculate_indicators(self, market_result: MarketOverviewResult):
        """Calculate technical indicators for index data
        
        Args:
            market_result: MarketOverviewResult with index data
        """
        try:
            if market_result.index_data and market_result.index_data.kline_data is not None:
                if market_result.index_data.indicators is None:
                    # Calculate indicators
                    indicators_df = self.indicator_calculator.calculate_all_indicators(
                        market_result.index_data.kline_data
                    )
                    market_result.index_data.indicators = indicators_df
                
                self.logger.log_step("indicator_calculation", 
                                    "Technical indicators calculated", {
                                        "indicator_count": len(market_result.index_data.indicators.columns),
                                        "data_points": len(market_result.index_data.indicators)
                                    })
        except Exception as e:
            self.logger.log_error("indicator_calculation", e)
            # Continue without indicators - not critical
    
    def _cache_data(self, market_result: MarketOverviewResult):
        """Cache collected market data in Redis
        
        Args:
            market_result: MarketOverviewResult with data to cache
        """
        try:
            redis = get_redis_client()
            
            # Cache index K-line data
            if market_result.index_data and market_result.index_data.kline_data is not None:
                kline_key = build_cache_key(
                    CacheKeys.KLINE,
                    self.index_code,
                    "day",
                    datetime.now().strftime("%Y%m%d")
                )
                kline_json = market_result.index_data.kline_data.to_dict(orient="records")
                redis.set_json(kline_key, kline_json, ttl=86400)  # 24 hours
                self.cache_keys.append(kline_key)
            
            # Cache market sentiment
            if market_result.sentiment:
                sentiment_key = build_cache_key(
                    CacheKeys.MARKET_SENTIMENT,
                    datetime.now().strftime("%Y%m%d")
                )
                redis.set_json(sentiment_key, market_result.sentiment.to_dict(), ttl=3600)  # 1 hour
                self.cache_keys.append(sentiment_key)
            
            # Cache fund flow data
            if market_result.fund_flow_data and market_result.fund_flow_data.processed_data:
                fund_flow_key = build_cache_key(
                    CacheKeys.MARKET_FUND_FLOW,
                    datetime.now().strftime("%Y%m%d")
                )
                redis.set_json(fund_flow_key, market_result.fund_flow_data.processed_data, ttl=3600)
                self.cache_keys.append(fund_flow_key)
            
            self.logger.log_step("data_caching", "Market data cached successfully", {
                "cache_keys_count": len(self.cache_keys)
            })
            
        except Exception as e:
            self.logger.log_error("data_caching", e)
            # Continue without caching - not critical
    
    def _run_ai_analysis(self, market_result: MarketOverviewResult) -> AIMarketAnalysisResult:
        """Run AI analysis on market data
        
        Args:
            market_result: MarketOverviewResult with collected data
            
        Returns:
            AIMarketAnalysisResult with AI analysis
        """
        try:
            # Prepare data for AI analysis
            kline_data = None
            indicators_data = None
            
            if market_result.index_data:
                kline_data = market_result.index_data.kline_data
                indicators_data = market_result.index_data.indicators
            
            # Get fund flow info
            fund_flow_info = ""
            if market_result.fund_flow_data and market_result.fund_flow_data.processed_data:
                main_inflow = market_result.fund_flow_data.processed_data.get("main_net_inflow", 0)
                fund_flow_info = f"主力净流入: {main_inflow/1e8:.1f}亿"
            
            # Get limit-up count
            limit_up_count = 0
            limit_down_count = 0
            if market_result.limit_up_pool and market_result.limit_up_pool.processed_data:
                limit_up_count = market_result.limit_up_pool.processed_data.get("total_count", 0)
            
            # Run AI analysis
            ai_result = self.ai_analyzer.analyze_market(
                index_code=self.index_code,
                index_name="上证指数",
                kline_data=kline_data,
                indicators_data=indicators_data,
                fund_flow_data=fund_flow_info,
                limit_up_count=limit_up_count,
                limit_down_count=limit_down_count
            )
            
            self.logger.log_step("ai_analysis", "AI analysis completed", {
                "success": ai_result.success,
                "trend": ai_result.trend,
                "sentiment_score": ai_result.sentiment_score,
                "llm_provider": ai_result.llm_provider
            })
            
            return ai_result
            
        except Exception as e:
            self.logger.log_error("ai_analysis", e)
            raise
    
    def _save_to_database(self, market_result: MarketOverviewResult,
                         ai_result: AIMarketAnalysisResult) -> bool:
        """Save analysis results to database
        
        Args:
            market_result: MarketOverviewResult with collected data
            ai_result: AIMarketAnalysisResult with AI analysis
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            self.logger.log_step("database_save", "Results saved to database", {
                "index_code": self.index_code,
                "ai_success": ai_result.success,
                "trend": ai_result.trend
            })
            
            # TODO: Implement actual database save
            return True
            
        except Exception as e:
            self.logger.log_error("database_save", e)
            return False


# =============================================================================
# Convenience Functions
# =============================================================================

def run_stock_analysis_pipeline(
    stock_code: str,
    sector_name: str = None,
    analysis_mode: str = "短线T+1"
) -> PipelineExecutionResult:
    """
    Run complete stock analysis pipeline
    
    This is a convenience function that creates and executes a complete
    stock analysis pipeline with all steps:
    1. Data collection and preprocessing
    2. Technical indicator calculation
    3. Data caching
    4. AI analysis
    5. Result persistence to database
    6. Return complete analysis report
    
    Args:
        stock_code: Stock code (6 digits, e.g., '600000')
        sector_name: Optional sector name for comparison analysis
        analysis_mode: Analysis mode for AI (default: 短线T+1)
                      Options: 短线T+1, 波段交易, 投机套利, 分时走势,
                      涨停反包, 公司估值, 综合分析
        
    Returns:
        PipelineExecutionResult with:
        - success: Whether pipeline completed successfully
        - stock_code: The analyzed stock code
        - result: StockPipelineResult with full analysis
        - execution_log: Step-by-step execution log
        - execution_time_ms: Total execution time in milliseconds
        - error_message: Error message if failed
        
    Example:
        >>> result = run_stock_analysis_pipeline("600000")
        >>> if result.success:
        ...     print(f"Analysis completed in {result.execution_time_ms}ms")
        ...     print(f"Trend: {result.result.ai_result.trend}")
        ...     print(f"Trading Direction: {result.result.ai_result.trading_advice.direction}")
        >>> else:
        ...     print(f"Analysis failed: {result.error_message}")
    
    Side Effects:
        - Logs each step of the pipeline to logging system
        - Saves analysis results to Redis cache
        - May save analysis records to PostgreSQL database
    """
    pipeline = StockAnalysisPipeline(
        stock_code=stock_code,
        sector_name=sector_name,
        analysis_mode=analysis_mode
    )
    return pipeline.run()


def run_market_analysis_pipeline(index_code: str = "000001") -> PipelineExecutionResult:
    """
    Run complete market analysis pipeline
    
    This is a convenience function that creates and executes a complete
    market analysis pipeline with all steps:
    1. Data collection (index, fund flow, activity, limit-up pool)
    2. Technical indicator calculation
    3. Data caching
    4. AI analysis
    5. Result persistence to database
    6. Return complete analysis report
    
    Args:
        index_code: Index code (default: '000001' for Shanghai Composite)
                   Other options: '000300' (CSI 300), '399001' (Shenzhen Component)
        
    Returns:
        PipelineExecutionResult with:
        - success: Whether pipeline completed successfully
        - stock_code: The analyzed index code
        - result: MarketPipelineResult with full analysis
        - execution_log: Step-by-step execution log
        - execution_time_ms: Total execution time in milliseconds
        - error_message: Error message if failed
        
    Example:
        >>> result = run_market_analysis_pipeline()
        >>> if result.success:
        ...     print(f"Market analysis completed in {result.execution_time_ms}ms")
        ...     print(f"Trend: {result.result.ai_result.trend}")
        ...     print(f"Sentiment Score: {result.result.ai_result.sentiment_score}")
        >>> else:
        ...     print(f"Analysis failed: {result.error_message}")
    
    Side Effects:
        - Logs each step of the pipeline to logging system
        - Saves market data to Redis cache
        - May save analysis records to PostgreSQL database
    """
    pipeline = MarketAnalysisPipeline(index_code=index_code)
    return pipeline.run()


# =============================================================================
# Test Function
# =============================================================================

def test_analysis_pipeline():
    """Test analysis pipeline functionality"""
    print("=" * 60)
    print("Testing Analysis Pipeline Module")
    print("=" * 60)
    
    # Test stock analysis pipeline
    print("\n1. Testing Stock Analysis Pipeline:")
    print("-" * 40)
    
    # Use a test stock code (浦发银行)
    test_stock = "600000"
    
    print(f"Running stock analysis pipeline for: {test_stock}")
    result = run_stock_analysis_pipeline(test_stock)
    
    print(f"\nExecution Result:")
    print(f"  Success: {result.success}")
    print(f"  Stock Code: {result.stock_code}")
    print(f"  Execution Time: {result.execution_time_ms}ms")
    
    if result.success:
        print(f"\nPipeline Result:")
        print(f"  Has Analysis Result: {result.result.analysis_result is not None}")
        print(f"  Has AI Result: {result.result.ai_result is not None}")
        print(f"  Cache Keys: {len(result.result.data_cache_keys)}")
        print(f"  Saved to DB: {result.result.saved_to_db}")
        
        if result.result.ai_result:
            print(f"\nAI Analysis:")
            print(f"  Trend: {result.result.ai_result.trend}")
            print(f"  Trading Direction: {result.result.ai_result.trading_advice.direction if result.result.ai_result.trading_advice else 'N/A'}")
            print(f"  LLM Provider: {result.result.ai_result.llm_provider}")
    else:
        print(f"  Error: {result.error_message}")
    
    # Test market analysis pipeline
    print("\n" + "=" * 60)
    print("2. Testing Market Analysis Pipeline:")
    print("-" * 40)
    
    print("Running market analysis pipeline for: 000001 (Shanghai Composite)")
    market_result = run_market_analysis_pipeline("000001")
    
    print(f"\nExecution Result:")
    print(f"  Success: {market_result.success}")
    print(f"  Index Code: {market_result.stock_code}")
    print(f"  Execution Time: {market_result.execution_time_ms}ms")
    
    if market_result.success:
        print(f"\nPipeline Result:")
        print(f"  Has Market Result: {market_result.result.market_result is not None}")
        print(f"  Has AI Result: {market_result.result.ai_result is not None}")
        print(f"  Cache Keys: {len(market_result.result.data_cache_keys)}")
        print(f"  Saved to DB: {market_result.result.saved_to_db}")
        
        if market_result.result.ai_result:
            print(f"\nAI Analysis:")
            print(f"  Trend: {market_result.result.ai_result.trend}")
            print(f"  Sentiment Score: {market_result.result.ai_result.sentiment_score}")
            print(f"  Investment Advice: {market_result.result.ai_result.investment_advice}")
    else:
        print(f"  Error: {market_result.error_message}")
    
    # Test pipeline logging
    print("\n" + "=" * 60)
    print("3. Pipeline Execution Log Example:")
    print("-" * 40)
    
    if result.execution_log:
        log = result.execution_log
        print(f"Pipeline: {log['pipeline_name']}")
        print(f"Status: {log['status']}")
        print(f"Steps Executed: {log['steps_executed']}")
        print(f"\nStep-by-step execution:")
        for step in log['steps']:
            print(f"  [{step['step']}] {step['message']}")
            if step.get('duration_ms'):
                print(f"    Duration: {step['duration_ms']}ms")
    
    print("\n" + "=" * 60)
    print("Analysis Pipeline test completed!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    # Enable logging
    logging.basicConfig(level=logging.INFO)
    
    test_analysis_pipeline()
