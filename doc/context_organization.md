# Prompt 上下文组织方案

## 1. 总览
Context Service 负责为分布式 Agent 动态生成高质量 Prompt。本方案将上下文划分为 **5 块内容**，并遵循 **3 条注入原则**，以在保证决策准确性的同时尽量压缩 token。

## 2. Prompt 五块内容
| 区块 | 作用 | 典型字段 |
|------|------|---------|
| 1. SYSTEM | 设定角色、语言、输出格式等长期规则 | role, language, output_format, tool_policy |
| 2. TASK | 当前正在执行的任务定义 | id, title, steps, conditionals, next |
| 3. ALLOWED_TOOLS | 本任务可调用的工具及参数模式 | name, description, args_schema |
| 4. CONTEXT_DATA | 动态业务 & 环境数据 | 全局变量、结果数据、时间、运行环境、外部系统状态 |
| 5. INSTRUCTION | 指令 Agent 如何返回结果 | tool 调用格式、跳转格式、异常处理 |

### 2.1 SYSTEM
- 角色定位：如 “客户投诉流程执行 Agent”。
- 语言约束：必须中文输出。
- 输出格式：JSON 结构化返回。
- 允许思维模式：chain-of-thought 用于外部 scratch-pad。

### 2.2 TASK
- 只注入“当前任务”而非全流程。
- 包含正文步骤、条件分支、跳转目标。

### 2.3 ALLOWED_TOOLS
- 从 Tool Registry 动态查询当前任务使用到的工具。
- 仅列出 name、description、args_schema 三项。

### 2.4 CONTEXT_DATA
- 业务变量：`complaint_severity`, `customer_type` 等。
- 结果数据：上一步工具返回值（如 `ticket_id`）。
- 环境状态：当前时间、runtime_env、外部系统健康度等。

### 2.5 INSTRUCTION
- 工具调用返回格式：`{"tool":"<name>", "args":{...}}`。
- 任务完成跳转格式：`{"next_task":"<id>"}`。
- 其它：错误重试、等待用户。

## 3. 三条注入原则
1. **最小相关性**：仅当任务正文引用到变量/关键词时才注入对应数据。
2. **动态抽取**：运行时解析 `@tool`、`{{var}}`、关键字（如 “小时内”）来决定注入内容。
3. **缓存与摘要**：
   - SYSTEM 永久缓存；
   - 不变信息（runtime_env 等）提前放 SYSTEM；
   - 大对象先摘要，例如健康检查仅注入 `healthy|degraded|down`。

## 4. 环境状态四维度
| 维度 | 字段示例 | 触发条件 |
|------|---------|---------|
| 时间 | current_time, runtime_duration | 任务含时间逻辑或占位符 |
| 运行环境 | runtime_env, code_version | 任务含工具调用或环境差异 |
| 会话信息 | operator, role, user_pref | 任务需考虑权限/偏好 |
| 外部系统 | crm_status, api_rate_limit | 任务调用对应系统 |

## 5. Prompt 示例
```text
### SYSTEM
你是客户投诉流程执行 Agent …

### TASK
id: escalate_complaint
steps:
1. …
3. @tool notification_service

### ALLOWED_TOOLS
notification_service: 向相关部门推送紧急通知
必填参数: {"ticket_id":"string","severity":"string"}

### CONTEXT_DATA
ticket_id: "T20250715001"
complaint_severity: "高"
current_time: "2025-07-15T18:42:09+08:00"
crm_status: "healthy"

### INSTRUCTION
1. 若需调用工具，返回 {"tool":…, "args":{…}}
2. 若任务完成，返回 {"next_task":"customer_confirmation"}
```

## 6. 风险控制
- LLM 返回非 JSON：使用正则校验 + 重试策略。
- Token 过长：Prompt Builder 在 CONTEXT_DATA 层面先做裁剪。
- 工具升级：Tool Registry 加版本字段并通过 `args_schema.version` 管控。 