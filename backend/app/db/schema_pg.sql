-- Stock Analysis System Database Schema (PostgreSQL 15)
-- Database: stock_analysis_db
-- Created: 2026-01-25

-- Drop tables if they exist (for fresh initialization)
-- DROP TABLE IF EXISTS sector_kline_data CASCADE;
-- DROP TABLE IF EXISTS stock_intraday_data CASCADE;
-- DROP TABLE IF EXISTS limit_up_stock_pool CASCADE;
-- DROP TABLE IF EXISTS market_activity CASCADE;
-- DROP TABLE IF EXISTS market_fund_flow CASCADE;
-- DROP TABLE IF EXISTS market_sentiment CASCADE;
-- DROP TABLE IF EXISTS financial_news CASCADE;
-- DROP TABLE IF EXISTS analysis_history CASCADE;
-- DROP TABLE IF EXISTS stock_indicators CASCADE;
-- DROP TABLE IF EXISTS stock_kline_data CASCADE;
-- DROP TABLE IF EXISTS stock_info CASCADE;

-- 1. Stock Info Table
CREATE TABLE IF NOT EXISTS stock_info (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL UNIQUE,
    stock_name VARCHAR(50) NOT NULL,
    exchange VARCHAR(10),
    industry VARCHAR(50),
    market_cap BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stock_code ON stock_info(stock_code);
CREATE INDEX IF NOT EXISTS idx_industry ON stock_info(industry);

-- 2. K-line Data Table
CREATE TABLE IF NOT EXISTS stock_kline_data (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    kline_type VARCHAR(10) NOT NULL,  -- 'day', 'week', 'month'
    trade_date DATE NOT NULL,
    open_price NUMERIC(10,2),
    high_price NUMERIC(10,2),
    low_price NUMERIC(10,2),
    close_price NUMERIC(10,2),
    volume BIGINT,
    amount NUMERIC(20,2),
    percentage_change NUMERIC(10,2),
    turnover NUMERIC(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_code, kline_type, trade_date)
);

CREATE INDEX IF NOT EXISTS idx_kline_trade_date ON stock_kline_data(trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_kline_stock_code ON stock_kline_data(stock_code);
CREATE INDEX IF NOT EXISTS idx_kline_stock_date ON stock_kline_data(stock_code, trade_date DESC);

-- 3. Technical Indicators Table
CREATE TABLE IF NOT EXISTS stock_indicators (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    indicator_type VARCHAR(20) NOT NULL,  -- 'MACD', 'KDJ', 'RSI', etc.
    kline_type VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    indicator_data JSONB,  -- Store indicator values as JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_code, indicator_type, kline_type, trade_date)
);

CREATE INDEX IF NOT EXISTS idx_indicator_trade_date ON stock_indicators(trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_indicator_stock_code ON stock_indicators(stock_code);
CREATE INDEX IF NOT EXISTS idx_indicator_stock_date ON stock_indicators(stock_code, trade_date DESC);

-- 4. Analysis History Table
CREATE TABLE IF NOT EXISTS analysis_history (
    id SERIAL PRIMARY KEY,
    analysis_id VARCHAR(36) NOT NULL UNIQUE,
    stock_code VARCHAR(10) NOT NULL,
    analysis_type VARCHAR(20),  -- 'index', 'stock'
    analysis_mode VARCHAR(50),  -- '短线T+1', etc.
    analysis_time TIMESTAMP NOT NULL,
    kline_type VARCHAR(10),
    input_data JSONB,
    analysis_result TEXT,
    trading_advice JSONB,
    sentiment_score NUMERIC(3,2),
    confidence_score NUMERIC(3,2),
    recommendation VARCHAR(20),
    llm_model VARCHAR(50),
    prompt_version VARCHAR(10),
    input_hash VARCHAR(64),
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'completed', 'failed', 'timeout'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_analysis_stock_time ON analysis_history(stock_code, analysis_time DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_id ON analysis_history(analysis_id);
CREATE INDEX IF NOT EXISTS idx_analysis_status ON analysis_history(status);
CREATE INDEX IF NOT EXISTS idx_analysis_mode ON analysis_history(analysis_mode);

-- 5. Financial News Table
CREATE TABLE IF NOT EXISTS financial_news (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    source VARCHAR(50),
    url VARCHAR(500),
    publish_time TIMESTAMP,
    crawl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    related_stocks JSONB,  -- Array of stock codes
    investment_advice TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_news_publish_time ON financial_news(publish_time DESC);
CREATE INDEX IF NOT EXISTS idx_news_source ON financial_news(source);

-- 6. Market Sentiment Table
CREATE TABLE IF NOT EXISTS market_sentiment (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL UNIQUE,
    index_code VARCHAR(10) DEFAULT '000001',
    sentiment_score NUMERIC(3,2),
    bull_bear_ratio NUMERIC(5,2),
    rise_fall_count JSONB,
    volume_ratio NUMERIC(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sentiment_date ON market_sentiment(trade_date DESC);

-- 7. Market Fund Flow Table
CREATE TABLE IF NOT EXISTS market_fund_flow (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL UNIQUE,
    sh_close_price NUMERIC(10,2),
    sh_change_pct NUMERIC(10,4),
    sz_close_price NUMERIC(10,2),
    sz_change_pct NUMERIC(10,4),
    main_net_inflow NUMERIC(20,2),
    main_net_inflow_ratio NUMERIC(10,4),
    super_large_net_inflow NUMERIC(20,2),
    super_large_net_inflow_ratio NUMERIC(10,4),
    large_net_inflow NUMERIC(20,2),
    large_net_inflow_ratio NUMERIC(10,4),
    medium_net_inflow NUMERIC(20,2),
    medium_net_inflow_ratio NUMERIC(10,4),
    small_net_inflow NUMERIC(20,2),
    small_net_inflow_ratio NUMERIC(10,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fundflow_date ON market_fund_flow(trade_date DESC);

-- 8. Market Activity Table
CREATE TABLE IF NOT EXISTS market_activity (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL UNIQUE,
    rise_count INT,
    limit_up_count INT,
    real_limit_up_count INT,
    st_limit_up_count INT,
    fall_count INT,
    limit_down_count INT,
    real_limit_down_count INT,
    st_limit_down_count INT,
    flat_count INT,
    suspend_count INT,
    activity_level VARCHAR(20),
    stat_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_activity_date ON market_activity(trade_date DESC);

-- 9. Limit Up Stock Pool Table
CREATE TABLE IF NOT EXISTS limit_up_stock_pool (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50),
    change_pct NUMERIC(10,4),
    latest_price NUMERIC(10,2),
    turnover_amount NUMERIC(20,2),
    circulation_market_value NUMERIC(20,2),
    total_market_value NUMERIC(20,2),
    turnover_rate NUMERIC(10,4),
    limit_up_funds NUMERIC(20,2),
    first_limit_time TIME,
    last_limit_time TIME,
    burst_count INT,
    limit_up_stats VARCHAR(50),
    continuous_limit_count INT,
    industry VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trade_date, stock_code)
);

CREATE INDEX IF NOT EXISTS idx_limitup_date ON limit_up_stock_pool(trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_limitup_stock_code ON limit_up_stock_pool(stock_code);
CREATE INDEX IF NOT EXISTS idx_limitup_industry ON limit_up_stock_pool(industry);

-- 10. Intraday Data Table
CREATE TABLE IF NOT EXISTS stock_intraday_data (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    trade_time TIME NOT NULL,
    period_type VARCHAR(10) NOT NULL,  -- '1min', '5min', etc.
    adjust_type VARCHAR(10) DEFAULT '',
    open_price NUMERIC(10,2),
    close_price NUMERIC(10,2),
    high_price NUMERIC(10,2),
    low_price NUMERIC(10,2),
    volume NUMERIC(20,2),
    turnover_amount NUMERIC(20,2),
    avg_price NUMERIC(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_code, trade_date, trade_time, period_type)
);

CREATE INDEX IF NOT EXISTS idx_intraday_date ON stock_intraday_data(trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_intraday_stock_code ON stock_intraday_data(stock_code);

-- 11. Sector K-line Data Table
CREATE TABLE IF NOT EXISTS sector_kline_data (
    id SERIAL PRIMARY KEY,
    sector_code VARCHAR(20) NOT NULL,
    kline_type VARCHAR(10) NOT NULL,  -- 'day', 'week', 'month'
    trade_date DATE NOT NULL,
    open_price NUMERIC(10,2),
    high_price NUMERIC(10,2),
    low_price NUMERIC(10,2),
    close_price NUMERIC(10,2),
    volume BIGINT,
    amount NUMERIC(20,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(sector_code, kline_type, trade_date)
);

CREATE INDEX IF NOT EXISTS idx_sector_date ON sector_kline_data(trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_sector_code ON sector_kline_data(sector_code);

-- 12. Cache Metadata Table
CREATE TABLE IF NOT EXISTS cache_metadata (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(255) NOT NULL UNIQUE,
    cache_type VARCHAR(50),
    last_updated TIMESTAMP,
    expiry_time TIMESTAMP,
    is_complete BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cache_key ON cache_metadata(cache_key);
CREATE INDEX IF NOT EXISTS idx_cache_type ON cache_metadata(cache_type);

-- Insert sample data
INSERT INTO stock_info (stock_code, stock_name, exchange, industry) 
VALUES ('600000', '浦发银行', 'SSE', '银行')
ON CONFLICT (stock_code) DO UPDATE SET updated_at = CURRENT_TIMESTAMP;

INSERT INTO stock_info (stock_code, stock_name, exchange, industry) 
VALUES ('601398', '工商银行', 'SSE', '银行')
ON CONFLICT (stock_code) DO UPDATE SET updated_at = CURRENT_TIMESTAMP;

INSERT INTO stock_info (stock_code, stock_name, exchange, industry) 
VALUES ('600519', '贵州茅台', 'SSE', '食品饮料')
ON CONFLICT (stock_code) DO UPDATE SET updated_at = CURRENT_TIMESTAMP;

-- Verify schema creation
SELECT 'Schema initialization completed successfully' as message;
