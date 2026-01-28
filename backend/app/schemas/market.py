"""
Market-related API Schemas
"""
from typing import List, Optional
from datetime import date, time
from pydantic import BaseModel, Field


class MarketIndexData(BaseModel):
    """Market Index Data Point"""
    trade_date: date = Field(..., description="Trade date")
    open_price: float = Field(..., description="Opening price")
    high_price: float = Field(..., description="Highest price")
    low_price: float = Field(..., description="Lowest price")
    close_price: float = Field(..., description="Closing price")
    volume: int = Field(..., description="Volume")
    amount: float = Field(..., description="Turnover amount")

    class Config:
        json_schema_extra = {
            "example": {
                "trade_date": "2024-01-15",
                "open_price": 3200.50,
                "high_price": 3220.30,
                "low_price": 3190.20,
                "close_price": 3210.80,
                "volume": 100000000,
                "amount": 120000000000.00
            }
        }


class MarketSentiment(BaseModel):
    """Market Sentiment Data"""
    trade_date: date = Field(..., description="Trade date")
    index_code: str = Field(default="000001", description="Index code")
    sentiment_score: Optional[float] = Field(None, ge=0, le=100, description="Sentiment score (0-100)")
    bull_bear_ratio: Optional[float] = Field(None, description="Bull/bear ratio")
    rise_fall_count: Optional[dict] = Field(None, description="Rise/fall count")
    volume_ratio: Optional[float] = Field(None, description="Volume ratio")

    class Config:
        json_schema_extra = {
            "example": {
                "trade_date": "2024-01-15",
                "index_code": "000001",
                "sentiment_score": 65.5,
                "bull_bear_ratio": 1.2,
                "rise_fall_count": {
                    "rise": 2500,
                    "fall": 1800,
                    "flat": 300
                },
                "volume_ratio": 1.15
            }
        }


class FundFlowData(BaseModel):
    """Market Fund Flow Data"""
    trade_date: date = Field(..., description="Trade date")
    sh_close_price: Optional[float] = Field(None, description="Shanghai close price")
    sh_change_pct: Optional[float] = Field(None, description="Shanghai change percentage")
    sz_close_price: Optional[float] = Field(None, description="Shenzhen close price")
    sz_change_pct: Optional[float] = Field(None, description="Shenzhen change percentage")
    main_net_inflow: Optional[float] = Field(None, description="Main fund net inflow")
    main_net_inflow_ratio: Optional[float] = Field(None, description="Main fund net inflow ratio")
    super_large_net_inflow: Optional[float] = Field(None, description="Super large order net inflow")
    super_large_net_inflow_ratio: Optional[float] = Field(None, description="Super large order net inflow ratio")
    large_net_inflow: Optional[float] = Field(None, description="Large order net inflow")
    large_net_inflow_ratio: Optional[float] = Field(None, description="Large order net inflow ratio")
    medium_net_inflow: Optional[float] = Field(None, description="Medium order net inflow")
    medium_net_inflow_ratio: Optional[float] = Field(None, description="Medium order net inflow ratio")
    small_net_inflow: Optional[float] = Field(None, description="Small order net inflow")
    small_net_inflow_ratio: Optional[float] = Field(None, description="Small order net inflow ratio")

    class Config:
        json_schema_extra = {
            "example": {
                "trade_date": "2024-01-15",
                "sh_close_price": 3210.80,
                "sh_change_pct": 0.5,
                "sz_close_price": 10500.30,
                "sz_change_pct": 0.8,
                "main_net_inflow": -50000000.00,
                "main_net_inflow_ratio": -0.5,
                "super_large_net_inflow": -80000000.00,
                "super_large_net_inflow_ratio": -0.8,
                "large_net_inflow": 30000000.00,
                "large_net_inflow_ratio": 0.3,
                "medium_net_inflow": -10000000.00,
                "medium_net_inflow_ratio": -0.1,
                "small_net_inflow": 10000000.00,
                "small_net_inflow_ratio": 0.1
            }
        }


class LimitUpStock(BaseModel):
    """Limit-up Stock Data"""
    stock_code: str = Field(..., description="Stock code")
    stock_name: str = Field(..., description="Stock name")
    change_pct: Optional[float] = Field(None, description="Change percentage")
    latest_price: Optional[float] = Field(None, description="Latest price")
    turnover_amount: Optional[float] = Field(None, description="Turnover amount")
    circulation_market_value: Optional[float] = Field(None, description="Circulation market value")
    total_market_value: Optional[float] = Field(None, description="Total market value")
    turnover_rate: Optional[float] = Field(None, description="Turnover rate")
    limit_up_funds: Optional[float] = Field(None, description="Limit-up funds")
    first_limit_time: Optional[time] = Field(None, description="First limit-up time")
    last_limit_time: Optional[time] = Field(None, description="Last limit-up time")
    burst_count: Optional[int] = Field(None, ge=0, description="Burst count")
    limit_up_stats: Optional[str] = Field(None, description="Limit-up stats")
    continuous_limit_count: Optional[int] = Field(None, ge=0, description="Continuous limit-up count")
    industry: Optional[str] = Field(None, description="Industry")

    class Config:
        json_schema_extra = {
            "example": {
                "stock_code": "600000",
                "stock_name": "浦发银行",
                "change_pct": 10.0,
                "latest_price": 10.00,
                "turnover_amount": 1000000000.00,
                "circulation_market_value": 50000000000.00,
                "total_market_value": 60000000000.00,
                "turnover_rate": 2.5,
                "limit_up_funds": 50000000.00,
                "first_limit_time": "09:30:00",
                "last_limit_time": "09:30:00",
                "burst_count": 0,
                "limit_up_stats": "1板",
                "continuous_limit_count": 1,
                "industry": "银行"
            }
        }


class MarketActivity(BaseModel):
    """Market Activity Data"""
    trade_date: date = Field(..., description="Trade date")
    rise_count: Optional[int] = Field(None, ge=0, description="Rise count")
    limit_up_count: Optional[int] = Field(None, ge=0, description="Limit-up count")
    real_limit_up_count: Optional[int] = Field(None, ge=0, description="Real limit-up count")
    st_limit_up_count: Optional[int] = Field(None, ge=0, description="ST limit-up count")
    fall_count: Optional[int] = Field(None, ge=0, description="Fall count")
    limit_down_count: Optional[int] = Field(None, ge=0, description="Limit-down count")
    real_limit_down_count: Optional[int] = Field(None, ge=0, description="Real limit-down count")
    st_limit_down_count: Optional[int] = Field(None, ge=0, description="ST limit-down count")
    flat_count: Optional[int] = Field(None, ge=0, description="Flat count")
    suspend_count: Optional[int] = Field(None, ge=0, description="Suspend count")
    activity_level: Optional[str] = Field(None, description="Activity level")
    stat_time: Optional[str] = Field(None, description="Statistics time")

    class Config:
        json_schema_extra = {
            "example": {
                "trade_date": "2024-01-15",
                "rise_count": 2500,
                "limit_up_count": 50,
                "real_limit_up_count": 45,
                "st_limit_up_count": 5,
                "fall_count": 1800,
                "limit_down_count": 10,
                "real_limit_down_count": 8,
                "st_limit_down_count": 2,
                "flat_count": 300,
                "suspend_count": 50,
                "activity_level": "活跃",
                "stat_time": "2024-01-15 15:00:00"
            }
        }