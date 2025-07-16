# Context Service 数据结构设计

## 1. 概述

本文档定义了Context Service生态系统中所有核心模块的数据结构，包括数据类型、字段约束和样例数据。

---

## 2. Event Queue (EQ) - 事件队列数据结构

### 2.1 TaskEvent - 任务事件

```typescript
interface TaskEvent {
  event_id: string;           // 事件唯一标识，格式: evt_{uuid}
  task_id: string;            // 任务ID，UUID格式
  agent_id: string;           // 目标Agent ID
  payload: TaskPayload;       // 任务载荷
  priority: number;           // 优先级 (0-1000，数值越大优先级越高)
  status: EventStatus;        // 事件状态
  available_at: string;       // 可执行时间，ISO 8601格式
  max_attempts: number;       // 最大重试次数
  current_attempts: number;   // 当前重试次数
  visibility_timeout: number; // 可见性超时时间(秒)
  receipt_handle?: string;    // 接收句柄
  created_at: string;         // 创建时间
  updated_at: string;         // 更新时间
}

type EventStatus = 'queued' | 'processing' | 'completed' | 'failed' | 'expired';

interface TaskPayload {
  slice_index: number;        // 任务切片索引
  variables: Record<string, any>; // 全局变量
  context: ExecutionContext;  // 执行上下文
  retry_reason?: string;      // 重试原因
}

interface ExecutionContext {
  retry_count: number;        // 重试计数
  previous_results: string[]; // 前置结果ID列表
  execution_mode?: string;    // 执行模式
  timeout?: number;           // 超时时间
}
```

**样例数据:**
```json
{
  "event_id": "evt_550e8400e29b41d4a716446655440000",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_id": "550e8400-e29b-41d4-a716-446655440001",
  "payload": {
    "slice_index": 0,
    "variables": {
      "complaint_severity": "高",
      "customer_type": "VIP客户",
      "customer_id": "CUST_20250115001"
    },
    "context": {
      "retry_count": 0,
      "previous_results": [],
      "execution_mode": "auto",
      "timeout": 300
    }
  },
  "priority": 100,
  "status": "queued",
  "available_at": "2025-01-15T10:08:09.144390Z",
  "max_attempts": 3,
  "current_attempts": 0,
  "visibility_timeout": 300,
  "created_at": "2025-01-15T10:08:09.144390Z",
  "updated_at": "2025-01-15T10:08:09.144390Z"
}
```

---

## 3. Agent Registry (AR) - Agent元数据中心数据结构

### 3.1 Agent - Agent实体

```typescript
interface Agent {
  agent_id: string;           // Agent唯一标识，UUID格式
  name: string;               // Agent名称
  role: string;               // Agent角色
  base_prompt: string;        // 基础提示词
  capabilities: string[];     // 能力列表
  network_zone: string;       // 网络区域
  tool_scope: ToolScope;      // 工具权限范围
  knowledge_config: KnowledgeConfig; // 知识配置
  default_env: Record<string, any>; // 默认环境变量
  status: AgentStatus;        // Agent状态
  metrics: AgentMetrics;      // 性能指标
  last_heartbeat: string;     // 最后心跳时间
  created_at: string;         // 创建时间
  updated_at: string;         // 更新时间
}

type AgentStatus = 'active' | 'inactive' | 'busy' | 'error' | 'maintenance';

interface ToolScope {
  allowed_tools: string[];    // 允许使用的工具列表
  execution_modes: ExecutionMode[]; // 支持的执行模式
  security_level: SecurityLevel; // 安全级别
}

type ExecutionMode = 'cloud' | 'agent' | 'hybrid';
type SecurityLevel = 'public' | 'internal' | 'confidential' | 'restricted';

interface KnowledgeConfig {
  domains: string[];          // 知识域列表
  max_snippets: number;       // 最大知识片段数
  trust_threshold: number;    // 信任度阈值 (0-5)
  cache_ttl: number;          // 缓存TTL(秒)
}

interface AgentMetrics {
  cpu_usage: number;          // CPU使用率 (0-100)
  memory_usage: number;       // 内存使用率 (0-100)
  active_tasks: number;       // 活跃任务数
  completed_tasks: number;    // 已完成任务数
  success_rate: number;       // 成功率 (0-1)
  avg_response_time: number;  // 平均响应时间(毫秒)
}
```

**样例数据:**
```json
{
  "agent_id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "complaint-handler-agent",
  "role": "complaint_handler",
  "base_prompt": "你是一个专业的客户投诉处理Agent，负责按照标准流程处理客户投诉，确保客户满意度和问题解决效率。",
  "capabilities": ["python3.10", "gpu", "camera", "nlp_processing"],
  "network_zone": "dc-beijing",
  "tool_scope": {
    "allowed_tools": [
      "crm_system_create",
      "notification_service",
      "satisfaction_survey"
    ],
    "execution_modes": ["cloud", "agent"],
    "security_level": "internal"
  },
  "knowledge_config": {
    "domains": ["crm_policy", "regulation_cn_gdpr", "customer_service"],
    "max_snippets": 5,
    "trust_threshold": 3,
    "cache_ttl": 3600
  },
  "default_env": {
    "language": "zh-CN",
    "timezone": "Asia/Shanghai",
    "response_format": "json"
  },
  "status": "active",
  "metrics": {
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "active_tasks": 2,
    "completed_tasks": 156,
    "success_rate": 0.94,
    "avg_response_time": 1250
  },
  "last_heartbeat": "2025-01-15T10:15:30.256789Z",
  "created_at": "2025-01-15T09:30:00.000000Z",
  "updated_at": "2025-01-15T10:15:30.256789Z"
}
```

---

## 4. Task Store (TS) - 任务存储数据结构

### 4.1 Task - 主任务

```typescript
interface Task {
  task_id: string;            // 任务唯一标识，UUID格式
  name: string;               // 任务名称
  description: string;        // 任务描述
  dsl_content: string;        // DSL原始内容
  parsed_structure: ParsedDSL; // 解析后的结构
  global_variables: Record<string, any>; // 全局变量
  status: TaskStatus;         // 任务状态
  priority: number;           // 优先级
  created_by: string;         // 创建者ID
  assigned_agent: string;     // 分配的Agent ID
  execution_config: ExecutionConfig; // 执行配置
  metadata: TaskMetadata;     // 任务元数据
  created_at: string;         // 创建时间
  updated_at: string;         // 更新时间
  completed_at?: string;      // 完成时间
}

type TaskStatus = 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';

interface ParsedDSL {
  version: string;            // DSL版本
  tasks: TaskDefinition[];    // 任务定义列表
  dependencies: TaskDependency[]; // 任务依赖关系
  global_config: Record<string, any>; // 全局配置
}

interface TaskDefinition {
  id: string;                 // 任务ID
  title: string;              // 任务标题
  description?: string;       // 任务描述
  steps: string[];            // 执行步骤
  tools: string[];            // 需要的工具
  expected_output?: string;   // 期望输出
  timeout?: number;           // 超时时间
}

interface TaskDependency {
  task_id: string;            // 任务ID
  depends_on: string[];       // 依赖的任务ID列表
  condition?: string;         // 依赖条件
}

interface ExecutionConfig {
  max_retries: number;        // 最大重试次数
  timeout: number;            // 超时时间(秒)
  parallel_execution: boolean; // 是否并行执行
  auto_continue: boolean;     // 是否自动继续
}

interface TaskMetadata {
  source: string;             // 来源
  tags: string[];             // 标签
  estimated_duration: number; // 预估执行时间(秒)
  complexity_level: number;   // 复杂度等级 (1-5)
}
```

### 4.2 TaskSlice - 任务切片

```typescript
interface TaskSlice {
  slice_id: string;           // 切片唯一标识
  task_id: string;            // 所属任务ID
  slice_index: number;        // 切片索引
  task_name: string;          // 任务名称
  content: string;            // 切片内容
  required_tools: string[];   // 需要的工具
  input_variables: string[];  // 输入变量
  output_variables: string[]; // 输出变量
  dependencies: string[];     // 依赖的切片ID
  status: SliceStatus;        // 切片状态
  execution_order: number;    // 执行顺序
  estimated_duration: number; // 预估执行时间
  actual_duration?: number;   // 实际执行时间
  retry_count: number;        // 重试次数
  created_at: string;         // 创建时间
  updated_at: string;         // 更新时间
}

type SliceStatus = 'pending' | 'ready' | 'running' | 'completed' | 'failed' | 'skipped';
```

**样例数据:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "客户投诉处理流程",
  "description": "处理VIP客户的高优先级投诉",
  "dsl_content": "@task receive_complaint\ntitle: 接收与评估投诉\nsteps:\n1. 使用CRM系统创建新的投诉工单\n2. 记录客户信息、联系方式和投诉内容\n3. @tool crm_system_create",
  "parsed_structure": {
    "version": "1.0",
    "tasks": [
      {
        "id": "receive_complaint",
        "title": "接收与评估投诉",
        "steps": [
          "使用CRM系统创建新的投诉工单",
          "记录客户信息、联系方式和投诉内容"
        ],
        "tools": ["crm_system_create"],
        "timeout": 300
      }
    ],
    "dependencies": [],
    "global_config": {
      "language": "zh-CN",
      "timezone": "Asia/Shanghai"
    }
  },
  "global_variables": {
    "complaint_severity": "高",
    "customer_type": "VIP客户",
    "customer_id": "CUST_20250115001",
    "complaint_category": "服务质量"
  },
  "status": "running",
  "priority": 100,
  "created_by": "user_admin",
  "assigned_agent": "550e8400-e29b-41d4-a716-446655440001",
  "execution_config": {
    "max_retries": 3,
    "timeout": 1800,
    "parallel_execution": false,
    "auto_continue": true
  },
  "metadata": {
    "source": "customer_service_portal",
    "tags": ["complaint", "vip", "high_priority"],
    "estimated_duration": 600,
    "complexity_level": 3
  },
  "created_at": "2025-01-15T10:00:00.000000Z",
  "updated_at": "2025-01-15T10:08:09.144390Z"
}
```

---

## 5. Knowledge Service (KS) - 知识服务数据结构

### 5.1 KnowledgeSnippet - 知识片段

```typescript
interface KnowledgeSnippet {
  snippet_id: string;         // 片段唯一标识
  source: string;             // 知识源标识
  domain: string;             // 知识域
  content: string;            // 内容
  title?: string;             // 标题
  summary?: string;           // 摘要
  trust_level: number;        // 信任度 (1-5)
  relevance_score: number;    // 相关性分数 (0-1)
  vector_embedding: number[]; // 向量嵌入
  metadata: SnippetMetadata;  // 元数据
  last_updated: string;       // 最后更新时间
  created_at: string;         // 创建时间
}

interface SnippetMetadata {
  language: string;           // 语言
  content_type: string;       // 内容类型
  word_count: number;         // 字数
  tags: string[];             // 标签
  author?: string;            // 作者
  version?: string;           // 版本
}

interface KnowledgeSource {
  source_id: string;          // 源唯一标识
  title: string;              // 标题
  type: SourceType;           // 源类型
  trust_level: number;        // 信任度
  refresh_cycle: RefreshCycle; // 刷新周期
  content_url?: string;       // 内容URL
  status: SourceStatus;       // 状态
  metadata: SourceMetadata;   // 元数据
  last_refresh: string;       // 最后刷新时间
  created_at: string;         // 创建时间
}

type SourceType = 'static_doc' | 'api_endpoint' | 'database' | 'web_crawl';
type RefreshCycle = 'manual' | 'hourly' | 'daily' | 'weekly' | 'monthly';
type SourceStatus = 'active' | 'inactive' | 'error' | 'updating';

interface SourceMetadata {
  department?: string;        // 部门
  version?: string;           // 版本
  language: string;           // 语言
  format: string;             // 格式
  size_bytes?: number;        // 大小(字节)
}
```

**样例数据:**
```json
{
  "snippet_id": "snip_550e8400e29b41d4a716446655440000",
  "source": "crm_policy#section_42",
  "domain": "crm_policy",
  "content": "客户投诉需在24小时内进行第一次响应，对于VIP客户或高严重等级投诉需要在2小时内响应。投诉处理流程包括：1) 创建工单 2) 分配处理人员 3) 调查分析 4) 制定解决方案 5) 跟进执行 6) 客户确认。",
  "title": "客户投诉响应时间要求",
  "summary": "定义了不同类型客户投诉的响应时间标准和处理流程",
  "trust_level": 5,
  "relevance_score": 0.92,
  "vector_embedding": [0.1, 0.2, -0.3, 0.4, 0.5],
  "metadata": {
    "language": "zh-CN",
    "content_type": "policy",
    "word_count": 85,
    "tags": ["投诉处理", "响应时间", "VIP客户"],
    "author": "客服部",
    "version": "v2.1"
  },
  "last_updated": "2024-12-15T10:30:00Z",
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

## 6. Result Store (RS) - 结果存储数据结构

### 6.1 TaskResult - 任务结果

```typescript
interface TaskResult {
  result_id: string;          // 结果唯一标识
  task_id: string;            // 任务ID
  slice_index: number;        // 切片索引
  agent_id: string;           // 执行Agent ID
  result_type: ResultType;    // 结果类型
  status: ResultStatus;       // 结果状态
  data: ResultData;           // 结果数据
  variables_updated: Record<string, any>; // 更新的变量
  execution_metadata: ExecutionMetadata; // 执行元数据
  quality_score?: number;     // 质量分数
  review_status?: ReviewStatus; // 评审状态
  created_at: string;         // 创建时间
  updated_at: string;         // 更新时间
}

type ResultType = 'task_result' | 'tool_result' | 'intermediate_result' | 'final_result';
type ResultStatus = 'success' | 'partial_success' | 'failed' | 'timeout' | 'cancelled';
type ReviewStatus = 'pending' | 'approved' | 'rejected' | 'needs_revision';

interface ResultData {
  output: any;                // 输出结果
  tool_results: ToolResult[]; // 工具执行结果
  summary?: string;           // 结果摘要
  next_action?: string;       // 下一步动作
  error_message?: string;     // 错误信息
}

interface ToolResult {
  tool_name: string;          // 工具名称
  success: boolean;           // 是否成功
  execution_time: number;     // 执行时间(秒)
  data: any;                  // 返回数据
  error_message?: string;     // 错误信息
  retry_count: number;        // 重试次数
}

interface ExecutionMetadata {
  total_time: number;         // 总执行时间(秒)
  llm_calls: number;          // LLM调用次数
  tokens_used: number;        // 使用的Token数
  memory_usage: number;       // 内存使用量(MB)
  cpu_time: number;           // CPU时间(秒)
}
```

### 6.2 VariableHistory - 变量历史

```typescript
interface VariableHistory {
  history_id: string;         // 历史记录ID
  variable_name: string;      // 变量名
  task_id: string;            // 任务ID
  slice_index: number;        // 切片索引
  old_value: any;             // 旧值
  new_value: any;             // 新值
  change_type: ChangeType;    // 变更类型
  changed_by: string;         // 变更者
  reason?: string;            // 变更原因
  timestamp: string;          // 变更时间
}

type ChangeType = 'create' | 'update' | 'delete' | 'merge';
```

**样例数据:**
```json
{
  "result_id": "res_550e8400e29b41d4a716446655440000",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "slice_index": 0,
  "agent_id": "550e8400-e29b-41d4-a716-446655440001",
  "result_type": "task_result",
  "status": "success",
  "data": {
    "output": {
      "ticket_created": true,
      "ticket_id": "T20250115001",
      "status": "created"
    },
    "tool_results": [
      {
        "tool_name": "crm_system_create",
        "success": true,
        "execution_time": 1.25,
        "data": {
          "ticket_id": "T20250115001",
          "status": "created",
          "assigned_to": "agent_001"
        },
        "retry_count": 0
      }
    ],
    "summary": "成功创建投诉工单T20250115001，已分配给处理人员",
    "next_action": "escalate_complaint"
  },
  "variables_updated": {
    "ticket_id": "T20250115001",
    "complaint_status": "processing",
    "assigned_agent": "agent_001"
  },
  "execution_metadata": {
    "total_time": 5.67,
    "llm_calls": 1,
    "tokens_used": 1450,
    "memory_usage": 128.5,
    "cpu_time": 2.3
  },
  "quality_score": 0.92,
  "review_status": "approved",
  "created_at": "2025-01-15T10:15:30.256789Z",
  "updated_at": "2025-01-15T10:15:30.256789Z"
}
```

---

## 7. Review Model (RM) - 评估模块数据结构

### 7.1 ReviewResult - 评估结果

```typescript
interface ReviewResult {
  review_id: string;          // 评估唯一标识
  task_id: string;            // 任务ID
  slice_index: number;        // 切片索引
  result_id: string;          // 结果ID
  status: ReviewStatus;       // 评估状态
  overall_score: number;      // 总体分数 (0-1)
  dimension_scores: DimensionScores; // 维度分数
  feedback: ReviewFeedback;   // 反馈信息
  recommendations: Recommendation[]; // 建议
  reviewer: string;           // 评估者
  review_criteria: ReviewCriteria; // 评估标准
  evaluated_at: string;       // 评估时间
  created_at: string;         // 创建时间
}

type ReviewStatus = 'pass' | 'fail' | 'conditional_pass' | 'needs_review';

interface DimensionScores {
  tool_execution: number;     // 工具执行质量 (0-1)
  variable_completion: number; // 变量完整性 (0-1)
  output_quality: number;     // 输出质量 (0-1)
  efficiency: number;         // 执行效率 (0-1)
  compliance: number;         // 合规性 (0-1)
}

interface ReviewFeedback {
  strengths: string[];        // 优点
  weaknesses: string[];       // 不足
  suggestions: string[];      // 改进建议
  detailed_comments: Record<string, string>; // 详细评论
}

interface Recommendation {
  type: RecommendationType;   // 建议类型
  action: string;             // 具体动作
  reason: string;             // 原因
  priority: number;           // 优先级 (1-5)
  next_slice_index?: number;  // 下一个切片索引
}

type RecommendationType = 'continue' | 'retry' | 'skip' | 'escalate' | 'manual_review';

interface ReviewCriteria {
  required_tools: string[];   // 必需工具
  required_variables: string[]; // 必需变量
  quality_threshold: number;  // 质量阈值
  timeout_threshold: number;  // 超时阈值
  custom_rules: CustomRule[]; // 自定义规则
}

interface CustomRule {
  rule_id: string;            // 规则ID
  description: string;        // 规则描述
  condition: string;          // 条件表达式
  weight: number;             // 权重 (0-1)
}
```

**样例数据:**
```json
{
  "review_id": "rev_550e8400e29b41d4a716446655440000",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "slice_index": 0,
  "result_id": "res_550e8400e29b41d4a716446655440000",
  "status": "pass",
  "overall_score": 0.92,
  "dimension_scores": {
    "tool_execution": 1.0,
    "variable_completion": 1.0,
    "output_quality": 0.85,
    "efficiency": 0.90,
    "compliance": 0.95
  },
  "feedback": {
    "strengths": [
      "所有必需工具执行成功",
      "变量设置完整准确",
      "响应时间符合要求"
    ],
    "weaknesses": [
      "输出格式可以更加标准化"
    ],
    "suggestions": [
      "建议在输出中增加时间戳",
      "可以添加更详细的执行日志"
    ],
    "detailed_comments": {
      "tool_execution": "CRM工具调用成功，返回数据完整",
      "output_quality": "输出内容准确但格式需要改进"
    }
  },
  "recommendations": [
    {
      "type": "continue",
      "action": "proceed_to_next_slice",
      "reason": "任务完成质量良好，可继续下一步",
      "priority": 1,
      "next_slice_index": 1
    }
  ],
  "reviewer": "auto_evaluator_v1.2",
  "review_criteria": {
    "required_tools": ["crm_system_create"],
    "required_variables": ["ticket_id"],
    "quality_threshold": 0.8,
    "timeout_threshold": 300,
    "custom_rules": [
      {
        "rule_id": "ticket_format_check",
        "description": "检查工单ID格式",
        "condition": "ticket_id.startsWith('T') && ticket_id.length == 12",
        "weight": 0.1
      }
    ]
  },
  "evaluated_at": "2025-01-15T10:16:00.123456Z",
  "created_at": "2025-01-15T10:16:00.123456Z"
}
```

---

## 8. Tool Registry (TR) - 工具注册表数据结构

### 8.1 Tool - 工具定义

```typescript
interface Tool {
  tool_id: string;            // 工具唯一标识
  name: string;               // 工具名称
  version: string;            // 版本号
  execution_mode: ExecutionMode; // 执行模式
  agent_runtime?: string;     // Agent运行时要求
  network_scope: NetworkScope; // 网络范围
  security_level: SecurityLevel; // 安全级别
  description: string;        // 描述
  schema: ToolSchema;         // 参数Schema
  response_schema?: any;      // 响应Schema
  keywords: string[];         // 关键词
  status: ToolStatus;         // 工具状态
  metadata: ToolMetadata;     // 元数据
  usage_stats: UsageStats;    // 使用统计
  created_at: string;         // 创建时间
  updated_at: string;         // 更新时间
}

type NetworkScope = 'public' | 'intranet' | 'private' | 'isolated';
type ToolStatus = 'active' | 'deprecated' | 'beta' | 'maintenance' | 'disabled';

interface ToolSchema {
  type: string;               // Schema类型
  properties: Record<string, PropertySchema>; // 属性定义
  required: string[];         // 必需字段
  additionalProperties?: boolean; // 是否允许额外属性
}

interface PropertySchema {
  type: string;               // 属性类型
  description?: string;       // 描述
  enum?: any[];               // 枚举值
  default?: any;              // 默认值
  format?: string;            // 格式
  minimum?: number;           // 最小值
  maximum?: number;           // 最大值
  pattern?: string;           // 正则模式
}

interface ToolMetadata {
  category: string;           // 分类
  provider: string;           // 提供者
  documentation_url?: string; // 文档URL
  support_contact?: string;   // 支持联系方式
  sla: ServiceLevelAgreement; // 服务等级协议
  dependencies: string[];     // 依赖项
}

interface ServiceLevelAgreement {
  response_time: string;      // 响应时间
  availability: string;       // 可用性
  throughput?: string;        // 吞吐量
}

interface UsageStats {
  total_calls: number;        // 总调用次数
  success_rate: number;       // 成功率
  avg_response_time: number;  // 平均响应时间(毫秒)
  last_used: string;          // 最后使用时间
  popular_agents: string[];   // 常用Agent列表
}
```

**样例数据:**
```json
{
  "tool_id": "550e8400-e29b-41d4-a716-446655440010",
  "name": "crm_system_create",
  "version": "v1.2.0",
  "execution_mode": "cloud",
  "agent_runtime": null,
  "network_scope": "intranet",
  "security_level": "internal",
  "description": "创建CRM系统投诉工单，支持客户信息录入和工单分配",
  "schema": {
    "type": "object",
    "properties": {
      "customer_info": {
        "type": "object",
        "description": "客户信息",
        "properties": {
          "name": {
            "type": "string",
            "description": "客户姓名"
          },
          "phone": {
            "type": "string",
            "description": "联系电话",
            "pattern": "^1[3-9]\\d{9}$"
          },
          "email": {
            "type": "string",
            "description": "邮箱地址",
            "format": "email"
          }
        },
        "required": ["name", "phone"]
      },
      "complaint_content": {
        "type": "string",
        "description": "投诉内容详情",
        "minimum": 10,
        "maximum": 1000
      },
      "severity": {
        "type": "string",
        "description": "严重程度",
        "enum": ["低", "中", "高"],
        "default": "中"
      }
    },
    "required": ["customer_info", "complaint_content"]
  },
  "response_schema": {
    "type": "object",
    "properties": {
      "ticket_id": {"type": "string"},
      "status": {"type": "string"},
      "assigned_to": {"type": "string"}
    }
  },
  "keywords": ["CRM", "投诉", "工单", "客户服务"],
  "status": "active",
  "metadata": {
    "category": "customer_service",
    "provider": "internal_crm_team",
    "documentation_url": "https://internal.company.com/tools/crm_create",
    "support_contact": "crm-support@company.com",
    "sla": {
      "response_time": "2s",
      "availability": "99.9%",
      "throughput": "1000 req/min"
    },
    "dependencies": ["crm_database", "notification_service"]
  },
  "usage_stats": {
    "total_calls": 15420,
    "success_rate": 0.987,
    "avg_response_time": 1250,
    "last_used": "2025-01-15T10:15:30.256789Z",
    "popular_agents": [
      "complaint-handler-agent",
      "customer-service-agent"
    ]
  },
  "created_at": "2024-01-01T00:00:00.000000Z",
  "updated_at": "2025-01-10T15:30:00.000000Z"
}
```

---

## 9. Context Service (CS) - 上下文服务数据结构

### 9.1 ContextRequest - 上下文请求

```typescript
interface ContextRequest {
  request_id: string;         // 请求唯一标识
  agent_id: string;           // Agent ID
  task_id: string;            // 任务ID
  slice_index: number;        // 切片索引
  globals: Record<string, any>; // 全局变量
  retrieval_query?: string;   // 检索查询
  options: ContextOptions;    // 选项配置
  timestamp: string;          // 请求时间
}

interface ContextOptions {
  include_knowledge: boolean; // 是否包含知识
  include_history: boolean;   // 是否包含历史
  max_context_length: number; // 最大上下文长度
  cache_enabled: boolean;     // 是否启用缓存
  priority: number;           // 优先级
}

interface ContextResponse {
  request_id: string;         // 请求ID
  prompt_blocks: PromptBlocks; // 提示块
  context_metadata: ContextMetadata; // 上下文元数据
  cache_info: CacheInfo;      // 缓存信息
  generated_at: string;       // 生成时间
}

interface PromptBlocks {
  system: string;             // 系统提示
  task: string;               // 任务描述
  allowed_tools: string;      // 允许的工具
  context_data: string;       // 上下文数据
  instruction: string;        // 执行指令
  knowledge?: string;         // 知识片段
  history?: string;           // 历史信息
}

interface ContextMetadata {
  total_tokens: number;       // 总Token数
  knowledge_snippets_count: number; // 知识片段数量
  tools_available: number;    // 可用工具数量
  cache_hit: boolean;         // 是否命中缓存
  generation_time: number;    // 生成时间(毫秒)
  sources: string[];          // 数据源列表
}

interface CacheInfo {
  cache_key: string;          // 缓存键
  hit: boolean;               // 是否命中
  ttl: number;                // 生存时间(秒)
  created_at?: string;        // 缓存创建时间
}
```

### 9.2 ReportRequest - 结果上报请求

```typescript
interface ReportRequest {
  request_id: string;         // 请求唯一标识
  task_id: string;            // 任务ID
  agent_id: string;           // Agent ID
  slice_index: number;        // 切片索引
  tool_results: ToolResult[]; // 工具结果
  task_results: TaskResults;  // 任务结果
  execution_metadata: ExecutionMetadata; // 执行元数据
  timestamp: string;          // 上报时间
}

interface TaskResults {
  status: ResultStatus;       // 状态
  next_task?: string;         // 下一个任务
  variables_updated: Record<string, any>; // 更新的变量
  summary: string;            // 结果摘要
  confidence_score?: number;  // 置信度分数
  error_details?: ErrorDetails; // 错误详情
}

interface ErrorDetails {
  error_code: string;         // 错误代码
  error_message: string;      // 错误消息
  stack_trace?: string;       // 堆栈跟踪
  recovery_suggestions: string[]; // 恢复建议
}

interface ReportResponse {
  request_id: string;         // 请求ID
  review_result: ReviewStatus; // 评审结果
  next_action: NextAction;    // 下一步动作
  next_slice_index?: number;  // 下一个切片索引
  updated_variables: Record<string, any>; // 更新的变量
  feedback?: string;          // 反馈信息
  processed_at: string;       // 处理时间
}

type NextAction = 'continue' | 'retry' | 'pause' | 'escalate' | 'complete';
```

**样例数据:**
```json
{
  "request_id": "req_550e8400e29b41d4a716446655440000",
  "agent_id": "550e8400-e29b-41d4-a716-446655440001",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "slice_index": 0,
  "globals": {
    "complaint_severity": "高",
    "customer_type": "VIP客户",
    "customer_id": "CUST_20250115001"
  },
  "retrieval_query": "客户投诉处理相关政策",
  "options": {
    "include_knowledge": true,
    "include_history": true,
    "max_context_length": 4000,
    "cache_enabled": true,
    "priority": 100
  },
  "timestamp": "2025-01-15T10:08:09.144390Z"
}
```

---

## 10. 数据库索引设计

### 10.1 主要索引

```sql
-- Event Queue 索引
CREATE INDEX idx_task_events_status_priority ON task_events(status, priority DESC, available_at);
CREATE INDEX idx_task_events_agent_id ON task_events(agent_id, status);
CREATE INDEX idx_task_events_task_id ON task_events(task_id);

-- Agent Registry 索引
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_role ON agents(role);
CREATE INDEX idx_agents_capabilities ON agents USING GIN(capabilities);

-- Task Store 索引
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_assigned_agent ON tasks(assigned_agent, status);
CREATE INDEX idx_task_slices_task_id ON task_slices(task_id, slice_index);
CREATE INDEX idx_task_slices_status ON task_slices(status, execution_order);

-- Knowledge Service 索引
CREATE INDEX idx_knowledge_snippets_domain ON knowledge_snippets(domain);
CREATE INDEX idx_knowledge_snippets_trust_level ON knowledge_snippets(trust_level DESC);
CREATE INDEX idx_knowledge_snippets_vector ON knowledge_snippets USING ivfflat(vector_embedding);

-- Result Store 索引
CREATE INDEX idx_task_results_task_id ON task_results(task_id, slice_index);
CREATE INDEX idx_task_results_agent_id ON task_results(agent_id, created_at DESC);
CREATE INDEX idx_variable_history_name ON variable_history(variable_name, timestamp DESC);

-- Review Model 索引
CREATE INDEX idx_review_results_task_id ON review_results(task_id, slice_index);
CREATE INDEX idx_review_results_status ON review_results(status, evaluated_at DESC);

-- Tool Registry 索引
CREATE INDEX idx_tools_name_version ON tools(name, version);
CREATE INDEX idx_tools_status ON tools(status);
CREATE INDEX idx_tools_keywords ON tools USING GIN(keywords);
```

### 10.2 分区策略

```sql
-- 按时间分区的表
CREATE TABLE task_results_2025_01 PARTITION OF task_results
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE task_results_2025_02 PARTITION OF task_results
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- 按状态分区的表
CREATE TABLE task_events_active PARTITION OF task_events
    FOR VALUES IN ('queued', 'processing');

CREATE TABLE task_events_completed PARTITION OF task_events
    FOR VALUES IN ('completed', 'failed', 'expired');
```

---

## 11. 数据验证规则

### 11.1 字段约束

```typescript
// 通用验证规则
const ValidationRules = {
  // UUID格式验证
  uuid: /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i,
  
  // 时间格式验证 (ISO 8601)
  timestamp: /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3,6})?Z$/,
  
  // 优先级范围
  priority: { min: 0, max: 1000 },
  
  // 分数范围
  score: { min: 0, max: 1 },
  
  // 信任度范围
  trust_level: { min: 1, max: 5 },
  
  // 字符串长度限制
  string_limits: {
    name: { min: 1, max: 100 },
    description: { min: 0, max: 1000 },
    content: { min: 0, max: 10000 },
    summary: { min: 0, max: 500 }
  }
};
```

### 11.2 业务规则验证

```typescript
// 业务逻辑验证
const BusinessRules = {
  // 任务切片索引必须连续
  validateSliceIndex: (slices: TaskSlice[]) => {
    const indices = slices.map(s => s.slice_index).sort((a, b) => a - b);
    return indices.every((index, i) => index === i);
  },
  
  // Agent必须有对应的工具权限
  validateToolPermission: (agent: Agent, toolName: string) => {
    return agent.tool_scope.allowed_tools.includes(toolName);
  },
  
  // 任务依赖关系不能形成循环
  validateNoCyclicDependency: (dependencies: TaskDependency[]) => {
    // 实现循环依赖检测算法
    return true; // 简化示例
  }
};
```

---

## 12. 总结

本数据结构设计文档为Context Service生态系统提供了完整的数据模型定义，包括：

### 12.1 设计特点

1. **类型安全**: 使用TypeScript接口定义，确保类型一致性
2. **可扩展性**: 预留metadata字段，支持未来扩展
3. **性能优化**: 合理的索引设计和分区策略
4. **数据完整性**: 完善的约束和验证规则
5. **可追溯性**: 完整的时间戳和历史记录

### 12.2 关键数据流

1. **任务执行流**: Task → TaskSlice → TaskEvent → TaskResult
2. **上下文生成流**: ContextRequest → Agent + Knowledge + Tools → ContextResponse
3. **结果评估流**: TaskResult → ReviewResult → NextAction
4. **变量传递流**: GlobalVariables → TaskExecution → VariableHistory

### 12.3 数据一致性保证

1. **事务边界**: 关键操作使用数据库事务
2. **外键约束**: 确保引用完整性
3. **状态机**: 严格的状态转换规则
4. **版本控制**: 支持数据版本管理

这套数据结构设计为构建高效、可靠的Context Service系统提供了坚实的数据基础。