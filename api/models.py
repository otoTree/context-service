"""API数据模型定义"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID


class TaskMetadata(BaseModel):
    """任务元数据"""
    description: Optional[str] = None
    version: Optional[str] = "1.0"
    tags: Optional[List[str]] = None


class DSLUploadRequest(BaseModel):
    """DSL文件上传请求"""
    agent_id: UUID
    metadata: Optional[TaskMetadata] = None


class DSLTextRequest(BaseModel):
    """DSL文本输入请求"""
    dsl_content: str
    agent_id: UUID
    metadata: Optional[TaskMetadata] = None


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: UUID
    status: str
    slices_count: int
    variables: List[str]
    tools_required: List[str]
    message: str


class TaskDetailResponse(BaseModel):
    """任务详情响应"""
    task_id: UUID
    agent_id: UUID
    status: str
    slices_count: int
    variables: List[str]
    tools_required: List[str]
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class TaskSliceData(BaseModel):
    """任务切片数据"""
    slice_id: int
    task_name: str
    task_title: str
    description: List[str]
    tools: List[Dict[str, Any]]
    conditions: List[Dict[str, Any]]
    variables_used: List[str]
    default_next: Optional[str] = None


class TaskSlicesResponse(BaseModel):
    """任务切片响应"""
    task_id: UUID
    slices: List[TaskSliceData]


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    detail: Optional[str] = None
    line_number: Optional[int] = None