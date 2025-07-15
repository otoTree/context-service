"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2025-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply initial schema migration."""
    
    # Enable extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    
    # Create ENUM types
    agent_status_enum = postgresql.ENUM('active', 'inactive', 'error', name='agent_status_enum')
    agent_status_enum.create(op.get_bind())
    
    task_status_enum = postgresql.ENUM('pending', 'in_progress', 'completed', 'failed', 'cancelled', name='task_status_enum')
    task_status_enum.create(op.get_bind())
    
    tool_mode_enum = postgresql.ENUM('cloud', 'local', name='tool_mode_enum')
    tool_mode_enum.create(op.get_bind())
    
    result_type_enum = postgresql.ENUM('tool_result', 'task_result', name='result_type_enum')
    result_type_enum.create(op.get_bind())
    
    review_status_enum = postgresql.ENUM('pass', 'fail', name='review_status_enum')
    review_status_enum.create(op.get_bind())
    
    # Create EVENT QUEUE table
    op.create_table('event_queue',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('priority', sa.SmallInteger(), nullable=False, server_default='100'),
        sa.Column('available_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('visibility_timeout', sa.Integer(), nullable=False, server_default='300'),
        sa.Column('attempts', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.SmallInteger(), nullable=False, server_default='3'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )
    
    # Create AGENT REGISTRY table
    op.create_table('agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('base_prompt', sa.Text(), nullable=False),
        sa.Column('allowed_tool_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), server_default="'{}'"),
        sa.Column('status', agent_status_enum, nullable=False, server_default='active'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )
    
    # Create TASK STORE tables
    op.create_table('tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('parent_task_id', postgresql.UUID(as_uuid=True)),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', task_status_enum, nullable=False, server_default='pending'),
        sa.Column('priority', sa.SmallInteger(), nullable=False, server_default='100'),
        sa.Column('retries', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.Column('scheduled_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['parent_task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE')
    )
    
    op.create_table('task_slices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('slice_index', sa.Integer(), nullable=False),
        sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', task_status_enum, nullable=False, server_default='pending'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('task_id', 'slice_index')
    )
    
    # Create TOOL REGISTRY tables
    op.create_table('tools',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('version', sa.Text(), nullable=False, server_default='v1.0.0'),
        sa.Column('execution_mode', tool_mode_enum, nullable=False, server_default='cloud'),
        sa.Column('schema', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('name', 'version')
    )
    
    op.create_table('tool_keywords',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('keyword', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ondelete='CASCADE')
    )
    
    # Create RESULT STORE table
    op.create_table('task_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True)),
        sa.Column('result_type', result_type_enum, nullable=False),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ondelete='SET NULL')
    )
    
    # Create REVIEW MODEL table
    op.create_table('review_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', review_status_enum, nullable=False),
        sa.Column('score', sa.Numeric(5, 2)),
        sa.Column('reviewer', sa.Text(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE')
    )
    
    # Create indexes
    op.create_index('idx_event_queue_available', 'event_queue', ['available_at'])
    op.create_index('idx_event_queue_task', 'event_queue', ['task_id'])
    op.create_index('idx_event_queue_priority_available', 'event_queue', ['priority', 'available_at'])
    
    op.create_index('idx_agents_name', 'agents', ['name'])
    op.create_index('idx_agents_status', 'agents', ['status'])
    
    op.create_index('idx_tasks_status', 'tasks', ['status'])
    op.create_index('idx_tasks_agent_status', 'tasks', ['agent_id', 'status'])
    op.create_index('idx_tasks_parent', 'tasks', ['parent_task_id'])
    op.create_index('idx_tasks_scheduled', 'tasks', ['scheduled_at'])
    op.create_index('idx_task_slices_task', 'task_slices', ['task_id'])
    op.create_index('idx_task_slices_task_index', 'task_slices', ['task_id', 'slice_index'])
    
    op.create_index('idx_tools_name', 'tools', ['name'])
    op.create_index('idx_tools_execution_mode', 'tools', ['execution_mode'])
    op.create_index('idx_tool_keywords_keyword', 'tool_keywords', ['keyword'], postgresql_using='gin', postgresql_ops={'keyword': 'gin_trgm_ops'})
    op.create_index('idx_tool_keywords_tool', 'tool_keywords', ['tool_id'])
    
    op.create_index('idx_task_results_task', 'task_results', ['task_id'])
    op.create_index('idx_task_results_tool', 'task_results', ['tool_id'])
    op.create_index('idx_task_results_type', 'task_results', ['result_type'])
    op.create_index('idx_task_results_created', 'task_results', ['created_at'])
    
    op.create_index('idx_review_status', 'review_records', ['status'])
    op.create_index('idx_review_task', 'review_records', ['task_id'])
    op.create_index('idx_review_created', 'review_records', ['created_at'])
    
    # Create update trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Apply triggers to tables with updated_at column
    op.execute("CREATE TRIGGER update_event_queue_updated_at BEFORE UPDATE ON event_queue FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()")
    op.execute("CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()")
    op.execute("CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()")
    op.execute("CREATE TRIGGER update_task_slices_updated_at BEFORE UPDATE ON task_slices FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()")
    op.execute("CREATE TRIGGER update_tools_updated_at BEFORE UPDATE ON tools FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()")
    
    # Insert initial data
    # Insert a default test agent
    op.execute("""
        INSERT INTO agents (id, name, description, base_prompt, status) VALUES 
        (
            uuid_generate_v4(),
            'test_agent',
            '测试用Agent',
            '你是一个测试Agent，用于验证Context Service的功能。',
            'active'
        )
    """)
    
    # Insert some basic tool definitions
    op.execute("""
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
        )
    """)


def downgrade() -> None:
    """Reverse initial schema migration."""
    
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_tools_updated_at ON tools")
    op.execute("DROP TRIGGER IF EXISTS update_task_slices_updated_at ON task_slices")
    op.execute("DROP TRIGGER IF EXISTS update_tasks_updated_at ON tasks")
    op.execute("DROP TRIGGER IF EXISTS update_agents_updated_at ON agents")
    op.execute("DROP TRIGGER IF EXISTS update_event_queue_updated_at ON event_queue")
    
    # Drop function
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
    
    # Drop tables in reverse order
    op.drop_table('review_records')
    op.drop_table('task_results')
    op.drop_table('tool_keywords')
    op.drop_table('tools')
    op.drop_table('task_slices')
    op.drop_table('tasks')
    op.drop_table('agents')
    op.drop_table('event_queue')
    
    # Drop ENUM types
    review_status_enum = postgresql.ENUM(name='review_status_enum')
    review_status_enum.drop(op.get_bind())
    
    result_type_enum = postgresql.ENUM(name='result_type_enum')
    result_type_enum.drop(op.get_bind())
    
    tool_mode_enum = postgresql.ENUM(name='tool_mode_enum')
    tool_mode_enum.drop(op.get_bind())
    
    task_status_enum = postgresql.ENUM(name='task_status_enum')
    task_status_enum.drop(op.get_bind())
    
    agent_status_enum = postgresql.ENUM(name='agent_status_enum')
    agent_status_enum.drop(op.get_bind())
    
    # Drop extensions (optional, may be used by other apps)
    # op.execute("DROP EXTENSION IF EXISTS pg_trgm")
    # op.execute("DROP EXTENSION IF EXISTS \"uuid-ossp\"") 