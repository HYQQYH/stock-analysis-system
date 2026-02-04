"""
AI Analyzer Module for Stock Analysis System

This module provides AI-powered analysis capabilities:
- Stock analysis (single stock with optional sector data)
- Market analysis (overall market conditions)
- News insight extraction (investment recommendations from news)

Features:
- Unified LLM integration with multiple providers
- Automatic retry and timeout handling
- Response parsing and validation
- Structured output generation

Version: v1.0 (2026-02-02)
Author: AI Assistant
"""

import json
import time
import re
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from abc import ABC, abstractmethod

from app.llm_config import (
    LLMManager, 
    LLMResponse, 
    LLMTokenUsage,
    get_llm_manager,
    invoke_llm,
    create_chat_message
)
from app.prompts import (
    build_analysis_prompt,
    build_duanxian_prompt,
    build_boduan_prompt,
    build_n1n_prompt,
    build_touji_prompt,
    build_fenshi_prompt,
    build_guzhi_prompt,
    market_analysis_prompt,
    recommend_prompt,
    dapan_analysis_prompt,
    dataframe_to_markdown,
    format_trading_advice
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TradingAdvice:
    """Structured trading advice from AI analysis"""
    direction: str = ""  # 买入/卖出/持有
    target_price: float = 0.0
    quantity: int = 0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    holding_period: int = 0  # 交易日
    risk_level: str = ""  # 高/中/低
    confidence_score: float = 0.0
    reasoning: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "direction": self.direction,
            "target_price": self.target_price,
            "quantity": self.quantity,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "holding_period": self.holding_period,
            "risk_level": self.risk_level,
            "confidence_score": self.confidence_score,
            "reasoning": self.reasoning
        }


@dataclass
class StockAnalysisResult:
    """Complete stock analysis result"""
    stock_code: str
    stock_name: str
    analysis_mode: str
    analysis_type: str  # 技术面/基本面/综合
    trend: str  # 上涨/下跌/震荡
    trading_advice: TradingAdvice
    analysis_content: str = ""
    success: bool = True
    error_message: Optional[str] = None
    key_indicators: Dict[str, Any] = field(default_factory=dict)
    risk_warning: str = ""
    confidence_score: float = 0.0
    llm_provider: str = ""
    llm_model: str = ""
    token_usage: Dict[str, int] = field(default_factory=dict)
    analysis_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "analysis_mode": self.analysis_mode,
            "analysis_type": self.analysis_type,
            "trend": self.trend,
            "trading_advice": self.trading_advice.to_dict(),
            "analysis_content": self.analysis_content,
            "key_indicators": self.key_indicators,
            "risk_warning": self.risk_warning,
            "confidence_score": self.confidence_score,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "token_usage": self.token_usage,
            "analysis_time": self.analysis_time,
            "success": self.success,
            "error_message": self.error_message
        }


@dataclass
class MarketAnalysisResult:
    """Market analysis result"""
    index_code: str
    index_name: str
    trend: str
    analysis_content: str = ""
    support_levels: List[float] = field(default_factory=list)
    resistance_levels: List[float] = field(default_factory=list)
    sentiment_score: float = 0.0
    investment_advice: str = ""
    confidence_score: float = 0.0
    llm_provider: str = ""
    llm_model: str = ""
    token_usage: Dict[str, int] = field(default_factory=dict)
    analysis_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    success: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "index_code": self.index_code,
            "index_name": self.index_name,
            "trend": self.trend,
            "support_levels": self.support_levels,
            "resistance_levels": self.resistance_levels,
            "analysis_content": self.analysis_content,
            "sentiment_score": self.sentiment_score,
            "investment_advice": self.investment_advice,
            "confidence_score": self.confidence_score,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "token_usage": self.token_usage,
            "analysis_time": self.analysis_time,
            "success": self.success,
            "error_message": self.error_message
        }


@dataclass
class NewsInsightResult:
    """News insight extraction result"""
    recommended_stocks: List[Dict[str, Any]] = field(default_factory=list)
    market_sentiment: str = ""
    analysis_content: str = ""
    confidence_score: float = 0.0
    llm_provider: str = ""
    llm_model: str = ""
    token_usage: Dict[str, int] = field(default_factory=dict)
    analysis_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    success: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommended_stocks": self.recommended_stocks,
            "market_sentiment": self.market_sentiment,
            "analysis_content": self.analysis_content,
            "confidence_score": self.confidence_score,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "token_usage": self.token_usage,
            "analysis_time": self.analysis_time,
            "success": self.success,
            "error_message": self.error_message
        }


class AIAnalyzer:
    """AI-powered analyzer for stocks, market, and news"""
    
    # Supported analysis modes
    ANALYSIS_MODES = {
        "短线T+1": build_duanxian_prompt,
        "波段交易": build_boduan_prompt,
        "投机套利": build_touji_prompt,
        "分时走势": build_fenshi_prompt,
        "涨停反包": build_n1n_prompt,
        "公司估值": build_guzhi_prompt,
        "综合分析": build_analysis_prompt
    }
    
    def __init__(self, llm_manager: Optional[LLMManager] = None):
        """Initialize AI analyzer
        
        Args:
            llm_manager: Optional LLM manager instance (uses global if not provided)
        """
        self.llm = llm_manager or get_llm_manager()
        self.max_retries = 3
        self.retry_delay = 1.0
        self.request_timeout = 120  # seconds
    
    def _invoke_with_retry(self, messages: List[Dict[str, str]]) -> LLMResponse:
        """Invoke LLM with automatic retry on failure
        
        Args:
            messages: Chat messages
            
        Returns:
            LLMResponse with content or error
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                response = self.llm.invoke(messages, use_fallback=False)
                
                if response.success:
                    return response
                
                last_error = response.error_message
                logger.warning(f"LLM invoke attempt {attempt + 1} failed: {last_error}")
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"LLM invoke attempt {attempt + 1} exception: {last_error}")
            
            # Wait before retry (exponential backoff)
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (2 ** attempt))
        
        # All retries exhausted
        return LLMResponse(
            content="",
            provider="",
            model="",
            token_usage=LLMTokenUsage(),
            response_time_ms=0,
            success=False,
            error_message=f"All {self.max_retries} attempts failed: {last_error}"
        )
    
    def _parse_trading_advice(self, text: str) -> TradingAdvice:
        """Parse trading advice from LLM response text
        
        Args:
            text: LLM response text containing trading advice
            
        Returns:
            TradingAdvice object
        """
        advice = TradingAdvice()
        
        # Extract direction
        direction_match = re.search(r'交易方向[：:]\s*(\S+)', text)
        if direction_match:
            advice.direction = direction_match.group(1).strip()
        
        # Extract target price
        price_match = re.search(r'目标价格[：:]\s*([\d.]+)', text)
        if price_match:
            advice.target_price = float(price_match.group(1))
        
        # Extract quantity
        quantity_match = re.search(r'交易数量[：:]\s*(\d+)', text)
        if quantity_match:
            advice.quantity = int(quantity_match.group(1))
        
        # Extract stop loss
        stop_loss_match = re.search(r'止损价格[：:]\s*([\d.]+)', text)
        if stop_loss_match:
            advice.stop_loss = float(stop_loss_match.group(1))
        
        # Extract take profit
        take_profit_match = re.search(r'止盈目标[：:]\s*([\d.]+)', text)
        if take_profit_match:
            advice.take_profit = float(take_profit_match.group(1))
        
        # Extract holding period
        holding_match = re.search(r'持仓时间[：:]\s*(\d+)', text)
        if holding_match:
            advice.holding_period = int(holding_match.group(1))
        
        # Extract risk level
        risk_match = re.search(r'风险等级[：:]\s*(\S+)', text)
        if risk_match:
            advice.risk_level = risk_match.group(1).strip()
        
        # Extract confidence score
        confidence_match = re.search(r'置信度[：:]\s*([\d.]+)', text)
        if confidence_match:
            advice.confidence_score = float(confidence_match.group(1))
        
        # Extract reasoning
        reasoning_match = re.search(r'分析理由[：:]\s*(.+?)(?:交易建议|$)', text, re.DOTALL)
        if reasoning_match:
            advice.reasoning = reasoning_match.group(1).strip()
        
        return advice
    
    def _extract_json_from_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response (handles markdown code blocks)
        
        Args:
            text: LLM response text
            
        Returns:
            Parsed JSON dict or None
        """
        # Try to find JSON in markdown code blocks
        json_pattern = r'```(?:json)?\s*\n(.+?)\n```'
        match = re.search(json_pattern, text, re.DOTALL)
        
        if match:
            json_str = match.group(1)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON without code blocks
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try to find first { } pattern
        brace_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        match = re.search(brace_pattern, text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        
        return None
    
    def analyze_stock(
        self,
        stock_data: Dict[str, Any],
        analysis_mode: str = "短线T+1",
        sector_data: Optional[Dict[str, Any]] = None,
        news_list: Optional[List[Dict[str, Any]]] = None
    ) -> StockAnalysisResult:
        """Analyze a single stock with AI
        
        Args:
            stock_data: Stock data including kline, indicators, company info
            analysis_mode: Analysis mode (短线T+1, 波段交易, etc.)
            sector_data: Optional sector data for comparison
            news_list: Optional list of related news
            
        Returns:
            StockAnalysisResult with structured analysis
        """
        start_time = time.time()
        # import ipdb; ipdb.set_trace()
        try:
            # Extract stock info
            stock_code = stock_data.get('stock_code', 'N/A')
            stock_name = stock_data.get('stock_name', 'N/A')
            
            # Build prompt based on analysis mode
            if analysis_mode in self.ANALYSIS_MODES:
                prompt_builder = self.ANALYSIS_MODES[analysis_mode]
            else:
                prompt_builder = self.ANALYSIS_MODES["短线T+1"]  # Default
            
            # Convert data to appropriate format
            kline_df = stock_data.get('kline_data')
            
            # if kline_df is not None:
            #     kline_md = dataframe_to_markdown(kline_df)
            # else:
            #     kline_md = stock_data.get('kline_str', '无K线数据')
            
            indicators_df = stock_data.get('indicators_data')
            # if indicators_df is not None:
            #     indicators_md = dataframe_to_markdown(indicators_df)
            # else:
            #     indicators_md = stock_data.get('indicators_str', '无技术指标数据')
            
            company_info = stock_data.get('company_info', {})
            # if isinstance(company_info, dict):
            #     company_str = json.dumps(company_info, ensure_ascii=False, indent=2)
            # else:
            #     company_str = str(company_info)
            
            # Prepare news
            news_str = "暂无相关新闻"
            if news_list:
                news_items = []
                for i, news in enumerate(news_list[:5], 1):
                    news_items.append(
                        f"新闻{i}: [{news.get('time', '')}] {news.get('title', '')}"
                    )
                news_str = "\n".join(news_items)
            
            # Prepare sector data
            sector_str = "无板块数据"
            if sector_data:
                sector_name = sector_data.get('sector_name', '')
                sector_kline = sector_data.get('kline_data')
                if sector_kline is not None:
                    sector_str = f"板块名称: {sector_name}\n{dataframe_to_markdown(sector_kline)}"
            
            # Build prompt based on mode
            if analysis_mode == "短线T+1":
                # Get stock info dict
                stock_info = {
                    'code': stock_code,
                    'name': stock_name,
                    'business': stock_data.get('industry', '')
                }
                
                stock_weekly_df = stock_data.get('weekly_kline_data')
                # stock_weekly_md = dataframe_to_markdown(stock_weekly_df) if stock_weekly_df is not None else ""
                
                dapan_df = stock_data.get('market_kline_data')
                # dapan_md = dataframe_to_markdown(dapan_df) if dapan_df is not None else ""
                
                market_activity_df = stock_data.get('market_activity_data')
                # market_activity_md = dataframe_to_markdown(market_activity_df) if market_activity_df is not None else ""
                
                concept_name = sector_data.get('sector_name', '') if sector_data else ""
                concept_status = sector_data.get('kline_data') if sector_data else None
                
                prompt = build_duanxian_prompt(
                    stock_info=stock_info,
                    stock_status=kline_df,
                    stock_weekly_status=stock_weekly_df,
                    news_list=news_list or [],
                    dapan=dapan_df,
                    market_activity=market_activity_df,
                    concept_name=concept_name,
                    concept_status=concept_status
                )
            elif analysis_mode == "波段交易":
                stock_info = {
                    'code': stock_code,
                    'name': stock_name,
                    'business': stock_data.get('industry', '')
                }
                
                financial_df = stock_data.get('financial_data')
                stock_weekly_df = stock_data.get('weekly_kline_data')
                dapan_df = stock_data.get('market_kline_data')
                concept_name = sector_data.get('sector_name', '') if sector_data else ""
                concept_status = sector_data.get('kline_data') if sector_data else None
                
                prompt = build_boduan_prompt(
                    stock_info=stock_info,
                    financial_status=financial_df,
                    stock_status=kline_df,
                    stock_weekly_status=stock_weekly_df,
                    dapan=dapan_df,
                    concept_name=concept_name,
                    concept_status=concept_status
                )
            elif analysis_mode == "涨停反包":
                stock_info = {
                    'code': stock_code,
                    'name': stock_name,
                    'business': stock_data.get('industry', '')
                }
                
                stock_zt_info = stock_data.get('limit_up_info', {})
                stock_weekly_df = stock_data.get('weekly_kline_data')
                dapan_df = stock_data.get('market_kline_data')
                market_activity_df = stock_data.get('market_activity_data')
                concept_name = sector_data.get('sector_name', '') if sector_data else ""
                concept_status = sector_data.get('kline_data') if sector_data else None
                
                prompt = build_n1n_prompt(
                    stock_info=stock_info,
                    stock_zt_info=stock_zt_info,
                    stock_status=kline_df,
                    stock_weekly_status=stock_weekly_df,
                    news_list=news_list or [],
                    dapan=dapan_df,
                    market_activity=market_activity_df,
                    concept_name=concept_name,
                    concept_status=concept_status
                )
            else:
                # Default to basic analysis
                prompt = build_analysis_prompt(
                    stock_info={'code': stock_code, 'name': stock_name, 'business': ''},
                    stock_status=kline_df,
                    news_list=news_list or [],
                    financial_data=stock_data.get('financial_data')
                )
            
            logger.info("Generated Prompt:")
            logger.info(prompt)
            # Create messages
            messages = [
                create_chat_message("system", "你是一位专业的股票分析师，请提供客观、准确的分析。"),
                create_chat_message("user", prompt)
            ]
            
            # Invoke LLM with retry
            response = self._invoke_with_retry(messages)
            logger.info("LLM Response:")
            logger.info(response.content)
            
            # Parse response
            analysis_content = response.content
            trading_advice = self._parse_trading_advice(analysis_content)
            
            # Try to extract structured data
            json_data = self._extract_json_from_response(analysis_content)
            
            # Extract trend
            trend = "震荡"  # Default
            if json_data:
                trend = json_data.get('trend', trend)
                if 'trading_advice' in json_data:
                    ta = json_data['trading_advice']
                    if isinstance(ta, dict):
                        trading_advice.direction = ta.get('direction', trading_advice.direction)
                        trading_advice.target_price = ta.get('target_price', trading_advice.target_price)
                        trading_advice.stop_loss = ta.get('stop_loss', trading_advice.stop_loss)
                        trading_advice.take_profit = ta.get('take_profit', trading_advice.take_profit)
                        trading_advice.holding_period = ta.get('holding_period', trading_advice.holding_period)
                        trading_advice.risk_level = ta.get('risk_level', trading_advice.risk_level)
            
            # Determine confidence score
            confidence_score = json_data.get('confidence_score', 0.0) if json_data else 0.0
            
            return StockAnalysisResult(
                stock_code=stock_code,
                stock_name=stock_name,
                analysis_mode=analysis_mode,
                analysis_type="综合分析",
                trend=trend,
                trading_advice=trading_advice,
                analysis_content=analysis_content,
                key_indicators={
                    "price": stock_data.get('current_price', 0),
                    "change": stock_data.get('change_percent', 0),
                    "volume_ratio": stock_data.get('volume_ratio', 0),
                    "turnover_rate": stock_data.get('turnover_rate', 0)
                },
                risk_warning=json_data.get('risk_warning', '') if json_data else '',
                confidence_score=confidence_score,
                llm_provider=response.provider,
                llm_model=response.model,
                token_usage={
                    "prompt_tokens": response.token_usage.prompt_tokens,
                    "completion_tokens": response.token_usage.completion_tokens,
                    "total_tokens": response.token_usage.total_tokens
                },
                analysis_time=datetime.now(timezone.utc).isoformat(),
                success=True
            )
            
        except Exception as e:
            logger.error(f"Stock analysis failed: {e}")
            return StockAnalysisResult(
                stock_code=stock_data.get('stock_code', 'N/A'),
                stock_name=stock_data.get('stock_name', 'N/A'),
                analysis_mode=analysis_mode,
                analysis_type="综合分析",
                trend="震荡",
                trading_advice=TradingAdvice(),
                analysis_content="",
                confidence_score=0.0,
                llm_provider="",
                llm_model="",
                success=False,
                error_message=str(e)
            )
    
    def analyze_market(
        self,
        index_code: str = "000001",
        index_name: str = "上证指数",
        kline_data: Any = None,
        indicators_data: Any = None,
        fund_flow_data: str = "",
        limit_up_count: int = 0,
        limit_down_count: int = 0,
        days: int = 30
    ) -> MarketAnalysisResult:
        """Analyze overall market conditions
        
        Args:
            index_code: Index code
            index_name: Index name
            kline_data: Index kline data (DataFrame or string)
            indicators_data: Technical indicators data
            fund_flow_data: Fund flow information string
            limit_up_count: Number of limit-up stocks
            limit_down_count: Number of limit-down stocks
            days: Number of days for analysis
            
        Returns:
            MarketAnalysisResult with structured analysis
        """
        try:
            # Convert kline data
            if kline_data is not None:
                kline_md = dataframe_to_markdown(kline_data)
            else:
                kline_md = "无K线数据"
            
            # Convert indicators data
            if indicators_data is not None:
                indicators_md = dataframe_to_markdown(indicators_data)
            else:
                indicators_md = "无技术指标数据"
            
            # Build prompt
            prompt = dapan_analysis_prompt(
                daily_data=kline_data,
                weekly_data=None,
                monthly_data=None
            )
            
            # Create messages
            messages = [
                create_chat_message("system", "你是一位专业的股票分析师，专注于大盘走势分析。"),
                create_chat_message("user", prompt)
            ]
            
            # Invoke LLM with retry
            response = self._invoke_with_retry(messages)
            
            # Parse response
            analysis_content = response.content
            logger.info("Market Analysis LLM Response:")
            logger.info(analysis_content)
            
            # Try to extract structured data
            json_data = self._extract_json_from_response(analysis_content)
            
            # Extract key information
            trend = json_data.get('trend', '震荡') if json_data else '震荡'
            support_levels = json_data.get('support_levels', []) if json_data else []
            resistance_levels = json_data.get('resistance_levels', []) if json_data else []
            sentiment_score = json_data.get('sentiment_score', 50.0) if json_data else 50.0
            investment_advice = json_data.get('investment_advice', '') if json_data else ''
            confidence_score = json_data.get('confidence_score', 0.0) if json_data else 0.0
            
            return MarketAnalysisResult(
                index_code=index_code,
                index_name=index_name,
                trend=trend,
                support_levels=support_levels,
                resistance_levels=resistance_levels,
                analysis_content=analysis_content,
                sentiment_score=sentiment_score,
                investment_advice=investment_advice,
                confidence_score=confidence_score,
                llm_provider=response.provider,
                llm_model=response.model,
                token_usage={
                    "prompt_tokens": response.token_usage.prompt_tokens,
                    "completion_tokens": response.token_usage.completion_tokens,
                    "total_tokens": response.token_usage.total_tokens
                },
                analysis_time=datetime.now(timezone.utc).isoformat(),
                success=True
            )
            
        except Exception as e:
            logger.error(f"Market analysis failed: {e}")
            return MarketAnalysisResult(
                index_code=index_code,
                index_name=index_name,
                trend="震荡",
                analysis_content="",
                success=False,
                error_message=str(e)
            )
    
    def extract_news_insights(self, news_list: List[Dict[str, Any]]) -> NewsInsightResult:
        """Extract investment insights from news list
        
        Args:
            news_list: List of news articles with title, time, content
            
        Returns:
            NewsInsightResult with recommended stocks and analysis
        """
        try:
            # Build prompt
            prompt = market_analysis_prompt(news_list, topk=10)
            
            # Create messages
            messages = [
                create_chat_message("system", "你是一位专业的投资分析师，擅长从新闻中挖掘投资机会。"),
                create_chat_message("user", prompt)
            ]
            
            # Invoke LLM with retry
            response = self._invoke_with_retry(messages)
            
            # Parse response
            analysis_content = response.content
            
            # Try to extract structured data
            json_data = self._extract_json_from_response(analysis_content)
            
            # Extract recommended stocks
            recommended_stocks = []
            if json_data and 'recommended_stocks' in json_data:
                recommended_stocks = json_data['recommended_stocks']
            elif json_data and 'stocks' in json_data:
                recommended_stocks = json_data['stocks']
            
            # Try to parse from text if not in JSON
            if not recommended_stocks:
                stock_pattern = r'(\d{6})'
                stock_matches = re.findall(stock_pattern, analysis_content)
                for code in set(stock_matches):
                    recommended_stocks.append({
                        "stock_code": code,
                        "reason": "从新闻内容中识别"
                    })
            
            # Extract market sentiment
            market_sentiment = ""
            if json_data and 'market_sentiment' in json_data:
                market_sentiment = json_data['market_sentiment']
            elif json_data and 'sentiment' in json_data:
                market_sentiment = json_data['sentiment']
            
            confidence_score = json_data.get('confidence_score', 0.0) if json_data else 0.0
            
            return NewsInsightResult(
                recommended_stocks=recommended_stocks[:10],  # Limit to 10
                market_sentiment=market_sentiment,
                analysis_content=analysis_content,
                confidence_score=confidence_score,
                llm_provider=response.provider,
                llm_model=response.model,
                token_usage={
                    "prompt_tokens": response.token_usage.prompt_tokens,
                    "completion_tokens": response.token_usage.completion_tokens,
                    "total_tokens": response.token_usage.total_tokens
                },
                analysis_time=datetime.now(timezone.utc).isoformat(),
                success=True
            )
            
        except Exception as e:
            logger.error(f"News insight extraction failed: {e}")
            return NewsInsightResult(
                analysis_content="",
                success=False,
                error_message=str(e)
            )


# Global analyzer instance
_analyzer: Optional[AIAnalyzer] = None


def get_ai_analyzer() -> AIAnalyzer:
    """Get or create the global AI analyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = AIAnalyzer()
    return _analyzer


def analyze_stock(
    stock_data: Dict[str, Any],
    analysis_mode: str = "短线T+1",
    sector_data: Optional[Dict[str, Any]] = None,
    news_list: Optional[List[Dict[str, Any]]] = None
) -> StockAnalysisResult:
    """Convenience function to analyze a stock"""
    analyzer = get_ai_analyzer()
    return analyzer.analyze_stock(stock_data, analysis_mode, sector_data, news_list)


def analyze_market(
    index_code: str = "000001",
    index_name: str = "上证指数",
    kline_data: Any = None,
    indicators_data: Any = None,
    fund_flow_data: str = "",
    limit_up_count: int = 0,
    limit_down_count: int = 0,
    days: int = 30
) -> MarketAnalysisResult:
    """Convenience function to analyze market"""
    analyzer = get_ai_analyzer()
    return analyzer.analyze_market(
        index_code, index_name, kline_data, indicators_data,
        fund_flow_data, limit_up_count, limit_down_count, days
    )


def extract_news_insights(news_list: List[Dict[str, Any]]) -> NewsInsightResult:
    """Convenience function to extract insights from news"""
    analyzer = get_ai_analyzer()
    return analyzer.extract_news_insights(news_list)


# =============================================================================
# Test Function
# =============================================================================

def test_ai_analyzer():
    """Test AI analyzer functionality"""
    print("=" * 60)
    print("Testing AI Analyzer...")
    print("=" * 60)
    
    analyzer = get_ai_analyzer()
    
    # Test stock analysis (mock data without real API keys)
    print("\n1. Testing Stock Analysis:")
    mock_stock_data = {
        'stock_code': '600000',
        'stock_name': '浦发银行',
        'current_price': 10.25,
        'change_percent': 2.15,
        'industry': '银行业',
        'kline_str': '日期 | 收盘\n2026-01-27 | 10.08\n2026-01-28 | 10.12\n2026-01-29 | 10.25'
    }
    
    result = analyzer.analyze_stock(mock_stock_data, analysis_mode="短线T+1")
    print(f"   Success: {result.success}")
    print(f"   Stock: {result.stock_code} - {result.stock_name}")
    print(f"   Trend: {result.trend}")
    if result.trading_advice:
        print(f"   Trading Direction: {result.trading_advice.direction}")
    print(f"   LLM Provider: {result.llm_provider}")
    if result.error_message:
        print(f"   Error: {result.error_message}")
    
    # Test market analysis
    print("\n2. Testing Market Analysis:")
    result = analyzer.analyze_market(
        index_code="000001",
        index_name="上证指数",
        kline_data=None,
        indicators_data=None,
        fund_flow_data="主力净流入: +25.6亿",
        limit_up_count=85,
        limit_down_count=5
    )
    print(f"   Success: {result.success}")
    print(f"   Trend: {result.trend}")
    print(f"   LLM Provider: {result.llm_provider}")
    if result.error_message:
        print(f"   Error: {result.error_message}")
    
    # Test news insight extraction
    print("\n3. Testing News Insight Extraction:")
    mock_news = [
        {'title': '央行降息', 'time': '2026-01-29', 'content': '央行宣布降息25个基点'},
        {'title': '新能源政策利好', 'time': '2026-01-28', 'content': '新能源行业获得政策支持'}
    ]
    result = analyzer.extract_news_insights(mock_news)
    print(f"   Success: {result.success}")
    print(f"   Recommended Stocks: {len(result.recommended_stocks)}")
    print(f"   Market Sentiment: {result.market_sentiment}")
    print(f"   LLM Provider: {result.llm_provider}")
    if result.error_message:
        print(f"   Error: {result.error_message}")
    
    print("\n" + "=" * 60)
    print("AI Analyzer test completed!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    test_ai_analyzer()
