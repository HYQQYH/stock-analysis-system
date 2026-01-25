"""Database Schema Definition (SQL)"""

# Stock Basic Information Table
STOCK_INFO_TABLE = """
CREATE TABLE IF NOT EXISTS stock_info (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    stock_name VARCHAR(50) NOT NULL COMMENT '股票名称',
    exchange VARCHAR(10) NOT NULL COMMENT '交易所: SH/SZ',
    industry VARCHAR(50) COMMENT '所属行业',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_code (stock_code),
    INDEX idx_exchange (exchange),
    INDEX idx_industry (industry)
) COMMENT='股票基本信息表' ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# K-line Data Table
KLINE_DATA_TABLE = """
CREATE TABLE IF NOT EXISTS stock_kline_data (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    kline_type ENUM('day', 'week', 'month') NOT NULL COMMENT 'K线类型',
    trade_date DATE NOT NULL COMMENT '交易日期',
    open_price DECIMAL(10,2) NOT NULL COMMENT '开盘价',
    high_price DECIMAL(10,2) NOT NULL COMMENT '最高价',
    low_price DECIMAL(10,2) NOT NULL COMMENT '最低价',
    close_price DECIMAL(10,2) NOT NULL COMMENT '收盘价',
    volume BIGINT NOT NULL COMMENT '成交量',
    amount DECIMAL(20,2) NOT NULL COMMENT '成交额',
    percentage_change DECIMAL(10,2) NOT NULL COMMENT '涨跌幅',
    turnover DECIMAL(10,2) NOT NULL COMMENT '换手率',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_kline (stock_code, kline_type, trade_date),
    INDEX idx_trade_date (trade_date),
    INDEX idx_stock_code (stock_code)
) COMMENT='K线数据表' ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# Technical Indicators Table
INDICATORS_TABLE = """
CREATE TABLE IF NOT EXISTS stock_indicators (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    indicator_type VARCHAR(20) NOT NULL COMMENT '指标类型: MACD/KDJ等',
    kline_type ENUM('day', 'week', 'month') NOT NULL,
    trade_date DATE NOT NULL COMMENT '交易日期',
    indicator_data JSON NOT NULL COMMENT '指标数值(JSON格式)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_indicator (stock_code, indicator_type, kline_type, trade_date),
    INDEX idx_trade_date (trade_date),
    INDEX idx_stock_code (stock_code)
) COMMENT='技术指标数据表' ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# Analysis History Table
ANALYSIS_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS analysis_history (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    analysis_id VARCHAR(36) NOT NULL UNIQUE COMMENT '分析任务ID (UUID)',
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    analysis_type ENUM('index', 'stock') NOT NULL COMMENT '分析类型',
    analysis_mode VARCHAR(50) COMMENT '分析模式(基础/波段/短线等)',
    analysis_time TIMESTAMP NOT NULL COMMENT '分析时间',
    kline_type ENUM('day', 'week', 'month') NOT NULL,
    input_data JSON COMMENT '输入数据摘要',
    analysis_result LONGTEXT COMMENT 'AI分析结果',
    trading_advice JSON COMMENT '交易建议(JSON格式)',
    sentiment_score DECIMAL(3,2) COMMENT '情绪得分',
    confidence_score DECIMAL(3,2) COMMENT '置信度分数',
    recommendation VARCHAR(20) COMMENT '建议: 买入/持有/卖出',
    llm_model VARCHAR(50) COMMENT '使用的LLM模型',
    prompt_version VARCHAR(10) COMMENT '提示词版本',
    input_hash VARCHAR(64) COMMENT '输入数据摘要(用于去重)',
    status ENUM('pending', 'completed', 'failed', 'timeout') DEFAULT 'pending' COMMENT '分析状态',
    error_message TEXT COMMENT '错误信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_stock_time (stock_code, analysis_time),
    INDEX idx_analysis_id (analysis_id),
    INDEX idx_status (status),
    INDEX idx_analysis_mode (analysis_mode)
) COMMENT='分析历史记录表' ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# Financial News Table
FINANCIAL_NEWS_TABLE = """
CREATE TABLE IF NOT EXISTS financial_news (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(500) NOT NULL COMMENT '新闻标题',
    content LONGTEXT COMMENT '新闻内容',
    source VARCHAR(50) COMMENT '来源',
    url VARCHAR(500) COMMENT '新闻链接',
    publish_time TIMESTAMP COMMENT '发布时间',
    crawl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '抓取时间',
    related_stocks JSON COMMENT '相关股票代码列表',
    investment_advice LONGTEXT COMMENT 'AI投资建议',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_publish_time (publish_time),
    INDEX idx_source (source)
) COMMENT='财经新闻表' ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# Market Sentiment Table
MARKET_SENTIMENT_TABLE = """
CREATE TABLE IF NOT EXISTS market_sentiment (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    trade_date DATE NOT NULL,
    index_code VARCHAR(10) DEFAULT '000001' COMMENT '指数代码',
    sentiment_score DECIMAL(3,2) COMMENT '情绪得分(0-100)',
    bull_bear_ratio DECIMAL(5,2) COMMENT '多空比例',
    rise_fall_count JSON COMMENT '涨跌家数',
    volume_ratio DECIMAL(5,2) COMMENT '量比',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_date (trade_date),
    INDEX idx_trade_date (trade_date)
) COMMENT='大盘情绪数据表' ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# Market Fund Flow Table
MARKET_FUND_FLOW_TABLE = """
CREATE TABLE IF NOT EXISTS market_fund_flow (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    trade_date DATE NOT NULL COMMENT '交易日期',
    sh_close_price DECIMAL(10,2) COMMENT '上证收盘价',
    sh_change_pct DECIMAL(10,4) COMMENT '上证涨跌幅(%)',
    sz_close_price DECIMAL(10,2) COMMENT '深证收盘价',
    sz_change_pct DECIMAL(10,4) COMMENT '深证涨跌幅(%)',
    main_net_inflow DECIMAL(20,2) COMMENT '主力净流入净额',
    main_net_inflow_ratio DECIMAL(10,4) COMMENT '主力净流入净占比(%)',
    super_large_net_inflow DECIMAL(20,2) COMMENT '超大单净流入净额',
    super_large_net_inflow_ratio DECIMAL(10,4) COMMENT '超大单净流入净占比(%)',
    large_net_inflow DECIMAL(20,2) COMMENT '大单净流入净额',
    large_net_inflow_ratio DECIMAL(10,4) COMMENT '大单净流入净占比(%)',
    medium_net_inflow DECIMAL(20,2) COMMENT '中单净流入净额',
    medium_net_inflow_ratio DECIMAL(10,4) COMMENT '中单净流入净占比(%)',
    small_net_inflow DECIMAL(20,2) COMMENT '小单净流入净额',
    small_net_inflow_ratio DECIMAL(10,4) COMMENT '小单净流入净占比(%)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_trade_date (trade_date),
    INDEX idx_trade_date (trade_date)
) COMMENT='大盘资金流向数据表' ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# Market Activity Table
MARKET_ACTIVITY_TABLE = """
CREATE TABLE IF NOT EXISTS market_activity (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    trade_date DATE NOT NULL COMMENT '交易日期',
    rise_count INT COMMENT '上涨家数',
    limit_up_count INT COMMENT '涨停家数',
    real_limit_up_count INT COMMENT '真实涨停家数',
    st_limit_up_count INT COMMENT 'ST/ST*涨停家数',
    fall_count INT COMMENT '下跌家数',
    limit_down_count INT COMMENT '跌停家数',
    real_limit_down_count INT COMMENT '真实跌停家数',
    st_limit_down_count INT COMMENT 'ST/ST*跌停家数',
    flat_count INT COMMENT '平盘家数',
    suspend_count INT COMMENT '停牌家数',
    activity_level VARCHAR(20) COMMENT '活跃度',
    stat_time TIMESTAMP COMMENT '统计时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_trade_date (trade_date),
    INDEX idx_trade_date (trade_date)
) COMMENT='市场活跃度数据表' ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# Limit Up Stock Pool Table
LIMIT_UP_STOCK_POOL_TABLE = """
CREATE TABLE IF NOT EXISTS limit_up_stock_pool (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    trade_date DATE NOT NULL COMMENT '交易日期',
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    stock_name VARCHAR(50) NOT NULL COMMENT '股票名称',
    change_pct DECIMAL(10,4) COMMENT '涨跌幅(%)',
    latest_price DECIMAL(10,2) COMMENT '最新价',
    turnover_amount DECIMAL(20,2) COMMENT '成交额',
    circulation_market_value DECIMAL(20,2) COMMENT '流通市值',
    total_market_value DECIMAL(20,2) COMMENT '总市值',
    turnover_rate DECIMAL(10,4) COMMENT '换手率(%)',
    limit_up_funds DECIMAL(20,2) COMMENT '封板资金',
    first_limit_time TIME COMMENT '首次封板时间',
    last_limit_time TIME COMMENT '最后封板时间',
    burst_count INT COMMENT '炸板次数',
    limit_up_stats VARCHAR(50) COMMENT '涨停统计',
    continuous_limit_count INT COMMENT '连板数',
    industry VARCHAR(50) COMMENT '所属行业',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_date_stock (trade_date, stock_code),
    INDEX idx_trade_date (trade_date),
    INDEX idx_stock_code (stock_code),
    INDEX idx_industry (industry)
) COMMENT='涨停股池数据表' ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# Intraday Data Table
INTRADAY_DATA_TABLE = """
CREATE TABLE IF NOT EXISTS stock_intraday_data (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    trade_date DATE NOT NULL COMMENT '交易日期',
    trade_time TIME NOT NULL COMMENT '交易时间',
    period_type VARCHAR(10) NOT NULL COMMENT '周期类型: 1min/5min/15min/30min/60min',
    adjust_type VARCHAR(10) DEFAULT '' COMMENT '复权类型: 空/qfq/hfq',
    open_price DECIMAL(10,2) COMMENT '开盘价',
    close_price DECIMAL(10,2) COMMENT '收盘价',
    high_price DECIMAL(10,2) COMMENT '最高价',
    low_price DECIMAL(10,2) COMMENT '最低价',
    volume DECIMAL(20,2) COMMENT '成交量(手)',
    turnover_amount DECIMAL(20,2) COMMENT '成交额',
    avg_price DECIMAL(10,2) COMMENT '均价',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_time (stock_code, trade_date, trade_time, period_type),
    INDEX idx_trade_date (trade_date),
    INDEX idx_stock_code (stock_code)
) COMMENT='个股分时数据表' ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# Sector K-line Data Table
SECTOR_KLINE_DATA_TABLE = """
CREATE TABLE IF NOT EXISTS sector_kline_data (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    sector_code VARCHAR(20) NOT NULL COMMENT '板块代码',
    kline_type ENUM('day', 'week', 'month') NOT NULL COMMENT 'K线类型',
    trade_date DATE NOT NULL COMMENT '交易日期',
    open_price DECIMAL(10,2) NOT NULL COMMENT '开盘价',
    high_price DECIMAL(10,2) NOT NULL COMMENT '最高价',
    low_price DECIMAL(10,2) NOT NULL COMMENT '最低价',
    close_price DECIMAL(10,2) NOT NULL COMMENT '收盘价',
    volume BIGINT NOT NULL COMMENT '成交量',
    amount DECIMAL(20,2) NOT NULL COMMENT '成交额',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_sector_kline (sector_code, kline_type, trade_date),
    INDEX idx_trade_date (trade_date),
    INDEX idx_sector_code (sector_code)
) COMMENT='板块K线数据表' ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# All SQL statements
ALL_TABLES_SQL = [
    STOCK_INFO_TABLE,
    KLINE_DATA_TABLE,
    INDICATORS_TABLE,
    ANALYSIS_HISTORY_TABLE,
    FINANCIAL_NEWS_TABLE,
    MARKET_SENTIMENT_TABLE,
    MARKET_FUND_FLOW_TABLE,
    MARKET_ACTIVITY_TABLE,
    LIMIT_UP_STOCK_POOL_TABLE,
    INTRADAY_DATA_TABLE,
    SECTOR_KLINE_DATA_TABLE,
]
