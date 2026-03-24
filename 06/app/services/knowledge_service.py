"""
论文引用：此模块实现 RAG 的检索流程

运维知识检索服务，基于向量数据库提供语义检索能力：
1. 接收自然语言查询
2. 转换为向量
3. 在向量库中检索相似片段
4. 可选：按元数据过滤
5. 返回相关知识块
"""
from typing import List, Dict, Optional
from pathlib import Path
import os
import re
from app.services.vector_store import VectorStore
from app.config import KNOWLEDGE_DIR


class KnowledgeService:
    """运维知识检索服务"""
    
    def __init__(self, persist_dir: str = None):
        if persist_dir is None:
            from app.config import VECTOR_STORE_DIR
            persist_dir = str(VECTOR_STORE_DIR)
        self.vector_store = VectorStore(persist_dir=persist_dir)
    
    def retrieve(
        self,
        query: str,
        service: str = None,
        fault_type: str = None,
        top_k: int = 3
    ) -> List[Dict]:
        """
        RAG 检索流程：
        1. 接收自然语言查询
        2. 转换为向量
        3. 在向量库中检索相似片段
        4. 可选：按元数据过滤
        5. 返回相关知识块
        
        Args:
            query: 自然语言查询
            service: 服务名过滤（可选）
            fault_type: 故障类型过滤（可选）
            top_k: 返回结果数量
        
        Returns:
            List[Dict]: 检索到的知识块列表
        """
        filters = {}
        if service:
            filters["service_name"] = service
        if fault_type:
            filters["fault_type"] = fault_type
        
        results = self.vector_store.search(
            query=query,
            top_k=top_k,
            filters=filters if filters else None
        )
        
        return self._format_results(results)
    
    def _format_results(self, results: List[Dict]) -> List[Dict]:
        """格式化检索结果"""
        formatted = []
        for item in results:
            formatted.append({
                "content": item.get("content", ""),
                "source": item.get("source", ""),
                "score": item.get("score", 0.0),
                "metadata": item.get("metadata", {})
            })
        return formatted
    
    def index_documents(self, documents: List[Dict]) -> int:
        """
        将文档索引到向量库
        
        Args:
            documents: 文档列表，每项包含：
                - content: 文本内容
                - doc_id: 文档ID
                - title: 标题
                - service_name: 服务名
                - fault_type: 故障类型
                - keywords: 关键词列表
                - source_type: 来源类型
        
        Returns:
            索引的文档数量
        """
        return self.vector_store.add_documents(documents)
    
    def search_by_keywords(
        self,
        keywords: List[str],
        top_k: int = 5
    ) -> List[Dict]:
        """
        基于关键词搜索（不使用向量检索）
        
        Args:
            keywords: 关键词列表
            top_k: 返回结果数量
        
        Returns:
            List[Dict]: 检索到的知识块
        """
        query = " ".join(keywords)
        return self.retrieve(query, top_k=top_k)


def parse_document_metadata(content: str) -> Dict:
    """
    从文档内容中解析元数据（front-matter）
    
    支持 YAML 格式的 front-matter:
    ---
    doc_id: SOP-DB-001
    title: 数据库连接池耗尽故障处理
    service_name: payment-service
    fault_type: database
    keywords: [connection, pool, timeout]
    source_type: SOP
    ---
    """
    metadata = {
        "doc_id": "",
        "title": "",
        "service_name": "",
        "fault_type": "",
        "keywords": [],
        "source_type": "SOP"
    }
    
    # 提取 front-matter
    pattern = r'^---\s*\n(.*?)\n---'
    match = re.match(pattern, content, re.DOTALL)
    
    if match:
        front_matter = match.group(1)
        for line in front_matter.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if key == "keywords":
                    # 解析列表
                    keywords_str = value.strip('[]')
                    metadata["keywords"] = [k.strip() for k in keywords_str.split(',')]
                elif key in metadata:
                    metadata[key] = value
    
    return metadata


def chunk_document(content: str, doc_id: str, chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
    """
    将长文档切分为小块
    
    Args:
        content: 文档内容
        doc_id: 文档ID
        chunk_size: 块大小（字符数）
        overlap: 块之间的重叠字符数
    
    Returns:
        List[Dict]: 文档块列表
    """
    # 提取 front-matter
    metadata = parse_document_metadata(content)
    
    # 移除 front-matter，只保留正文
    body = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
    
    # 按段落分割
    paragraphs = [p.strip() for p in body.split('\n\n') if p.strip()]
    
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) < chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append({
                    "content": current_chunk.strip(),
                    "doc_id": doc_id,
                    "title": metadata.get("title", ""),
                    "service_name": metadata.get("service_name", ""),
                    "fault_type": metadata.get("fault_type", ""),
                    "keywords": metadata.get("keywords", []),
                    "source_type": metadata.get("source_type", "SOP")
                })
            current_chunk = para + "\n\n"
    
    # 添加最后一个块
    if current_chunk:
        chunks.append({
            "content": current_chunk.strip(),
            "doc_id": doc_id,
            "title": metadata.get("title", ""),
            "service_name": metadata.get("service_name", ""),
            "fault_type": metadata.get("fault_type", ""),
            "keywords": metadata.get("keywords", []),
            "source_type": metadata.get("source_type", "SOP")
        })
    
    return chunks


def load_and_index_knowledge_dir(knowledge_dir: Path = None) -> int:
    """
    加载并索引知识目录下的所有文档
    
    Args:
        knowledge_dir: 知识目录路径，默认使用 KNOWLEDGE_DIR
    
    Returns:
        索引的文档块数量
    """
    if knowledge_dir is None:
        knowledge_dir = KNOWLEDGE_DIR
    
    if not knowledge_dir.exists():
        print(f"知识目录不存在: {knowledge_dir}")
        return 0
    
    service = KnowledgeService()
    total_chunks = 0
    
    # 遍历所有 md 文件
    for md_file in knowledge_dir.glob("*.md"):
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 提取文档 ID
            doc_id = md_file.stem
            
            # 切分文档
            chunks = chunk_document(content, doc_id)
            
            # 索引到向量库
            if chunks:
                count = service.index_documents(chunks)
                total_chunks += count
                print(f"已索引 {md_file.name}: {count} 个块")
        
        except Exception as e:
            print(f"处理文件 {md_file} 失败: {e}")
    
    return total_chunks


# 便捷函数
def search_knowledge(query: str, service_name: Optional[str] = None, top_k: int = 3) -> List[Dict]:
    """
    检索运维知识库（便捷函数）
    基于关键词匹配的简单实现
    """
    service = KnowledgeService()
    results = service.retrieve(query, service=service_name, top_k=top_k)
    
    if not results:
        # 后备：使用关键词匹配
        keyword_mapping = {
            "数据库连接": ["SOP_Database.md"],
            "connection": ["SOP_Database.md"],
            "pool": ["SOP_Database.md"],
            "timeout": ["SOP_Database.md"],
            "CPU": ["SOP_CPU.md"],
            "cpu": ["SOP_CPU.md"],
            "spike": ["SOP_CPU.md"],
            "内存": ["SOP_Memory.md"],
            "memory": ["SOP_Memory.md"],
            "leak": ["SOP_Memory.md"],
            "OOM": ["SOP_Memory.md"],
        }
        
        matched_files = set()
        query_lower = query.lower()
        
        for keyword, files in keyword_mapping.items():
            if keyword.lower() in query_lower:
                matched_files.update(files)
        
        if not matched_files:
            all_files = list(KNOWLEDGE_DIR.glob("*.md"))
            matched_files = [f.name for f in all_files]
        
        results = []
        for filename in list(matched_files)[:top_k]:
            file_path = KNOWLEDGE_DIR / filename
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    score = 0.8
                    if service_name and service_name.lower() in content.lower():
                        score = 0.9
                    
                    results.append({
                        "content": content[:500],
                        "source": filename,
                        "score": score,
                        "metadata": {}
                    })
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
    
    return results
