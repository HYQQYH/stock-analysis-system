## Architecture Notes - 2026-01-25

### 文件与模块说明（概要）
- `backend/app/db/schema_pg.sql`：PostgreSQL 初始化建表脚本（用于容器第一次初始化时建表）。
- `backend/app/models/models.py`：SQLAlchemy ORM 模型定义，模型与 `schema_pg.sql` 对应。
- `backend/app/db/database.py`：数据库连接与会话管理（SQLAlchemy 引擎、SessionLocal、依赖注入）。
- `backend/app/db/redis_cache.py`：Redis 连接与缓存工具封装。
- `docker-compose-dev.yml`：开发环境的容器编排文件（包含 `postgres`、`redis`、`backend` 服务）。

### 架构设计决策
- 选用 PostgreSQL 15 作为初期关系型数据库，理由：更严格的 SQL 标准兼容性、更完善的 JSONB 支持，方便存储指标与分析结果的结构化数据。
- 使用 Redis 作为缓存层和短期数据存储（K 线缓存、任务状态、LLM 调用缓存等），提高响应性能并降低数据库读负载。
- 将 ORM（SQLAlchemy）与原生 SQL 建表脚本并行维护：
	- 原生 SQL 用于容器初始化与 DBA 操作；
	- ORM 用于应用运行时的数据操作与模型映射；
	- 建议使用 Alembic 管理迁移以避免不一致。

### 关键模块交互关系
- 启动流程（容器化）:
	1. `postgres` 容器使用 `/docker-entrypoint-initdb.d/schema.sql` 初始化数据库。
	2. `redis` 容器启动并监听连接。
	3. `backend` 服务读取环境变量 `DATABASE_URL` 与 `REDIS_URL`，初始化连接并提供 API。

- 运行时交互:
	- API 层（`app/main.py`）通过依赖注入从 `app/db/database.py` 获取 DB session；通过 `app/db/redis_cache.py` 获取 Redis 客户端。
	- `services` 层（如 `data_collector`, `kline_manager`, `indicator_calculator`）从 Redis 读取缓存优先的数据，未命中时回退到 PostgreSQL 并异步写回缓存。
	- `ai_analyzer` 调用 LLM 服务并将结果写入 `analysis_history`（PostgreSQL），同时在 Redis 中缓存中间状态以支持轮询查询。

### 部署注意事项
- `schema_pg.sql` 仅在数据卷首次创建时执行。若需要在已有数据卷上更新 schema，请使用 Alembic 或人工迁移脚本。
- 在开发环境下，推荐将 `docker-compose-dev.yml` 中 `backend` 服务的 `depends_on` 保持为 `condition: service_healthy`，并在 `backend` 启动脚本中实现重试连接逻辑以应对数据库尚未就绪的情况。

---
**记录人**: 自动化实施助手
**时间**: 2026-01-25


### 新增文件与职责（2026-01-25）
- `backend/app/services/data_collector.py`：封装 `akshare` 的数据采集调用；提供 `fetch_kline_data`, `fetch_limit_up_pool`, `fetch_market_fund_flow`, `fetch_market_sentiment`，并实现重试/backoff 逻辑以提高健壮性。
- `backend/app/services/kline_manager.py`：K 线数据管理，采用缓存优先策略：`cache_kline_data`（写入 Redis）、`save_kline_to_db`（向 PostgreSQL 持久化，包含去重/幂等策略）、`get_kline_data`（优先从 Redis 回退到 DB）。
- `backend/app/tasks.py`：基于 APScheduler 的定时任务与手动触发器实现；实现周期性采集（17:00 市场汇总、涨停池等）、缓存清理、以及后台持久化扫描 `persist_cached_klines`（使用 `ThreadPoolExecutor` 提交 `save_kline_to_db` 任务）。
- `backend/app/api/tasks.py`：暴露 HTTP API 以手动触发采集与持久化任务：`/api/v1/tasks/collect/*`, `/api/v1/tasks/persist/klines`, `/api/v1/tasks/cache/cleanup`。

### 架构设计决策（补充）
- 缓存优先读策略：K 线等高频请求优先从 Redis 返回，未命中或缓存失效时再访问 PostgreSQL 并异步写回缓存，以保持低延迟 API 响应。
- 后台持久化采用线程池：考虑到实现简单与无外部依赖，初版将使用 `ThreadPoolExecutor` 在进程内提交持久化任务；长期建议通过 Celery/RQ 等队列系统替换，以支持重试、任务监控和分布式执行。
- 调度器位置：当前将 APScheduler 与 FastAPI 应用生命周期绑定（应用 startup: `start_scheduler()`；shutdown: `stop_scheduler()`），此做法适合单实例开发环境。生产环境应将调度器迁移为独立服务或使用分布式锁（如 Redis 锁）避免多副本重复执行。

### 关键模块交互关系（更新）
- 定时/手动采集流程：
	1. `app/tasks.py` 调度器触发 `DataCollector.fetch_*`，或 API 触发相同方法。
	2. 采集到的原始数据被 `KlineManager.cache_kline_data` 写入 Redis（包含 `meta.hash` 用于幂等判定）。
	3. 后台持久化器 `persist_cached_klines` 扫描 Redis `kline:*` 键并将数据交给 `KlineManager.save_kline_to_db`，保存到 PostgreSQL；成功后在 Redis 中写入 `<key>:persisted` 标记。 
	4. API 层查询 K 线时优先读取 Redis；若缓存不存在则从 PostgreSQL 回退并可选择再次缓存结果。

### 监控与可观测性建议
- 为 `persist_cached_klines`、`collect_market_summary`、`collect_limit_up_pool` 等任务添加指标（计数成功/失败、耗时分布）便于运维监控。
- 将任务日志级别与结构化日志（`structlog` 或 JSON logger）结合，便于集中式日志查询与报警。

---
**记录人**: 自动化实施助手
**时间**: 2026-01-25