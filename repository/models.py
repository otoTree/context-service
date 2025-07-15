"""数据库模型定义"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, SmallInteger, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Agent(Base):
    """Agent模型"""
    __tablename__ = "agents"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    base_prompt = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    tasks = relationship("Task", back_populates="agent")


class Task(Base):
    """任务模型"""
    __tablename__ = "tasks"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    parent_task_id = Column(PGUUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True)
    agent_id = Column(PGUUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    payload = Column(JSONB, nullable=False)
    status = Column(String, nullable=False, default="pending")
    priority = Column(SmallInteger, nullable=False, default=100)
    retries = Column(SmallInteger, nullable=False, default=0)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    agent = relationship("Agent", back_populates="tasks")
    parent_task = relationship("Task", remote_side=[id])
    slices = relationship("TaskSlice", back_populates="task", cascade="all, delete-orphan")
    results = relationship("TaskResult", back_populates="task")


class TaskSlice(Base):
    """任务切片模型"""
    __tablename__ = "task_slices"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id = Column(PGUUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    slice_index = Column(Integer, nullable=False)
    content = Column(JSONB, nullable=False)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    task = relationship("Task", back_populates="slices")


class Tool(Base):
    """工具模型"""
    __tablename__ = "tools"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False, default="v1.0.0")
    execution_mode = Column(String, nullable=False, default="cloud")
    schema = Column(JSONB, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    results = relationship("TaskResult", back_populates="tool")


class TaskResult(Base):
    """任务结果模型"""
    __tablename__ = "task_results"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id = Column(PGUUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    tool_id = Column(PGUUID(as_uuid=True), ForeignKey("tools.id"), nullable=True)
    result_type = Column(String, nullable=False)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    task = relationship("Task", back_populates="results")
    tool = relationship("Tool", back_populates="results")