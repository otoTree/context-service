"""任务服务 - DSL解析和任务切片管理"""
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from service.dsl_parser import DSLParser, DSLParseError, DSLParseResult
from service.slice_generator import SliceGenerator
from repository.models import Task, TaskSlice, Agent
from api.models import TaskResponse, TaskDetailResponse, TaskSlicesResponse, TaskSliceData


class TaskService:
    """任务服务类"""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.dsl_parser = DSLParser()
    
    async def create_task_from_dsl(self, 
                                   dsl_content: str, 
                                   agent_id: UUID, 
                                   metadata: Optional[Dict[str, Any]] = None,
                                   source_file: Optional[str] = None) -> TaskResponse:
        """从DSL内容创建任务"""
        try:
            # 验证Agent存在
            agent = await self._get_agent(agent_id)
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            # 解析DSL
            parse_result = self.dsl_parser.parse(dsl_content)
            
            # 生成任务切片
            slices_data = self._generate_task_slices(parse_result)
            
            # 创建任务记录
            task = await self._create_task_record(agent_id, parse_result, metadata, source_file)
            
            # 创建切片记录
            await self._create_slice_records(task.id, slices_data)
            
            # 提交事务
            await self.db_session.commit()
            
            # 返回响应
            return TaskResponse(
                task_id=task.id,
                status="parsed",
                slices_count=len(slices_data),
                variables=list(parse_result.variables.keys()),
                tools_required=self._extract_tools_from_slices(slices_data),
                message="DSL解析成功，任务切片已创建"
            )
            
        except DSLParseError as e:
            await self.db_session.rollback()
            raise ValueError(f"DSL解析错误 (第{e.line_number}行): {e.message}")
        except Exception as e:
            await self.db_session.rollback()
            raise ValueError(f"创建任务失败: {str(e)}")
    
    async def get_task_detail(self, task_id: UUID) -> Optional[TaskDetailResponse]:
        """获取任务详情"""
        stmt = select(Task).options(selectinload(Task.slices)).where(Task.id == task_id)
        result = await self.db_session.execute(stmt)
        task = result.scalar_one_or_none()
        
        if not task:
            return None
        
        # 从payload中提取信息
        payload = task.payload
        variables = list(payload.get("global_variables", {}).keys())
        tools_required = self._extract_tools_from_payload(payload)
        
        return TaskDetailResponse(
            task_id=task.id,
            agent_id=task.agent_id,
            status=task.status,
            slices_count=len(task.slices),
            variables=variables,
            tools_required=tools_required,
            created_at=task.created_at,
            metadata=payload.get("metadata")
        )
    
    async def get_task_slices(self, task_id: UUID) -> Optional[TaskSlicesResponse]:
        """获取任务切片"""
        stmt = select(Task).options(selectinload(Task.slices)).where(Task.id == task_id)
        result = await self.db_session.execute(stmt)
        task = result.scalar_one_or_none()
        
        if not task:
            return None
        
        # 按slice_index排序
        sorted_slices = sorted(task.slices, key=lambda x: x.slice_index)
        
        slice_data_list = []
        for slice_record in sorted_slices:
            content = slice_record.content
            slice_data = TaskSliceData(
                slice_id=slice_record.slice_index,
                task_name=content.get("task_name", ""),
                task_title=content.get("task_title", ""),
                description=content.get("description", []),
                tools=content.get("tools", []),
                conditions=content.get("conditions", []),
                variables_used=content.get("variables_used", []),
                default_next=content.get("default_next")
            )
            slice_data_list.append(slice_data)
        
        return TaskSlicesResponse(
            task_id=task_id,
            slices=slice_data_list
        )
    
    async def _get_agent(self, agent_id: UUID) -> Optional[Agent]:
        """获取Agent"""
        stmt = select(Agent).where(Agent.id == agent_id)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _create_task_record(self, 
                                  agent_id: UUID, 
                                  parse_result: DSLParseResult,
                                  metadata: Optional[Dict[str, Any]] = None,
                                  source_file: Optional[str] = None) -> Task:
        """创建任务记录"""
        # 构建payload
        payload = {
            "dsl_metadata": {
                **parse_result.metadata,
                "source_file": source_file,
                "generated_at": datetime.now().isoformat()
            },
            "global_variables": {
                name: {
                    "type": var.type,
                    "default": var.default_value,
                    "description": f"{name}变量"
                }
                for name, var in parse_result.variables.items()
            },
            "metadata": metadata or {}
        }
        
        task = Task(
            agent_id=agent_id,
            payload=payload,
            status="parsed"
        )
        
        self.db_session.add(task)
        await self.db_session.flush()  # 获取ID
        return task
    
    async def _create_slice_records(self, task_id: UUID, slices_data: List[Dict[str, Any]]):
        """创建切片记录"""
        for index, slice_data in enumerate(slices_data):
            task_slice = TaskSlice(
                task_id=task_id,
                slice_index=index,
                content=slice_data
            )
            self.db_session.add(task_slice)
    
    def _generate_task_slices(self, parse_result: DSLParseResult) -> List[Dict[str, Any]]:
        """生成任务切片"""
        generator = SliceGenerator()
        slice_objects = generator.generate_slices(parse_result)
        
        # 转换为字典格式用于数据库存储
        slices = []
        for slice_obj in slice_objects:
            slice_data = {
                "name": slice_obj.name,
                "description": slice_obj.description,
                "task_type": slice_obj.task_type,
                "parameters": slice_obj.parameters,
                "dependencies": slice_obj.dependencies,
                "status": slice_obj.status,
                "order_index": slice_obj.order_index,
                "expected_output": slice_obj.expected_output
            }
            slices.append(slice_data)
        
        return slices
    
    def _extract_tools_from_slices(self, slices_data: List[Dict[str, Any]]) -> List[str]:
        """从切片数据中提取工具列表"""
        tools = set()
        for slice_data in slices_data:
            for tool in slice_data.get("tools", []):
                tools.add(tool["name"])
        return list(tools)
    
    def _extract_tools_from_payload(self, payload: Dict[str, Any]) -> List[str]:
        """从payload中提取工具列表"""
        # 这里需要从已存储的切片中提取，暂时返回空列表
        # 在实际使用中，可以通过查询task_slices表来获取
        return []