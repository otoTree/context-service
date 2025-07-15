"""任务相关API路由"""
import tempfile
import os
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from repository.database import get_db_session
from service.task_service import TaskService
from api.models import (
    DSLTextRequest, TaskResponse, TaskDetailResponse, 
    TaskSlicesResponse, ErrorResponse, TaskMetadata
)

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


@router.post("/upload-dsl", response_model=TaskResponse)
async def upload_dsl_file(
    file: UploadFile = File(..., description="DSL文件 (.dsl格式)"),
    agent_id: UUID = Form(..., description="目标Agent的UUID"),
    description: Optional[str] = Form(None, description="任务描述"),
    version: Optional[str] = Form("1.0", description="版本号"),
    tags: Optional[str] = Form(None, description="标签列表，逗号分隔"),
    db: AsyncSession = Depends(get_db_session)
):
    """上传DSL文件并解析为任务切片"""
    try:
        # 验证文件类型
        if not file.filename or not file.filename.endswith('.dsl'):
            raise HTTPException(status_code=400, detail="文件必须是.dsl格式")
        
        # 读取文件内容
        content = await file.read()
        dsl_content = content.decode('utf-8')
        
        # 构建元数据
        metadata = {
            "description": description,
            "version": version,
            "source_type": "file_upload",
            "filename": file.filename
        }
        
        if tags:
            metadata["tags"] = [tag.strip() for tag in tags.split(",")]
        
        # 创建任务
        task_service = TaskService(db)
        result = await task_service.create_task_from_dsl(
            dsl_content=dsl_content,
            agent_id=agent_id,
            metadata=metadata,
            source_file=file.filename
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@router.post("/create-from-text", response_model=TaskResponse)
async def create_task_from_text(
    request: DSLTextRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """从文本内容创建任务切片"""
    try:
        # 构建元数据
        metadata = {
            "source_type": "text_input"
        }
        
        if request.metadata:
            metadata.update({
                "description": request.metadata.description,
                "version": request.metadata.version,
                "tags": request.metadata.tags
            })
        
        # 创建任务
        task_service = TaskService(db)
        result = await task_service.create_task_from_dsl(
            dsl_content=request.dsl_content,
            agent_id=request.agent_id,
            metadata=metadata
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task_detail(
    task_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """获取任务详情"""
    try:
        task_service = TaskService(db)
        result = await task_service.get_task_detail(task_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@router.get("/{task_id}/slices", response_model=TaskSlicesResponse)
async def get_task_slices(
    task_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """获取任务切片详情"""
    try:
        task_service = TaskService(db)
        result = await task_service.get_task_slices(task_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@router.get("/", response_model=list[TaskDetailResponse])
async def list_tasks(
    agent_id: Optional[UUID] = None,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session)
):
    """获取任务列表"""
    try:
        # 这里可以实现任务列表查询逻辑
        # 暂时返回空列表，后续可以扩展
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")