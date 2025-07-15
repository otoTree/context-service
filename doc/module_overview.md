# 模块职责一览

下表简要说明 `architecture_diagram.md` 中出现的各个模块（节点）在整套「Agent + Context Service」体系中的定位与核心职责。

| 模块 | 职能定位 | 核心职责 | 主要输入 | 主要输出 |
|------|----------|----------|----------|----------|
| Event Queue (EQ) | 任务调度缓冲池 | 按优先级缓冲待执行任务，支持重试与消费确认 | {task_id, payload} | 由 Agent 拉取的任务事件 |
| Agent (A) | 智能体执行核心 | 解析 Prompt Blocks，调用工具并产出 tool_results / task_results | Prompt Blocks | tool_results, task_results |
| Context Service (CS) | 运行时粘合层 | 汇聚 AR、TS、TR、KS、RS 数据生成 Prompt Blocks；执行后写回结果 | get_context 请求 | Prompt Blocks；report_result 调用 |
| Agent Registry (AR) | Agent 元数据中心 | 维护 Agent 元信息、默认 SYSTEM、工具白名单、运行状态等；提供 CRUD API | agent_id | base_prompt, tool_scope, status |
| Task Store (TS) | 任务持久化与切片服务 | 拆分任务、管理生命周期、支撑 SOP/DSL 上传解析 | task_id / SOP 文件 | task_object, 子任务列表 |
| Tool Registry (TR) | 工具定义仓库 | 维护工具 Schema、版本、执行模式；支持按关键词 RAG | 工具查询关键词 | ALLOWED_TOOLS 片段 |
| Knowledge Service (KS) | 知识检索服务 | 向量 / 全文检索知识片段，供 CS 注入 CONTEXT_DATA | retrieval_query, knowledge_scope | knowledge_snippets |
| Result Store (RS) | 结果与变量仓库 | 持久化运行结果；支持历史查询并向 CS 返回关联结果 | task_id, results | 历史结果片段 |
| Review Model (RM) | 结果评估模块 | 自动评估 task_results，决定重试或推进下一任务 | task_results | pass / fail 标记 |
| Cloud Tools (CT) | 云端工具执行引擎 | 通过网络调用外部 API / 服务 | args | API 响应 |
| Local Tools (LT) | 本地工具执行引擎 | 在本机运行脚本或 SDK | args | 本地执行结果 |

> 说明：
> 1. **Prompt Blocks** 包含 SYSTEM / TASK / ALLOWED_TOOLS / CONTEXT_DATA / INSTRUCTION 五个区块，详见 `doc/context_organization.md`。
> 2. **knowledge_snippets** 被 CS 归并到 Prompt 的 CONTEXT_DATA 中，对 Agent 来说是透明字段。 