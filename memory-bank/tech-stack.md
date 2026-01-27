# 股票分析系统 - 技术栈推荐

**文档版本**: v1.0  
**更新日期**: 2026-01-21

---

## 1. 技术栈总览

本文档基于 [stock-design-document.md](stock-design-document.md) 的系统需求，为股票分析系统推荐最合适的技术栈。系统是一个集数据采集、技术指标计算、AI智能分析和可视化展示于一体的综合性金融分析平台。

### 架构层次划分

```
前端应用层 → 后端服务层 → 数据存储层 → 外部集成层
```

---

## 2. 后端技术栈推荐

### 2.1 核心框架选择

#### **推荐方案：Python FastAPI**

**选择理由：**

1. **生态完美匹配**
   - Python 在数据处理、数据科学领域生态最成熟
   - 便于集成 akshare、pandas、numpy 等数据处理库
   - LLM 生态最完善（LangChain、llamaindex 等）
   - 机器学习库支持（scikit-learn、tensorflow）

2. **性能卓越**
   - FastAPI 基于 Starlette 和 Pydantic，性能接近 Go/Rust
   - 异步支持（async/await），天然支持高并发
   - 自动文档生成（Swagger UI），降低前后端沟通成本
   - 验证库内置，数据验证高效

3. **开发效率高**
   - 代码简洁、易读易维护
   - 自动生成 API 文档，无需手动编写
   - 快速原型开发，快速迭代
   - 调试友好，错误信息清晰

4. **社区活跃**
   - 官方文档完善
   - 社区资源丰富
   - 第三方库支持充分

**备选方案对比：**

| 框架 | 性能 | 数据处理 | 学习曲线 | 生态 | 推荐度 |
|------|------|---------|---------|------|--------|
| FastAPI | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **首选** |
| Flask | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | 备选 |
| Django | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 不推荐（过重） |
| Node.js | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | 不推荐（数据处理弱） |

---

### 2.2 关键依赖库

#### 数据处理与获取

```ini
# 股票数据源
akshare==1.14.88              # 主数据源：K线、财务、资金流向、涨停股池等

# 数据处理与分析
pandas==2.1.3                 # DataFrame 处理，数据清洗
numpy==1.26.2                 # 数值计算基础库
scipy==1.11.4                 # 科学计算
```

**为什么使用 akshare？**
- 原生支持股票数据获取（K线、财务指标、涨停股池）
- 接口众多且无登录限制
- 更新频率高（每日更新）
- 与 pandas DataFrame 无缝集成

#### 技术指标计算

```ini
pandas-ta==0.3.14b            # 专业技术指标计算库（推荐）
# 或
TA-Lib==0.4.28                # C 编译库，性能最优（需编译环境）
```

**pandas-ta vs TA-Lib 对比：**

| 因素 | pandas-ta | TA-Lib |
|------|-----------|--------|
| 安装难度 | 简单 pip 安装 | 需 C 编译环境 |
| 性能 | 中等 | 最优 |
| 指标数量 | 140+ | 200+ |
| DataFrame 集成 | 原生支持 | 需转换 |
| 推荐度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

**结论**：优先推荐 `pandas-ta`（开箱即用），也可两者并用

#### 网页爬虫与 HTTP 请求

```ini
# HTTP 请求
httpx==0.25.0                 # 异步 HTTP 客户端（推荐，比 requests 更快）
requests==2.31.0              # 备选：同步 HTTP 客户端

# 网页爬虫
beautifulsoup4==4.12.2        # HTML/XML 解析
lxml==4.9.3                   # XML/HTML 高性能解析器
selenium==4.15.1              # 动态网页爬虫（需要 JavaScript 渲染时）
```

#### AI/LLM 集成

```ini
# LLM 集成框架
langchain==0.1.1              # LLM 应用框架（推荐）
langchain-openai==0.0.5       # OpenAI 集成
langchain-community==0.0.10   # 第三方 LLM 支持

# 直接调用 SDK（可选）
openai==1.3.8                 # OpenAI API SDK
dashscope==1.13.0             # 阿里通义千问 SDK
ernie==0.1.0                  # 百度文心一言 SDK
```

**为什么选 LangChain？**
- 统一接口，支持多个 LLM 供应商
- 提示词管理和模板化
- 链式调用，业务逻辑清晰
- 生态丰富，集成便利

#### 提示词管理系统

```ini
# 提示词管理
jinja2==3.1.2                 # 模板引擎，用于动态填充提示词
pydantic==2.5.0               # 数据验证和序列化（提示词结构化）
```

**提示词管理架构：**
- **提示词存储**：在 `backend/app/prompts.py` 中定义所有分析模式的提示词函数
  - 每个分析模式对应一个 build_*_prompt() 函数
  - 支持参数化提示词模板
  - 内置数据格式转换（DataFrame → Markdown表格）
  
- **提示词版本控制**：
  - 在函数注释中记录版本和更新日期
  - 支持多个版本的提示词并行使用
  
- **输出解析**：
  - LLM 输出结果标准化
  - 使用 Pydantic 模型定义输出 Schema
  - 自动校验输出是否符合预期格式

**9种分析模式的提示词函数列表**：
1. `build_analysis_prompt()` - 个股基础面技术面综合分析
2. `market_analysis_prompt()` - 市场新闻挖掘
3. `recommend_prompt()` - 股票推荐分析
4. `build_guzhi_prompt()` - 公司估值分析
5. `build_touji_prompt()` - 投机套利分析
6. `build_fenshi_prompt()` - 分时走势分析
7. `build_boduan_prompt()` - 波段交易分析
8. `build_duanxian_prompt()` - 短线T+1分析
9. `build_n1n_prompt()` - N+1+N涨停反包分析

#### 异步任务调度

```ini
# 定时任务调度
apscheduler==3.10.4           # 纯 Python 实现（简单任务推荐）
celery==5.3.4                 # 分布式任务队列（复杂任务推荐）
redis==5.0.1                  # Celery 后端存储
```

**选择指南：**
- **简单场景**（定时获取数据、定期爬取新闻）：使用 `apscheduler`
- **复杂场景**（需要分布式处理、任务重试、监控）：使用 `celery + redis`

**推荐方案**：初期使用 `apscheduler`，后期扩展至 `celery`

#### 数据库驱动

```ini
# MySQL 驱动
pymysql==1.1.0                # 纯 Python 实现，易安装
mysql-connector-python==8.2.0 # 官方驱动，性能更优

# ORM 框架
sqlalchemy==2.0.23            # 最流行的 Python ORM
alembic==1.13.0               # SQLAlchemy 迁移工具
```

#### Redis 客户端

```ini
redis==5.0.1                  # 官方 Redis 客户端
```

---

### 2.3 开发工具与运维

#### 依赖管理与环境

```ini
python==3.10.0 或 3.11.0      # Python 版本（推荐 3.11）
pip                           # 包管理工具
poetry==1.7.0                 # 依赖锁定工具（推荐）
pipenv==2023.12.1             # 虚拟环境管理（备选）
```

#### 日志与监控

```ini
python-logging==0.5.1.2       # 内置 logging 足够
# 或扩展方案
structlog==23.2.0             # 结构化日志
python-json-logger==2.0.7     # JSON 格式日志
```

#### 配置管理

```ini
python-dotenv==1.0.0          # 环境变量管理
pydantic-settings==2.1.0      # Pydantic V2 配置管理
```

---

## 3. 前端技术栈推荐

### 3.1 框架选择

#### **推荐方案：React + TypeScript**

**选择理由：**

1. **组件化架构**
   - 天然适合股票数据展示的复杂 UI
   - 可复用的图表、表格、输入组件
   - 单向数据流，易于维护和测试

2. **生态最完善**
   - 图表库丰富（ECharts、Recharts、Chart.js）
   - 状态管理成熟（Redux、Zustand、Jotai）
   - 工具链完善（Vite、webpack）

3. **开发体验最佳**
   - JSX 语法直观
   - DevTools 调试强大
   - HMR（热模块重载）开发效率高

4. **性能优异**
   - 虚拟 DOM，高效渲染
   - 代码分割、懒加载支持
   - 大规模应用验证充分

**备选方案对比：**

| 框架 | 上手难度 | 生态 | 图表支持 | 推荐度 |
|------|--------|------|---------|--------|
| React | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **首选** |
| Vue 3 | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 次选 |
| Angular | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 不推荐（过重） |
| Svelte | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 学习中 |

---

### 3.2 前端依赖栈

#### 核心框架与构建工具

```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "typescript": "^5.3.0",
  "vite": "^5.0.0"            // 超快构建工具，替代 webpack
}
```

#### 路由与状态管理

```json
{
  "react-router-dom": "^6.20.0",   // 路由管理
  "zustand": "^4.4.7"              // 轻量状态管理（推荐）
  // 或
  "redux": "^4.2.1",
  "react-redux": "^8.1.3",
  "@reduxjs/toolkit": "^1.9.7"     // Redux 简化工具
}
```

**Zustand vs Redux：**
- **Zustand**：简洁优雅，代码少，学习曲线平缓（推荐）
- **Redux**：功能强大，适合超大型应用

#### 图表库

```json
{
  "echarts": "^5.4.3",             // 功能最完整（推荐）
  "echarts-for-react": "^3.0.2",   // React 包装
  
  // 或备选
  "recharts": "^2.10.3",           // React 原生，简洁
  "chart.js": "^4.4.0",
  "react-chartjs-2": "^5.2.0"
}
```

**ECharts vs Recharts：**
- **ECharts**：功能完整，K线图表效果最佳（推荐）
- **Recharts**：React 原生，学习曲线平缓

#### HTTP 请求库

```json
{
  "axios": "^1.6.2",               // 最流行，用法简单（推荐）
  "react-query": "^3.39.3",        // 数据获取和缓存管理
  // 或
  "@tanstack/react-query": "^5.28.0"  // React Query 新版本
}
```

#### UI 组件库

```json
{
  "antd": "^5.11.0",               // 企业级 UI 库（功能完整）
  // 或
  "material-ui": "^5.14.0",        // Material Design
  // 轻量选项
  "shadcn/ui": "latest"            // 可定制组件库（推荐用于定制需求）
}
```

#### 样式处理

```json
{
  "tailwindcss": "^3.3.0",         // Utility-first CSS（推荐）
  "postcss": "^8.4.31",
  
  // 或
  "styled-components": "^6.1.0"    // CSS-in-JS
}
```

#### 工具库

```json
{
  "dayjs": "^1.11.10",             // 日期处理（比 moment 轻量）
  "lodash-es": "^4.17.21",         // 工具函数库
  "classnames": "^2.3.2",          // 类名管理
  "jotai": "^2.4.0"                // 原子状态管理（可选）
}
```

#### 开发工具

```json
{
  "@types/react": "^18.2.37",
  "@types/node": "^20.10.5",
  "eslint": "^8.55.0",
  "prettier": "^3.1.1",
  "@vitejs/plugin-react": "^4.2.1"
}
```

---

### 3.3 前端项目结构

```
frontend/
├── src/
│   ├── pages/
│   │   ├── StockAnalysis/          # 股票分析页面
│   │   ├── IndexAnalysis/          # 大盘分析页面
│   │   ├── NewsCenter/             # 新闻资讯页面
│   │   ├── LimitUpPool/            # 涨停股池页面
│   │   └── Layout.tsx              # 布局页面
│   ├── components/
│   │   ├── StockSearch/            # 股票搜索组件
│   │   ├── KLineChart/             # K线图表
│   │   ├── IndicatorDisplay/       # 指标展示
│   │   ├── NewsCard/               # 新闻卡片
│   │   └── common/                 # 通用组件
│   ├── services/
│   │   ├── api.ts                  # API 调用封装
│   │   └── cache.ts                # 缓存管理
│   ├── hooks/
│   │   ├── useAnalysis.ts          # 分析 Hook
│   │   ├── useFetch.ts             # 数据获取 Hook
│   │   └── useLocalStorage.ts      # 本地存储 Hook
│   ├── store/
│   │   └── analysisStore.ts        # Zustand 状态管理
│   ├── types/
│   │   └── index.ts                # TypeScript 类型定义
│   ├── styles/
│   │   └── globals.css             # 全局样式
│   ├── App.tsx
│   └── main.tsx
├── public/
├── vite.config.ts
├── tsconfig.json
└── package.json
```

---

## 4. 数据存储技术栈

### 4.1 关系型数据库

#### **推荐方案：PostgreSQL 15**

**选择理由：**

1. **金融数据场景**
   - ACID 事务支持，数据安全可靠
   - JSON 字段支持技术指标存储
   - 强大的索引机制，查询性能优异

2. **成熟稳定**
   - 企业级应用验证充分
   - 官方文档完善
   - 社区支持强大

3. **版本特性**
   - PostgreSQL 15 支持窗口函数（时间序列查询便利）
   - 性能显著提升
   - CTE（公用表达式）支持

**版本选择：**
- **推荐**：PostgreSQL 15（最新稳定版）

**说明**: 由于预期系统的日活用户（DAU）为个位数，初期可以采用单实例 PostgreSQL（配合充足的垂直资源和合理索引）来满足性能需求；在未来需要扩展时再考虑读写分离或分库分表方案。

**备选方案：**

| 数据库 | 优点 | 缺点 | 场景 |
|--------|------|------|------|
| PostgreSQL 15 | 成熟稳定 | 并发写入一般 | **首选** |
| PostgreSQL | 功能强大，JSON 支持最佳 | 学习曲线较陡 | 数据量大时 |
| MariaDB | PostgreSQL 兼容，性能更优 | 社区较小 | 备选 |
| MongoDB | 灵活的 Schema | 事务支持弱 | 不推荐 |

---

### 4.2 缓存数据库

#### **推荐方案：Redis 7.0+**

**使用场景：**

1. **热点数据缓存**
   - 最近查询的股票数据
   - 技术指标计算结果
   - AI 分析结果

2. **实时情绪指标**
   - 大盘情绪数据
   - 资金流向实时数据

3. **会话管理**
   - 用户登录信息
   - 查询历史

4. **分布式锁**
   - 防止数据重复采集
   - 定时任务互斥

**配置建议：**

```ini
# redis.conf
maxmemory 4gb                    # 最大内存 4GB
maxmemory-policy allkeys-lru     # 淘汰策略：LRU
appendonly yes                   # 持久化：AOF
save 900 1                       # RDB 快照：15分钟1个修改
```

**Key 设计策略：**

```python
# 股票 K 线缓存
stock_kline:{code}:{type}:{date} = JSON
# TTL：7 天（每日更新）

# 技术指标缓存
indicator:{code}:{indicator_type}:{date} = JSON
# TTL：1 天

# 大盘情绪缓存
market_sentiment:{date} = JSON
# TTL：实时更新

# 新闻缓存
news:{category} = JSON
# TTL：12 小时

# 分析结果缓存
analysis:{code}:{type}:{date} = JSON
# TTL：1 天
```

**说明（缓存策略）**: 推荐采用 Redis-First（缓存优先）策略：
- 读：优先查询 Redis 缓存，缓存未命中时回退到 PostgreSQL。
- 写：先写入 Redis（快速响应），再异步落盘到 PostgreSQL（后台任务）。
- 容错：若 Redis 不可用，应直接查询 PostgreSQL 并记录警告；同时考虑重试和告警策略以便恢复。

由于系统预计 DAU 为个位数，该缓存优先策略可以显著降低同步写入对数据库的压力并保证低延迟响应；同时保留异步落盘保证数据持久化。

## 6. AI/LLM 分析框架

### 6.1 提示词管理系统

基于 `prompt.py` 中定义的9种分析模式，系统需要建立完善的提示词管理体系：

#### 提示词架构设计

**核心特点：**
- 每个分析模式对应一个专门的提示词生成函数
- 支持参数化模板，动态替换数据
- 内置数据格式转换（DataFrame → Markdown表格）
- 严格的输出格式规范

**9种分析模式的提示词系统**：

| 分析模式 | 函数名 | 输入数据类型 | 输出格式 | 适用周期 |
|---------|--------|------------|--------|---------|
| 基础面技术面综合 | `build_analysis_prompt()` | 股票基本信息、日K(30天+)、新闻、财务 | 多段分析+交易建议 | 通用 |
| 市场新闻挖掘 | `market_analysis_prompt()` | 新闻列表(top 10) | 3-5只推荐股票+理由 | 每日 |
| 股票推荐分析 | `recommend_prompt()` | 股票详细信息集合 | 深入分析+建议 | 通用 |
| 公司估值分析 | `build_guzhi_prompt()` | 基本信息、技术指标、估值方法 | 估值结果+涨幅预测 | 长期 |
| 投机套利分析 | `build_touji_prompt()` | 日K(14天)、周K、新闻、大盘、板块 | 买卖点+操作手法 | 短期 |
| 分时走势分析 | `build_fenshi_prompt()` | 分时数据、日K、周K、大盘 | 日内买卖点 | 当日 |
| 波段交易分析 | `build_boduan_prompt()` | 财务、日K(60天)、周K(26周)、大盘、板块 | 波段买卖+仓位策略 | 1-2周 |
| 短线T+1分析 | `build_duanxian_prompt()` | 日K(14天)、周K、新闻(1-4条)、大盘、板块 | 机会评级+交易计划+监控清单 | 1-5天 |
| N+1+N反包分析 | `build_n1n_prompt()` | 涨停信息、日K、周K、新闻、大盘、板块 | 反包概率+买卖点 | 当日 |

#### 提示词模板实现

**关键技术点：**

```python
# 1. 提示词函数设计原则
- 参数化：所有动态信息作为函数参数
- 结构化：输入数据需要标准化格式
- 可验证：输出 Schema 需要清晰定义
- 版本化：每个提示词需要版本号和更新日期

# 2. 数据格式转换
- DataFrame → Markdown 表格（便于 LLM 理解）
- 技术指标 → 结构化描述
- 新闻列表 → 摘要形式

# 3. 输出解析
- LLM 输出结果的标准化
- 使用 Pydantic 模型定义期望的 Schema
- 自动校验和异常处理
```

#### 提示词编写标准

**必须包含的元素：**
1. 角色定义（"你是一位...交易员"）
2. 分析框架（多维度、多时间周期）
3. 输入数据清单（明确的数据来源和格式）
4. 输出格式规范（严格的结构要求）
5. 约束条件（精确数值、避免模糊表述）

**示例标准格式**（参考 `build_duanxian_prompt`）：

```markdown
【核心分析框架】
1. 趋势定位系统
   1.1 [具体指标说明]
   1.2 [具体指标说明]

【输出要求】
1. 机会评级（三选一）
2. 精确交易计划
3. 仓位管理建议
4. 监控清单

【风险警示】
- [具体风险提示]
```

### 6.2 LLM 集成策略

#### 多模型支持

```python
# 支持的 LLM 供应商
- OpenAI GPT-4/3.5
- 阿里通义千问（DashScope）
- 百度文心一言（ERNIE）
- 智谱 GLM
- 本地开源模型备选（如 Llama 2）

# 模型选择策略
- 首选：OpenAI GPT-4（性能最优）
- 备选：通义千问（国内服务稳定）
- 降级：GPT-3.5 或本地模型（成本考量）

# 故障转移机制
配置多个 API Key，当一个模型服务异常时：
1. 快速切换到备选模型(换模型)
2. 记录切换日志，便于监控
3. 缓存输出结果，支持离线查询
```

#### LLM 调用配置

```ini
# 调用参数建议
temperature: 0.3-0.5           # 降低随机性，提高结果一致性
max_tokens: 2000-4000          # 确保输出足够长
top_p: 0.9                     # 核心采样参数
presence_penalty: 0.1          # 避免重复
frequency_penalty: 0.1         # 鼓励多样性

# 超时和重试
timeout: 60s
max_retries: 3
backoff_factor: 2
```

**API 交互模式（分析接口建议）**:
 - 对于耗时的 AI 分析请求，建议采用异步任务模式：POST /api/v1/analysis 提交任务后立即返回 `analysis_id`（状态: pending），客户端通过轮询 GET /api/v1/analysis/{analysis_id} 获取最终结果或状态更新。
 - 如果任务在预设超时限制内未完成，API 应返回失败状态和明确的错误信息（例如："analysis_timeout"），并记录原因以便后续重试或人工干预。
 - 对于轻量级、延迟敏感的短时分析，可提供同步接口，但需限制输入规模以保证可控的响应时间。

#### 成本优化

```
估算月度成本（基于日均 100 次分析请求）：
- 每次平均 token 消耗：~1500 tokens（输入+输出）
- 月度总 token：100 × 30 × 1500 = 450 万 tokens
- OpenAI GPT-4：~¥180（按 0.04/1K tokens）
- 通义千问：~¥45（按 0.01/1K tokens）

建议方案：
- 轻量分析用通义千问（成本低）
- 复杂分析用 GPT-4（质量高）
- 实现智能路由，自动选择模型
```

### 6.3 输出结果管理

#### 结果 Schema 定义

```python
# 使用 Pydantic 定义输出模型
class TradingAdvice(BaseModel):
    direction: str              # 买入/卖出
    target_price: float         # 目标价格
    quantity: int               # 交易数量
    stop_loss: float            # 止损价格
    take_profit: float          # 止盈目标
    holding_period: int         # 持仓天数
    risk_level: str             # 风险等级
    
class AnalysisReport(BaseModel):
    analysis_type: str          # 分析模式
    summary: str                # 分析摘要
    details: str                # 详细分析
    trading_advice: TradingAdvice
    confidence_level: float     # 信心度（0-1）
    timestamp: datetime
```

#### 结果存储和查询

```sql
-- 分析历史记录表扩展
ALTER TABLE analysis_history ADD COLUMN (
    analysis_mode VARCHAR(50),      -- 分析模式（基础/波段/短线等）
    llm_model VARCHAR(50),          -- 使用的 LLM 模型
    prompt_version VARCHAR(10),     -- 提示词版本
    input_hash VARCHAR(64),         -- 输入数据摘要（用于去重）
    confidence_score DECIMAL(3,2),  -- 置信度分数
    INDEX idx_mode (analysis_mode),
    INDEX idx_timestamp (created_at)
);
```

---

## 7. 数据存储技术栈

### 5.1 股票数据源

#### **主数据源：akshare**

```python
import akshare as ak

# 关键接口列表
ak.stock_zh_a_hist()              # K线数据（日/周/月）
ak.stock_zh_a_hist_min_em()       # 分时数据
ak.stock_individual_basic_info_xq()  # 公司基本信息
ak.stock_financial_abstract_new_ths() # 财务指标
ak.stock_market_fund_flow()       # 大盘资金流向
ak.stock_market_activity_legu()   # 市场活跃度
ak.stock_zt_pool_em()             # 涨停股池
ak.stock_board_concept_index_ths() # 概念板块指数
ak.stock_news_em()                # 个股相关新闻
```

**为什么选择 akshare？**
- 接口最完整，覆盖设计文档所有数据需求
- 无登录限制，无 API Key 要求
- 更新频率高（日频）
- 与 pandas 无缝集成
- 文档详细，社区活跃

---

### 5.2 LLM 服务集成

#### **支持多个 LLM 提供商**

| LLM 服务 | API Key 获取 | 推荐度 | 使用场景 |
|---------|-----------|--------|---------|
| OpenAI GPT-4 | https://platform.openai.com | ⭐⭐⭐⭐⭐ | 分析质量最高 |
| 阿里通义千问 | https://qianwen.aliyun.com | ⭐⭐⭐⭐ | 国内延迟低 |
| 百度文心一言 | https://yiyan.baidu.com | ⭐⭐⭐⭐ | 国内生态好 |
| 智谱 GLM | https://open.bigmodel.cn | ⭐⭐⭐⭐ | 国内可用 |

**集成方式**（使用 LangChain）：

```python
# 方案 1：OpenAI
from langchain.llms import OpenAI

llm = OpenAI(
    model_name="gpt-4",
    api_key="your-api-key",
    temperature=0.7
)

# 方案 2：通义千问
from langchain.chat_models import ChatAlibaba

llm = ChatAlibaba(
    model_name="qwen-plus",
    dashscope_api_key="your-api-key"
)

# 方案 3：文心一言
from langchain.llms import Baidu

llm = Baidu(
    model_name="ernie-bot",
    baidu_api_key="your-api-key"
)
```

**成本对比（2024 年价格）：**

| LLM | 输入价格 | 输出价格 | 月均成本估算 |
|-----|---------|---------|-----------|
| GPT-4 | $0.03/1K | $0.06/1K | $30-100 |
| 通义千问 | ¥0.001/1K | ¥0.002/1K | ¥50-200 |
| 文心一言 | ¥0.008/1K | ¥0.008/1K | ¥50-300 |

**推荐策略：**
1. 初期使用 GPT-4（分析质量最高，验证方案可行性）
2. 大规模部署使用通义千问（成本低，国内延迟低）
3. 支持多模型切换，实现智能降级

---

## 6. 部署与运维技术栈
首选本地部署：建议使用 Docker 容器或本地启动脚本进行部署（优先本地/自托管方式），在需要时再考虑云托管方案。


### 6.1 容器化

#### **推荐方案：Docker + Docker Compose**

**关键文件：**

```dockerfile
# Dockerfile (后端)
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/stock_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - mysql
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_PASSWORD: stock_pass_2026
      - POSTGRES_DB: stock_analysis_db
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7.0-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

---

### 6.2 Web 服务器

#### **推荐方案：Nginx**

**配置要点：**

```nginx
# nginx.conf
server {
    listen 80;
    server_name example.com;

    # 前端静态资源
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket 支持（可选）
    location /ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

### 6.3 监控与日志

#### **推荐方案：Prometheus + Grafana + ELK**

**核心组件：**

```ini
# 指标监控
prometheus==latest          # 指标采集
grafana==latest            # 仪表板展示

# 日志收集
elasticsearch==8.0         # 日志存储
kibana==8.0               # 日志查询
logstash==8.0             # 日志处理

# Python 集成
prometheus-client==0.19.0  # Python 客户端
python-json-logger==2.0.7  # JSON 日志格式
```

**关键指标：**

```python
# 核心业务指标
analysis_request_total      # 分析请求总数
analysis_duration_seconds   # 分析耗时
llm_api_calls              # LLM API 调用数
data_fetch_errors          # 数据获取错误

# 系统指标
http_request_duration_seconds
http_requests_total
database_connection_pool_size
redis_command_duration_seconds
```

---

## 7. 开发工具与工作流

### 7.1 版本控制与协作

```ini
git                         # 版本控制
github/gitee               # 代码托管
```

**分支策略：**
```
main                        # 生产分支
├── develop                # 开发分支
│   ├── feature/*          # 功能分支
│   ├── bugfix/*           # 修复分支
│   └── refactor/*         # 重构分支
└── release/*              # 发布分支
```

---

### 7.2 IDE 与编辑器

**后端开发：**
- VS Code（推荐）+ Python 扩展
- PyCharm Professional（功能强大）

**前端开发：**
- VS Code（推荐）+ Vue 等扩展
- WebStorm（功能专业）

---

### 7.3 代码质量工具

#### 后端（Python）

```ini
# 代码检查
pylint==3.0.0
flake8==6.1.0
black==23.12.0             # 代码格式化

# 类型检查
mypy==1.7.1

# 测试
pytest==7.4.3
pytest-cov==4.1.0
pytest-asyncio==0.21.1    # 异步测试支持
```

#### 前端（React）

```json
{
  "eslint": "^8.55.0",
  "prettier": "^3.1.1",
  "vitest": "^1.0.4",
  "@testing-library/react": "^14.1.2"
}
```

---

### 7.4 文档生成

```ini
# API 文档（FastAPI 自动生成）
# http://localhost:8000/docs

# 代码文档
sphinx==7.2.6              # Python 文档生成
sphinx-rtd-theme==2.0.0    # ReadTheDocs 主题

# 前端文档
storybook==7.6.0           # React 组件文档
```

---

## 8. 完整技术栈总结表

### 8.1 技术栈对照表

| 层次 | 组件 | 技术方案 | 版本 | 推荐度 |
|------|------|---------|------|--------|
| **后端框架** | Web 框架 | FastAPI | 0.108+ | ⭐⭐⭐⭐⭐ |
| | 数据处理 | Pandas | 2.1.0+ | ⭐⭐⭐⭐⭐ |
| | 数据源 | akshare | 1.14+ | ⭐⭐⭐⭐⭐ |
| | 技术指标 | pandas-ta | 0.3+ | ⭐⭐⭐⭐⭐ |
| | LLM 框架 | LangChain | 0.1+ | ⭐⭐⭐⭐⭐ |
| | 任务调度 | APScheduler | 3.10+ | ⭐⭐⭐⭐ |
| | 数据库 ORM | SQLAlchemy | 2.0+ | ⭐⭐⭐⭐⭐ |
| **前端框架** | UI 框架 | React | 18.2+ | ⭐⭐⭐⭐⭐ |
| | 语言 | TypeScript | 5.3+ | ⭐⭐⭐⭐⭐ |
| | 构建工具 | Vite | 5.0+ | ⭐⭐⭐⭐⭐ |
| | 路由 | React Router | 6.20+ | ⭐⭐⭐⭐⭐ |
| | 状态管理 | Zustand | 4.4+ | ⭐⭐⭐⭐⭐ |
| | 图表库 | ECharts | 5.4+ | ⭐⭐⭐⭐⭐ |
| | UI 组件 | Ant Design | 5.11+ | ⭐⭐⭐⭐ |
| | 样式 | Tailwind CSS | 3.3+ | ⭐⭐⭐⭐ |
| **数据存储** | 关系型 DB | PostgreSQL | 8.0.35+ | ⭐⭐⭐⭐⭐ |
| | 缓存 DB | Redis | 7.0+ | ⭐⭐⭐⭐⭐ |
| **部署运维** | 容器化 | Docker | 24.0+ | ⭐⭐⭐⭐⭐ |
| | 编排 | Docker Compose | 2.23+ | ⭐⭐⭐⭐⭐ |
| | Web 服务器 | Nginx | 1.25+ | ⭐⭐⭐⭐⭐ |
| | 监控 | Prometheus | latest | ⭐⭐⭐⭐ |
| | 日志 | ELK Stack | 8.0+ | ⭐⭐⭐⭐ |

---

### 8.2 依赖版本冻结建议

**后端 requirements.txt（推荐版本）：**

```
# 核心框架
fastapi==0.108.0
uvicorn[standard]==0.24.0
pydantic==2.5.3
pydantic-settings==2.1.0

# 数据处理
pandas==2.1.3
numpy==1.26.2
scipy==1.11.4

# 数据源
akshare==1.14.88

# 技术指标
pandas-ta==0.3.14b

# HTTP 请求
httpx==0.25.0
requests==2.31.0

# 网页爬虫
beautifulsoup4==4.12.2
lxml==4.9.3

# LLM 集成
langchain==0.1.1
langchain-openai==0.0.5
langchain-community==0.0.10

# 数据库
sqlalchemy==2.0.23
pymysql==1.1.0
redis==5.0.1
alembic==1.13.0

# 任务调度
apscheduler==3.10.4

# 日志与监控
structlog==23.2.0
python-json-logger==2.0.7
prometheus-client==0.19.0

# 工具
python-dotenv==1.0.0
python-multipart==0.0.6
```

**前端 package.json（推荐版本）：**

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "zustand": "^4.4.7",
    "axios": "^1.6.2",
    "@tanstack/react-query": "^5.28.0",
    "echarts": "^5.4.3",
    "echarts-for-react": "^3.0.2",
    "antd": "^5.11.0",
    "dayjs": "^1.11.10",
    "lodash-es": "^4.17.21"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "@vitejs/plugin-react": "^4.2.1",
    "@types/react": "^18.2.37",
    "@types/react-dom": "^18.2.15",
    "tailwindcss": "^3.3.0",
    "postcss": "^8.4.31",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.55.0",
    "prettier": "^3.1.1"
  }
}
```

---

## 9. 技术栈学习路线

### 9.1 开发人员技能要求

| 角色 | 必修技能 | 优选技能 | 学习周期 |
|------|---------|---------|---------|
| **后端开发** | Python, FastAPI, SQL | 数据分析, LLM, Docker | 4-8 周 |
| **前端开发** | React, TypeScript, CSS | 数据可视化, 状态管理 | 4-6 周 |
| **全栈开发** | 后端 + 前端所有 | 系统设计, DevOps | 8-12 周 |

---

### 9.2 推荐学习顺序

**后端开发路线：**
1. Python 基础（1 周）
2. FastAPI 框架（1 周）
3. 数据处理：pandas + numpy（1-2 周）
4. 数据库：PostgreSQL + SQLAlchemy（1-2 周）
5. akshare 和数据采集（1 周）
6. LLM 集成：LangChain（1 周）
7. Docker 部署（1 周）

**前端开发路线：**
1. React 基础（1 周）
2. TypeScript（1 周）
3. 组件开发（1-2 周）
4. 图表集成：ECharts（1 周）
5. 状态管理：Zustand（0.5 周）
6. 路由和 API 集成（1 周）
7. 样式和美化（1 周）

---

## 10. 成本估算

### 10.1 基础设施成本（月均）

| 项目 | 成本 | 说明 |
|------|------|------|
| 云服务器 | ¥200-500 | 2-4 核 CPU, 4-8GB RAM |
| 数据库 | ¥100-300 | PostgreSQL RDS |
| 缓存 | ¥50-100 | Redis 缓存 |
| CDN | ¥50-100 | 前端静态资源加速 |
| LLM API | ¥50-500 | 根据调用频率 |
| **合计** | **¥450-1400** | - |

### 10.2 开发成本

| 阶段 | 工作量 | 人员 | 时间 |
|------|--------|------|------|
| 基础架构 | 80 小时 | 1 人 | 2 周 |
| 数据采集 | 120 小时 | 1 人 | 3 周 |
| AI 集成 | 120 小时 | 1 人 | 3 周 |
| 前端开发 | 120 小时 | 1 人 | 3 周 |
| 测试部署 | 80 小时 | 1 人 | 2 周 |
| **总计** | **520 小时** | **1 人** | **13 周** |

---

## 11. 风险与建议

### 11.1 技术风险与应对

| 风险 | 影响程度 | 应对措施 |
|------|--------|---------|
| akshare API 变更 | 高 | 多源备份，监控 API 更新 |
| LLM API 可用性 | 中 | 多模型支持，本地备份方案 |
| 数据库性能 | 中 | 合理索引，读写分离 |
| 前端复杂性 | 中 | 组件化架构，充分测试 |

### 11.2 优化建议

1. **分阶段部署**
   - Phase 1：核心分析功能
   - Phase 2：大盘分析模块
   - Phase 3：新闻爬取模块

2. **性能优化优先级**
   - 缓存策略（Redis）→ 数据库查询优化 → 前端渲染优化

3. **开发工具投入**
   - IDE：VS Code（免费）+ 扩展
   - 协作：GitHub（免费）
   - 监控：开源方案（Prometheus + Grafana）

---

## 12. 技术栈决策矩阵

### 核心技术决策

```
┌─────────────────────────────────────────────────────────┐
│                   后端（Python）                        │
│  ┌──────────┐  ┌─────────┐  ┌────────────┐            │
│  │FastAPI  │→ │Pandas  │→ │akshare    │            │
│  └──────────┘  └─────────┘  └────────────┘            │
│        ↓            ↓              ↓                    │
│  ┌──────────────────────────────────────┐              │
│  │   PostgreSQL 8.0 + Redis 7.0              │              │
│  │   SQLAlchemy ORM + APScheduler       │              │
│  │   LangChain + LLM API                │              │
│  └──────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              前端（React + TypeScript）                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  React  │→ │  Vite   │→ │ECharts   │             │
│  └──────────┘  └──────────┘  └──────────┘             │
│        ↓            ↓              ↓                    │
│  ┌──────────────────────────────────────┐              │
│  │   Zustand + React Router DOM         │              │
│  │   Axios + React Query                │              │
│  │   Ant Design + Tailwind CSS          │              │
│  └──────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│           部署 & 运维（Docker + Nginx）                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Docker  │→ │Nginx    │→ │ 云服务器  │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
```

---

## 13. 总结与建议

### 13.1 最终推荐方案

本技术栈推荐方案经过综合评估，具有以下特点：

✅ **最优的技术匹配**
- Python 生态最符合金融数据分析需求
- FastAPI + React 组合是当前最流行的全栈方案
- akshare 完美覆盖所有数据获取需求

✅ **最高的开发效率**
- FastAPI 自动 API 文档
- React + TypeScript 提升代码质量
- Vite 超快的开发体验

✅ **最好的成本收益**
- 开源工具为主，降低许可成本
- 社区活跃，第三方资源丰富
- 人才相对容易招聘

✅ **最强的可维护性**
- 技术栈生态稳定
- 文档完善，学习资源丰富
- 团队易于扩展

### 13.2 立即行动建议

1. **周一**：环境搭建（Python + Node.js + PostgreSQL + Redis）
2. **周二-三**：项目框架初始化（FastAPI + React）
3. **周四-五**：数据采集模块原型（akshare 集成）
4. **下周**：API 设计和前端页面框架

### 13.3 持续改进计划

- **月度审查**：技术栈更新检查
- **季度优化**：性能瓶颈分析和优化
- **年度评估**：架构升级和扩展性检讨

---

## 附录

### 参考资源链接

**后端框架文档：**
- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://docs.sqlalchemy.org/

**前端框架文档：**
- React: https://react.dev/
- Vite: https://vitejs.dev/

**数据处理库：**
- pandas: https://pandas.pydata.org/
- akshare: https://akshare.akfamily.xyz/

**部署工具：**
- Docker: https://www.docker.com/
- Nginx: https://nginx.org/

---

**文档完成日期**：2026-01-21  
**作者**：AI Assistant  
**版本控制**：Tech Stack v1.0
