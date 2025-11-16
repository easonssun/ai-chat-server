"""
RAG与LLM集成模块
提供将RAG搜索结果整合到LLM提示中的功能
"""

from rag.rag_system import RAG
from typing import List, Dict, Any


class RAGIntegration:
    """RAG与LLM集成类"""
    
    def __init__(self, collection_name: str = "documents"):
        """
        初始化RAG集成
        
        Args:
            collection_name: Milvus集合名称
        """
        self.collection_name = collection_name
        self.rag = RAG
    
    def search_documents(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        搜索相关文档
        
        Args:
            query: 查询语句
            k: 返回结果数量
            
        Returns:
            包含文档内容和元数据的字典列表
        """
        try:
            results = self.rag.search(query, self.collection_name, k)
            formatted_results = []
            
            for doc in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "source": doc.metadata.get("source", "Unknown")
                })
            
            return formatted_results
        except Exception as e:
            print(f"文档搜索出错: {e}")
            return []
    
    def format_context_for_prompt(self, documents: List[Dict[str, Any]]) -> str:
        """
        将搜索到的文档格式化为提示上下文
        
        Args:
            documents: 文档列表
            
        Returns:
            格式化的上下文字符串
        """
        if not documents:
            return "未找到相关文档。"
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(
                f"文档 {i}:\n"
                f"内容: {doc['content']}\n"
                f"来源: {doc['source']}\n"
            )
        
        return "\n".join(context_parts)
    
    def create_rag_prompt(self, query: str, k: int = 5) -> str:
        """
        创建包含RAG上下文的完整提示
        
        Args:
            query: 用户查询
            k: 搜索文档数量
            
        Returns:
            包含上下文的完整提示
        """
        # 搜索相关文档
        documents = self.search_documents(query, k)
        
        # 格式化上下文
        context = self.format_context_for_prompt(documents)
        
        # 创建完整提示
        rag_prompt = (
            f"基于以下文档内容回答问题。如果文档中没有相关信息，请说明无法基于提供的文档回答该问题。\n\n"
            f"相关文档:\n{context}\n\n"
            f"问题: {query}\n\n"
            f"请根据上述文档内容回答问题:"
        )
        
        return rag_prompt


# 创建默认实例
rag_integration = RAGIntegration()