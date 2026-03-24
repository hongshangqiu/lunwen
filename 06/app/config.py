import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 数据目录
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = DATA_DIR / "logs"
KNOWLEDGE_DIR = DATA_DIR / "docs"

# 向量数据库目录
VECTOR_STORE_DIR = BASE_DIR / "vector_store" / "chroma_db"

# 大模型配置
LLM_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
LLM_BASE_URL: Optional[str] = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL: Optional[str] = os.getenv("MODEL_ID", "gpt-3.5-turbo")

# Prometheus 配置 (可选)
PROMETHEUS_URL: Optional[str] = os.getenv("PROMETHEUS_URL", "http://localhost:9090")

# 服务配置
API_PREFIX = "/api"
BACKEND_PORT = int(os.getenv("BACKEND_PORT", 8001))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# 日志配置
LOG_FILE = LOGS_DIR / "app.log"
