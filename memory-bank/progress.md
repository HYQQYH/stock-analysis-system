# Progress Log - 2026-01-25

## Summary
- Phase: 第1阶段（第1-2周）基础架构搭建 — 已完成（见下）

## 已完成工作项
- 创建并规范化数据库 schema: `backend/app/db/schema_pg.sql`（PostgreSQL 15 兼容）
- 在 `backend/app/models/models.py` 中完成 SQLAlchemy ORM 模型定义并与 schema 对齐
- 编写并添加 `docker-compose-dev.yml`，包含 `postgres:15-alpine` 与 `redis:7-alpine` 服务
- 通过 Docker 启动并验证了 PostgreSQL 与 Redis 容器

## 验证测试结果
- PostgreSQL 容器: `stock_analysis_postgres` 已成功初始化并执行 `schema_pg.sql`。
	- 已创建表（通过 `\dt` 检查）:
		- `stock_info`, `stock_kline_data`, `stock_indicators`, `analysis_history`, `financial_news`,
			`market_sentiment`, `market_fund_flow`, `market_activity`, `limit_up_stock_pool`,
			`stock_intraday_data`, `sector_kline_data`, `cache_metadata`（共 12 张表）
	- 示例数据已插入（`stock_info` 示例记录 3 条；`SELECT count(*) FROM stock_info;` 返回 3）

- Redis 容器: `stock_analysis_redis` 已就绪并可连通。
	- `PING` 返回 `PONG`；可成功 `SET` 与 `GET` 测试键（`test_key` → `ok`）

## 遇到的问题与解决方案
- 问题: 初始 `backend/app/db/schema.sql` 为项目内 Python 字符串常量形式，不适合直接作为容器初始化 SQL 文件。
	- 解决: 新增 `backend/app/db/schema_pg.sql`（PostgreSQL 语法），并挂载到容器初始化目录 `/docker-entrypoint-initdb.d/`，确保容器启动时自动执行建表脚本。

- 问题: `docker-compose` 使用的 `version` 字段触发了弃用告警。
	- 解决: 该警告无阻影响启动，后续可删除 `version` 字段以消除警告（已在本次 `docker-compose-dev.yml` 中保留但可改进）。

## 学到的架构洞察
- 在项目中同时保留 SQL 建表脚本（用于容器初始化/DB 管理）和 ORM 模型（用于运行时）是必要的，二者需保持同步并由 CI 或初始化脚本校验。
- 将 SQL 文件挂载到 `docker-entrypoint-initdb.d/` 是在容器首次初始化阶段自动建表的简洁方式，但需注意该文件仅在数据库数据卷为空时生效。

## 下一步 / 建议
1. 在 `backend/.env`（基于 `.env.example`）中写入当前开发数据库与 Redis 连接字符串并加入 `.gitignore`（若尚未）。
2. 在 `backend/app/db/database.py` 中增加一个 `init_db()` 函数，可在非容器场景或 CI 中运行以确保 schema 与 ORM 同步（可用 Alembic 替代）。
3. 创建并运行一个小型 Python 验证脚本，使用 SQLAlchemy 导入模型并执行简单查询（我可以代为执行）。
4. 将 `docker-compose-dev.yml` 的 `version` 字段移除并在 README 中记录启动命令。

---
## 步骤 5.1-5.4：akshare 集成与数据采集（新增）

### 完成的工作项
- 在 `backend/app/services/` 中新增 `data_collector.py`（封装 akshare 调用并实现重试）
- 新增 `kline_manager.py`（实现 Redis 缓存优先策略、DB upsert 接口 `save_kline_to_db` 与回退读取）
- 新增 `tasks.py`（基于 APScheduler 的定时任务调度，包含市场汇总、涨停池、指数 K 线采集、缓存清理）
- 将调度器在应用启动时启动/停止：在 `backend/app/main.py` 中集成 `start_scheduler()` / `stop_scheduler()`
- 新增 API 路由 `backend/app/api/tasks.py`，提供手动触发任务的 HTTP 接口（collect、persist、cleanup）

### 测试验证结果
- 添加单元测试 `backend/tests/test_data_collector.py`：覆盖方法存在性、重试行为与返回 DataFrame 的基本 coercion。
- 在本地虚拟环境中运行测试：`pytest backend/tests/test_data_collector.py` → `3 passed`。

### 遇到的问题与解决方案
- 问题：`akshare` 的某些函数签名在不同版本中存在差异，直接调用可能抛出 `TypeError`。
	- 解决：在 `DataCollector.fetch_kline_data` 中添加兼容层（先尝试命名参数调用，失败时退回到通用调用），并通过 `_call_with_retry` 捕获并重试。
- 问题：测试不应依赖网络或外部 akshare 服务。
	- 解决：测试中使用 `monkeypatch` 模拟 `akshare.stock_zh_a_hist` 返回字典，确保本地测试稳定且快速。

### 学到的架构洞察
- 缓存优先（Redis）可以显著降低 DB 读取压力，但必须实现幂等的落盘策略；在本次实现中使用输入摘要与按键标记持久化状态作为简易方案。
- 线程池（ThreadPoolExecutor）适合轻量级后台持久化任务；若数据量或并发增加，应切换到独立的任务队列（如 Celery/RQ）来解耦调度和执行。
- 将调度器与应用生命周期绑定（startup/shutdown）便于管理，但应注意在容器化场景中（尤其是多副本）避免重复执行任务 — 生产部署时建议将调度器迁移到单独的 worker 服务或使用分布式锁。

---
**记录人**: 自动化实施助手
**时间**: 2026-01-25

---
**记录人**: 自动化实施助手
**时间**: 2026-01-25
