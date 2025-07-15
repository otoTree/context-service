-- Context Service Database Schema
-- Version: 0.1.0
-- Based on: doc/database_schema.md

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable trigram extension for text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- =============================================================================
-- ENUM Type Definitions
-- =============================================================================

CREATE TYPE agent_status_enum AS ENUM ('active', 'inactive', 'error');
CREATE TYPE task_status_enum AS ENUM ('pending', 'in_progress', 'completed', 'failed', 'cancelled');
CREATE TYPE tool_mode_enum AS ENUM ('cloud', 'local');
CREATE TYPE result_type_enum AS ENUM ('tool_result', 'task_result');
CREATE TYPE review_status_enum AS ENUM ('pass', 'fail');

-- =============================================================================
-- EVENT QUEUE - 任务调度缓冲池
-- =============================================================================

CREATE TABLE event_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL,
    payload JSONB NOT NULL,
    priority SMALLINT NOT NULL DEFAULT 100,
    available_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    visibility_timeout INTEGER NOT NULL DEFAULT 300,
    attempts SMALLINT NOT NULL DEFAULT 0,
    max_attempts SMALLINT NOT NULL DEFAULT 3,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- AGENT REGISTRY - Agent 元数据中心
-- =============================================================================

CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    base_prompt TEXT NOT NULL,
    allowed_tool_ids UUID[] DEFAULT '{}',
    status agent_status_enum NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- TASK STORE - 任务持久化与切片服务
-- =============================================================================

CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_task_id UUID,
    agent_id UUID NOT NULL,
    payload JSONB NOT NULL,
    status task_status_enum NOT NULL DEFAULT 'pending',
    priority SMALLINT NOT NULL DEFAULT 100,
    retries SMALLINT NOT NULL DEFAULT 0,
    scheduled_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (parent_task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

CREATE TABLE task_slices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL,
    slice_index INTEGER NOT NULL,
    content JSONB NOT NULL,
    status task_status_enum NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    UNIQUE(task_id, slice_index)
);

-- =============================================================================
-- TOOL REGISTRY - 工具定义仓库
-- =============================================================================

CREATE TABLE tools (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT 'v1.0.0',
    execution_mode tool_mode_enum NOT NULL DEFAULT 'cloud',
    schema JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(name, version)
);

CREATE TABLE tool_keywords (
    id BIGSERIAL PRIMARY KEY,
    tool_id UUID NOT NULL,
    keyword TEXT NOT NULL,
    FOREIGN KEY (tool_id) REFERENCES tools(id) ON DELETE CASCADE
);

-- =============================================================================
-- RESULT STORE - 结果与变量仓库
-- =============================================================================

CREATE TABLE task_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL,
    tool_id UUID,
    result_type result_type_enum NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (tool_id) REFERENCES tools(id) ON DELETE SET NULL
);

-- =============================================================================
-- REVIEW MODEL - 结果评估
-- =============================================================================

CREATE TABLE review_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL,
    status review_status_enum NOT NULL,
    score NUMERIC(5,2),
    reviewer TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- =============================================================================
-- INDEXES - 索引创建
-- =============================================================================

-- EVENT QUEUE indexes
CREATE INDEX idx_event_queue_available ON event_queue (available_at);
CREATE INDEX idx_event_queue_task ON event_queue (task_id);
CREATE INDEX idx_event_queue_priority_available ON event_queue (priority, available_at);

-- AGENT REGISTRY indexes
CREATE INDEX idx_agents_name ON agents (name);
CREATE INDEX idx_agents_status ON agents (status);

-- TASK STORE indexes
CREATE INDEX idx_tasks_status ON tasks (status);
CREATE INDEX idx_tasks_agent_status ON tasks (agent_id, status);
CREATE INDEX idx_tasks_parent ON tasks (parent_task_id);
CREATE INDEX idx_tasks_scheduled ON tasks (scheduled_at);
CREATE INDEX idx_task_slices_task ON task_slices (task_id);
CREATE INDEX idx_task_slices_task_index ON task_slices (task_id, slice_index);

-- TOOL REGISTRY indexes
CREATE INDEX idx_tools_name ON tools (name);
CREATE INDEX idx_tools_execution_mode ON tools (execution_mode);
CREATE INDEX idx_tool_keywords_keyword ON tool_keywords USING gin (keyword gin_trgm_ops);
CREATE INDEX idx_tool_keywords_tool ON tool_keywords (tool_id);

-- RESULT STORE indexes
CREATE INDEX idx_task_results_task ON task_results (task_id);
CREATE INDEX idx_task_results_tool ON task_results (tool_id);
CREATE INDEX idx_task_results_type ON task_results (result_type);
CREATE INDEX idx_task_results_created ON task_results (created_at);

-- REVIEW MODEL indexes
CREATE INDEX idx_review_status ON review_records (status);
CREATE INDEX idx_review_task ON review_records (task_id);
CREATE INDEX idx_review_created ON review_records (created_at);

-- =============================================================================
-- TRIGGERS - 自动更新updated_at字段
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to tables with updated_at column
CREATE TRIGGER update_event_queue_updated_at BEFORE UPDATE ON event_queue
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_task_slices_updated_at BEFORE UPDATE ON task_slices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tools_updated_at BEFORE UPDATE ON tools
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- INITIAL DATA - 一些初始化数据
-- =============================================================================

-- 插入一个默认的测试Agent
INSERT INTO agents (id, name, description, base_prompt, status) VALUES 
(
    uuid_generate_v4(),
    'test_agent',
    '测试用Agent',
    '你是一个测试Agent，用于验证Context Service的功能。',
    'active'
);

-- 插入一些基础工具定义
INSERT INTO tools (id, name, version, execution_mode, schema, description) VALUES 
(
    uuid_generate_v4(),
    'notification_service',
    'v1.0.0',
    'cloud',
    '{"type": "object", "properties": {"ticket_id": {"type": "string"}, "severity": {"type": "string"}}, "required": ["ticket_id", "severity"]}',
    '向相关部门推送紧急通知'
),
(
    uuid_generate_v4(),
    'crm_query',
    'v1.0.0',
    'cloud',
    '{"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["query"]}',
    'CRM系统查询工具'
),
(
    uuid_generate_v4(),
    'local_file_reader',
    'v1.0.0',
    'local',
    '{"type": "object", "properties": {"file_path": {"type": "string"}}, "required": ["file_path"]}',
    '本地文件读取工具'
); 