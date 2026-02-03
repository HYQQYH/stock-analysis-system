# 股票分析系统实施计划

**文档版本**: v1.0  
**更新日期**: 2026-01-21  
**目标时间**: 13 周完整交付  

---

## 关键决策（用户已确认）

- **MVP**: 核心 API + K 线 + 指标 + 单只股票 AI 报告（优先实现短线T+1分析）。
- **优先分析模式**: 短线T+1 分析（作为第一阶段 AI 报告模板）。
- **LLM 供应商**: 智谱GLM（作为首选模型，用于测试与生产）。
- **数据保留与存储规模**: 默认保留 1 个月；当前不设置严格存储上限，可在后续按需调整。
- **身份认证与权限**: 第一阶段不启用 JWT 或角色权限（公开 API 仅用于内部/受控环境）。
- **测试覆盖与验收**: 必须包含关键 API 测试、数据正确性验证，以及前后端单元/集成测试（关键路径覆盖）。
- **部署目标环境**: 优先采用 `docker-compose` 本地部署（第1版）。
- **监控指标与初始阈值**:
  - **API 95 百分位响应时间**: < 500ms
  - **LLM 错误率（调用失败/异常）**: < 5%
  - **分析任务队列长度**: < 50（超过时触发告警/降级策略）
  - **Redis 命中率**: > 90%
- **前端显示**: 不在前端展示板块对比（板块数据仅作为分析输入/背景）。
- **分析 API 默认行为**: POST `/api/v1/analysis` 采用异步任务模式：接口立即返回 `analysis_id` 与初始状态（`pending`），客户端通过 GET `/api/v1/analysis/{analysis_id}` 查询结果。若需同步接口，可作为轻量版另行提供和限制输入规模。

### 分析结果 Schema 示例

以下为第一阶段 `analysis_history` 中保存的示例结构（供前后端对齐）：

```
{
  "analysis_id": "<uuid>",
  "stock_code": "600000",
  "analysis_mode": "短线T+1",
  "analysis_time": "2026-01-23T12:00:00Z",
  "analysis_result": "...AI 分析文本或结构化 JSON...",
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
  "input_hash": "<sha256>",
  "status": "completed"
}
```


## 一、项目阶段划分

### 整体规划（13周）
1. **第1-2周**: 基础架构搭建（代码仓库、开发环境、数据库初始化）
2. **第3-4周**: 数据采集与处理（akshare 集成、K线数据获取）
3. **第5-6周**: 后端核心功能（技术指标计算、API 设计）
4. **第7-8周**: AI 分析模块（LLM 集成、提示词设计）
5. **第9-10周**: 前端开发（UI 框架、页面组件）
6. **第11-12周**: 系统集成与测试（端到端测试、性能优化）
7. **第13周**: 部署准备（Docker、Nginx 配置）

---

## 二、第1-2周：基础架构搭建

### 2.1 开发环境初始化

#### 步骤 1.1：配置 Python 开发环境
- **任务**: 在 Windows 机器上安装 Python 3.12 和 pip
- **验证方法**:
  - 在 PowerShell 中运行 `python --version`，确认输出为 `Python 3.12.x`
  - 运行 `pip --version`，确认 pip 版本为最新
  - 运行 `python -m venv aistock_env` 创建虚拟环境，然后激活它
  - 验证虚拟环境已激活（命令行前缀应显示环境名称）

#### 步骤 1.2：初始化项目目录结构
- **任务**: 在工作区根目录创建以下文件夹结构
  ```
  stock-analysis-system/
  ├── backend/
  │   ├── app/
  │   │   ├── __init__.py
  │   │   ├── main.py
  │   │   ├── api/
  │   │   │   └── __init__.py
  │   │   ├── services/
  │   │   │   └── __init__.py
  │   │   ├── models/
  │   │   │   └── __init__.py
  │   │   ├── db/
  │   │   │   └── __init__.py
  │   │   └── utils/
  │   │       └── __init__.py
  │   ├── requirements.txt
  │   ├── .env.example
  │   └── README.md
  ├── frontend/
  │   ├── src/
  │   ├── public/
  │   ├── package.json
  │   └── README.md
  ├── docker-compose.yml
  ├── README.md
  ├── CHANGELOG.md
  └── memory-bank/
      ├── architecture.md
      ├── stock-design-document.md
      └── tech-stack.md
  ```
- **验证方法**:
  - 使用命令 `tree /F backend` 列出目录树
  - 确认所有 `__init__.py` 文件都已创建
  - 检查 README.md 文件已创建在相应位置

#### 步骤 1.3：初始化 Git 仓库和分支策略
- **任务**: 初始化 Git 仓库，设置分支保护规则
  - 初始化 .gitignore 文件（排除 __pycache__、.env、虚拟环境目录等）
  - 创建 develop 和 main 分支
  - 创建初始提交
- **验证方法**:
  - 运行 `git status` 确认 Git 已初始化
  - 运行 `git branch` 列出分支，应包含 main 和 develop
  - 检查 .gitignore 文件是否存在且包含常见忽略项
  - 运行 `git log` 确认有初始提交

### 2.2 后端依赖配置

#### 步骤 2.1：创建 Python 依赖清单
- **任务**: 在 `backend/requirements.txt` 中添加第1-2周所需的核心依赖
  - 核心框架: fastapi、uvicorn、pydantic
  - 数据处理: pandas、numpy
  - 数据库: sqlalchemy、pymysql、redis
  - 环境配置: python-dotenv
  - 开发工具: pytest、black、flake8
- **验证方法**:
  - 打开 requirements.txt 文件，确认所有依赖都已列出
  - 依赖版本应与 tech-stack.md 中推荐的版本一致
  - 依赖按分类注释（框架、数据处理等）

#### 步骤 2.2：创建虚拟环境并安装依赖
- **任务**: 为后端项目创建和配置 Python 虚拟环境
  - 在 backend/ 目录创建虚拟环境
  - 激活虚拟环境
  - 安装 requirements.txt 中的所有依赖
- **验证方法**:
  - 虚拟环境目录已创建，文件夹中包含 Scripts、Lib 等标准目录
  - 运行 `pip list` 确认所有依赖已安装
  - 运行 `python -c "import fastapi; print(fastapi.__version__)"` 确认 FastAPI 已可导入

#### 步骤 2.3：创建环境变量配置模板
- **任务**: 在 `backend/.env.example` 中创建环境变量模板
  - 包含: DATABASE_URL、REDIS_URL、OPENAI_API_KEY 等占位符
  - 添加注释说明每个变量的含义
- **验证方法**:
  - .env.example 文件存在于 backend/ 目录
  - 文件包含至少 5 个主要环境变量
  - 每个变量都有简洁的注释说明其用途

### 2.3 数据库初始化

#### 步骤 3.1：设计数据库 Schema
- **任务**: 设计核心数据库表结构（PostgreSQL）
  - 股票基本信息表（stock_info）: 代码、名称、上市日期等
  - K线数据表（kline_data）: 股票代码、日期、开收高低、成交量等
  - 技术指标表（indicators）: 指标类型、计算结果、计算日期
  - 分析记录表（analysis_records）: 分析时间、股票代码、分析结果、AI 报告
  - 新闻表（news）: 新闻标题、内容、来源、发布时间
  - 大盘数据表（market_data）: 大盘资金流向、市场活跃度指标
- **验证方法**:
  - 在 `backend/app/db/` 目录下创建 schema_pg.sql 文件
  - 文件中包含所有表的 CREATE TABLE 语句
  - 每个表都包含主键、索引和必要的约束
  - SQL 语法符合 PostgreSQL 15 标准

**说明**: 预计系统日活用户（DAU）为个位数，初期可采用单实例 PostgreSQL 配置（垂直扩展），通过合理索引和资源调优满足性能需求；分库分表、读写分离等水平扩展方案作为后续扩展选项。

#### 步骤 3.2：创建 SQLAlchemy ORM 模型定义
- **任务**: 在 `backend/app/models/` 中定义数据库 ORM 模型
  - 为每个表创建对应的 SQLAlchemy 模型类
  - 定义字段类型、长度、约束等属性
  - 添加模型之间的关系定义
- **验证方法**:
  - 每个数据库表都有对应的模型类文件
  - 模型文件中定义的字段与 schema.sql 中的列相匹配
  - 模型类可以正确导入，无语法错误
  - 运行 `python -c "from app.models import *; print('Models imported successfully')"` 确认导入无误

#### 步骤 3.3：初始化 PostgreSQL 数据库
- **任务**: 在本地 PostgreSQL 实例中创建数据库和表
  - 使用 Docker 启动 PostgreSQL 15 容器（可选）或使用已安装的 PostgreSQL
  - 创建数据库 `stock_analysis_db`
  - 执行 schema_pg.sql 创建所有表
- **验证方法**:
  - 连接到 PostgreSQL 数据库，运行 `\dt` 显示所有表
  - 确认所有表都已创建
  - 对每个表运行 `\d <table_name>` 验证字段定义

#### 步骤 3.4：初始化 Redis 缓存
- **任务**: 配置和启动 Redis 服务
  - 使用 Docker 启动 Redis 7.0 容器或使用已安装的 Redis
  - 配置 Redis 连接参数（主机、端口、数据库编号）
  - 创建 Redis 连接池配置
- **验证方法**:
  - 运行 `redis-cli ping` 或 `docker exec <redis_container> redis-cli ping`
  - 确认返回 PONG 响应
  - 尝试在 Python 中连接 Redis: `python -c "import redis; r = redis.Redis(); print(r.ping())"`

### 2.4 后端框架初始化

#### 步骤 4.1：创建 FastAPI 应用骨架
- **任务**: 在 `backend/app/main.py` 中创建 FastAPI 应用的基础框架
  - 初始化 FastAPI 应用实例
  - 添加 CORS 中间件配置
  - 定义健康检查接口（GET /health）
  - 定义根路径接口说明（GET /）
- **验证方法**:
  - 运行 `uvicorn app.main:app --reload` 启动开发服务器
  - 在浏览器中访问 `http://localhost:8000/`，确认应用可访问
  - 访问 `http://localhost:8000/health`，应返回状态 200
  - 访问 `http://localhost:8000/docs` 查看 Swagger UI，确认生成成功

#### 步骤 4.2：创建数据库连接管理
- **任务**: 在 `backend/app/db/` 中创建数据库连接和会话管理
  - 创建数据库引擎配置（使用 SQLAlchemy）
  - 创建会话工厂
  - 创建依赖注入函数，用于 FastAPI 路由获取数据库会话
- **验证方法**:
  - 创建测试脚本验证数据库连接
  - 运行测试脚本，确认能成功连接到 PostgreSQL 和 Redis
  - 验证会话获取和释放流程正常

#### 步骤 4.3：创建配置管理系统
- **任务**: 在 `backend/app/` 中创建 `config.py` 统一管理应用配置
  - 使用 pydantic-settings 实现配置类
  - 包含数据库、Redis、API、日志等配置项
  - 支持从 .env 文件和环境变量加载配置
- **验证方法**:
  - 创建 .env 文件（基于 .env.example），填入测试数据库连接信息
  - 运行 `python -c "from app.config import settings; print(settings.DATABASE_URL)"` 确认配置加载
  - 验证配置值与 .env 文件一致（使用 PostgreSQL 连接字符串）

---

## 三、第3-4周：数据采集与处理

### 3.1 akshare 集成

#### 步骤 5.1：安装和测试 akshare 库
- **任务**: 安装 akshare 并验证其主要数据接口
  - 在 requirements.txt 中添加 akshare 依赖
  - 安装库
  - 测试 akshare 的关键接口
- **验证方法**:
  - 运行 `pip install akshare` 确认安装成功
  - 创建测试脚本分别测试以下接口:
    - `ak.stock_zh_a_hist()` - 获取上证指数 K 线数据
    - `ak.stock_zt_pool_em()` - 获取涨停股池
    - `ak.stock_market_fund_flow()` - 获取大盘资金流向
  - 验证每个接口返回数据格式为 pandas DataFrame
  - 记录返回数据的字段名称和数据类型

#### 步骤 5.2：创建数据采集服务
- **任务**: 在 `backend/app/services/` 中创建 `data_collector.py` 数据采集模块
  - 创建 DataCollector 类，封装 akshare 接口调用
  - 实现方法: `fetch_kline_data(code, period)` - 获取 K 线数据
  - 实现方法: `fetch_market_sentiment()` - 获取大盘情绪数据
  - 实现方法: `fetch_limit_up_pool()` - 获取涨停股池
  - 实现方法: `fetch_market_fund_flow()` - 获取大盘资金流向
  - 添加错误处理和重试机制
- **验证方法**:
  - 创建测试脚本导入 DataCollector 类
  - 调用各个方法，验证返回结果不为空
  - 检查返回数据的字段是否完整
  - 运行 `pytest backend/tests/test_data_collector.py` 执行单元测试
  - 所有测试应通过

#### 步骤 5.3：实现 K 线数据管理
- **任务**: 在 `backend/app/services/` 中创建 `kline_manager.py` K 线数据管理模块
 - 实现方法: `cache_kline_data(code, period, data)` - **优先**将 K 线数据写入 Redis 缓存（缓存优先策略），并返回缓存确认
 - 实现方法: `save_kline_to_db(code, period, data)` - 异步将缓存数据落盘到 PostgreSQL（后台任务，避免阻塞实时请求）
 - 实现方法: `get_kline_data(code, period, days)` - 获取历史 K 线数据（优先从 Redis 缓存，缓存未命中回退到 PostgreSQL）
 - 实现数据去重和一致性校验，确保 Redis 与 PostgreSQL 最终一致（可采用输入摘要/哈希和幂等写入策略）
 - **验证方法**:
  - 编写测试用例覆盖上述方法
  - 调用 cache_kline_data 后，通过 Redis 命令验证数据已缓存
  - 在后台异步任务执行后，验证 PostgreSQL 中数据已持久化（可接受延迟范围内）
  - 验证 get_kline_data 在 Redis 可用和不可用两种场景下均能正确返回（Redis 不可用时回退到 PostgreSQL）
  - 验证去重逻辑和幂等性，避免重复写入

#### 步骤 5.4：创建定时数据采集任务
- **任务**: 在 `backend/app/` 中创建 `tasks.py` 定时任务模块
  - 配置 APScheduler 用于定时执行采集任务
  - 实现任务: 每日收盘后 17:00 采集上证指数、大盘情绪、涨停股池
  - 实现任务: 每日收盘后 17:30 采集个股基本信息和财务数据（指定股票列表）
  - 实现任务: 每日 09:30 清理过期缓存
  - 添加任务执行日志
- **验证方法**:
  - 创建测试脚本手动触发定时任务
  - 检查 PostgreSQL 和 Redis 中数据是否按预期更新
  - 验证日志记录了任务执行时间和状态
  - 检查任务成功执行而不报错

### 3.2 数据处理与清洗

#### 步骤 6.1：创建数据处理服务
- **任务**: 在 `backend/app/services/` 中创建 `data_processor.py` 数据处理模块
  - 实现方法: `clean_kline_data(df)` - 清洗 K 线数据（去重、填充缺失值）
  - 实现方法: `normalize_kline_data(df)` - 标准化数据格式和字段名
  - 实现方法: `calculate_time_range(code, period)` - 计算数据时间范围
  - 实现方法: `validate_data_completeness(df)` - 验证数据完整性
  - 添加异常捕获和日志记录
- **验证方法**:
  - 准备包含缺陷数据的测试 DataFrame（重复行、缺失值等）
  - 调用 clean_kline_data，验证返回数据已清洗
  - 调用 normalize_kline_data，验证字段名和数据类型统一
  - 调用 validate_data_completeness，验证返回有效的完整性报告

#### 步骤 6.2：实现缓存策略
- **任务**: 在 `backend/app/` 中创建 `cache.py` 缓存管理模块
  - 定义缓存键命名规则
  - 实现缓存装饰器 @cache_result，支持自定义 TTL
  - 实现方法: `invalidate_cache(pattern)` - 批量清理缓存
  - 实现缓存预热逻辑
- **验证方法**:
  - 使用缓存装饰器装饰测试函数
  - 验证第一次调用执行函数，第二次调用从缓存返回
  - 验证缓存过期时间生效
  - 测试缓存清理是否正常工作

---

## 四、第5-6周：后端核心功能

### 4.1 技术指标计算

#### 步骤 7.1：集成 pandas-ta 技术指标库
- **任务**: 安装 pandas-ta 并创建指标计算服务
  - 在 requirements.txt 中添加 pandas-ta 依赖
  - 在 `backend/app/services/` 中创建 `indicator_calculator.py`
  - 实现方法: `calculate_macd(kline_df)` - 计算 MACD 指标
  - 实现方法: `calculate_kdj(kline_df)` - 计算 KDJ 指标
  - 实现方法: `calculate_rsi(kline_df)` - 计算 RSI 指标
  - 实现方法: `calculate_all_indicators(kline_df)` - 一次性计算所有指标
- **验证方法**:
  - 准备包含 OHLCV 列的测试 DataFrame（至少 100 行数据）
  - 调用各个指标计算方法
  - 验证返回 DataFrame 包含对应的指标列
  - 验证指标值在合理范围内（例如 RSI 在 0-100 之间）

#### 步骤 7.2：创建指标存储和查询接口
- **任务**: 在 `backend/app/services/` 中创建 `indicator_manager.py` 指标管理模块
  - 实现方法: `save_indicators(code, period, indicators_df)` - 保存指标到数据库
  - 实现方法: `cache_indicators(code, period, indicators_df)` - 缓存指标到 Redis
  - 实现方法: `get_indicators(code, period)` - 查询指标数据
  - 实现定期更新指标的机制
- **验证方法**:
  - 计算某只股票的指标数据
  - 调用 save_indicators 存储到数据库，查询验证数据已保存
  - 调用 cache_indicators 缓存，验证 Redis 中有数据
  - 调用 get_indicators 查询，验证返回正确的指标数据

### 4.2 API 路由设计与实现

#### 步骤 8.1：设计 API 规范
- **任务**: 为后端 API 设计统一的请求/响应规范
  - 定义成功响应格式: `{code: 0, message: "success", data: {...}}`
  - 定义错误响应格式: `{code: <error_code>, message: "<error_msg>"}`
  - 定义分页响应格式: `{total: <count>, page: <current>, data: [...]}`
  - 定义 HTTP 状态码使用规则（200、201、400、401、500 等）
- **验证方法**:
  - 在 `backend/app/schemas/` 中创建 Pydantic 响应模型
  - 验证模型可以被 FastAPI 自动验证和序列化
  - 文档中记录所有 API 的请求/响应格式示例

#### 步骤 8.2：创建股票查询 API
- **任务**: 在 `backend/app/api/` 中创建 `stocks.py` 路由文件
  - 实现接口: POST /api/v1/stocks/search - 查询股票基本信息
  - 实现接口: GET /api/v1/stocks/{code}/kline - 获取 K 线数据
  - 实现接口: GET /api/v1/stocks/{code}/indicators - 获取技术指标
  - 实现接口: GET /api/v1/stocks/{code}/info - 获取公司基本信息
  - 每个接口添加参数验证和错误处理
- **验证方法**:
  - 使用 Postman 或 curl 测试每个 API 端点
  - 验证正常请求返回 200 状态和预期数据格式
  - 验证参数验证错误返回 400 状态
  - 验证数据库无相关数据时返回 404 或空列表
  - 验证所有 API 在 Swagger UI 中正确显示

#### 步骤 8.3：创建大盘数据 API
- **任务**: 在 `backend/app/api/` 中创建 `market.py` 路由文件
  - 实现接口: GET /api/v1/market/index - 获取上证指数数据
  - 实现接口: GET /api/v1/market/sentiment - 获取大盘情绪
  - 实现接口: GET /api/v1/market/fund-flow - 获取资金流向
  - 实现接口: GET /api/v1/market/limit-up - 获取涨停股池
- **验证方法**:
  - 使用 Postman 测试每个 API
  - 验证返回的数据字段与设计文档中的规范一致
  - 验证数据按日期倒序排列
  - 验证 API 性能（响应时间 < 1 秒）

#### 步骤 8.4：创建分析历史记录 API ✅ 已完成
- **任务**: 在 `backend/app/api/` 中创建 `analysis.py` 路由文件
 - 实现接口: POST /api/v1/analysis - 创建分析任务（提交后异步执行）
   - 行为说明：该接口应立即返回任务 ID（`analysis_id`）和初始状态（`pending`），真实分析在后台异步执行以避免阻塞请求。
 - 实现接口: GET /api/v1/analysis/{analysis_id} - 获取分析结果或任务状态（支持轮询）
 - 实现接口: GET /api/v1/analysis/history - 获取分析历史记录（支持分页和股票代码筛选）
 - 实现接口: DELETE /api/v1/analysis/{analysis_id} - 删除分析记录
 - **验证方法**:
  - 调用 POST 接口创建分析任务，验证立即返回 `analysis_id` 和 `pending` 状态
  - 在后台任务完成后，通过 GET 接口获取最终结果并验证结构化字段（analysis_result、trading_advice、confidence_score 等）
  - 验证超时和失败场景：当后台任务在预设超时时间内未完成，GET 接口应返回失败状态及错误码（例如：`analysis_timeout`）和可读错误信息
  - 验证轮询策略在高并发请求下的稳定性（防止频繁查询导致资源浪费）
  
#### 步骤 8.5：创建前端历史分析记录组件 ✅ 已完成（2026-02-03）
- **任务**: 在 `frontend/src/components/` 中创建 `HistoryList.tsx` 历史记录组件
  - 实现从后端 API 获取历史分析记录（支持分页和按股票代码筛选）
  - 实现本地存储降级策略（后端调用失败时使用本地持久化数据）
  - 实现查看详情功能（点击查看分析结果详情）
  - 实现删除历史记录功能
  - 实现刷新和分页功能
  - 集成到 StockAnalysis 页面中展示历史记录
- **创建文件**:
  - `frontend/src/components/HistoryList.tsx` - 历史分析记录组件
  - `frontend/src/components/index.ts` - 更新组件导出
  - 更新 `frontend/src/pages/StockAnalysis.tsx` - 集成 HistoryList 组件
- **验证方法**:
  - 在股票分析页面底部显示历史记录列表
  - 验证分页功能正常工作
  - 验证筛选功能按股票代码过滤
  - 验证删除功能正常工作

### 4.3 业务逻辑整合

#### 步骤 9.1：创建股票分析业务逻辑 ✅ 已完成
- **任务**: 在 `backend/app/services/` 中创建 `stock_analysis.py` 业务逻辑模块
  - 实现方法: `analyze_single_stock(code)` - 获取单只股票的完整数据
    - 查询/采集 K 线数据（日、周、月）
    - 计算技术指标
    - 获取公司基本信息和财务数据
    - 获取相关新闻
    - 返回整合的数据包
  - 实现方法: `analyze_with_sector(code, sector_name)` - 获取股票和板块数据
  - 实现数据验证和异常处理
- **验证方法**:
  - ✅ 编写单元测试，测试特定股票代码（如 600000）
  - ✅ 验证返回数据包含所有必要字段
  - ✅ 验证处理无效股票代码时返回有意义的错误
- **创建文件**:
  - `backend/app/services/stock_analysis.py` - 股票分析业务逻辑模块
  - `backend/tests/test_stock_analysis.py` - 单元测试文件 (40个测试全部通过)

#### 步骤 9.2：创建大盘分析业务逻辑 ✅ 已完成
- **任务**: 在 `backend/app/services/` 中创建 `market_analysis.py` 业务逻辑模块
  - 实现方法: `get_market_overview()` - 获取大盘全景数据
    - 获取上证指数 K 线和技术指标
    - 获取大盘资金流向
    - 获取市场活跃度
    - 获取涨停股池
    - 返回整合的大盘数据
  - 实现方法: `analyze_market_sentiment()` - 分析市场情绪
- **验证方法**:
  - ✅ 调用 get_market_overview 方法
  - ✅ 验证返回数据包含所有大盘指标
  - ✅ 验证数据的时间戳和日期信息正确
- **创建文件**:
  - `backend/app/services/market_analysis.py` - 大盘分析业务逻辑模块
  - `backend/tests/test_market_analysis.py` - 单元测试文件 (30个测试全部通过)

---

## 五、第7-8周：AI 分析模块

### 5.1 LLM 集成

#### 步骤 10.1：安装和配置 LangChain ✅ 已完成
- **任务**: 集成 LangChain 和 LLM 服务
  - ✅ 在 requirements.txt 中添加 langchain、langchain-openai 等依赖（已存在）
  - ✅ 在 `backend/app/` 中创建 `llm_config.py` LLM 配置模块
  - ✅ 支持多个 LLM 提供商（OpenAI、阿里通义千问、智谱GLM、Ollama本地模型）
  - ✅ 实现 LLM 选择逻辑和故障转移（自动回退机制）
- **验证方法**:
  - ✅ 在 .env 中配置 OPENAI_API_KEY（测试用）
  - ✅ 创建测试脚本初始化 LLM 客户端（test_llm_connection 函数）
  - ✅ 调用 LLM 的简单接口验证连接成功（测试时无API key会优雅失败）
  - ✅ 验证配置中的模型名称和参数正确
- **创建文件**:
  - `backend/app/llm_config.py` - LLM配置模块（支持4个提供商，直接HTTP API调用）
  - `backend/tests/test_llm_config.py` - 单元测试文件 (38个测试全部通过)

#### 步骤 10.2：创建提示词管理系统
- **任务**: 在 `backend/app/` 中创建 `prompts.py` 提示词管理模块
  - 为不同分析场景定义提示词模板
    - 大盘走势分析提示词
    - 个股分析提示词
    - 个股+板块对比分析提示词
    - 市场情绪分析提示词
  - 实现提示词参数化，支持动态传入数据
  - 实现提示词版本控制
- **验证方法**:
  - 对各个模板进行测试，确保参数替换正常
  - 验证提示词长度合理（不超过 LLM 上下文限制）
  - 在提示词中包含明确的输出格式指示

#### 步骤 10.3：创建 AI 分析服务
- **任务**: 在 `backend/app/services/` 中创建 `ai_analyzer.py` AI 分析模块
  - 实现方法: `analyze_stock(stock_data, optional_sector_data)` - 分析单只股票
    - 准备分析数据摘要
    - 填充提示词模板
    - 调用 LLM API
    - 解析和验证 LLM 响应
    - 返回结构化分析报告
  - 实现方法: `analyze_market()` - 分析大盘行情
  - 实现方法: `extract_news_insights(news_list)` - 从新闻提取投资建议
  - 添加重试、超时处理
- **验证方法**:
  - 创建测试脚本调用分析方法
  - 验证 LLM 调用成功且返回有意义的分析内容
  - 验证异常处理（如 API 超时）
  - 检查返回结果能否正确解析为 JSON 或结构化格式

### 5.2 分析流程整合

#### 步骤 11.1：创建端到端分析流程
- **任务**: 在 `backend/app/services/` 中创建 `analysis_pipeline.py` 分析流程模块
  - 实现方法: `run_stock_analysis_pipeline(code, optional_sector)` - 完整的个股分析流程
    - 数据采集和预处理
    - 技术指标计算
    - 数据缓存
    - AI 分析
    - 结果保存到数据库
    - 返回完整分析报告
  - 实现方法: `run_market_analysis_pipeline()` - 完整的大盘分析流程
  - 添加流程日志记录
- **验证方法**:
  - 调用 run_stock_analysis_pipeline，验证各个步骤依次执行
  - 检查数据库中是否保存了分析结果
  - 验证 Redis 中缓存了必要的数据
  - 检查日志中记录了每个步骤的执行情况

#### 步骤 11.2：更新分析 API 实现 AI 分析
- **任务**: 更新 `backend/app/api/analysis.py` 实现真实的 AI 分析
  - 更新 POST /api/v1/analysis 接口
    - 调用 analysis_pipeline.run_stock_analysis_pipeline
    - 等待分析完成并返回结果
    - 或者异步处理并返回任务 ID
  - 更新 GET /api/v1/analysis/{analysis_id} 接口
    - 从数据库查询分析结果
    - 返回完整的分析报告和 AI 分析内容
- **验证方法**:
  - 通过 API 发送分析请求
  - 验证返回的分析报告包含 AI 生成的内容
  - 验证结果保存到数据库
  - 验证多次查询同一分析 ID 返回一致的结果

---

## 六、第9-10周：前端开发

### 6.1 前端项目初始化

#### 步骤 12.1：初始化 React 项目
- **任务**: 使用 Vite 创建 React + TypeScript 项目
  - 在 frontend/ 目录初始化 Vite React 项目
  - 配置 TypeScript
  - 安装核心依赖（React Router、Zustand、Axios 等）
  - 配置 ESLint 和 Prettier
- **验证方法**:
  - 运行 `npm run dev` 启动开发服务器
  - 在浏览器中访问应用，验证能正常加载
  - 检查 package.json 中所有必要依赖已安装
  - 运行 `npm run build` 验证构建成功

#### 步骤 12.2：配置路由结构
- **任务**: 在 `frontend/src/` 中设置 React Router
  - 创建路由配置文件
  - 定义主要路由页面
    - / → 首页/仪表板
    - /stock-analysis → 股票分析页
    - /market-analysis → 大盘分析页
    - /news → 新闻资讯页
    - /limit-up → 涨停股池页
  - 创建布局组件（导航栏、侧边栏）
- **验证方法**:
  - 验证路由配置文件没有语法错误
  - 通过浏览器导航验证各个路由可以访问
  - 验证路由切换时 URL 正确更新

#### 步骤 12.3：配置状态管理（Zustand）
- **任务**: 在 `frontend/src/store/` 中创建 Zustand 状态管理
  - 创建 stockStore - 管理当前查询的股票数据
  - 创建 analysisStore - 管理分析历史和结果
  - 创建 uiStore - 管理 UI 状态（加载状态、模态框等）
  - 实现数据持久化到本地存储
- **验证方法**:
  - 编写测试验证状态初始化正确
  - 验证状态修改函数工作正确
  - 验证本地存储持久化生效

### 6.2 页面和组件开发

#### 步骤 13.1：创建股票查询页面
- **任务**: 在 `frontend/src/pages/` 中创建 StockAnalysis 页面
  - 股票代码输入框
  - 板块名称输入框（可选）
  - K 线类型选择（日K/周K/月K）
  - 查询按钮
  - 加载状态指示
  - 错误提示
- **验证方法**:
  - 在浏览器中加载页面，验证页面结构正确
  - 输入有效的股票代码，点击查询按钮
  - 验证加载状态显示和隐藏
  - 验证错误处理（如输入无效代码）

#### 步骤 13.2：创建图表和数据展示组件
- **任务**: 在 `frontend/src/components/` 中创建数据展示组件
  - K 线图表组件（使用 ECharts）
  - 技术指标卡片组件
  - 公司信息展示组件
  - AI 分析报告展示组件
  - 新闻列表组件
  - 大盘数据看板组件
- **验证方法**:
  - 使用 Storybook 预览各个组件
  - 验证组件能正确接收和展示数据
  - 验证响应式设计在不同屏幕尺寸下工作

#### 步骤 13.3：创建大盘分析页面
- **任务**: 在 `frontend/src/pages/` 中创建 MarketAnalysis 页面
  - 上证指数 K 线图表
  - 技术指标展示
  - 资金流向数据表格
  - 市场活跃度指标卡片
  - 涨停股票列表
- **验证方法**:
  - 加载页面验证各部分显示正确
  - 验证数据表格可以排序和分页
  - 验证图表交互功能正常

#### 步骤 13.4：创建新闻资讯页面
- **任务**: 在 `frontend/src/pages/` 中创建 News 页面
  - 新闻列表展示
  - 新闻搜索和筛选
  - 新闻详情展示
  - AI 提取的投资建议展示
- **验证方法**:
  - 验证新闻列表可以加载并展示
  - 验证搜索功能工作
  - 验证点击新闻可以查看详情

### 6.3 API 集成

#### 步骤 14.1：创建 API 客户端
- **任务**: 在 `frontend/src/services/` 中创建 API 调用模块
  - 配置 Axios 实例，包括基础 URL、超时、错误拦截
  - 创建 stockApi.ts - 股票相关 API 调用
  - 创建 marketApi.ts - 大盘相关 API 调用
  - 创建 analysisApi.ts - 分析相关 API 调用
  - 创建 newsApi.ts - 新闻相关 API 调用
- **验证方法**:
  - 编写测试验证 API 调用格式正确
  - 使用 Postman 手动测试后端 API
  - 在浏览器开发者工具中查看请求/响应

#### 步骤 14.2：集成 React Query 数据管理
- **任务**: 使用 React Query 管理异步数据
  - 创建 hooks（useStockQuery、useMarketQuery 等）
  - 配置查询缓存和过期时间
  - 实现数据预加载
- **验证方法**:
  - 验证查询结果缓存生效
  - 验证错误和加载状态正确传递到组件
  - 验证手动刷新数据工作

---

## 七、第11-12周：系统集成与测试

### 7.1 端到端测试

#### 步骤 15.1：创建集成测试套件
- **任务**: 编写后端集成测试
  - 测试数据采集流程（akshare 接口调用）
  - 测试数据存储流程（数据库写入/查询）
  - 测试 API 端点（请求/响应）
  - 测试 AI 分析流程（LLM 集成）
- **验证方法**:
  - 运行 `pytest backend/tests/` 执行所有集成测试
  - 验证测试覆盖率 > 70%
  - 所有测试通过

#### 步骤 15.2：创建前端集成测试
- **任务**: 编写前端集成测试
  - 测试页面加载和路由导航
  - 测试用户输入和表单提交
  - 测试 API 调用和数据展示
  - 测试错误处理
- **验证方法**:
  - 使用 Vitest 和 React Testing Library 编写测试
  - 运行 `npm run test` 执行测试
  - 验证测试通过

#### 步骤 15.3：执行系统验收测试
- **任务**: 从用户角度进行完整流程测试
  - 场景 1：输入股票代码，查看分析结果
  - 场景 2：查看大盘数据和涨停股池
  - 场景 3：查看新闻和投资建议
  - 场景 4：查看历史分析记录
- **验证方法**:
  - 手动执行每个测试场景
  - 记录测试结果（通过/失败）
  - 记录发现的缺陷和改进建议

### 7.2 性能测试

#### 步骤 16.1：进行后端性能测试
- **任务**: 测试后端 API 的性能和并发能力
  - 使用 Apache JMeter 或 Locust 进行压测
  - 测试 GET /api/v1/stocks/{code}/kline 接口
    - 目标：100 并发用户，响应时间 < 500ms
  - 测试 GET /api/v1/market/sentiment 接口
    - 目标：200 并发用户，响应时间 < 300ms
  - 测试 POST /api/v1/analysis 接口
    - 目标：50 并发用户，AI 分析完成时间 < 30s
- **验证方法**:
  - 生成性能测试报告
  - 验证响应时间和吞吐量达到目标
  - 记录内存使用和 CPU 占用

#### 步骤 16.2：进行前端性能测试
- **任务**: 测试前端加载和交互性能
  - 测试首屏加载时间（目标 < 3s）
  - 测试 JavaScript 执行时间
  - 测试图表渲染性能
  - 测试移动端响应性
- **验证方法**:
  - 使用 Lighthouse 生成性能报告
  - 使用浏览器 DevTools 分析性能指标
  - 验证 Core Web Vitals 指标达标

### 7.3 缺陷修复和优化

#### 步骤 17.1：缺陷修复
- **任务**: 修复测试中发现的缺陷
  - 记录所有缺陷（严重性、影响范围、重现步骤）
  - 按优先级修复缺陷
  - 针对每个缺陷执行验证测试
- **验证方法**:
  - 为每个缺陷创建 Git Issue
  - 修复后进行同行评审
  - 执行回归测试确认缺陷已修复

#### 步骤 17.2：性能优化
- **任务**: 基于性能测试结果优化系统
  - 优化 API 响应时间
    - 添加数据库索引
    - 优化查询 SQL
    - 增加缓存层
  - 优化前端加载速度
    - 代码分割和懒加载
    - 压缩资源（CSS、JS、图片）
    - CDN 加速
- **验证方法**:
  - 比较优化前后的性能指标
  - 验证优化后指标有显著改善
  - 不引入新的缺陷

---

## 八、第13周：部署准备
部署方式：优先采用本地部署（Docker 容器或本地启动脚本），后续根据需要再考虑云端托管或 CI/CD 自动化部署。

### 8.1 容器化和部署配置

#### 步骤 18.1：创建 Docker 镜像
- **任务**: 为后端和前端创建 Docker 镜像
  - 创建 Dockerfile（后端）
    - 基础镜像：python:3.11-slim
    - 复制代码和依赖
    - 配置启动命令
  - 创建 Dockerfile（前端）
    - 基础镜像：node:18-alpine（构建）+ nginx:alpine（运行）
    - 构建前端应用
    - 配置 Nginx 服务
- **验证方法**:
  - 运行 `docker build -t stock-backend:latest ./backend` 构建后端镜像
  - 运行 `docker build -t stock-frontend:latest ./frontend` 构建前端镜像
  - 使用 `docker run` 启动容器，验证应用正常运行

#### 步骤 18.2：配置 Docker Compose
- **任务**: 在项目根目录创建 docker-compose.yml 编排文件
  - 定义 backend 服务（FastAPI）
  - 定义 frontend 服务（Nginx）
  - 定义 PostgreSQL 服务
  - 定义 redis 服务
  - 配置网络和卷
  - 配置环境变量和启动依赖
- **验证方法**:
  - 运行 `docker-compose up` 启动所有服务
  - 验证每个服务的容器都已启动
  - 验证容器之间的网络连接正常
  - 检查日志，确认没有启动错误

#### 步骤 18.3：配置 Nginx
- **任务**: 创建 Nginx 配置文件用于反向代理
  - 配置 80 端口监听
  - 配置前端静态资源服务
  - 配置后端 API 反向代理（/api → http://backend:8000）
  - 配置 GZIP 压缩和缓存策略
  - 配置错误页面
- **验证方法**:
  - 使用 `docker exec` 进入 Nginx 容器测试配置
  - 验证前端资源能正常加载
  - 验证 API 请求正确代理到后端

### 8.2 环境配置和文档

#### 步骤 19.1：完善项目文档
- **任务**: 编写和完善项目文档
  - 更新 README.md - 项目概述、快速开始、技术栈
  - 编写 INSTALL.md - 详细安装步骤
  - 编写 API.md - API 文档（或使用 Swagger UI）
  - 编写 DEPLOYMENT.md - 部署步骤
  - 编写 CONTRIBUTING.md - 贡献指南
- **验证方法**:
  - 新手按照 README 能否成功启动项目
  - 按照 INSTALL.md 能否成功安装所有依赖
  - 按照 DEPLOYMENT.md 能否成功部署到服务器

#### 步骤 19.2：配置自动化工具
- **任务**: 配置 CI/CD 和自动化工具（可选）
  - 配置 Git Hooks（pre-commit 自动运行 lint 和 format）
  - 配置 GitHub Actions 或 GitLab CI（可选）
    - 自动运行测试
    - 自动构建 Docker 镜像
    - 自动部署
- **验证方法**:
  - 进行 Git 提交，验证 pre-commit hooks 执行
  - 检查提交代码是否自动格式化

### 8.3 上线前检查清单

#### 步骤 20.1：执行上线前检查
- **任务**: 在部署前进行最后的完整检查
  - [ ] 所有单元测试通过
  - [ ] 集成测试通过
  - [ ] 性能测试达到目标
  - [ ] 缺陷修复完成
  - [ ] 代码审查完成
  - [ ] 数据库迁移脚本已准备
  - [ ] 环境配置已验证
  - [ ] 文档已更新
  - [ ] 备份和恢复计划已制定
  - [ ] 监控和告警已配置
- **验证方法**:
  - 在部署前清单上逐项签核
  - 记录任何未完成项和风险

---

## 九、质量保证指标

### 单元测试
- **目标**: 关键服务层测试覆盖率 > 70%
- **验证方法**: 运行 `pytest --cov` 生成覆盖率报告

### 集成测试
- **目标**: 主要业务流程测试用例 ≥ 30 个
- **验证方法**: 记录所有测试用例及执行结果

### API 文档
- **目标**: 所有 API 端点都有文档和使用示例
- **验证方法**: 访问 Swagger UI，验证文档完整

### 代码质量
- **目标**: 使用 Black 格式化，通过 Flake8 检查
- **验证方法**: 运行 `flake8 backend/` 和 `black --check backend/`

### 性能指标
- **后端 API 响应时间**: < 500ms（95 百分位）
- **前端首屏加载时间**: < 3s
- **AI 分析完成时间**: < 30s

---

## 十、风险与应对措施

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| akshare API 变更 | 中 | 监控 GitHub，准备备选数据源 |
| LLM API 延迟或限流 | 中 | 实现队列和缓存，支持多模型 |
| 数据库性能瓶颈 | 高 | 提前优化索引，实施读写分离 |
| 前端浏览器兼容性 | 低 | 充分的跨浏览器测试 |
| 团队协作冲突 | 中 | 明确分工，定期同步进度 |

---

## 十一、完整功能（第二阶段）

后续可以在第 13 周之后持续添加以下功能：

### 阶段 2 功能列表（第 14-20 周）
1. **用户管理系统** - 用户注册、登录、权限管理
2. **实时行情推送** - WebSocket 集成，实时数据推送
3. **投资组合管理** - 用户自定义投资组合，收益率追踪
4. **警报通知** - 股价达到预设价位时提醒
5. **数据可视化增强** - 更多图表类型，自定义仪表板
6. **移动端适配** - React Native 或响应式 Web 应用
7. **导出功能** - 分析报告导出为 PDF、Excel
8. **国际化** - 多语言支持（英文、日文等）
9. **性能监控** - 系统监控面板，实时性能数据

---

## 十二、检查清单

### 项目启动前
- [ ] 已读完 stock-design-document.md 和 tech-stack.md
- [ ] 已建立项目目录结构
- [ ] 已初始化 Git 仓库
- [ ] 已确认开发环境（Python、Node.js、PostgreSQL、Redis）

### 各周完成前
- [ ] 所有任务都已完成
- [ ] 所有测试都已通过
- [ ] 代码已通过审查
- [ ] 文档已更新
- [ ] 进度已提交和备份

---

## 附录：测试验证模板

### API 测试模板
```
测试接口: [接口路径]
请求方法: [GET/POST/PUT/DELETE]
请求参数: [参数列表]
期望结果: [预期响应]

测试步骤:
1. [具体步骤]
2. [具体步骤]

实际结果: [记录实际结果]
通过/失败: [选择]
备注: [补充说明]
```

### 功能测试模板
```
功能名称: [功能描述]
测试用例 ID: [编号]
前置条件: [需要的初始状态]

测试步骤:
1. [操作步骤]
2. [验证步骤]

预期结果: [应该发生什么]
实际结果: [真实发生了什么]
通过/失败: [选择]
缺陷 ID: [如有关联缺陷]
```

---

**文档作者**: AI Assistant  
**版本**: v1.0  
**最后更新**: 2026-01-21
