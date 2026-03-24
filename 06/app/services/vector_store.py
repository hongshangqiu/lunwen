"""
向量数据库封装模块
论文引用：此模块实现知识库的向量化存储与检索

提供运维知识的向量化存储和语义检索功能，支持：
- 文档块添加和向量化
- 基于语义的相似性检索
- 元数据过滤
"""
from typing import List, Dict, Optional
from pathlib import Path
import json
import hashlib
from dataclasses import dataclass, field

try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False


@dataclass
class DocumentChunk:
    """文档块数据结构"""
    content: str
    doc_id: str
    title: str = ""
    service_name: str = ""
    fault_type: str = ""
    keywords: List[str] = field(default_factory=list)
    source_type: str = "SOP"  # SOP/案例/架构


class VectorStore:
    """
    运维知识向量库封装
    
    基于 ChromaDB 实现的向量数据库，支持：
    - 持久化存储
    - 语义检索
    - 元数据过滤
    """
    
    COLLECTION_NAME = "ops_knowledge"
    
    def __init__(self, persist_dir: str = "vector_store/chroma_db"):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        if HAS_CHROMADB:
            self.client = chromadb.PersistentClient(
                path=str(self.persist_dir),
                settings=Settings(anonymized_telemetry=False)
            )
            self.collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"description": "运维知识库向量存储"}
            )
        else:
            self.client = None
            self.collection = None
            self._fallback_store: List[Dict] = []
    
    def _generate_id(self, content: str, doc_id: str) -> str:
        """生成唯一 ID"""
        unique_str = f"{doc_id}:{content[:100]}"
        return hashlib.md5(unique_str.encode()).hexdigest()
    
    def _extract_keywords_from_content(self, content: str) -> List[str]:
        """从内容中提取关键词"""
        common_keywords = [
            "timeout", "connection", "pool", "exhausted", "cpu", "memory",
            "leak", "oom", "database", "disk", "network", "latency",
            "error", "warning", "deadlock", "crash", "slow", "spike"
        ]
        content_lower = content.lower()
        found = [kw for kw in common_keywords if kw in content_lower]
        return found
    
    def add_documents(self, chunks: List[Dict]) -> int:
        """
        添加文档块到向量库
        
        Args:
            chunks: List[{
                "content": str,        # 文本内容
                "doc_id": str,         # 文档ID
                "title": str,          # 标题
                "service_name": str,   # 服务名
                "fault_type": str,     # 故障类型
                "keywords": List[str], # 关键词
                "source_type": str     # 来源类型 SOP/案例/架构
            }]
        
        Returns:
            添加的文档数量
        """
        if not chunks:
            return 0
        
        if self.collection is None:
            # 使用内存存储作为后备
            for chunk in chunks:
                self._fallback_store.append({
                    "content": chunk.get("content", ""),
                    "doc_id": chunk.get("doc_id", ""),
                    "metadata": {
                        "title": chunk.get("title", ""),
                        "service_name": chunk.get("service_name", ""),
                        "fault_type": chunk.get("fault_type", ""),
                        "keywords": chunk.get("keywords", []),
                        "source_type": chunk.get("source_type", "SOP")
                    }
                })
            return len(chunks)
        
        # ChromaDB 实现
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for chunk in chunks:
            chunk_id = self._generate_id(chunk.get("content", ""), chunk.get("doc_id", ""))
            
            # 提取关键词
            keywords = chunk.get("keywords", [])
            if not keywords:
                keywords = self._extract_keywords_from_content(chunk.get("content", ""))
            
            ids.append(chunk_id)
            documents.append(chunk.get("content", ""))
            metadatas.append({
                "doc_id": chunk.get("doc_id", ""),
                "title": chunk.get("title", ""),
                "service_name": chunk.get("service_name", ""),
                "fault_type": chunk.get("fault_type", ""),
                "keywords": json.dumps(keywords),
                "source_type": chunk.get("source_type", "SOP")
            })
            
            # 生成伪嵌入（用于后备模式）
            embeddings.append([0.0] * 384)
        
        # 添加到 ChromaDB
        try:
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
        except Exception as e:
            print(f"添加文档到向量库失败: {e}")
            return 0
        
        return len(chunks)
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        向量检索
        
        Args:
            query: 查询文本
            top_k: 返回数量
            filters: 元数据过滤条件
        
        Returns:
            List[{
                "content": str,
                "source": str,
                "score": float,
                "metadata": dict
            }]
        """
        if self.collection is None:
            return self._fallback_search(query, top_k, filters)
        
        # 构建查询条件
        where_clause = {}
        if filters:
            for key, value in filters.items():
                if value is not None:
                    where_clause[key] = value
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_clause if where_clause else None
            )
            
            # 格式化结果
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    distance = results["distances"][0][i] if results["distances"] else 0.0
                    
                    # 将距离转换为相似度分数
                    score = max(0.0, 1.0 - distance / 2.0)
                    
                    formatted_results.append({
                        "content": doc,
                        "source": metadata.get("doc_id", metadata.get("title", "unknown")),
                        "score": round(score, 4),
                        "metadata": {
                            "title": metadata.get("title", ""),
                            "service_name": metadata.get("service_name", ""),
                            "fault_type": metadata.get("fault_type", ""),
                            "keywords": json.loads(metadata.get("keywords", "[]")),
                            "source_type": metadata.get("source_type", "SOP")
                        }
                    })
            
            return formatted_results
        
        except Exception as e:
            print(f"向量检索失败: {e}")
            return self._fallback_search(query, top_k, filters)
    
    def _fallback_search(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict]
    ) -> List[Dict]:
        """后备搜索实现（基于关键词匹配）"""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored_results = []
        
        for item in self._fallback_store:
            content = item.get("content", "").lower()
            metadata = item.get("metadata", {})
            
            # 应用过滤器
            if filters:
                skip = False
                for key, value in filters.items():
                    meta_value = metadata.get(key, "")
                    if isinstance(meta_value, str) and value.lower() not in meta_value.lower():
                        skip = True
                        break
                if skip:
                    continue
            
            # 简单评分：计算查询词在内容中的出现次数
            score = sum(1 for word in query_words if word in content)
            
            # 如果没有精确匹配，检查关键词
            if score == 0:
                for keyword in metadata.get("keywords", []):
                    if keyword.lower() in query_lower:
                        score = 0.5
                        break
            
            if score > 0:
                scored_results.append({
                    "content": item.get("content", ""),
                    "source": item.get("doc_id", "unknown"),
                    "score": score / len(query_words),
                    "metadata": metadata
                })
        
        # 按分数排序
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]
    
    def delete_by_doc_id(self, doc_id: str) -> bool:
        """删除指定文档的所有块"""
        if self.collection is None:
            self._fallback_store = [
                item for item in self._fallback_store
                if item.get("doc_id") != doc_id
            ]
            return True
        
        try:
            # 获取该文档的所有 ID
            result = self.collection.get(where={"doc_id": doc_id})
            if result and result["ids"]:
                self.collection.delete(ids=result["ids"])
            return True
        except Exception as e:
            print(f"删除文档失败: {e}")
            return False
    
    def count(self) -> int:
        """获取存储的文档数量"""
        if self.collection is None:
            return len(self._fallback_store)
        
        try:
            return self.collection.count()
        except:
            return len(self._fallback_store)
    
    def clear(self) -> bool:
        """清空向量库"""
        if self.collection is None:
            self._fallback_store = []
            return True
        
        try:
            self.client.delete_collection(self.COLLECTION_NAME)
            self.collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"description": "运维知识库向量存储"}
            )
            return True
        except Exception as e:
            print(f"清空向量库失败: {e}")
            return False
