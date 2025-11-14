from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_community.vectorstores import Milvus
from langchain_text_splitters import RecursiveCharacterTextSplitter


class RAGSystem:
    def __init__(self, milvus_url: str = "http://localhost:19530"):

        # 初始化嵌入模型
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2"
        )

        # 连接参数
        self.vector_store = Milvus(
            embedding_function=self.embeddings,
            connection_args={"uri": milvus_url},
            index_params={"index_type": "FLAT", "metric_type": "L2"},
        )

    def process_directory(
        self, directory_path: str, collection_name: str = "documents"
    ):
        """处理整个目录的文档"""
        # 加载所有文档
        loader = DirectoryLoader(
            directory_path, glob="**/*.pdf", loader_cls=PyPDFLoader
        )
        documents = loader.load()

        # 分割文本
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # chunk size (characters)
            chunk_overlap=200,  # chunk overlap (characters)
            add_start_index=True,  # track index in original document
        )
        docs = text_splitter.split_documents(documents)

        # 存储到 Milvus
        vector_store = Milvus.from_documents(
            docs,
            self.embeddings,
            collection_name=collection_name,
            connection_args=self.connection_args,
        )

        print(f"成功处理 {len(docs)} 个文档块")
        return vector_store

    def search(self, query: str, collection_name: str = "documents", k: int = 5):
        """搜索文档"""
        vector_store = Milvus(
            self.embeddings,
            collection_name=collection_name,
            connection_args=self.connection_args,
        )

        results = vector_store.similarity_search(query, k=k)
        return results


# 使用示例
def advanced_example():
    rag = RAGSystem()

    # 处理文档目录
    vector_store = rag.process_directory("./documents")

    # 搜索
    results = rag.search("机器学习的基本概念", k=3)

    for i, doc in enumerate(results):
        print(f"\n结果 {i+1}:")
        print(f"内容: {doc.page_content[:300]}...")
        print(f"来源: {doc.metadata.get('source', 'Unknown')}")
