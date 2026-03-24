"""
知识库向量化脚本

将 data/docs/ 目录下的知识文档向量化并存储到向量数据库中。
支持 front-matter 元数据解析和文档自动分块。
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
import json
import hashlib

from app.config import KNOWLEDGE_DIR, VECTOR_STORE_DIR
from app.services.knowledge_service import (
    KnowledgeService,
    chunk_document,
    load_and_index_knowledge_dir
)


def generate_doc_id(filename: str, index: int = 0) -> str:
    """生成文档 ID"""
    unique_str = f"{filename}:{index}"
    return hashlib.md5(unique_str.encode()).hexdigest()[:8]


def process_single_document(file_path: Path) -> dict:
    """处理单个文档文件"""
    print(f"\n处理文件: {file_path.name}")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if not content.strip():
            print(f"  ⚠️ 文件为空，跳过")
            return None
        
        # 解析 front-matter
        from app.services.knowledge_service import parse_document_metadata
        metadata = parse_document_metadata(content)
        
        # 设置默认值
        if not metadata.get("doc_id"):
            metadata["doc_id"] = file_path.stem
        if not metadata.get("title"):
            metadata["title"] = file_path.stem.replace("_", " ")
        
        print(f"  标题: {metadata['title']}")
        print(f"  故障类型: {metadata['fault_type'] or '未指定'}")
        print(f"  服务名: {metadata['service_name'] or '未指定'}")
        
        # 分块
        chunks = chunk_document(content, metadata["doc_id"])
        print(f"  分块数量: {len(chunks)}")
        
        return {
            "metadata": metadata,
            "chunks": chunks,
            "file_path": file_path
        }
    
    except Exception as e:
        print(f"  ❌ 处理失败: {e}")
        return None


def main():
    """主函数"""
    print("=" * 60)
    print("LLM-Ops Copilot 知识库向量化脚本")
    print("=" * 60)
    
    # 检查知识目录
    if not KNOWLEDGE_DIR.exists():
        print(f"\n❌ 错误: 知识目录不存在: {KNOWLEDGE_DIR}")
        print("请确保 data/docs/ 目录存在并包含知识文档 (.md 文件)")
        return
    
    # 列出所有 md 文件
    md_files = list(KNOWLEDGE_DIR.glob("*.md"))
    
    if not md_files:
        print(f"\n⚠️ 警告: 知识目录中没有找到 .md 文件")
        print(f"目录: {KNOWLEDGE_DIR}")
        return
    
    print(f"\n找到 {len(md_files)} 个知识文档")
    
    # 处理每个文档
    all_chunks = []
    for file_path in md_files:
        result = process_single_document(file_path)
        if result:
            all_chunks.extend(result["chunks"])
    
    if not all_chunks:
        print("\n❌ 没有可索引的文档块")
        return
    
    print(f"\n总共 {len(all_chunks)} 个文档块待索引")
    
    # 创建向量服务并索引
    print("\n开始向量化索引...")
    service = KnowledgeService()
    
    # 可选：清空现有索引
    if input("是否清空现有索引? (y/N): ").lower() == 'y':
        print("清空现有索引...")
        service.vector_store.clear()
    
    # 索引文档
    count = service.index_documents(all_chunks)
    print(f"\n✅ 索引完成! 共索引 {count} 个文档块")
    
    # 显示统计信息
    print("\n" + "=" * 60)
    print("索引统计:")
    print(f"  向量库路径: {VECTOR_STORE_DIR}")
    print(f"  文档总数: {len(md_files)}")
    print(f"  文档块总数: {count}")
    print(f"  向量库大小: {service.vector_store.count()} 条")
    print("=" * 60)


if __name__ == "__main__":
    main()
