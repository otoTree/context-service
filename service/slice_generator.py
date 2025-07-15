"""任务切片生成器"""
from typing import List, Dict, Any, Optional
from uuid import uuid4
from dataclasses import dataclass

from service.dsl_parser import DSLParseResult, DSLTask, DSLTool, DSLCondition


@dataclass
class TaskSlice:
    """任务切片数据结构"""
    slice_id: str
    name: str
    description: str
    task_type: str  # 'tool_call', 'condition_check', 'variable_assignment'
    dependencies: List[str]  # 依赖的切片ID列表
    parameters: Dict[str, Any]
    expected_output: Optional[str] = None
    status: str = "pending"
    order_index: int = 0


class SliceGenerator:
    """任务切片生成器
    
    负责将解析后的DSL任务转换为可执行的任务切片
    """
    
    def __init__(self):
        self.slice_counter = 0
    
    def generate_slices(self, parse_result: DSLParseResult) -> List[TaskSlice]:
        """从DSL解析结果生成任务切片
        
        Args:
            parse_result: DSL解析结果
            
        Returns:
            任务切片列表
        """
        slices = []
        self.slice_counter = 0
        
        # 首先为所有变量创建初始化切片
        for var in parse_result.variables:
            slice_obj = self._create_variable_slice(var.name, var.value)
            slices.append(slice_obj)
        
        # 为每个任务生成切片
        for task in parse_result.tasks:
            task_slices = self._generate_task_slices(task, parse_result)
            slices.extend(task_slices)
        
        # 设置切片的执行顺序
        self._set_execution_order(slices)
        
        return slices
    
    def _create_variable_slice(self, var_name: str, var_value: str) -> TaskSlice:
        """创建变量初始化切片"""
        self.slice_counter += 1
        
        return TaskSlice(
            slice_id=f"var_{self.slice_counter}_{var_name}",
            name=f"初始化变量: {var_name}",
            description=f"设置变量 {var_name} 的初始值",
            task_type="variable_assignment",
            dependencies=[],
            parameters={
                "variable_name": var_name,
                "variable_value": var_value,
                "operation": "initialize"
            },
            expected_output=var_name,
            order_index=self.slice_counter
        )
    
    def _generate_task_slices(self, task: DSLTask, parse_result: DSLParseResult) -> List[TaskSlice]:
        """为单个任务生成切片"""
        slices = []
        
        # 处理任务依赖
        dependencies = self._resolve_task_dependencies(task, parse_result)
        
        # 为任务中的每个工具调用创建切片
        for tool in task.tools:
            tool_slice = self._create_tool_slice(task, tool, dependencies)
            slices.append(tool_slice)
            
            # 为工具调用的条件检查创建切片
            for condition in task.conditions:
                condition_slice = self._create_condition_slice(
                    task, condition, [tool_slice.slice_id]
                )
                slices.append(condition_slice)
        
        return slices
    
    def _create_tool_slice(self, task: DSLTask, tool: DSLTool, dependencies: List[str]) -> TaskSlice:
        """创建工具调用切片"""
        self.slice_counter += 1
        
        # 解析工具参数中的变量引用
        resolved_params = self._resolve_parameters(tool.parameters)
        
        return TaskSlice(
            slice_id=f"tool_{self.slice_counter}_{tool.name}",
            name=f"调用工具: {tool.name}",
            description=f"在任务 {task.name} 中调用 {tool.name} 工具",
            task_type="tool_call",
            dependencies=dependencies,
            parameters={
                "tool_name": tool.name,
                "tool_parameters": resolved_params,
                "task_context": task.name
            },
            expected_output=f"{tool.name}_result",
            order_index=self.slice_counter
        )
    
    def _create_condition_slice(self, task: DSLTask, condition: DSLCondition, dependencies: List[str]) -> TaskSlice:
        """创建条件检查切片"""
        self.slice_counter += 1
        
        return TaskSlice(
            slice_id=f"condition_{self.slice_counter}_{condition.type}",
            name=f"条件检查: {condition.type}",
            description=f"在任务 {task.name} 中检查 {condition.type} 条件",
            task_type="condition_check",
            dependencies=dependencies,
            parameters={
                "condition_type": condition.type,
                "condition_expression": condition.expression,
                "actions": condition.actions,
                "task_context": task.name
            },
            expected_output=f"{condition.type}_result",
            order_index=self.slice_counter
        )
    
    def _resolve_task_dependencies(self, task: DSLTask, parse_result: DSLParseResult) -> List[str]:
        """解析任务依赖关系"""
        dependencies = []
        
        # 检查 @depends_on 声明
        for dep_task_name in task.dependencies:
            # 查找依赖任务的所有切片
            for other_task in parse_result.tasks:
                if other_task.name == dep_task_name:
                    # 添加依赖任务的最后一个切片作为依赖
                    dependencies.append(f"task_{other_task.name}_final")
                    break
        
        return dependencies
    
    def _resolve_parameters(self, parameters: Dict[str, str]) -> Dict[str, Any]:
        """解析参数中的变量引用"""
        resolved = {}
        
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith('$'):
                # 这是一个变量引用
                var_name = value[1:]  # 移除 $ 前缀
                resolved[key] = {
                    "type": "variable_reference",
                    "variable_name": var_name,
                    "original_value": value
                }
            else:
                resolved[key] = {
                    "type": "literal",
                    "value": value
                }
        
        return resolved
    
    def _set_execution_order(self, slices: List[TaskSlice]) -> None:
        """设置切片的执行顺序"""
        # 使用拓扑排序确定执行顺序
        ordered_slices = self._topological_sort(slices)
        
        for i, slice_obj in enumerate(ordered_slices):
            slice_obj.order_index = i + 1
    
    def _topological_sort(self, slices: List[TaskSlice]) -> List[TaskSlice]:
        """对切片进行拓扑排序"""
        # 创建切片ID到切片对象的映射
        slice_map = {s.slice_id: s for s in slices}
        
        # 计算每个切片的入度
        in_degree = {s.slice_id: 0 for s in slices}
        for slice_obj in slices:
            for dep in slice_obj.dependencies:
                if dep in in_degree:
                    in_degree[slice_obj.slice_id] += 1
        
        # 使用队列进行拓扑排序
        queue = [s for s in slices if in_degree[s.slice_id] == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            # 更新依赖当前切片的其他切片的入度
            for slice_obj in slices:
                if current.slice_id in slice_obj.dependencies:
                    in_degree[slice_obj.slice_id] -= 1
                    if in_degree[slice_obj.slice_id] == 0:
                        queue.append(slice_obj)
        
        return result
    
    def get_slice_statistics(self, slices: List[TaskSlice]) -> Dict[str, Any]:
        """获取切片统计信息"""
        stats = {
            "total_slices": len(slices),
            "slice_types": {},
            "max_dependencies": 0,
            "avg_dependencies": 0
        }
        
        total_deps = 0
        for slice_obj in slices:
            # 统计切片类型
            slice_type = slice_obj.task_type
            stats["slice_types"][slice_type] = stats["slice_types"].get(slice_type, 0) + 1
            
            # 统计依赖关系
            dep_count = len(slice_obj.dependencies)
            total_deps += dep_count
            stats["max_dependencies"] = max(stats["max_dependencies"], dep_count)
        
        if len(slices) > 0:
            stats["avg_dependencies"] = total_deps / len(slices)
        
        return stats