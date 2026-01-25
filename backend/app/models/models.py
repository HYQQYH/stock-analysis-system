"""SQLAlchemy ORM Models for Stock Analysis System"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Time, Text, LargeBinary, Enum, JSON
from sqlalchemy import Index, ForeignKey, UniqueConstraint, CheckConstraint
from app.db.database import Base
import enum


class KlineTypeEnum(str, enum.Enum):
    """K-line type enumeration"""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class AnalysisTypeEnum(str, enum.Enum):
    """Analysis type enumeration"""
    INDEX = "index"
    STOCK = "stock"


class AnalysisStatusEnum(str, enum.Enum):
    """Analysis status enumeration"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class StockInfo(Base):
    """Stock Basic Information Model"""
    __tablename__ = "stock_info"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False, unique=True, index=True)
    stock_name = Column(String(50), nullable=False)
    exchange = Column(String(10), nullable=False, index=True)
    industry = Column(String(50), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<StockInfo(code={self.stock_code}, name={self.stock_name})>"


class StockKlineData(Base):
    """K-line Data Model"""
    __tablename__ = "stock_kline_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False, index=True)
    kline_type = Column(Enum(KlineTypeEnum), nullable=False)
    trade_date = Column(Date, nullable=False, index=True)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    percentage_change = Column(Float, nullable=False)
    turnover = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Composite unique constraint
    __table_args__ = (
        UniqueConstraint('stock_code', 'kline_type', 'trade_date', name='uk_stock_kline'),
    )

    def __repr__(self):
        return f"<StockKlineData(code={self.stock_code}, date={self.trade_date}, close={self.close_price})>"


class StockIndicators(Base):
    """Technical Indicators Model"""
    __tablename__ = "stock_indicators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False, index=True)
    indicator_type = Column(String(20), nullable=False)
    kline_type = Column(Enum(KlineTypeEnum), nullable=False)
    trade_date = Column(Date, nullable=False, index=True)
    indicator_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('stock_code', 'indicator_type', 'kline_type', 'trade_date', 
                        name='uk_indicator'),
    )

    def __repr__(self):
        return f"<StockIndicators(code={self.stock_code}, type={self.indicator_type})>"


class AnalysisHistory(Base):
    """Analysis History Model"""
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String(36), nullable=False, unique=True, index=True)
    stock_code = Column(String(10), nullable=False, index=True)
    analysis_type = Column(Enum(AnalysisTypeEnum), nullable=False)
    analysis_mode = Column(String(50), index=True)
    analysis_time = Column(DateTime, nullable=False)
    kline_type = Column(Enum(KlineTypeEnum), nullable=False)
    input_data = Column(JSON)
    analysis_result = Column(Text)
    trading_advice = Column(JSON)
    sentiment_score = Column(Float)
    confidence_score = Column(Float)
    recommendation = Column(String(20))
    llm_model = Column(String(50))
    prompt_version = Column(String(10))
    input_hash = Column(String(64))
    status = Column(Enum(AnalysisStatusEnum), default=AnalysisStatusEnum.PENDING, index=True)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AnalysisHistory(id={self.analysis_id}, code={self.stock_code}, status={self.status})>"


class FinancialNews(Base):
    """Financial News Model"""
    __tablename__ = "financial_news"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    source = Column(String(50), index=True)
    url = Column(String(500))
    publish_time = Column(DateTime, index=True)
    crawl_time = Column(DateTime, default=datetime.utcnow)
    related_stocks = Column(JSON)
    investment_advice = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<FinancialNews(title={self.title[:50]}...)>"


class MarketSentiment(Base):
    """Market Sentiment Model"""
    __tablename__ = "market_sentiment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_date = Column(Date, nullable=False, unique=True, index=True)
    index_code = Column(String(10), default="000001")
    sentiment_score = Column(Float)
    bull_bear_ratio = Column(Float)
    rise_fall_count = Column(JSON)
    volume_ratio = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MarketSentiment(date={self.trade_date}, score={self.sentiment_score})>"


class MarketFundFlow(Base):
    """Market Fund Flow Model"""
    __tablename__ = "market_fund_flow"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_date = Column(Date, nullable=False, unique=True, index=True)
    sh_close_price = Column(Float)
    sh_change_pct = Column(Float)
    sz_close_price = Column(Float)
    sz_change_pct = Column(Float)
    main_net_inflow = Column(Float)
    main_net_inflow_ratio = Column(Float)
    super_large_net_inflow = Column(Float)
    super_large_net_inflow_ratio = Column(Float)
    large_net_inflow = Column(Float)
    large_net_inflow_ratio = Column(Float)
    medium_net_inflow = Column(Float)
    medium_net_inflow_ratio = Column(Float)
    small_net_inflow = Column(Float)
    small_net_inflow_ratio = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MarketFundFlow(date={self.trade_date})>"


class MarketActivity(Base):
    """Market Activity Model"""
    __tablename__ = "market_activity"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_date = Column(Date, nullable=False, unique=True, index=True)
    rise_count = Column(Integer)
    limit_up_count = Column(Integer)
    real_limit_up_count = Column(Integer)
    st_limit_up_count = Column(Integer)
    fall_count = Column(Integer)
    limit_down_count = Column(Integer)
    real_limit_down_count = Column(Integer)
    st_limit_down_count = Column(Integer)
    flat_count = Column(Integer)
    suspend_count = Column(Integer)
    activity_level = Column(String(20))
    stat_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MarketActivity(date={self.trade_date})>"


class LimitUpStockPool(Base):
    """Limit Up Stock Pool Model"""
    __tablename__ = "limit_up_stock_pool"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_date = Column(Date, nullable=False, index=True)
    stock_code = Column(String(10), nullable=False, index=True)
    stock_name = Column(String(50), nullable=False)
    change_pct = Column(Float)
    latest_price = Column(Float)
    turnover_amount = Column(Float)
    circulation_market_value = Column(Float)
    total_market_value = Column(Float)
    turnover_rate = Column(Float)
    limit_up_funds = Column(Float)
    first_limit_time = Column(Time)
    last_limit_time = Column(Time)
    burst_count = Column(Integer)
    limit_up_stats = Column(String(50))
    continuous_limit_count = Column(Integer)
    industry = Column(String(50), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('trade_date', 'stock_code', name='uk_date_stock'),
    )

    def __repr__(self):
        return f"<LimitUpStockPool(date={self.trade_date}, code={self.stock_code})>"


class StockIntradayData(Base):
    """Intraday Data Model"""
    __tablename__ = "stock_intraday_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True)
    trade_time = Column(Time, nullable=False)
    period_type = Column(String(10), nullable=False)
    adjust_type = Column(String(10), default="")
    open_price = Column(Float)
    close_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    volume = Column(Float)
    turnover_amount = Column(Float)
    avg_price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('stock_code', 'trade_date', 'trade_time', 'period_type', 
                        name='uk_stock_time'),
    )

    def __repr__(self):
        return f"<StockIntradayData(code={self.stock_code}, date={self.trade_date}, time={self.trade_time})>"


class SectorKlineData(Base):
    """Sector K-line Data Model"""
    __tablename__ = "sector_kline_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sector_code = Column(String(20), nullable=False, index=True)
    kline_type = Column(Enum(KlineTypeEnum), nullable=False)
    trade_date = Column(Date, nullable=False, index=True)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('sector_code', 'kline_type', 'trade_date', name='uk_sector_kline'),
    )

    def __repr__(self):
        return f"<SectorKlineData(sector={self.sector_code}, date={self.trade_date})>"
