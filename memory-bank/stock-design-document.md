# 股票分析系统设计文档

## 1. 系统概述

### 1.1 项目描述
股票分析系统是一个集数据采集、技术指标计算、AI智能分析和可视化展示于一体的综合性金融分析平台。系统通过多源数据融合，结合大语言模型（LLM）能力，为用户提供深度的股票市场分析和投资建议。

### 1.2 核心目标
- 自动化采集上证指数及个股的K线数据、成交数据和大盘情绪数据
- 计算MACD、KDJ等技术指标
- 基于AI分析生成市场走势和个股分析报告
- 爬取财经新闻并提取潜在投资机会
- 提供友好的Web界面进行交互和结果展示

### 1.3 目标用户
- 个人投资者
- 股票分析师
- 量化交易研究员

---

## 2. 功能需求

### 2.1 功能一：大盘多维度分析

#### 2.1.1 大盘基础走势分析
**功能描述：**
- 获取上证指数的日K、周K、月K成交数据
- 计算技术指标（MACD、KDJ、RSI、均线等）
- 识别支撑位/压力位、关键时空节点
- 判断大盘是否存在波段做多机会或下跌风险

**输入数据：**
- 上证指数历史K线数据（日线近60天、周线近26周、月线近12个月）
- 大盘资金流向数据（使用akshare的`stock_market_fund_flow`接口）
- 市场活跃度数据（使用akshare的`stock_market_activity_legu`接口）

**输出结果：**
- 技术指标计算结果
- 趋势判定（上升/下降/震荡）
- 支撑位/压力位的具体数值
- 波段机会或风险预警
- 预期上涨/下跌点位

#### 2.1.2 大盘资金面情绪分析
**功能描述：**
- 分析大盘资金流向（主力、超大单、大单、中单、小单的净流入趋势）
- 分析市场赚钱效应（涨停/跌停家数、活跃度、上涨家数）
- 结合涨停股池数据判断市场热点板块
- 评估市场整体情绪和资金动向

**输入数据：**
- 大盘资金流向数据（每日更新）
- 市场活跃度指标
- 每日涨停股池数据（使用akshare的`stock_zt_pool_em`接口）

**输出结果：**
- 资金流向分析报告（各类资金的净流入情况）
- 市场情绪评分
- 热点板块识别（涨停个股的行业分布）
- 市场温度评估（冷/温/热）

---

### 2.2 功能二：个股多维度分析（支持多种分析模式）

**功能概述：**
根据分析目标的不同，系统支持以下多种个股分析模式。用户可通过前端指定分析模式或系统自动推荐：

#### 2.2.1 基础面技术面综合分析
**适用场景**：通用个股分析、投资决策
**功能描述**：
- 整合基本面（公司信息、财务数据）、技术面（K线指标）、市场情绪（新闻、大盘环境）
- 生成详细的分析报告和具体交易建议

**输入数据**：
- 股票代码
- 日K线数据（近30天+）
- 公司基本信息、财务指标
- 相关新闻（3-5条最新）
- 大盘近期走势、市场活跃度

**输出结果**：
- 多维度分析报告（基本面+技术面+市场情绪）
- 具体交易建议：交易方向、目标价格、止损止盈、持仓期限、风险等级

#### 2.2.2 波段交易分析
**适用场景**：中期波段操作（1-2周）
**功能描述**：
- 基于多周期（日线+周线）技术形态分析
- 识别支撑位/压力位、均线系统强弱
- 评估波段内的买入/卖出机会
- 提供仓位管理建议

**输入数据**：
- 股票代码
- 日K线数据（近60天）
- 周K线数据（近26周）
- 财务指标数据
- 大盘走势

**输出结果**：
- 趋势定位分析（支撑位/压力位的具体数值）
- 理想建仓区域
- 止损位、目标价位
- 仓位管理策略

#### 2.2.3 短线T+1分析
**适用场景**：超短线操作（1-5个交易日）
**功能描述**：
- 高频率多维度共振分析（个股vs板块vs大盘）
- 量价动能诊断、异常资金流追踪
- 舆情热度+催化剂时间窗口分析
- 精确到分的交易点位，配合量化风控

**输入数据**：
- 股票代码
- 日K线数据（近14天）
- 周K线数据（近8周）
- 最新新闻（1-4条）
- 大盘近期走势
- 市场温度计（赚钱效应）
- 所属板块走势（可选）

**输出结果**：
- 机会评级（高确定性/观望/规避风险）
- 精确交易计划（入场价位、止损、目标价位、持仓周期）
- 凯利公式计算的仓位建议
- 实时监控清单（3个关键指标）

#### 2.2.4 N+1+N涨停反包分析
**适用场景**：涨停板分析、当日反包预测
**功能描述**：
- 识别N+1+N形态（昨日涨停+今日高开低走上影）
- 量化反包概率
- 评估涨停质量（封单强弱、炸板次数、时间分布）

**输入数据**：
- 股票代码、涨停信息（封板资金、炸板次数、首尾封板时间）
- 日K线数据
- 周K线数据
- 相关新闻
- 大盘走势、市场活跃度
- 所属板块走势（可选）

**输出结果**：
- 反包概率评估
- 预期反包买卖点
- 风险提示（流动性、政策风险等）

#### 2.2.5 投机套利分析
**适用场景**：短期趋势交易、对标超短手法
**功能描述**：
- 结合日线+周线技术形态
- 分析新闻催化剂的时间窗口
- 判断个股相对强度（vs所属板块、vs大盘）
- 给出具体的套利操作方法

**输入数据**：
- 股票代码、公司基本信息
- 日K线数据（近14天）
- 周K线数据
- 最新新闻（1-2条）
- 大盘走势、市场活跃度
- 所属板块走势

**输出结果**：
- 买卖点分析
- 具体操作手法（例：先下跌到xx元再买入；或冲高卖出做T买回）
- 止损止盈点位
- 大盘回调风险评估

#### 2.2.6 公司估值分析
**适用场景**：长期投资、基本面重点关注
**功能描述**：
- 基于不同估值方法评估公司价值
- 计算潜在涨幅预期
- 分析行业格局、产能产量变化趋势

**输入数据**：
- 股票代码
- 公司基本信息
- 财务指标
- 技术指标数据
- 行业信息、竞争格局

**输出结果**：
- 公司基本面评估
- 行业发展前景分析
- 产能/产量/售价/成本分析（过去1年+未来预期）
- 估值结果、潜在涨幅预测
- 交易建议

**功能通用说明**：
- 所有模式都支持可选的板块对比参数（使用 `stock_board_concept_index_ths` 获取板块K线）
- 板块数据仅作为分析背景信息输入，前端不展示板块图表对比
- 所有交易建议数值必须具体、可执行，不使用范围描述
- 输出格式严格规范，支持系统自动解析

---

### 2.3 功能三：财经新闻爬取与机会挖掘
**功能描述：**
- 定时从财经网站爬取最新财经新闻
- 使用AI模型分析新闻内容
- 自动挖掘新闻涉及的潜在投资标的
- 给出投资建议和逻辑分析

**输入数据：**
- 财经新闻列表（标题、时间、内容摘要）

**输出结果：**
- 抓取的热门新闻列表
- AI识别的潜在投资标的（3-5只股票）
- 每只推荐股票的理由和所属行业

---

### 2.4 功能四：个股基本面与财务分析
**功能描述：**
- 获取个股公司基本信息
- 获取财务指标和变化趋势
- AI生成财务健康度评估

**输入数据：**
- 股票代码
- 公司基本信息、主营业务
- 财务指标数据（收入、利润、毛利率、ROE等）

**输出结果：**
- 公司基本信息
- 财务指标数据和同比增长情况
- 财务健康度分析报告

---

### 2.5 功能五：个股分时数据分析
**功能描述：**
- 获取个股分时数据（1分钟、5分钟、15分钟、30分钟、60分钟）
- 支持复权处理
- 计算分时级别的技术指标
- 分析盘中资金流向和价格波动

**输入数据：**
- 股票代码
- 时间周期和日期范围
- 复权类型

**输出结果：**
- 分时K线数据和技术指标
- 盘中波动分析
- 关键价格点位识别

---

### 2.6 功能六：前端界面与数据管理
**功能描述：**
- 提供Web前端界面支持多种分析模式选择
- 用户可输入股票编码和选择分析类型
- 显示分析结论详情
- 查看历史分析记录
- 查看爬取的热门新闻内容
- 查看大盘数据和涨停股池

**主要界面模块：**

1. **股票分析查询页**
   - 股票编码输入框
   - 分析模式选择（单选下拉框）：
     * 基础面技术面综合分析
     * 波段交易分析
     * 短线T+1分析
     * 涨停反包分析
     * 投机套利分析
     * 公司估值分析
   - K线类型选择（日K/周K/月K，仅在部分模式可用）
   - 板块名称输入框（可选，用于分析时的参考背景）
   - 分析按钮
   - 分析结果展示区
     - K线图和技术指标图表
     - AI分析报告（多段落结构化文本）
     - 具体交易建议（结构化数据展示）
   - 历史分析记录查看

2. **大盘分析页**
   - 大盘基础走势分析结果
   - 大盘K线走势图（日线、周线、月线）
   - 技术指标显示
   - 资金流向数据展示
   - 市场活跃度指标
   - 涨停股池展示（当日热点股票）

3. **新闻资讯页**
   - 热门财经新闻列表
   - 新闻详情查看
   - AI提取的投资建议展示

4. **涨停板页**
   - 每日涨停股票列表
   - 涨停股票详情（代码、名称、涨停价格、封板资金、炸板次数、首尾封板时间等）
   - 涨停股票所属行业分布

---

## 3. 系统架构

### 3.1 高层架构

```
┌─────────────────────────────────────────────────────────────┐
│                         前端界面层                            │
│              (股票查询 | 大盘分析 | 新闻资讯)                  │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP/REST API
┌───────────────────────▼─────────────────────────────────────┐
│                        后端服务层                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  API网关服务  │  │  业务逻辑层   │  │  数据处理层   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  数据存储层   │ │  外部服务层   │ │  AI分析层     │
│  ┌────────┐  │ │ ┌──────────┐ │ │ ┌──────────┐ │
│  │ MySQL  │  │ │ │新浪财经  │ │ │ │ LLM API  │ │
│  └────────┘  │ │ └──────────┘ │ │ └──────────┘ │
│  ┌────────┐  │ │ ┌──────────┐ │ │ ┌──────────┐ │
│  │ Redis  │  │ │ │股票数据源│ │ │ │提示词模板 │ │
│  └────────┘  │ │ └──────────┘ │ │ └──────────┘ │
└──────────────┘ └──────────────┘ └──────────────┘
```

### 3.2 组件说明

**前端组件：**
- 用户界面组件（股票查询、大盘展示、新闻列表）
- 图表可视化组件（K线图、技术指标图）
- 响应式布局组件

**后端服务：**
- API网关：统一入口，路由分发
- 业务逻辑服务：核心业务处理
- 数据采集服务：定时任务调度
- AI分析服务：与大模型交互

**数据层：**
- MySQL：持久化存储分析历史、新闻数据
- Redis：缓存热点数据、会话管理

 **外部集成：**
 - akshare库：获取股票数据、K线数据、财务指标、涨停股池、资金流向等；同时可通过 `stock_news_em` 等接口获取个股相关新闻（示例：`ak.stock_news_em(symbol="603777")`），akshare 接口返回 `pd.DataFrame` 或 `pd.Series`。
 - 财经网站API：获取新闻资讯
- LLM服务：AI分析能力（如OpenAI、通义千问、文心一言、智谱GLM等）

---

## 4. 技术栈推荐

### 4.1 后端技术栈
- **框架**: Python FastAPI / Flask
- **理由**: 
  - Python在数据处理和AI领域生态丰富
  - FastAPI高性能、自动生成API文档
  - 易于集成pandas、numpy等数据处理库

### 4.2 前端技术栈
- **框架**: React.js / Vue.js 3
- **理由**: 
  - 组件化开发，维护性好
  - 丰富的图表库支持（ECharts、Recharts）
  - 响应式设计，移动端友好

### 4.3 数据库
- **关系型数据库**: MySQL 8.0
  - 存储用户数据、分析历史、新闻记录
- **缓存数据库**: Redis 7.0
  - 缓存热门股票数据、实时行情
  - 会话管理

### 4.4 数据采集与处理
- **数据源库**: akshare - 获取股票K线、财务指标、涨停股池、资金流向、市场活跃度等数据
- **HTTP请求**: requests / httpx
- **网页爬虫**: BeautifulSoup4 / Scrapy
- **数据解析**: lxml
- **数值计算**: NumPy, pandas
- **技术指标计算**: TA-Lib / pandas-ta

### 4.5 AI/LLM集成
- **LLM SDK**: LangChain / OpenAI SDK
- **支持的模型**: 
  - OpenAI GPT-4/GPT-3.5
  - 阿里通义千问
  - 百度文心一言
  - 智谱AI GLM

### 4.6 定时任务
- **任务调度**: APScheduler / Celery + Redis
- **理由**: 
  - 定时爬取新闻
  - 定时更新股票数据
  - 后台异步处理

### 4.7 部署与运维
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx
- **日志**: Python logging + ELK Stack
- **监控**: Prometheus + Grafana

---

## 5. 数据库设计

### 5.1 数据表结构

#### 5.1.1 股票基本信息表 (stock_info)
```sql
CREATE TABLE stock_info (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    stock_name VARCHAR(50) NOT NULL COMMENT '股票名称',
    exchange VARCHAR(10) NOT NULL COMMENT '交易所: SH/SZ',
    industry VARCHAR(50) COMMENT '所属行业',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_code (stock_code)
) COMMENT='股票基本信息表';
```

#### 5.1.2 K线数据表 (stock_kline_data)
```sql
CREATE TABLE stock_kline_data (
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
    UNIQUE KEY uk_stock_kline (stock_code, kline_type, trade_date),
    INDEX idx_trade_date (trade_date)
) COMMENT='K线数据表';
```

#### 5.1.3 技术指标数据表 (stock_indicators)
```sql
CREATE TABLE stock_indicators (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    indicator_type VARCHAR(20) NOT NULL COMMENT '指标类型: MACD/KDJ等',
    kline_type ENUM('day', 'week', 'month') NOT NULL,
    trade_date DATE NOT NULL,
    indicator_data JSON NOT NULL COMMENT '指标数值(JSON格式)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_indicator (stock_code, indicator_type, kline_type, trade_date)
) COMMENT='技术指标数据表';
```

#### 5.1.4 分析历史记录表 (analysis_history)
```sql
CREATE TABLE analysis_history (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    analysis_type ENUM('index', 'stock') NOT NULL COMMENT '分析类型',
    analysis_time TIMESTAMP NOT NULL COMMENT '分析时间',
    kline_type ENUM('day', 'week', 'month') NOT NULL,
    input_data JSON COMMENT '输入数据摘要',
    analysis_result TEXT COMMENT 'AI分析结果',
    sentiment_score DECIMAL(3,2) COMMENT '情绪得分',
    recommendation VARCHAR(20) COMMENT '建议: 买入/持有/卖出',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_stock_time (stock_code, analysis_time)
) COMMENT='分析历史记录表';
```

#### 5.1.5 财经新闻表 (financial_news)
```sql
CREATE TABLE financial_news (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(500) NOT NULL COMMENT '新闻标题',
    content TEXT COMMENT '新闻内容',
    source VARCHAR(50) COMMENT '来源',
    url VARCHAR(500) COMMENT '新闻链接',
    publish_time TIMESTAMP COMMENT '发布时间',
    crawl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '抓取时间',
    related_stocks JSON COMMENT '相关股票代码列表',
    investment_advice TEXT COMMENT 'AI投资建议',
    INDEX idx_publish_time (publish_time)
) COMMENT='财经新闻表';
```

#### 5.1.6 大盘情绪数据表 (market_sentiment)
```sql
CREATE TABLE market_sentiment (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    trade_date DATE NOT NULL,
    index_code VARCHAR(10) DEFAULT '000001' COMMENT '指数代码',
    sentiment_score DECIMAL(3,2) COMMENT '情绪得分(0-100)',
    bull_bear_ratio DECIMAL(5,2) COMMENT '多空比例',
    rise_fall_count JSON COMMENT '涨跌家数',
    volume_ratio DECIMAL(5,2) COMMENT '量比',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_date (trade_date)
) COMMENT='大盘情绪数据表';
```

#### 5.1.7 板块K线数据表 (sector_kline_data)
```sql
CREATE TABLE sector_kline_data (
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
    INDEX idx_trade_date (trade_date)
) COMMENT='板块K线数据表';
```

#### 5.1.8 板块技术指标数据表 (sector_indicators)
```sql
CREATE TABLE sector_indicators (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    sector_code VARCHAR(20) NOT NULL COMMENT '板块代码',
    indicator_type VARCHAR(20) NOT NULL COMMENT '指标类型: MACD/KDJ等',
    kline_type ENUM('day', 'week', 'month') NOT NULL,
    trade_date DATE NOT NULL,
    indicator_data JSON NOT NULL COMMENT '指标数值(JSON格式)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_indicator (sector_code, indicator_type, kline_type, trade_date)
) COMMENT='板块技术指标数据表';
```

#### 5.1.9 个股公司详细信息表 (stock_company_detail)
```sql
CREATE TABLE stock_company_detail (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    stock_name VARCHAR(100) COMMENT '股票名称',
    short_name VARCHAR(100) COMMENT '公司简称',
    main_business TEXT COMMENT '主营业务',
    industry VARCHAR(100) COMMENT '所属行业',
    region VARCHAR(50) COMMENT '所属地区',
    company_intro TEXT COMMENT '公司简介',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_code (stock_code)
) COMMENT='个股公司详细信息表 - 使用akshare stock_individual_basic_info_xq接口';
```


#### 5.1.10 大盘资金流向数据表 (market_fund_flow)
```sql
CREATE TABLE market_fund_flow (
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
    UNIQUE KEY uk_trade_date (trade_date)
) COMMENT='大盘资金流向数据表 - 使用akshare stock_market_fund_flow接口';
```

#### 5.1.11 市场活跃度数据表 (market_activity)
```sql
CREATE TABLE market_activity (
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
    UNIQUE KEY uk_trade_date (trade_date)
) COMMENT='市场活跃度数据表 - 使用akshare stock_market_activity_legu接口';
```

#### 5.1.12 涨停股池数据表 (limit_up_stock_pool)
```sql
CREATE TABLE limit_up_stock_pool (
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
    INDEX idx_industry (industry)
) COMMENT='涨停股池数据表 - 使用akshare stock_zt_pool_em接口';
```

#### 5.1.13 个股分时数据表 (stock_intraday_data)
```sql
CREATE TABLE stock_intraday_data (
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
    INDEX idx_trade_date (trade_date)
) COMMENT='个股分时数据表 - 使用akshare stock_zh_a_hist_min_em接口';
```

#### 5.1.14 概念板块指数数据表 (concept_sector_index)
```sql
CREATE TABLE concept_sector_index (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    sector_name VARCHAR(100) NOT NULL COMMENT '概念板块名称',
    trade_date DATE NOT NULL COMMENT '交易日期',
    open_price DECIMAL(10,2) COMMENT '开盘价',
    high_price DECIMAL(10,2) COMMENT '最高价',
    low_price DECIMAL(10,2) COMMENT '最低价',
    close_price DECIMAL(10,2) COMMENT '收盘价',
    volume BIGINT COMMENT '成交量',
    turnover_amount DECIMAL(20,2) COMMENT '成交额',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_sector_date (sector_name, trade_date),
    INDEX idx_trade_date (trade_date)
) COMMENT='概念板块指数数据表 - 使用akshare stock_board_concept_index_ths接口';
```

### 5.2 数据库索引策略
- 股票代码、交易日期建立复合索引
- 新闻发布时间建立索引，支持快速查询
- 分析历史按股票和时间建立索引
- 板块代码建立索引，支持快速查询股票所属板块
- 股票板块关联表建立双向索引，提高查询效率

---

## 6. API设计

### 6.1 API接口规范
- **协议**: HTTPS
- **格式**: RESTful
- **数据格式**: JSON
- **认证**: JWT Token (可选)

### 6.2 核心API接口

#### 6.2.1 股票分析相关

**POST /api/analyze/stock**
- **描述**: 分析指定股票
- **请求参数**:
  ```json
  {
    "stock_code": "600000",
    "kline_type": "day",
    "sector_names": ["银行板块", "金融科技"],
    "include_news": true
  }
  ```
  说明：sector_names为可选字段，不输入时仅分析个股
- **响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "stock_info": {...},
      "stock_kline_data": [...],
      "stock_indicators": {
        "macd": [...],
        "kdj": [...]
      },
      "analysis_result": "...",
      "recommendation": "买入",
      "sentiment_score": 75.5
    }
  }
  ```

**GET /api/analyze/history**
- **描述**: 查询股票历史分析记录
- **请求参数**: stock_code, page, page_size
- **响应**: 分页的历史分析记录列表

**POST /api/analyze/index**
- **描述**: 分析上证指数
- **请求参数**: kline_type
- **响应**: 指数分析结果

#### 6.2.2 数据查询相关

**GET /api/stock/{code}/kline**
- **描述**: 获取股票K线数据
- **请求参数**: type (day/week/month), start_date, end_date
- **响应**: K线数据数组

**GET /api/stock/{code}/indicators**
- **描述**: 获取技术指标
- **请求参数**: type, indicator_names
- **响应**: 技术指标数据


#### 6.2.3 新闻相关

**GET /api/news/latest**
- **描述**: 获取最新财经新闻
- **请求参数**: limit, page
- **响应**: 新闻列表

**GET /api/news/{id}**
- **描述**: 获取新闻详情
- **响应**: 新闻完整内容及投资建议

**POST /api/news/crawl**
- **描述**: 触发新闻爬取任务（管理员）
- **响应**: 任务ID

#### 6.2.4 大盘数据相关

**GET /api/market/sentiment**
- **描述**: 获取大盘情绪数据
- **请求参数**: date
- **响应**: 情绪数据

**GET /api/market/index-data**
- **描述**: 获取上证指数数据
- **请求参数**: type, start_date, end_date
- **响应**: 指数K线数据

**GET /api/market/fund-flow**
- **描述**: 获取大盘资金流向历史数据
- **请求参数**: start_date, end_date
- **响应**: 资金流向数据（使用akshare stock_market_fund_flow接口）

**GET /api/market/activity**
- **描述**: 获取市场活跃度数据
- **请求参数**: date
- **响应**: 市场活跃度指标（使用akshare stock_market_activity_legu接口）

#### 6.2.5 涨停股池相关

**GET /api/market/limit-up**
- **描述**: 获取指定日期的涨停股池
- **请求参数**: date (格式: '20241008')
- **响应**: 涨停股票列表
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "trade_date": "2024-10-08",
      "stocks": [
        {
          "stock_code": "600000",
          "stock_name": "股票名称",
          "change_pct": 10.0,
          "latest_price": 10.00,
          "turnover_amount": 1000000000,
          "first_limit_time": "09:30:00",
          "last_limit_time": "09:30:00",
          "burst_count": 0,
          "continuous_limit_count": 1,
          "industry": "银行"
        }
      ]
    }
  }
  ```

#### 6.2.6 个股基本信息相关

**GET /api/stock/{code}/company-info**
- **描述**: 获取公司基本信息
- **请求参数**: 无
- **响应**: 公司详细信息（使用akshare stock_individual_basic_info_xq接口）
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "stock_code": "SH601127",
      "stock_name": "赛力斯",
      "short_name": "赛力斯",
      "main_business": "新能源汽车及核心三电(电池、电驱、电控)、传统汽车及核心部件总成的研发、制造、销售及服务。"
    }
  }
  ```


#### 6.2.7 分时数据相关

**GET /api/stock/{code}/intraday**
- **描述**: 获取个股分时数据
- **请求参数**: 
  - period (1/5/15/30/60分钟)
  - start_date (格式: "2024-03-20 09:30:00")
  - end_date (格式: "2024-03-20 15:00:00")
  - adjust (不复权/qfq/hfq)
- **响应**: 分时K线数据（使用akshare stock_zh_a_hist_min_em接口）


### 6.3 错误码定义
- 200: 成功
- 400: 请求参数错误
- 401: 未授权
- 404: 资源不存在
- 500: 服务器内部错误

---

## 7. 模块设计

### 7.1 数据采集模块 (Data Collection Module)

**功能职责:**
- 使用akshare获取股票实时和历史数据
- 获取公司基本信息、财务指标
- 获取大盘资金流向和市场活跃度数据
- 获取涨停股池数据
- 获取概念板块数据
- 爬取财经新闻
- 定时任务调度
- 数据清洗和验证

**核心类:**
```python
import akshare as ak

class StockDataFetcher:
    """股票数据获取器 - 基于akshare"""
    def fetch_kline_data(code, kline_type, start_date, end_date):
        """获取K线数据 - 使用stock_zh_a_hist接口"""
        return ak.stock_zh_a_hist(
            symbol=code,
            period=kline_type,
            start_date=start_date,
            end_date=end_date
        )
    
    def fetch_intraday_data(code, period, start_date, end_date, adjust=''):
        """获取分时数据 - 使用stock_zh_a_hist_min_em接口"""
        return ak.stock_zh_a_hist_min_em(
            symbol=code,
            start_date=start_date,
            end_date=end_date,
            period=str(period),
            adjust=adjust
        )
    
    def fetch_company_info(self, code):
        """获取公司基本信息 - 使用stock_individual_basic_info_xq接口"""
        return ak.stock_individual_basic_info_xq(symbol=code)
    
    def fetch_financial_indicators(self, code, indicator='按报告期'):
        """获取财务指标 - 使用stock_financial_abstract_new_ths接口"""
        return ak.stock_financial_abstract_new_ths(
            symbol=code,
            indicator=indicator
        )

class MarketDataFetcher:
    """大盘数据获取器 - 基于akshare"""
    def fetch_fund_flow(self):
        """获取大盘资金流向 - 使用stock_market_fund_flow接口"""
        return ak.stock_market_fund_flow()
    
    def fetch_market_activity(self):
        """获取市场活跃度 - 使用stock_market_activity_legu接口"""
        return ak.stock_market_activity_legu()

class LimitUpStockFetcher:
    """涨停股池获取器 - 基于akshare"""
    def fetch_limit_up_pool(self, date):
        """获取涨停股池 - 使用stock_zt_pool_em接口"""
        return ak.stock_zt_pool_em(date=date)

class SectorDataFetcher:
    """板块数据获取器 - 基于akshare"""
    def fetch_concept_sector_index(self, symbol, start_date, end_date):
        """获取概念板块指数 - 使用stock_board_concept_index_ths接口"""
        return ak.stock_board_concept_index_ths(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )

class NewsCrawler:
    """新闻爬虫"""
    def crawl_sina_news(limit=20)
    def extract_news_content(url)

class Scheduler:
    """任务调度器"""
    def schedule_data_update()
    def schedule_news_crawl()
    def schedule_sector_data_update()
```

### 7.2 技术指标计算模块 (Technical Indicators Module)

**功能职责:**
- 计算MACD指标
- 计算KDJ指标
- 支持自定义指标扩展

**核心算法:**
```python
class IndicatorCalculator:
    """技术指标计算器"""
    def calculate_macd(prices, short=12, long=26, signal=9)
    def calculate_kdj(highs, lows, closes, n=9, m1=3, m2=3)
    def calculate_rsi(prices, period=14)
    def calculate_ma(prices, period)
```

**MACD计算公式:**
- EMA(12) = 12日指数移动平均
- EMA(26) = 26日指数移动平均
- DIF = EMA(12) - EMA(26)
- DEA = DIF的9日指数移动平均
- MACD = (DIF - DEA) × 2

**KDJ计算公式:**
- RSV = (今日收盘价 - N日内最低价) / (N日内最高价 - N日内最低价) × 100
- K = M1日RSV平滑移动平均
- D = M2日K平滑移动平均
- J = 3K - 2D

### 7.3 AI分析模块 (AI Analysis Module)

**功能职责:**
- 构建分析提示词
- 调用LLM API
- 解析分析结果
- 管理提示词模板

**核心类:**
```python
class AIAnalyzer:
    """AI分析引擎"""
    def analyze_stock(stock_data, indicators, news, template)
    def analyze_index(index_data, indicators, sentiment, template)
    def analyze_news(news_content, template)

class PromptTemplateManager:
    """提示词模板管理"""
    def get_template(template_name)
    def render_template(template, context)
```

**提示词模板示例:**

**大盘分析模板:**
```
你是一位专业的股票分析师。请根据以下数据分析上证指数的后期走势:

【K线数据】
{index_kline_data}

【技术指标】
MACD: {macd_data}
KDJ: {kdj_data}

【市场情绪】
情绪得分: {sentiment_score}
涨跌家数: {rise_fall_data}

请从以下维度进行分析:
1. 技术面分析（MACD、KDJ指标解读）
2. 市场情绪分析
3. 趋势判断（短期、中期、长期）
4. 关键支撑位和压力位
5. 投资建议（看多/看空/震荡，并说明理由）

请给出简洁、专业的分析结论。
```

**个股分析模板:**
```
你是一位专业的股票分析师。请根据以下数据分析该股票的投资价值:

【股票基本信息】
代码: {stock_code}
名称: {stock_name}

【个股K线数据】
{stock_kline_data}

【个股技术指标】
MACD: {stock_macd_data}
KDJ: {stock_kdj_data}

【所属板块k线数据】
该股票所属板块:
{sector_kline_data}

【相关新闻】
{related_news}

【大盘环境】
{index_analysis}

请从以下维度进行分析:
1. 技术面分析（个股指标信号、趋势判断）
2. 基本面信息（结合新闻）
3. 相对大盘表现
4. 风险评估
5. 投资建议（买入/持有/卖出/观望，目标价位）

请给出专业、客观的分析结论（板块信息仅作为背景输入，不单独输出板块对比或板块分析视图）。
```

### 7.4 Web服务模块 (Web Service Module)

**功能职责:**
- 提供RESTful API
- 请求参数验证
- 业务逻辑编排
- 响应格式化

**核心类:**
```python
# FastAPI应用示例
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.post("/api/analyze/stock")
async def analyze_stock(request: StockAnalysisRequest):
    # 参数验证
    if not validate_stock_code(request.stock_code):
        raise HTTPException(status_code=400, detail="Invalid stock code")
    
    # 数据获取
    kline_data = data_fetcher.fetch_kline_data(...)
    indicators = calculator.calculate_all(...)
    news = news_crawler.get_stock_news(...)
    
    # AI分析
    result = ai_analyzer.analyze_stock(...)
    
    # 保存历史
    db.save_analysis_history(...)
    
    return {"code": 200, "data": result}
```

### 7.5 前端模块 (Frontend Module)

**技术选型**: React + TypeScript

**页面结构:**
```
src/
├── pages/
│   ├── StockAnalysis/      # 股票分析页
│   ├── IndexAnalysis/      # 大盘分析页
│   └── NewsCenter/         # 新闻中心页
├── components/
│   ├── StockInput/         # 股票输入组件
│   ├── KLineChart/         # K线图表组件
│   ├── IndicatorDisplay/   # 指标展示组件
│   └── NewsList/           # 新闻列表组件
├── services/
│   └── api.ts              # API调用封装
└── hooks/
    └── useAnalysis.ts      # 分析相关Hook
```

**核心组件示例:**

**股票分析页面组件:**
```jsx
function StockAnalysisPage() {
  const [stockCode, setStockCode] = useState('');
  const [klineType, setKlineType] = useState('day');
  const [sectorNames, setSectorNames] = useState(''); // 板块名称，可选
  const [analysisResult, setAnalysisResult] = useState(null);
  const [historyList, setHistoryList] = useState([]);
  
  const handleAnalyze = async () => {
    // 解析板块名称（支持逗号分隔的多个板块）
    const sectorList = sectorNames ? sectorNames.split(',').map(s => s.trim()) : [];
    
    const result = await analyzeStock({
      stock_code: stockCode,
      kline_type: klineType,
      sector_names: sectorList,
      include_news: true
    });
    setAnalysisResult(result);
    await loadHistory(stockCode);
  };
  
  return (
    <div>
      <StockInput 
        value={stockCode} 
        onChange={setStockCode}
        onAnalyze={handleAnalyze}
      />
      
      {/* K线类型选择 */}
      <KlineTypeSelector 
        value={klineType}
        onChange={setKlineType}
        options={[
          { value: 'day', label: '日K' },
          { value: 'week', label: '周K' },
          { value: 'month', label: '月K' }
        ]}
      />
      
      {/* 板块名称输入框（可选） */}
      <SectorNameInput 
        value={sectorNames}
        onChange={setSectorNames}
        placeholder="输入板块名称（可选），多个板块用逗号分隔，如：银行板块,金融科技"
      />
      
      {analysisResult && (
        <>

          {/* 个股K线图和技术指标 */}
          <KLineChart data={analysisResult.stock_kline_data} />
          <IndicatorDisplay indicators={analysisResult.stock_indicators} />
          
          {/* AI分析结果 */}
          <AnalysisResult content={analysisResult.analysis_result} />
        </>
      )}
      <HistoryList items={historyList} />
    </div>
  );
}
```

### 7.6 数据持久化模块 (Database Module)
```

### 7.6 数据持久化模块 (Database Module)

**功能职责:**
- 数据库连接管理
- CRUD操作封装
- 事务管理
- 数据缓存

**核心类:**
```python
class DatabaseManager:
    """数据库管理器"""
    def __init__(self, db_url)
    def get_session()
    def close_session()

class StockRepository:
    """股票数据仓库"""
    def save_stock_info(stock_info)
    def save_kline_data(kline_data)
    def get_kline_data(code, kline_type, start_date, end_date)
    def get_analysis_history(code, page, page_size)

class NewsRepository:
    """新闻数据仓库"""
    def save_news(news_list)
    def get_latest_news(limit, page)
    def get_news_by_id(id)
```

---

## 8. 关键实现细节

### 8.1 技术指标计算实现

**MACD计算示例:**
```python
import pandas as pd
import numpy as np

def calculate_macd(prices, short=12, long=26, signal=9):
    """
    计算MACD指标
    :param prices: 收盘价序列
    :param short: 短期EMA周期
    :param long: 长期EMA周期
    :param signal: 信号线周期
    :return: dict {dif, dea, macd}
    """
    df = pd.DataFrame({'close': prices})
    
    # 计算EMA
    df['ema_short'] = df['close'].ewm(span=short, adjust=False).mean()
    df['ema_long'] = df['close'].ewm(span=long, adjust=False).mean()
    
    # 计算DIF和DEA
    df['dif'] = df['ema_short'] - df['ema_long']
    df['dea'] = df['dif'].ewm(span=signal, adjust=False).mean()
    
    # 计算MACD柱状图
    df['macd'] = 2 * (df['dif'] - df['dea'])
    
    return {
        'dif': df['dif'].tolist(),
        'dea': df['dea'].tolist(),
        'macd': df['macd'].tolist()
    }
```

**KDJ计算示例:**
```python
def calculate_kdj(highs, lows, closes, n=9, m1=3, m2=3):
    """
    计算KDJ指标
    :param highs: 最高价序列
    :param lows: 最低价序列
    :param closes: 收盘价序列
    :param n: RSV周期
    :param m1: K值平滑周期
    :param m2: D值平滑周期
    :return: dict {k, d, j}
    """
    df = pd.DataFrame({
        'high': highs,
        'low': lows,
        'close': closes
    })
    
    # 计算RSV
    low_list = df['low'].rolling(window=n, min_periods=1).min()
    high_list = df['high'].rolling(window=n, min_periods=1).max()
    rsv = (df['close'] - low_list) / (high_list - low_list) * 100
    
    # 计算K、D、J值
    df['k'] = rsv.ewm(com=m1-1, adjust=False).mean()
    df['d'] = df['k'].ewm(com=m2-1, adjust=False).mean()
    df['j'] = 3 * df['k'] - 2 * df['d']
    
    return {
        'k': df['k'].tolist(),
        'd': df['d'].tolist(),
        'j': df['j'].tolist()
    }
```

### 8.2 大盘情绪数据获取

**使用akshare获取市场活跃度数据:**
```python
import akshare as ak
import pandas as pd

class MarketDataFetcher:
    """市场数据获取器"""
    
    def fetch_market_activity(self):
        """获取市场活跃度 - 使用stock_market_activity_legu接口"""
        try:
            df = ak.stock_market_activity_legu()
            # 转换为字典格式
            activity_data = df.set_index('item')['value'].to_dict()
            
            return {
                'rise_count': int(activity_data.get('上涨', 0)),
                'limit_up_count': int(activity_data.get('涨停', 0)),
                'real_limit_up_count': int(activity_data.get('真实涨停', 0)),
                'st_limit_up_count': int(activity_data.get('st st*涨停', 0)),
                'fall_count': int(activity_data.get('下跌', 0)),
                'limit_down_count': int(activity_data.get('跌停', 0)),
                'real_limit_down_count': int(activity_data.get('真实跌停', 0)),
                'st_limit_down_count': int(activity_data.get('st st*跌停', 0)),
                'flat_count': int(activity_data.get('平盘', 0)),
                'suspend_count': int(activity_data.get('停牌', 0)),
                'activity_level': activity_data.get('活跃度', ''),
                'stat_time': activity_data.get('统计日期', '')
            }
        except Exception as e:
            print(f"获取市场活跃度失败: {e}")
            return None
    
    def fetch_fund_flow(self):
        """获取大盘资金流向 - 使用stock_market_fund_flow接口"""
        try:
            df = ak.stock_market_fund_flow()
            # 获取最新一天的数据
            latest_data = df.iloc[0]
            
            return {
                'trade_date': latest_data.get('日期', ''),
                'sh_close_price': latest_data.get('上证-收盘价', 0),
                'sh_change_pct': latest_data.get('上证-涨跌幅', 0),
                'sz_close_price': latest_data.get('深证-收盘价', 0),
                'sz_change_pct': latest_data.get('深证-涨跌幅', 0),
                'main_net_inflow': latest_data.get('主力净流入-净额', 0),
                'main_net_inflow_ratio': latest_data.get('主力净流入-净占比', 0),
                'super_large_net_inflow': latest_data.get('超大单净流入-净额', 0),
                'super_large_net_inflow_ratio': latest_data.get('超大单净流入-净占比', 0),
                'large_net_inflow': latest_data.get('大单净流入-净额', 0),
                'large_net_inflow_ratio': latest_data.get('大单净流入-净占比', 0),
                'medium_net_inflow': latest_data.get('中单净流入-净额', 0),
                'medium_net_inflow_ratio': latest_data.get('中单净流入-净占比', 0),
                'small_net_inflow': latest_data.get('小单净流入-净额', 0),
                'small_net_inflow_ratio': latest_data.get('小单净流入-净占比', 0)
            }
        except Exception as e:
            print(f"获取资金流向失败: {e}")
            return None
```

**情绪指标计算:**
```python
def calculate_market_sentiment():
    """
    计算大盘情绪指标
    """
    # 获取涨跌家数
    df = ak.stock_market_activity_legu()
    # 转换为字典格式
    activity_data = df.set_index('item')['value'].to_dict()
    
    # 计算情绪得分
    total_stocks = int(activity_data.get('上涨', 0)) + int(activity_data.get('下跌', 0)) + int(activity_data.get('平盘', 0))
    sentiment_score = (int(activity_data.get('上涨', 0)) / total_stocks) * 100
    
    # 计算多空比例
    bull_bear_ratio = int(activity_data.get('下跌', 0)) / (int(activity_data.get('下跌', 0)) + 1)
    
    # 获取量比
    volume_ratio = get_volume_ratio()
    
    return {
        'sentiment_score': round(sentiment_score, 2),
        'bull_bear_ratio': round(bull_bear_ratio, 2),
        'rise_fall_count': rise_fall,
        'volume_ratio': volume_ratio
    }
```

**股票数据获取示例 - 使用akshare:**
```python
import akshare as ak

class StockDataFetcher:
    """股票数据获取器"""
    
    def fetch_kline_data(self, code, kline_type='daily', start_date='20200101', end_date='20241231', adjust=''):
        """
        获取K线数据 - 使用stock_zh_a_hist接口
        :param code: 股票代码，如 '000001'
        :param kline_type: 周期类型 'daily'/'weekly'/'monthly'
        :param start_date: 开始日期，格式 '20200101'
        :param end_date: 结束日期，格式 '20241231'
        :param adjust: 复权类型 ''/'qfq'/'hfq'
        :return: DataFrame
        """
        try:
            df = ak.stock_zh_a_hist(
                symbol=code,
                period=kline_type,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )
            return df
        except Exception as e:
            print(f"获取K线数据失败: {e}")
            return None
    
    def fetch_company_info(self, code):
        """
        获取公司基本信息 - 使用stock_individual_basic_info_xq接口
        :param code: 股票代码，如 'SH601127'
        :return: dict
        """
        try:
            df = ak.stock_individual_basic_info_xq(symbol=code)
            # 转换为字典格式
            company_info = df.set_index('item')['value'].to_dict()
            
            return {
                'stock_code': code,
                'short_name': company_info.get('org_short_name_cn', ''),
                'main_business': company_info.get('main_operation_business', ''),
                'company_intro': company_info.get('org_short_name_cn', ''),
            }
        except Exception as e:
            print(f"获取公司信息失败: {e}")
            return None
    
    def fetch_financial_indicators(self, code, indicator='按报告期'):
        """
        获取财务指标 - 使用stock_financial_abstract_new_ths接口
        :param code: 股票代码，如 '000063'
        :param indicator: 指标类型 '按报告期'/'一季度'/'二季度'/'三季度'/'四季度'/'按年度'
        :return: DataFrame
        """
        try:
            df = ak.stock_financial_abstract_new_ths(
                symbol=code,
                indicator=indicator
            )
            return df
        except Exception as e:
            print(f"获取财务指标失败: {e}")
            return None
    
    def fetch_intraday_data(self, code, period='5', start_date='2024-03-20 09:30:00', 
                           end_date='2024-03-20 15:00:00', adjust=''):
        """
        获取分时数据 - 使用stock_zh_a_hist_min_em接口
        :param code: 股票代码，如 '000001'
        :param period: 周期 '1'/'5'/'15'/'30'/'60'
        :param start_date: 开始时间，格式 '2024-03-20 09:30:00'
        :param end_date: 结束时间，格式 '2024-03-20 15:00:00'
        :param adjust: 复权类型 ''/'qfq'/'hfq'
        :return: DataFrame
        """
        try:
            df = ak.stock_zh_a_hist_min_em(
                symbol=code,
                start_date=start_date,
                end_date=end_date,
                period=period,
                adjust=adjust
            )
            return df
        except Exception as e:
            print(f"获取分时数据失败: {e}")
            return None


class LimitUpStockFetcher:
    """涨停股池获取器"""
    
    def fetch_limit_up_pool(self, date='20241008'):
        """
        获取涨停股池 - 使用stock_zt_pool_em接口
        :param date: 日期，格式 '20241008'
        :return: DataFrame
        """
        try:
            df = ak.stock_zt_pool_em(date=date)
            return df
        except Exception as e:
            print(f"获取涨停股池失败: {e}")
            return None
    
    def analyze_limit_up_pool(self, date):
        """
        分析涨停股池
        :param date: 日期
        :return: 分析结果
        """
        df = self.fetch_limit_up_pool(date)
        if df is None or df.empty:
            return None
        
        # 分析行业分布
        industry_stats = df['所属行业'].value_counts().to_dict()
        
        # 分析连板情况
        continuous_stats = df['连板数'].value_counts().sort_index().to_dict()
        
        return {
            'total_count': len(df),
            'industry_distribution': industry_stats,
            'continuous_limit_stats': continuous_stats,
            'avg_turnover_rate': df['换手率'].mean(),
            'avg_market_value': df['总市值'].mean()
        }


class SectorDataFetcher:
    """板块数据获取器"""
    
    def fetch_concept_sector_index(self, symbol, start_date='20200101', end_date='20250228'):
        """
        获取概念板块指数 - 使用stock_board_concept_index_ths接口
        :param symbol: 概念板块名称，如 '阿里巴巴概念'
        :param start_date: 开始日期，格式 '20200101'
        :param end_date: 结束日期，格式 '20250228'
        :return: DataFrame
        """
        try:
            df = ak.stock_board_concept_index_ths(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            return df
        except Exception as e:
            print(f"获取概念板块指数失败: {e}")
            return None
```

### 8.3 新闻爬虫实现
**新浪财经新闻爬取示例:**
```python
import requests
from bs4 import BeautifulSoup
from datetime import datetime

class SinaNewsCrawler:
    """新浪财经新闻爬虫"""
    
    BASE_URL = "https://finance.sina.com.cn"
    
    def crawl_latest_news(self, limit=20):
        """
        爬取最新财经新闻
        :param limit: 爬取数量
        :return: 新闻列表
        """
        url = f"{self.BASE_URL}/roll/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_list = []
        news_items = soup.select('.feed-card-item')[:limit]
        
        for item in news_items:
            title_elem = item.select_one('.feed-card-title')
            time_elem = item.select_one('.feed-card-time')
            link_elem = item.select_one('a')
            
            if title_elem and link_elem:
                news = {
                    'title': title_elem.text.strip(),
                    'url': link_elem.get('href', ''),
                    'publish_time': self._parse_time(time_elem.text) if time_elem else None,
                    'source': '新浪财经'
                }
                
                # 获取新闻详情
                news['content'] = self._fetch_news_content(news['url'])
                news['crawl_time'] = datetime.now()
                
                news_list.append(news)
        
        return news_list
    
    def _fetch_news_content(self, url):
        """获取新闻详细内容"""
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            content_elem = soup.select_one('.article-content')
            return content_elem.text.strip() if content_elem else ""
        except Exception as e:
            print(f"获取新闻内容失败: {e}")
            return ""
    
    def _parse_time(self, time_str):
        """解析时间字符串"""
        # 实现时间解析逻辑
        pass
```

### 8.4 LLM集成实现

**使用LangChain集成LLM:**
```python
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

class AIAnalysisEngine:
    """AI分析引擎"""
    
    def __init__(self, api_key, model_name="gpt-3.5-turbo"):
        self.llm = OpenAI(
            openai_api_key=api_key,
            model_name=model_name,
            temperature=0.7,
            max_tokens=2000
        )
    
    def analyze_stock(self, stock_data, indicators, news, template_path):
        """
        股票AI分析
        """
        # 读取模板
        template = self._load_template(template_path)
        
        # 构建提示词
        prompt = PromptTemplate(
            input_variables=["stock_code", "stock_name", "kline_data", 
                           "macd_data", "kdj_data", "news", "index_analysis"],
            template=template
        )
        
        # 创建链
        chain = LLMChain(llm=self.llm, prompt=prompt)
        
        # 执行分析
        result = chain.run(
            stock_code=stock_data['code'],
            stock_name=stock_data['name'],
            kline_data=self._format_kline_data(stock_data['kline']),
            macd_data=self._format_indicators(indicators['macd']),
            kdj_data=self._format_indicators(indicators['kdj']),
            news=self._format_news(news),
            index_analysis=stock_data['index_analysis']
        )
        
        return result
    
    def _load_template(self, template_path):
        """加载提示词模板"""
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _format_kline_data(self, kline_data):
        """格式化K线数据"""
        # 实现数据格式化逻辑
        pass
    
    def _format_indicators(self, indicators):
        """格式化指标数据"""
        pass
    
    def _format_news(self, news):
        """格式化新闻数据"""
        pass
```

### 8.5 错误处理与数据验证

**数据验证装饰器:**
```python
from functools import wraps
from fastapi import HTTPException

def validate_stock_code(func):
    """股票代码验证装饰器"""
    @wraps(func)
    def wrapper(stock_code, *args, **kwargs):
        # 验证股票代码格式
        if not stock_code or len(stock_code) != 6 or not stock_code.isdigit():
            raise HTTPException(
                status_code=400,
                detail="股票代码格式错误，应为6位数字"
            )
        
        # 验证交易所
        if stock_code.startswith('6'):
            exchange = 'SH'
        elif stock_code.startswith(('0', '3')):
            exchange = 'SZ'
        else:
            raise HTTPException(
                status_code=400,
                detail="不支持的股票代码"
            )
        
        return func(stock_code, exchange, *args, **kwargs)
    
    return wrapper
```

---

## 9. 开发路线图

### 9.1 阶段一：基础架构搭建（1-2周）

**任务清单:**
- [ ] 项目初始化
  - 创建项目目录结构
  - 配置开发环境
  - 搭建基础代码框架
  
- [ ] 数据库设计
  - 设计数据库表结构
  - 创建数据库迁移脚本
  - 编写CRUD基础类

- [ ] API框架搭建
  - 配置FastAPI项目
  - 实现基础中间件（CORS、日志）
  - 编写API基础结构

- [ ] 前端项目搭建
  - 初始化React项目
  - 配置路由和状态管理
  - 搭建基础页面结构

**交付物:**
- 可运行的项目框架
- 数据库表结构文档
- API基础接口文档

---

### 9.2 阶段二：数据采集与处理（2-3周）

**任务清单:**
- [ ] 数据获取模块
  - 实现股票数据获取类
  - 实现新浪财经API集成
  - 编写数据清洗逻辑

- [ ] 新闻爬虫模块
  - 实现新闻爬虫类
  - 编写反爬虫策略
  - 实现增量更新机制

- [ ] 定时任务
  - 配置APScheduler
  - 实现数据更新任务
  - 实现新闻爬取任务

- [ ] 技术指标计算
  - 实现MACD计算
  - 实现KDJ计算
  - 单元测试

**交付物:**
- 完整的数据采集模块
- 技术指标计算模块
- 定时任务配置文档

---

### 9.3 阶段三：AI集成与业务逻辑（2-3周）

**任务清单:**
- [ ] AI集成
  - 配置LLM API
  - 实现提示词模板管理
  - 编写AI分析引擎

- [ ] 分析业务逻辑
  - 实现大盘分析逻辑
  - 实现个股分析逻辑
  - 实现新闻分析逻辑

- [ ] 提示词优化
  - 设计分析模板
  - 测试和调整提示词
  - 优化分析质量

- [ ] API开发
  - 实现分析相关API
  - 实现数据查询API
  - 编写API文档

**交付物:**
- 完整的AI分析模块
- 分析提示词模板
- API接口文档

---

### 9.4 阶段四：前端开发（2-3周）

**任务清单:**
- [ ] 页面开发
  - 股票分析页面
  - 大盘分析页面
  - 新闻中心页面

- [ ] 图表组件
  - 集成ECharts
  - 实现K线图组件
  - 实现指标展示组件

- [ ] 交互功能
  - 股票查询功能
  - 历史记录查看
  - 新闻列表展示

- [ ] 样式优化
  - 响应式布局
  - UI/UX优化
  - 主题配置

**交付物:**
- 完整的前端应用
- 用户界面文档
- 前端使用手册

---

### 9.5 阶段五：测试与部署（1-2周）

**任务清单:**
- [ ] 测试
  - 单元测试
  - 集成测试
  - 性能测试
  - 用户测试

- [ ] 部署准备
  - Docker镜像构建
  - 编写docker-compose配置
  - 配置Nginx

- [ ] 部署上线
  - 服务器环境配置
  - 应用部署
  - 监控配置

- [ ] 文档完善
  - 部署文档
  - 运维手册
  - 用户手册

**交付物:**
- 部署包和配置文件
- 部署文档和运维手册
- 用户使用手册

---

### 9.6 总时间估算

| 阶段 | 时间估算 | 人力投入 |
|------|---------|---------|
| 基础架构 | 1-2周 | 1人 |
| 数据采集 | 2-3周 | 1人 |
| AI集成 | 2-3周 | 1人 |
| 前端开发 | 2-3周 | 1人 |
| 测试部署 | 1-2周 | 1人 |
| **总计** | **8-13周** | - |

---

## 10. 风险与挑战

### 10.1 技术风险

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|---------|
| 数据源API限制或变更 | 高 | 中 | 多数据源备份，数据缓存 |
| 爬虫被反爬虫机制封禁 | 高 | 中 | 实现代理池，请求频率控制 |
| LLM API调用成本过高 | 中 | 中 | 结果缓存，提示词优化 |
| 技术指标计算错误 | 中 | 低 | 严格单元测试，与已知数据对比 |
| 系统性能瓶颈 | 中 | 中 | 异步处理，Redis缓存，数据库优化 |

### 10.2 业务风险

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|---------|
| AI分析结果准确性不足 | 高 | 中 | 多模型对比，人工审核机制 |
| 市场数据延迟影响分析 | 中 | 中 | 实时数据获取，定时任务优化 |
| 用户需求变更频繁 | 中 | 高 | 敏捷开发，模块化设计 |

### 10.3 运维风险

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|---------|
| 数据库性能问题 | 高 | 低 | 索引优化，读写分离 |
| 系统宕机 | 高 | 低 | 高可用架构，自动重启 |
| 数据安全泄露 | 高 | 低 | 数据加密，访问控制 |

---

## 11. 附录

### 11.1 相关资源

**官方文档:**
- FastAPI: https://fastapi.tiangolo.com/
- React: https://react.dev/
- Pandas: https://pandas.pydata.org/
- LangChain: https://python.langchain.com/
- TA-Lib: https://ta-lib.github.io/ta-lib-python/

**数据源:**
- akshare: https://akshare.akfamily.xyz/ - Python金融数据接口库
- 新浪财经: https://finance.sina.com.cn/
- 东方财富: https://www.eastmoney.com/

**LLM服务:**
- OpenAI: https://openai.com/
- 阿里云通义千问: https://qianwen.aliyun.com/
- 百度文心一言: https://yiyan.baidu.com/

### 11.2 参考资料

- 《量化投资策略与技术》
- 《Python金融数据分析》
- 《股票技术分析实战》

### 11.3 术语表

| 术语 | 解释 |
|------|------|
| K线 | 股票走势图，包含开盘价、收盘价、最高价、最低价 |
| MACD | 平滑异同移动平均线，趋势跟踪指标 |
| KDJ | 随机指标，超买超卖指标 |
| 日K/周K/月K | 以日/周/月为周期的K线图 |
| 大盘情绪 | 市场整体买卖情绪的量化指标 |
| LLM | 大语言模型，如GPT、通义千问等 |
| API | 应用程序接口，用于数据交互 |

---

## 12. 变更记录

| 版本 | 日期 | 修改内容 | 修改人 |
|------|------|---------|--------|
| v1.2 | 2026-01-21 | 功能二个股分析调整：取消自动获取个股所属板块，改为手动输入板块名称（可选） | - |
| v1.1 | 2025-01-21 | 集成akshare数据源，添加8个akshare接口支持 | - |
| v1.0 | 2025-01-20 | 初始版本创建 | - |

**v1.2 版本更新内容：**
1. 功能二（个股分析）调整：
   - 移除自动获取个股所属板块的功能
   - 将前端板块选择下拉框改为板块名称手动输入框（可选）
  - 支持用户手动输入一个或多个板块名称作为背景输入（不在前端展示板块对比）
   - 板块输入为可选字段，不输入时仅分析个股
2. API接口更新：
   - POST /api/analyze/stock 接口参数从 selected_sectors 改为 sector_names
   - sector_names 为可选参数，不提供时仅分析个股
3. 前端组件更新：
   - 移除 SectorSelector 下拉选择组件
   - 新增 SectorNameInput 手动输入组件
   - 支持逗号分隔的多个板块名称输入
4. 提示词模板更新：调整个股分析模板，适应可选板块分析模式

**v1.1 版本更新内容：**
1. 数据源更新：将新浪财经替换为akshare作为主要数据源
2. 新增功能模块：
   - 大盘资金流向分析（stock_market_fund_flow）
   - 市场活跃度分析（stock_market_activity_legu）
   - 个股公司基本信息获取（stock_individual_basic_info_xq）
   - 个股财务指标分析（stock_financial_abstract_new_ths）
   - 涨停股池数据获取（stock_zt_pool_em）
   - 个股分时数据分析（stock_zh_a_hist_min_em）
   - 概念板块指数获取（stock_board_concept_index_ths）
3. 新增数据库表：7个新表用于存储新增数据
