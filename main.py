from contextlib import asynccontextmanager
from fastapi import FastAPI
from api.task_routes import router as task_router
from repository.database import init_database, close_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    await init_database()
    yield
    # 关闭时清理资源
    await close_database()


app = FastAPI(
    title="Context Service", 
    version="0.1.0",
    description="DSL任务切片解析和存储服务",
    lifespan=lifespan
)

# 注册路由
app.include_router(task_router)


@app.get("/healthz", tags=["Health"])
async def health_check():
    """健康检查端点，返回服务状态。"""
    return {"status": "ok"}