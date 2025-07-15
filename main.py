from fastapi import FastAPI

app = FastAPI(title="Context Service", version="0.1.0")


@app.get("/healthz", tags=["Health"])
async def health_check():
    """健康检查端点，返回服务状态。"""
    return {"status": "ok"} 