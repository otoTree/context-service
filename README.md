# Context Service

本项目实现 Context Service 核心框架，负责为分布式 Agent 构建 Prompt 上下文、管理任务生命周期，并对结果进行评估。

## DSL任务切片服务

新增了DSL（领域特定语言）任务切片功能，支持：
- **DSL解析**: 解析自定义DSL语法，提取变量、工具调用、条件判断等
- **任务切片生成**: 将复杂任务分解为可执行的切片
- **文件上传**: 支持上传.dsl文件进行解析
- **文本输入**: 支持直接输入DSL文本内容
- **任务查询**: 提供任务详情和切片信息的查询接口

## 快速开始

### 环境准备

```bash
# 安装Python依赖
pip install -r requirements.txt

# 设置环境变量（可选）
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=context_service
export DB_USER=postgres
export DB_PASSWORD=postgres
```

### 数据库设置

确保PostgreSQL服务正在运行，并创建数据库：

```sql
CREATE DATABASE context_service;
```

运行数据库迁移脚本：

```bash
psql -U postgres -d context_service -f db/schema.sql
```

### 启动服务

```bash
# 使用启动脚本
python run_server.py

# 或者直接使用uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

访问以下地址：
- 健康检查: `http://localhost:8000/healthz`
- API文档: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API接口

### DSL任务切片相关接口

- `POST /api/tasks/upload-dsl` - 上传DSL文件
- `POST /api/tasks/create-from-text` - 从文本创建任务
- `GET /api/tasks/{task_id}` - 获取任务详情
- `GET /api/tasks/{task_id}/slices` - 获取任务切片
- `GET /api/tasks/` - 获取任务列表

### 测试

运行测试脚本验证API功能：

```bash
python test_api.py
```

## 目录结构

- `api/`           对外 API 层（包含任务切片相关路由）
- `service/`       核心业务逻辑（DSL解析器、切片生成器、任务服务）
- `repository/`    数据存取封装（数据库模型和连接管理）
- `mock/`          Mock Registry/Service Stub
- `observability/` 日志与监控
- `doc/`           设计文档
- `db/`            数据库相关文件
- `test_api.py`    API测试脚本
- `run_server.py`  服务启动脚本

## CI
GitHub Actions 工作流会在推送或 PR 时执行静态检查与测试，确保主分支稳定。