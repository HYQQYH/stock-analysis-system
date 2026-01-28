"""
Analysis-related API Schemas
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class AnalysisMode(str, Enum):
    """Analysis Mode Enum"""
    BASIC = "基础面技术面综合分析"
    WAVE = "波段交易分析"
    SHORT_TERM = "短线T+1分析"
    REBOUND = "涨停反包分析"
    SPECULATION = "投机套利分析"
    VALUATION = "公司估值分析"


class AnalysisStatus(str, Enum):
    """Analysis Status Enum"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class TradingAdvice(BaseModel):
    """Trading Advice Structure"""
    direction: Optional[str] = Field(None, description="Trading direction: 买入/持有/卖出/观望")
    target_price: Optional[float] = Field(None, description="Target price")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")
    holding_period: Optional[int] = Field(None, description="Holding period in days")
    risk_level: Optional[str] = Field(None, description="Risk level: 低/中/高")

    class Config:
        json_schema_extra = {
            "example": {
                "direction": "买入",
                "target_price": 10.5,
                "stop_loss": 9.5,
                "take_profit": 12.0,
                "holding_period": 3,
                "risk_level": "中"
            }
        }


class AnalysisRequest(BaseModel):
    """Create Analysis Request"""
    stock_code: str = Field(..., min_length=6, max_length=6, description="Stock code (6 digits)")
    analysis_mode: AnalysisMode = Field(..., description="Analysis mode")
    kline_type: str = Field(default="day", description="K-line type: day/week/month")
    sector_names: Optional[List[str]] = Field(None, description="Optional sector names for context")
    include_news: bool = Field(default=True, description="Include news in analysis")

    class Config:
        json_schema_extra = {
            "example": {
                "stock_code": "600000",
                "analysis_mode": "短线T+1分析",
                "kline_type": "day",
                "sector_names": ["银行板块", "金融科技"],
                "include_news": True
            }
        }


class AnalysisCreateResponse(BaseModel):
    """Create Analysis Response (immediate response)"""
    analysis_id: str = Field(..., description="Unique analysis ID")
    status: AnalysisStatus = Field(default=AnalysisStatus.PENDING, description="Initial status")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "pending",
                "created_at": "2026-01-28T12:00:00Z"
            }
        }


class AnalysisResult(BaseModel):
    """Analysis Result Structure"""
    analysis_result: Optional[str] = Field(None, description="AI analysis text or structured JSON")
    trading_advice: Optional[TradingAdvice] = Field(None, description="Trading advice")
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="Confidence score (0-1)")
    llm_model: Optional[str] = Field(None, description="LLM model used")
    prompt_version: Optional[str] = Field(None, description="Prompt template version")
    input_hash: Optional[str] = Field(None, description="Input data hash for deduplication")

    class Config:
        json_schema_extra = {
            "example": {
                "analysis_result": "Based on technical analysis, the stock shows strong upward momentum...",
                "trading_advice": {
                    "direction": "买入",
                    "target_price": 10.5,
                    "stop_loss": 9.5,
                    "take_profit": 12.0,
                    "holding_period": 3,
                    "risk_level": "中"
                },
                "confidence_score": 0.78,
                "llm_model": "智谱GLM",
                "prompt_version": "v1.0",
                "input_hash": "a1b2c3d4e5f6..."
            }
        }


class AnalysisDetail(BaseModel):
    """Analysis Detail Response"""
    analysis_id: str = Field(..., description="Unique analysis ID")
    stock_code: str = Field(..., description="Stock code")
    analysis_mode: str = Field(..., description="Analysis mode")
    status: AnalysisStatus = Field(..., description="Current status")
    analysis_time: Optional[datetime] = Field(None, description="Analysis completion time")
    input_data: Optional[dict] = Field(None, description="Input data summary")
    result: Optional[AnalysisResult] = Field(None, description="Analysis result (if completed)")
    error_message: Optional[str] = Field(None, description="Error message (if failed)")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
                "stock_code": "600000",
                "analysis_mode": "短线T+1分析",
                "status": "completed",
                "analysis_time": "2026-01-28T12:05:00Z",
                "input_data": {
                    "kline_data_days": 14,
                    "indicators": ["MACD", "KDJ", "RSI"]
                },
                "result": {
                    "analysis_result": "Based on technical analysis...",
                    "trading_advice": {
                        "direction": "买入",
                        "target_price": 10.5
                    },
                    "confidence_score": 0.78
                },
                "created_at": "2026-01-28T12:00:00Z",
                "updated_at": "2026-01-28T12:05:00Z"
            }
        }


class AnalysisHistoryItem(BaseModel):
    """Analysis History Item"""
    analysis_id: str = Field(..., description="Unique analysis ID")
    stock_code: str = Field(..., description="Stock code")
    analysis_mode: str = Field(..., description="Analysis mode")
    status: AnalysisStatus = Field(..., description="Status")
    analysis_time: Optional[datetime] = Field(None, description="Analysis time")
    confidence_score: Optional[float] = Field(None, description="Confidence score")
    created_at: datetime = Field(..., description="Creation time")

    class Config:
        json_schema_extra = {
            "example": {
                "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
                "stock_code": "600000",
                "analysis_mode": "短线T+1分析",
                "status": "completed",
                "analysis_time": "2026-01-28T12:05:00Z",
                "confidence_score": 0.78,
                "created_at": "2026-01-28T12:00:00Z"
            }
        }