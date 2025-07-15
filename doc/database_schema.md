# 数据库表设计（初版）

> 说明：
> 1. 以 PostgreSQL 为参考实现，部分字段使用 `jsonb` / `uuid` / `timestamptz` / `vector`（pgvector）等数据类型。
> 2. 大写单词为 **主模块**，与 `architecture_diagram.md` / `module_overview.md` 中的节点名称保持一致；其下缩进一级的为具体数据表。
> 3. 字段末尾带 *️⃣ 的字段建议建立索引。可根据实际查询模式再补充复合索引。
> 4. ENUM 类型仅示意，可按业务需要扩充。

---

## EVENT QUEUE（任务调度缓冲池）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | uuid | 主键 |
| task_id | uuid | 关联 `TASK_STORE.tasks.id` *️⃣ |
| payload | jsonb | 任务载荷快照 |
| priority | smallint | 优先级，数值越小优先级越高；默认 `100` *️⃣ |
| available_at | timestamptz | 可被消费的时间点（支持延时任务）*️⃣ |
| visibility_timeout | integer | 消费超时秒数，防止重复消费 |
| attempts | smallint | 已尝试次数 |
| max_attempts | smallint | 最大重试次数 |
| created_at | timestamptz | 创建时间 |
| updated_at | timestamptz | 更新时间 |

---

## AGENT REGISTRY（Agent 元数据中心）

### agents
| 字段 | 类型 | 说明 |
|------|------|------|
| id | uuid | 主键 |
| name | text | Agent 名称 *️⃣ |
| description | text | 描述 |
| base_prompt | text | 默认 SYSTEM Prompt |
| allowed_tool_ids | uuid[] | 允许调用的工具列表 |
| status | agent_status_enum | `active / inactive / error` |
| created_at | timestamptz | 创建时间 |
| updated_at | timestamptz | 更新时间 |

---

## TASK STORE（任务持久化与切片服务）

### tasks
| 字段 | 类型 | 说明 |
|------|------|------|
| id | uuid | 主键 |
| parent_task_id | uuid | 对应父任务，可为空实现多级切片 *️⃣ |
| agent_id | uuid | 关联 `AGENT_REGISTRY.agents.id` *️⃣ |
| payload | jsonb | 初始任务载荷 |
| status | task_status_enum | `pending / in_progress / completed / failed / cancelled` *️⃣ |
| priority | smallint | 调度优先级，默认 `100` |
| retries | smallint | 已重试次数 |
| scheduled_at | timestamptz | 计划开始时间 |
| started_at | timestamptz | 实际开始时间 |
| completed_at | timestamptz | 完成时间 |
| created_at | timestamptz | 创建时间 |
| updated_at | timestamptz | 更新时间 |

### task_slices
| 字段 | 类型 | 说明 |
|------|------|------|
| id | uuid | 主键 |
| task_id | uuid | 关联 `tasks.id` *️⃣ |
| slice_index | integer | 切片序号，0 起始 *️⃣ |
| content | jsonb | 切片内容（如 DSL 片段） |
| status | task_status_enum | 切片状态 |
| created_at | timestamptz | 创建时间 |
| updated_at | timestamptz | 更新时间 |

---

## TOOL REGISTRY（工具定义仓库）

### tools
| 字段 | 类型 | 说明 |
|------|------|------|
| id | uuid | 主键 |
| name | text | 工具名 *️⃣ |
| version | text | 版本号，例如 `v1.0.0` |
| execution_mode | tool_mode_enum | `cloud / local` |
| schema | jsonb | OpenAPI / JSON Schema 描述 |
| description | text | 描述 |
| created_at | timestamptz | 创建时间 |
| updated_at | timestamptz | 更新时间 |

### tool_keywords（可选，支持关键词 RAG）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键 |
| tool_id | uuid | 关联 `tools.id` *️⃣ |
| keyword | text | 关键词 *️⃣ |

---

## KNOWLEDGE SERVICE（知识检索）
> 该模块采用外部向量数据库 / 检索服务（如 Pinecone、Weaviate），本地数据库无需存储，故不创建数据表。

---

## RESULT STORE（结果与变量仓库）

### task_results
| 字段 | 类型 | 说明 |
|------|------|------|
| id | uuid | 主键 |
| task_id | uuid | 关联 `TASK_STORE.tasks.id` *️⃣ |
| tool_id | uuid | 可为空，关联 `TOOL_REGISTRY.tools.id` |
| result_type | result_type_enum | `tool_result / task_result` |
| data | jsonb | 结果数据 |
| created_at | timestamptz | 创建时间 |

---

## REVIEW MODEL（结果评估）

### review_records
| 字段 | 类型 | 说明 |
|------|------|------|
| id | uuid | 主键 |
| task_id | uuid | 关联 `TASK_STORE.tasks.id` *️⃣ |
| status | review_status_enum | `pass / fail` *️⃣ |
| score | numeric(5,2) | 评估分数 |
| reviewer | text | 评估器（模型 / 人工） |
| created_at | timestamptz | 创建时间 |

---

## ENUM Type 定义

```sql
CREATE TYPE agent_status_enum   AS ENUM ('active', 'inactive', 'error');
CREATE TYPE task_status_enum    AS ENUM ('pending', 'in_progress', 'completed', 'failed', 'cancelled');
CREATE TYPE tool_mode_enum      AS ENUM ('cloud', 'local');
CREATE TYPE result_type_enum    AS ENUM ('tool_result', 'task_result');
CREATE TYPE review_status_enum  AS ENUM ('pass', 'fail');
```

---

## 可能的索引示例

```sql
-- EVENT QUEUE
CREATE INDEX idx_event_queue_available   ON event_queue (available_at);
CREATE INDEX idx_event_queue_task        ON event_queue (task_id);

-- TASK STORE
CREATE INDEX idx_tasks_status            ON tasks (status);
CREATE INDEX idx_tasks_agent_status      ON tasks (agent_id, status);
CREATE INDEX idx_task_slices_task        ON task_slices (task_id);

-- TOOL REGISTRY
CREATE INDEX idx_tools_name              ON tools (name);
CREATE INDEX idx_tool_keywords_keyword   ON tool_keywords USING gin (keyword gin_trgm_ops);

-- KNOWLEDGE SERVICE
-- 无本地表，索引无需创建

-- RESULT STORE
CREATE INDEX idx_task_results_task       ON task_results (task_id);

-- REVIEW MODEL
CREATE INDEX idx_review_status           ON review_records (status);
```

---

> **后续工作**
> 1. 根据业务增长，补充如 `agent_run_logs`、`tool_execution_logs` 等审计/可观测性表。
> 2. 结合实际访问模式优化索引、分区策略。
> 3. 若任务量巨大，可将 `event_queue` 与 `tasks` 拆分至独立分库或使用消息中间件（如 Kafka / RabbitMQ）。 