# Task Store API 接口设计

## 1. 概述

Task Store 作为任务持久化与切片服务，负责DSL文件的解析、任务切片的生成与存储，以及为Context Service提供任务数据查询服务。

### 1.1 核心功能
- DSL文件上传与解析
- 任务切片生成与存储
- 任务生命周期管理
- 切片数据查询服务
- 任务执行状态跟踪

### 1.2 技术栈
- **框架**: FastAPI
- **数据库**: PostgreSQL + JSONB
- **文件处理**: multipart/form-data
- **认证**: JWT Token

---

## 2. 数据模型

### 2.1 Task 主任务模型
```json
{
  "id": "uuid",
  "parent_task_id": "uuid | null",
  "agent_id": "uuid",
  "payload": {
    "dsl_metadata": {
      "source_file": "filename.dsl",
      "generated_at": "2025-01-15T10:08:09.144390",
      "provider": "openai",
      "model": "deepseek-chat-0324"
    },
    "global_variables": {
      "complaint_severity": {
        "type": "string",
        "default": "",
        "description": "投诉严重等级"
      }
    },
    "runtime_variables": {
      "complaint_severity": "高"
    }
  },
  "status": "pending | in_progress | completed | failed | cancelled",
  "priority": 100,
  "retries": 0,
  "scheduled_at": "2025-01-15T10:08:09.144390",
  "started_at": "2025-01-15T10:08:09.144390",
  "completed_at": "2025-01-15T10:08:09.144390",
  "created_at": "2025-01-15T10:08:09.144390",
  "updated_at": "2025-01-15T10:08:09.144390"
}
```

### 2.2 Task Slice 切片模型
```json
{
  "id": "uuid",
  "task_id": "uuid",
  "slice_index": 0,
  "content": {
    "task_name": "receive_complaint",
    "task_title": "接收与评估投诉",
    "description": [
      "使用CRM系统创建新的投诉工单",
      "记录客户信息、联系方式和投诉内容"
    ],
    "tools": [
      {
        "name": "crm_system_create",
        "description": "创建投诉工单",
        "position": 1
      }
    ],
    "conditions": [
      {
        "expression": "complaint_severity == \"高\" OR customer_type == \"VIP客户\"",
        "true_next": "escalate_complaint",
        "false_next": "regular_processing"
      }
    ],
    "variables_used": ["complaint_severity", "customer_type"],
    "default_next": null
  },
  "status": "pending | in_progress | completed | failed | cancelled",
  "created_at": "2025-01-15T10:08:09.144390",
  "updated_at": "2025-01-15T10:08:09.144390"
}
```

---

## 3. API 接口规范

### 3.1 DSL 上传与解析

#### 3.1.1 文件上传接口
```http
POST /api/v1/tasks/upload-dsl
Content-Type: multipart/form-data
Authorization: Bearer {jwt_token}
```

**请求参数:**
- `file`: DSL文件 (.dsl 格式) [必填]
- `agent_id`: 目标Agent的UUID [必填]
- `metadata`: 任务元数据 [可选]
  - `description`: 任务描述
  - `version`: 版本号
  - `tags`: 标签列表
  - `priority`: 优先级 (默认100)

**响应示例:**
```json
{
  "success": true,
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "parsed",
    "slices_count": 7,
    "variables": ["complaint_severity", "customer_type"],
    "tools_required": [
      "crm_system_create",
      "notification_service",
      "satisfaction_survey",
      "crm_system_update"
    ],
    "created_at": "2025-01-15T10:08:09.144390"
  },
  "message": "DSL解析成功，任务切片已创建"
}
```

**错误响应:**
```json
{
  "success": false,
  "error": {
    "code": "PARSE_ERROR",
    "message": "DSL语法错误：第5行缺少@task声明",
    "details": {
      "line": 5,
      "column": 10,
      "context": "@var complaint_severity"
    }
  }
}
```

#### 3.1.2 文本输入接口
```http
POST /api/v1/tasks/create-from-text
Content-Type: application/json
Authorization: Bearer {jwt_token}
```

**请求体:**
```json
{
  "dsl_content": "# DSL文本内容...\n@var complaint_severity = \"\"\n@task receive_complaint 接收与评估投诉\n...",
  "agent_id": "550e8400-e29b-41d4-a716-446655440000",
  "metadata": {
    "description": "直接输入的DSL流程",
    "version": "1.0",
    "tags": ["customer_service"],
    "priority": 100
  }
}
```

**响应格式:** 与文件上传接口相同

### 3.2 任务管理

#### 3.2.1 任务查询接口
```http
GET /api/v1/tasks/{task_id}
Authorization: Bearer {jwt_token}
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "agent_id": "550e8400-e29b-41d4-a716-446655440001",
    "status": "in_progress",
    "slices_count": 7,
    "variables": ["complaint_severity", "customer_type"],
    "tools_required": [
      "crm_system_create",
      "notification_service",
      "satisfaction_survey",
      "crm_system_update"
    ],
    "progress": {
      "current_slice": 2,
      "completed_slices": 1,
      "failed_slices": 0
    },
    "created_at": "2025-01-15T10:08:09.144390",
    "updated_at": "2025-01-15T10:15:30.256789",
    "metadata": {
      "description": "客户投诉处理流程",
      "version": "1.0",
      "tags": ["customer_service", "complaint"]
    }
  }
}
```

#### 3.2.2 任务列表查询
```http
GET /api/v1/tasks
Authorization: Bearer {jwt_token}
```

**查询参数:**
- `agent_id`: 按Agent ID过滤
- `status`: 按状态过滤 (pending, in_progress, completed, failed, cancelled)
- `page`: 页码 (默认1)
- `limit`: 每页数量 (默认20, 最大100)
- `sort`: 排序字段 (created_at, updated_at, priority)
- `order`: 排序方向 (asc, desc)

**响应示例:**
```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "agent_id": "550e8400-e29b-41d4-a716-446655440001",
        "status": "completed",
        "slices_count": 7,
        "created_at": "2025-01-15T10:08:09.144390",
        "metadata": {
          "description": "客户投诉处理流程"
        }
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 45,
      "pages": 3
    }
  }
}
```

#### 3.2.3 任务状态更新
```http
PUT /api/v1/tasks/{task_id}/status
Content-Type: application/json
Authorization: Bearer {jwt_token}
```

**请求体:**
```json
{
  "status": "in_progress",
  "reason": "开始执行任务",
  "metadata": {
    "current_slice": 0,
    "executor": "agent-001"
  }
}
```

#### 3.2.4 任务删除
```http
DELETE /api/v1/tasks/{task_id}
Authorization: Bearer {jwt_token}
```

### 3.3 任务切片管理

#### 3.3.1 切片列表查询
```http
GET /api/v1/tasks/{task_id}/slices
Authorization: Bearer {jwt_token}
```

**查询参数:**
- `status`: 按状态过滤
- `slice_index`: 按切片索引过滤

**响应示例:**
```json
{
  "success": true,
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "slices": [
      {
        "slice_id": "550e8400-e29b-41d4-a716-446655440010",
        "slice_index": 0,
        "task_name": "receive_complaint",
        "task_title": "接收与评估投诉",
        "description": [
          "使用CRM系统创建新的投诉工单",
          "记录客户信息、联系方式和投诉内容"
        ],
        "tools": [
          {
            "name": "crm_system_create",
            "description": "创建投诉工单",
            "position": 1
          }
        ],
        "conditions": [
          {
            "expression": "complaint_severity == \"高\" OR customer_type == \"VIP客户\"",
            "true_next": "escalate_complaint",
            "false_next": "regular_processing"
          }
        ],
        "variables_used": ["complaint_severity", "customer_type"],
        "status": "completed",
        "created_at": "2025-01-15T10:08:09.144390",
        "updated_at": "2025-01-15T10:15:30.256789"
      }
    ],
    "total_slices": 7
  }
}
```

#### 3.3.2 单个切片查询
```http
GET /api/v1/tasks/{task_id}/slices/{slice_index}
Authorization: Bearer {jwt_token}
```

#### 3.3.3 切片状态更新
```http
PUT /api/v1/tasks/{task_id}/slices/{slice_index}/status
Content-Type: application/json
Authorization: Bearer {jwt_token}
```

**请求体:**
```json
{
  "status": "completed",
  "result": {
    "tool_results": [
      {
        "tool_name": "crm_system_create",
        "success": true,
        "data": {
          "ticket_id": "T20250115001"
        }
      }
    ],
    "variables_updated": {
      "ticket_id": "T20250115001"
    }
  }
}
```

### 3.4 Context Service 集成接口

#### 3.4.1 获取任务上下文
```http
GET /api/v1/context/tasks/{task_id}
Authorization: Bearer {jwt_token}
```

**查询参数:**
- `slice_index`: 指定切片索引 (可选)
- `include_variables`: 是否包含变量信息 (默认true)
- `include_tools`: 是否包含工具信息 (默认true)

**响应示例:**
```json
{
  "success": true,
  "data": {
    "task_info": {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "agent_id": "550e8400-e29b-41d4-a716-446655440001",
      "status": "in_progress"
    },
    "current_slice": {
      "slice_index": 2,
      "task_name": "escalate_complaint",
      "task_title": "升级处理",
      "description": ["将投诉升级到高级处理流程"],
      "tools": [
        {
          "name": "notification_service",
          "description": "发送紧急通知",
          "position": 1
        }
      ],
      "variables_used": ["complaint_severity", "customer_type"]
    },
    "global_variables": {
      "complaint_severity": {
        "type": "string",
        "current_value": "高",
        "description": "投诉严重等级"
      },
      "customer_type": {
        "type": "string",
        "current_value": "VIP客户",
        "description": "客户类型"
      }
    },
    "available_tools": [
      {
        "name": "notification_service",
        "description": "发送紧急通知",
        "schema": {
          "type": "object",
          "properties": {
            "message": {"type": "string"},
            "priority": {"type": "string", "enum": ["low", "medium", "high"]}
          },
          "required": ["message"]
        }
      }
    ]
  }
}
```

#### 3.4.2 批量获取切片信息
```http
POST /api/v1/context/slices/batch
Content-Type: application/json
Authorization: Bearer {jwt_token}
```

**请求体:**
```json
{
  "slice_requests": [
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "slice_index": 0
    },
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440001",
      "slice_index": 2
    }
  ],
  "include_variables": true,
  "include_tools": true
}
```

### 3.5 任务执行控制

#### 3.5.1 启动任务执行
```http
POST /api/v1/tasks/{task_id}/execute
Content-Type: application/json
Authorization: Bearer {jwt_token}
```

**请求体:**
```json
{
  "initial_variables": {
    "complaint_severity": "高",
    "customer_type": "VIP客户"
  },
  "execution_mode": "step_by_step",
  "options": {
    "auto_retry": true,
    "max_retries": 3,
    "timeout": 300
  }
}
```

**execution_mode 选项:**
- `step_by_step`: 逐步执行，每个切片完成后等待确认
- `auto`: 自动执行所有切片
- `manual`: 手动控制每个切片的执行

#### 3.5.2 暂停任务执行
```http
POST /api/v1/tasks/{task_id}/pause
Authorization: Bearer {jwt_token}
```

#### 3.5.3 恢复任务执行
```http
POST /api/v1/tasks/{task_id}/resume
Authorization: Bearer {jwt_token}
```

#### 3.5.4 取消任务执行
```http
POST /api/v1/tasks/{task_id}/cancel
Content-Type: application/json
Authorization: Bearer {jwt_token}
```

**请求体:**
```json
{
  "reason": "用户主动取消",
  "force": false
}
```

---

## 4. 错误处理

### 4.1 错误码定义

| 错误码 | HTTP状态码 | 描述 |
|--------|------------|------|
| `TASK_NOT_FOUND` | 404 | 任务不存在 |
| `SLICE_NOT_FOUND` | 404 | 切片不存在 |
| `PARSE_ERROR` | 400 | DSL解析错误 |
| `INVALID_STATUS` | 400 | 无效的状态转换 |
| `AGENT_NOT_FOUND` | 404 | Agent不存在 |
| `UNAUTHORIZED` | 401 | 未授权访问 |
| `FORBIDDEN` | 403 | 权限不足 |
| `VALIDATION_ERROR` | 422 | 请求参数验证失败 |
| `INTERNAL_ERROR` | 500 | 内部服务器错误 |
| `DATABASE_ERROR` | 500 | 数据库操作失败 |

### 4.2 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": {
      "field": "agent_id",
      "reason": "必须是有效的UUID格式",
      "value": "invalid-uuid"
    },
    "timestamp": "2025-01-15T10:08:09.144390",
    "request_id": "req_550e8400e29b41d4a716446655440000"
  }
}
```

---

## 5. 认证与授权

### 5.1 JWT Token 格式

**Header:**
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**Payload:**
```json
{
  "sub": "agent_id",
  "iat": 1642248489,
  "exp": 1642334889,
  "scope": ["task:read", "task:write", "slice:read", "slice:write"]
}
```

### 5.2 权限范围

| 权限 | 描述 |
|------|------|
| `task:read` | 读取任务信息 |
| `task:write` | 创建、更新、删除任务 |
| `slice:read` | 读取切片信息 |
| `slice:write` | 更新切片状态 |
| `context:read` | 读取上下文信息 |
| `admin` | 管理员权限 |

---

## 6. 性能与限制

### 6.1 请求限制

| 接口类型 | 限制 |
|----------|------|
| DSL上传 | 文件大小 ≤ 10MB |
| 文本输入 | 内容长度 ≤ 1MB |
| 批量查询 | 最多50个切片 |
| 列表查询 | 每页最多100条记录 |

### 6.2 缓存策略

- **任务元数据**: Redis缓存，TTL 5分钟
- **切片内容**: Redis缓存，TTL 10分钟
- **工具Schema**: Redis缓存，TTL 30分钟

### 6.3 数据库优化

- 对 `task_id`, `agent_id`, `status` 建立索引
- 对 `slice_index` 建立复合索引
- 使用 JSONB 的 GIN 索引优化查询

---

## 7. 监控与日志

### 7.1 关键指标

- DSL解析成功率
- 任务创建QPS
- 切片查询延迟
- 数据库连接池使用率
- 缓存命中率

### 7.2 日志格式

```json
{
  "timestamp": "2025-01-15T10:08:09.144390",
  "level": "INFO",
  "service": "task-store",
  "request_id": "req_550e8400e29b41d4a716446655440000",
  "method": "POST",
  "path": "/api/v1/tasks/upload-dsl",
  "agent_id": "550e8400-e29b-41d4-a716-446655440001",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "duration_ms": 245,
  "status_code": 200,
  "message": "DSL解析成功"
}
```

---

## 8. 部署与配置

### 8.1 环境变量

```bash
# 数据库配置
DATABASE_URL=postgresql://user:pass@localhost:5432/taskstore
REDIS_URL=redis://localhost:6379/0

# 服务配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
WORKERS=4

# 认证配置
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# 文件上传配置
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_DIR=/tmp/uploads

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 8.2 Docker 部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 9. 测试用例

### 9.1 单元测试覆盖

- DSL解析器测试
- 数据模型验证测试
- API端点测试
- 错误处理测试
- 权限验证测试

### 9.2 集成测试

- 完整的DSL上传到切片查询流程
- Context Service集成测试
- 数据库事务测试
- 缓存一致性测试

### 9.3 性能测试

- 并发DSL上传测试
- 大量切片查询测试
- 数据库连接池压力测试

---

## 10. 版本规划

### v1.0 (当前版本)
- ✅ 基础DSL解析与存储
- ✅ 任务和切片CRUD操作
- ✅ Context Service集成接口

### v1.1 (计划中)
- 🔄 任务模板功能
- 🔄 切片版本管理
- 🔄 批量操作优化

### v1.2 (未来版本)
- 📋 任务调度优化
- 📋 分布式锁支持
- 📋 任务依赖管理

---

## 11. 附录

### 11.1 DSL语法参考

```dsl
# 变量定义
@var variable_name = "default_value"

# 任务定义
@task task_name 任务标题
描述内容...
@tool tool_name
@if condition
  @next true_task
@else
  @next false_task
@endif

# 流程结束
@task END 流程结束
```

### 11.2 常见问题

**Q: DSL文件大小限制是多少？**
A: 目前限制为10MB，如需处理更大文件请联系管理员。

**Q: 支持哪些DSL语法特性？**
A: 支持变量定义、任务定义、工具调用、条件分支、任务跳转等核心特性。

**Q: 如何处理DSL解析错误？**
A: 系统会返回详细的错误信息，包括错误行号和上下文，便于快速定位问题。

**Q: 任务切片的执行顺序如何确定？**
A: 按照slice_index顺序执行，支持条件分支跳转到指定切片。