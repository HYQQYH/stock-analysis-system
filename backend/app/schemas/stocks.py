"""
Stock-related API Schemas
"""
from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field


class StockInfo(BaseModel):
    """Stock Basic Information"""
    stock_code: str = Field(..., description="Stock code")
    stock_name: str = Field(..., description="Stock name")
    exchange: str = Field(..., description="Exchange: SH/SZ")
    industry: Optional[str] = Field(None, description="Industry")
    listing_date: Optional[date] = Field(None, description="Listing date")

    class Config:
        json_schema_extra = {
            "example": {
                "stock_code": "600000",
                "stock_name": "浦发银行",
                "exchange": "SH",
                "industry": "银行",
                "listing_date": "1999-11-10"
            }
        }


class StockCompanyInfo(BaseModel):
    """Stock Company Detailed Information"""
    stock_code: str = Field(..., description="Stock code")
    stock_name: Optional[str] = Field(None, description="Stock name")
    short_name: Optional[str] = Field(None, description="Company short name")
    main_business: Optional[str] = Field(None, description="Main business")
    industry: Optional[str] = Field(None, description="Industry")
    region: Optional[str] = Field(None, description="Region")
    company_intro: Optional[str] = Field(None, description="Company introduction")

    class Config:
        json_schema_extra = {
            "example": {
                "stock_code": "SH601127",
                "stock_name": "赛力斯",
                "short_name": "赛力斯",
                "main_business": "新能源汽车及核心三电(电池、电驱、电控)、传统汽车及核心部件总成的研发、制造、销售及服务。",
                "industry": "汽车整车",
                "region": "重庆"
            }
        }


class KlineData(BaseModel):
    """K-line Data Point"""
    trade_date: date = Field(..., description="Trade date")
    open_price: float = Field(..., description="Opening price")
    high_price: float = Field(..., description="Highest price")
    low_price: float = Field(..., description="Lowest price")
    close_price: float = Field(..., description="Closing price")
    volume: int = Field(..., description="Volume")
    amount: float = Field(..., description="Turnover amount")
    percentage_change: Optional[float] = Field(None, description="Percentage change")
    turnover: Optional[float] = Field(None, description="Turnover rate")

    class Config:
        json_schema_extra = {
            "example": {
                "trade_date": "2024-01-15",
                "open_price": 10.50,
                "high_price": 10.80,
                "low_price": 10.30,
                "close_price": 10.70,
                "volume": 1000000,
                "amount": 10700000.00,
                "percentage_change": 1.90,
                "turnover": 2.5
            }
        }


class TechnicalIndicator(BaseModel):
    """Technical Indicator Data Point"""
    trade_date: date = Field(..., description="Trade date")
    values: dict = Field(..., description="Indicator values (e.g., MACD, KDJ, RSI)")

    class Config:
        json_schema_extra = {
            "example": {
                "trade_date": "2024-01-15",
                "values": {
                    "macd": 0.12,
                    "signal": 0.10,
                    "histogram": 0.02,
                    "k": 70.5,
                    "d": 65.3,
                    "j": 80.9,
                    "rsi": 68.5
                }
            }
        }


class StockSearchRequest(BaseModel):
    """Stock Search Request"""
    keyword: str = Field(..., min_length=1, description="Search keyword (code or name)")

    class Config:
        json_schema_extra = {
            "example": {
                "keyword": "600000"
            }
        }


class StockSearchResponse(BaseModel):
    """Stock Search Response"""
    stocks: List[StockInfo] = Field(..., description="List of matching stocks")

    class Config:
        json_schema_extra = {
            "example": {
                "stocks": [
                    {
                        "stock_code": "600000",
                        "stock_name": "浦发银行",
                        "exchange": "SH",
                        "industry": "银行"
                    }
                ]
            }
        }


class StockKlineResponse(BaseModel):
    """Stock K-line Data Response"""
    stock_code: str = Field(..., description="Stock code")
    kline_type: str = Field(..., description="K-line type: day/week/month")
    data: List[KlineData] = Field(..., description="K-line data")

    class Config:
        json_schema_extra = {
            "example": {
                "stock_code": "600000",
                "kline_type": "day",
                "data": []
            }
        }


class StockIndicatorsResponse(BaseModel):
    """Stock Technical Indicators Response"""
    stock_code: str = Field(..., description="Stock code")
    kline_type: str = Field(..., description="K-line type")
    indicators: List[TechnicalIndicator] = Field(..., description="Indicator data")

    class Config:
        json_schema_extra = {
            "example": {
                "stock_code": "600000",
                "kline_type": "day",
                "indicators": []
            }
        }