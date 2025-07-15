"""DSL解析器 - 将DSL文件解析为任务切片"""
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class DSLTokenType(Enum):
    """DSL语法元素类型"""
    VAR = "var"
    TASK = "task"
    TOOL = "tool"
    IF = "if"
    ELSE = "else"
    NEXT = "next"
    TEXT = "text"
    COMMENT = "comment"


@dataclass
class DSLVariable:
    """DSL变量定义"""
    name: str
    default_value: str
    type: str = "string"


@dataclass
class DSLTool:
    """DSL工具调用"""
    name: str
    description: str
    position: int


@dataclass
class DSLCondition:
    """DSL条件分支"""
    expression: str
    true_next: Optional[str]
    false_next: Optional[str]


@dataclass
class DSLTask:
    """DSL任务定义"""
    name: str
    title: str
    description: List[str]
    tools: List[DSLTool]
    conditions: List[DSLCondition]
    variables_used: List[str]
    default_next: Optional[str]


@dataclass
class DSLParseResult:
    """DSL解析结果"""
    variables: Dict[str, DSLVariable]
    tasks: Dict[str, DSLTask]
    metadata: Dict[str, Any]


class DSLParseError(Exception):
    """DSL解析错误"""
    def __init__(self, line_number: int, message: str):
        self.line_number = line_number
        self.message = message
        super().__init__(f"Line {line_number}: {message}")


class DSLParser:
    """DSL解析器"""
    
    def __init__(self):
        self.current_line = 0
        self.variables: Dict[str, DSLVariable] = {}
        self.tasks: Dict[str, DSLTask] = {}
        self.metadata: Dict[str, Any] = {}
    
    def parse(self, dsl_content: str) -> DSLParseResult:
        """解析DSL内容"""
        self._reset()
        lines = dsl_content.strip().split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            self.current_line = i + 1
            
            if not line or line.startswith('#'):
                # 处理注释和元数据
                self._parse_comment(line)
                i += 1
            elif line.startswith('@var'):
                # 解析变量定义
                self._parse_variable(line)
                i += 1
            elif line.startswith('@task'):
                # 解析任务定义（多行）
                i = self._parse_task(lines, i)
            else:
                i += 1
        
        # 验证解析结果
        self._validate_parse_result()
        
        return DSLParseResult(
            variables=self.variables,
            tasks=self.tasks,
            metadata=self.metadata
        )
    
    def _reset(self):
        """重置解析器状态"""
        self.current_line = 0
        self.variables.clear()
        self.tasks.clear()
        self.metadata.clear()
    
    def _parse_comment(self, line: str):
        """解析注释和元数据"""
        if line.startswith('# Source:'):
            self.metadata['source'] = line.replace('# Source:', '').strip()
        elif line.startswith('# Generated at:'):
            self.metadata['generated_at'] = line.replace('# Generated at:', '').strip()
        elif line.startswith('# Provider:'):
            self.metadata['provider'] = line.replace('# Provider:', '').strip()
        elif line.startswith('# Model:'):
            self.metadata['model'] = line.replace('# Model:', '').strip()
    
    def _parse_variable(self, line: str):
        """解析变量定义: @var complaint_severity = ""."""
        match = re.match(r'@var\s+(\w+)\s*=\s*"([^"]*)"', line)
        if not match:
            raise DSLParseError(self.current_line, f"Invalid variable syntax: {line}")
        
        var_name, default_value = match.groups()
        self.variables[var_name] = DSLVariable(
            name=var_name,
            default_value=default_value,
            type="string"
        )
    
    def _parse_task(self, lines: List[str], start_index: int) -> int:
        """解析任务定义（多行）"""
        task_line = lines[start_index].strip()
        
        # 解析任务头: @task task_name 任务标题
        match = re.match(r'@task\s+(\w+)\s*(.*)', task_line)
        if not match:
            raise DSLParseError(self.current_line, f"Invalid task syntax: {task_line}")
        
        task_name, task_title = match.groups()
        task_title = task_title.strip()
        
        # 解析任务体
        i = start_index + 1
        description = []
        tools = []
        conditions = []
        variables_used = []
        default_next = None
        
        while i < len(lines):
            line = lines[i].strip()
            self.current_line = i + 1
            
            if not line:
                i += 1
                continue
            elif line.startswith('@task'):
                # 下一个任务开始，结束当前任务解析
                break
            elif line.startswith('@tool'):
                # 解析工具调用
                tool = self._parse_tool(line, len(description))
                tools.append(tool)
            elif line.startswith('@if'):
                # 解析条件分支
                condition, next_i = self._parse_condition(lines, i)
                conditions.append(condition)
                i = next_i - 1  # 因为外层循环会+1
            elif line.startswith('@next'):
                # 解析默认跳转
                default_next = self._parse_next(line)
            else:
                # 普通描述文本
                description.append(line)
                # 提取变量引用
                variables_used.extend(self._extract_variables(line))
            
            i += 1
        
        # 创建任务对象
        self.tasks[task_name] = DSLTask(
            name=task_name,
            title=task_title,
            description=description,
            tools=tools,
            conditions=conditions,
            variables_used=list(set(variables_used)),
            default_next=default_next
        )
        
        return i
    
    def _parse_tool(self, line: str, position: int) -> DSLTool:
        """解析工具调用: @tool tool_name 工具描述"""
        match = re.match(r'@tool\s+(\w+)\s*(.*)', line)
        if not match:
            raise DSLParseError(self.current_line, f"Invalid tool syntax: {line}")
        
        tool_name, description = match.groups()
        return DSLTool(
            name=tool_name,
            description=description.strip(),
            position=position
        )
    
    def _parse_condition(self, lines: List[str], start_index: int) -> tuple[DSLCondition, int]:
        """解析条件分支"""
        if_line = lines[start_index].strip()
        
        # 解析if表达式
        match = re.match(r'@if\s+(.+)', if_line)
        if not match:
            raise DSLParseError(self.current_line, f"Invalid if syntax: {if_line}")
        
        expression = match.group(1).strip()
        true_next = None
        false_next = None
        
        i = start_index + 1
        while i < len(lines):
            line = lines[i].strip()
            self.current_line = i + 1
            
            if line.startswith('@next'):
                if true_next is None:
                    true_next = self._parse_next(line)
                else:
                    break  # 已经解析了true分支，退出
            elif line.startswith('@else'):
                i += 1
                if i < len(lines):
                    else_line = lines[i].strip()
                    if else_line.startswith('@next'):
                        false_next = self._parse_next(else_line)
                        i += 1
                        break
            elif line.startswith('@task') or line.startswith('@'):
                break
            
            i += 1
        
        return DSLCondition(
            expression=expression,
            true_next=true_next,
            false_next=false_next
        ), i
    
    def _parse_next(self, line: str) -> str:
        """解析跳转指令: @next task_name"""
        match = re.match(r'@next\s+(\w+)', line)
        if not match:
            raise DSLParseError(self.current_line, f"Invalid next syntax: {line}")
        
        return match.group(1)
    
    def _extract_variables(self, text: str) -> List[str]:
        """从文本中提取变量引用 {{variable_name}}"""
        pattern = r'\{\{(\w+)\}\}'
        return re.findall(pattern, text)
    
    def _validate_parse_result(self):
        """验证解析结果的完整性"""
        # 验证任务引用的完整性
        all_task_names = set(self.tasks.keys())
        
        for task_name, task in self.tasks.items():
            # 验证default_next引用
            if task.default_next and task.default_next not in all_task_names and task.default_next != "END":
                raise DSLParseError(0, f"Task '{task_name}' references unknown next task: '{task.default_next}'")
            
            # 验证条件分支引用
            for condition in task.conditions:
                if condition.true_next and condition.true_next not in all_task_names and condition.true_next != "END":
                    raise DSLParseError(0, f"Task '{task_name}' condition references unknown task: '{condition.true_next}'")
                if condition.false_next and condition.false_next not in all_task_names and condition.false_next != "END":
                    raise DSLParseError(0, f"Task '{task_name}' condition references unknown task: '{condition.false_next}'")
            
            # 验证变量引用
            for var_name in task.variables_used:
                if var_name not in self.variables:
                    raise DSLParseError(0, f"Task '{task_name}' uses undefined variable: '{var_name}'")


# 使用示例
def parse_dsl_file(file_path: str) -> DSLParseResult:
    """解析DSL文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    parser = DSLParser()
    return parser.parse(content)


def generate_task_slices(parse_result: DSLParseResult) -> List[Dict[str, Any]]:
    """根据解析结果生成任务切片数据"""
    slices = []
    
    for index, (task_name, task) in enumerate(parse_result.tasks.items()):
        slice_data = {
            "task_name": task.name,
            "task_title": task.title,
            "description": task.description,
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "position": tool.position
                }
                for tool in task.tools
            ],
            "conditions": [
                {
                    "expression": condition.expression,
                    "true_next": condition.true_next,
                    "false_next": condition.false_next
                }
                for condition in task.conditions
            ],
            "variables_used": task.variables_used,
            "default_next": task.default_next
        }
        
        slices.append({
            "slice_index": index,
            "content": slice_data,
            "status": "pending"
        })
    
    return slices


# 测试代码
if __name__ == "__main__":
    # 示例DSL内容
    dsl_content = '''
# LLM Generated DSL Code
# Source: sop_test_cases/level_2_medium_natural.txt
# Generated at: 2025-07-15T10:08:09.144390
# Provider: openai
# Model: deepseek-chat-0324

@var complaint_severity = ""
@var customer_type = ""

@task receive_complaint 接收与评估投诉
    使用CRM系统创建新的投诉工单
    @tool crm_system_create 创建投诉工单
    记录客户信息、联系方式和投诉内容
    初步设置投诉严重等级：{{complaint_severity}}
    查询客户类型：{{customer_type}}
    @if complaint_severity == "高" OR customer_type == "VIP客户"
        @next escalate_complaint
    @else
        @next regular_processing
    '''
    
    try:
        parser = DSLParser()
        result = parser.parse(dsl_content)
        
        print("解析成功！")
        print(f"变量数量: {len(result.variables)}")
        print(f"任务数量: {len(result.tasks)}")
        print(f"元数据: {result.metadata}")
        
        # 生成切片
        slices = generate_task_slices(result)
        print(f"生成切片数量: {len(slices)}")
        
    except DSLParseError as e:
        print(f"DSL解析错误: {e}") 