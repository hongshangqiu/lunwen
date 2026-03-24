from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.services import knowledge_service
from app.config import KNOWLEDGE_DIR

router = APIRouter()


class KnowledgeSearchRequest(BaseModel):
    """知识检索请求"""
    query: str
    serviceName: Optional[str] = None
    topK: int = 3


class ReindexRequest(BaseModel):
    """重新索引请求"""
    knowledge_dir: Optional[str] = None


@router.post("/knowledge/search", response_model=dict)
def search_knowledge(req: KnowledgeSearchRequest):
    """
    知识检索接口
    """
    try:
        chunks = knowledge_service.search_knowledge(
            query=req.query,
            service_name=req.serviceName,
            top_k=req.topK
        )
        return {
            "success": True,
            "data": {
                "chunks": chunks
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/stats", response_model=dict)
def get_knowledge_stats():
    """
    获取知识库统计信息
    """
    try:
        from pathlib import Path
        
        # 统计文档数量
        md_files = list(KNOWLEDGE_DIR.glob("*.md"))
        sources = [f.name for f in md_files]
        
        # 统计向量库
        service = knowledge_service.KnowledgeService()
        total_chunks = service.vector_store.count()
        
        return {
            "success": True,
            "data": {
                "total_documents": len(md_files),
                "total_chunks": total_chunks,
                "sources": sources
            }
        }
    except Exception as e:
        return {
            "success": True,
            "data": {
                "total_documents": 0,
                "total_chunks": 0,
                "sources": []
            }
        }


@router.post("/knowledge/reindex", response_model=dict)
def reindex_knowledge(req: ReindexRequest = None):
    """
    重新索引知识库
    """
    try:
        if req and req.knowledge_dir:
            from pathlib import Path
            knowledge_dir = Path(req.knowledge_dir)
        else:
            knowledge_dir = KNOWLEDGE_DIR
        
        # 清空现有索引
        service = knowledge_service.KnowledgeService()
        service.vector_store.clear()
        
        # 重新索引
        total_chunks = knowledge_service.load_and_index_knowledge_dir(knowledge_dir)
        
        return {
            "success": True,
            "data": {
                "message": "索引完成",
                "total_chunks": total_chunks
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/knowledge/clear", response_model=dict)
def clear_knowledge():
    """
    清空知识库索引
    """
    try:
        service = knowledge_service.KnowledgeService()
        service.vector_store.clear()
        
        return {
            "success": True,
            "data": {
                "message": "向量库已清空"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
