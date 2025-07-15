# Context Service

本项目实现 Context Service 核心框架，负责为分布式 Agent 构建 Prompt 上下文、管理任务生命周期，并对结果进行评估。

## 快速开始

```bash
# 安装 uv（若未安装）
pip install uv

# 安装依赖（使用清华 PyPI 镜像，已在 pyproject.toml 中配置）
uv pip install --system -r pyproject.toml

# 运行开发服务器
uvicorn main:app --reload
```

访问 `http://localhost:8000/healthz` 查看健康检查。

## 目录结构

- `api/`           对外 API 层（FastAPI Router 将在此处补充）
- `service/`       核心业务逻辑
- `repository/`    数据存取封装
- `mock/`          Mock Registry/Service Stub
- `observability/` 日志与监控
- `doc/`           设计文档

## CI
GitHub Actions 工作流会在推送或 PR 时执行静态检查与测试，确保主分支稳定。 