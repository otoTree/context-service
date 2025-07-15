# 消息传递格式与数据类型规范

> 版本：v0.1  
> 涵盖 `architecture_diagram.md` / `module_overview.md` 中跨模块消息。  
> 约定使用 **JSON** 作为序列化格式，字段命名采用 `snake_case`。

---

## 公共字段（Envelope）
| 字段 | 类型 | 说明 |
|------|------|------|
| message_id | `string(uuid)` | 全局唯一消息 ID |
| sent_at | `string(date-time)` | ISO8601 时间戳 |
| trace_id | `string` | 可选，链路追踪 ID |
| schema_version | `string` | 本文档版本号，例如 `v0.1` |

除特殊说明，以下所有消息均默认包含上述 Envelope，并以 **根级字段** 形式存在。

---

## 1. TaskEvent
**方向**：`Event Queue → Agent`

| 字段 | 类型 | 说明 |
|------|------|------|
| task_id | `string(uuid)` | 任务 ID |
| payload | `object` | 任务载荷（任意 JSON，对 Agent 透明） |
| retry_count | `integer` | 已重试次数 |
| max_attempts | `integer` | 最大重试次数 |

**示例**
```jsonc
{
  "message_id": "6f8414d7-8e69-4d6e-b516-6c2ef3fca8d8",
  "sent_at": "2025-07-15T02:03:04Z",
  "schema_version": "v0.1",
  "task_id": "190efc4c-3094-41d4-a6dc-4a0e140bd73e",
  "payload": { "agent_id": "sop agent" },
  "retry_count": 0,
  "max_attempts": 3
}
```

---

## 2. GetContextRequest
**方向**：`Agent → Context Service`

| 字段 | 类型 | 说明 |
|------|------|------|
| agent_id | `string(uuid)` | 发起请求的 Agent |
| task_id | `string(uuid)` | 目标任务 |
| globals | `object` | 运行期全局变量（KV） |

---

## 3. PromptBlocksResponse
**方向**：`Context Service → Agent`

| 字段 | 类型 | 说明 |
|------|------|------|
| system | `string` | SYSTEM Prompt |
| task | `string` | TASK Prompt |
| allowed_tools | `string` | ALLOWED_TOOLS Prompt（YAML / JSON 列表） |
| context_data | `string` | CONTEXT_DATA Prompt（知识片段） |
| instruction | `string` | 最终 INSTRUCTION |

> **注**：为保格式安全，Prompt Blocks 内容建议使用多行字符串或 Base64。

---

## 4. ToolCallRequest（暂时不做设计以及使用）
**方向**：`Agent → Cloud/Local Tool`

| 字段 | 类型 | 说明 |
|------|------|------|
| invocation_id | `string(uuid)` | 本次调用唯一 ID |
| tool_name | `string` | 工具名称 |
| tool_version | `string` | 工具版本 |
| args | `object` | 调用参数 |

### ToolCallResponse（暂时不做设计以及使用）
**方向**：`Tool → Agent`

| 字段 | 类型 | 说明 |
|------|------|------|
| invocation_id | `string(uuid)` | 与请求对应 |
| success | `boolean` | 是否成功 |
| data | `object` | 成功时的返回数据 |
| error | `object` | 失败时的错误信息（code, message） |

---

## 5. ReportResultRequest
**方向**：`Agent → Context Service`

| 字段 | 类型 | 说明 |
|------|------|------|
| task_id | `string(uuid)` | 关联任务 |
| tool_results | `array<ToolResult>` | 工具级结果列表 |
| task_results | `object` | Agent 生成的总结 / 最终输出 |

### ToolResult 对象
| 字段 | 类型 | 说明 |
|------|------|------|
| invocation_id | `string(uuid)` | 调用 ID |
| tool_id | `string(uuid)` | `TOOL_REGISTRY.tools.id` |
| result_type | `string(enum)` | `tool_result` 或其他 |
| data | `object` | 结果负载 |
| created_at | `string(date-time)` | 产生时间 |

---

## 6. EvaluationRequest
**方向**：`Context Service → Review Model`

| 字段 | 类型 | 说明 |
|------|------|------|
| task_id | `string(uuid)` | 待评估任务 |
| task_results | `object` | 同上报内容 |

### EvaluationResponse
**方向**：`Review Model → Result Store & Event Queue`

| 字段 | 类型 | 说明 |
|------|------|------|
| task_id | `string(uuid)` | 目标任务 |
| status | `string(enum)` | `pass` / `fail` |
| score | `number(0-100)` | 评估得分 |
| next_action | `string(enum)` | `retry` / `next_slice` / `none` |

---

## 7. RetryEvent
**方向**：`Review Model → Event Queue`

与 **TaskEvent** 字段一致，区别在于 `retry_count` 已增加。

---

## 数据类型约定（Type Aliases）
| 类型 | 说明 |
|------|------|
| `uuid` | [RFC 4122](https://www.rfc-editor.org/rfc/rfc4122) 标准 UUID 字符串 |
| `date-time` | ISO8601 字符串，如 `2025-07-15T02:03:04Z` |
| `enum` | 枚举值，见数据库中定义 |
| `object` | 任意嵌套 JSON 对象 |
| `array<T>` | JSON 数组，元素类型为 `T` |

---

## 兼容性策略
1. 使用 `schema_version` 字段进行向后兼容。  
2. 新增字段必须保持向后兼容，客户端需忽略未知字段。  
3. 枚举新增值需保证旧客户端处理为安全默认值。

---

> 变更记录
> - v0.1：初稿：定义核心消息与数据类型。 