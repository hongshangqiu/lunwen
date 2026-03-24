from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import API_PREFIX
from app.logging_config import setup_logger
from app.routers import scenes, metrics, logs, knowledge, analyze, evaluation

# 配置应用日志
logger = setup_logger("APIServer", "api_server.log")

app = FastAPI(
    title="LLM-Ops Copilot API",
    description="基于大模型的智能运维分析系统 API - LLM-Ops Copilot",
    version="2.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(scenes.router, prefix=API_PREFIX, tags=["场景管理"])
app.include_router(metrics.router, prefix=API_PREFIX, tags=["指标查询"])
app.include_router(logs.router, prefix=API_PREFIX, tags=["日志查询"])
app.include_router(knowledge.router, prefix=API_PREFIX, tags=["知识库"])
app.include_router(analyze.router, prefix=API_PREFIX, tags=["AI 分析"])
app.include_router(evaluation.router, prefix=API_PREFIX, tags=["实验评估"])


@app.get("/")
def root():
    """健康检查"""
    return {
        "message": "AIOps-LLM-RAG API is running",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    from app.config import BACKEND_PORT
    uvicorn.run(app, host="0.0.0.0", port=BACKEND_PORT)
