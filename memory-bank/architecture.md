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

