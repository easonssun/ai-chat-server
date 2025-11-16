from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import (
    DirectoryLoader,
    PyPDFLoader,
    TextLoader,
    CSVLoader,
    Docx2txtLoader,
    UnstructuredFileLoader,
)
from langchain_community.vectorstores import Milvus
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os


class RAGSystem:
    def __init__(self, milvus_url: str = "http://localhost:19530"):
        """初始化RAG系统"""
        # 初始化嵌入模型
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2"
        )

        self.milvus_url = milvus_url
        self.connection_args = {"uri": milvus_url}

        # 文件扩展名到加载器的映射
        self.loader_mapping = {
            ".pdf": PyPDFLoader,
            ".txt": TextLoader,
            ".csv": CSVLoader,
            ".docx": Docx2txtLoader,
        }

    def _get_vector_store(self, collection_name: str = "documents"):
        """获取指定 collection 的 vector store"""
        return Milvus(
            embedding_function=self.embeddings,
            connection_args=self.connection_args,
            collection_name=collection_name,
            index_params={"index_type": "FLAT", "metric_type": "L2"},
            drop_old=False,  # 重要：不要删除现有的 collection
        )

    def _get_loader_class(self, file_extension):
        """根据文件扩展名获取对应的加载器类"""
        return self.loader_mapping.get(file_extension.lower(), UnstructuredFileLoader)

    def add_file(self, file_path: str, collection_name: str = "documents"):
        """添加单个文件到 Milvus"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 获取文件扩展名
        _, ext = os.path.splitext(file_path)

        # 根据文件扩展名选择加载器
        loader_class = self._get_loader_class(ext)

        # 加载文档
        try:
            if loader_class == PyPDFLoader:
                loader = loader_class(file_path)
            elif loader_class == TextLoader:
                loader = loader_class(file_path, encoding="utf-8")
            elif loader_class == CSVLoader:
                loader = loader_class(file_path)
            elif loader_class == Docx2txtLoader:
                loader = loader_class(file_path)
            else:
                # UnstructuredFileLoader
                loader = loader_class(file_path)

            documents = loader.load()
            
            # 添加元数据
            for doc in documents:
                doc.metadata["source"] = file_path

            vector_store = self._get_vector_store(collection_name)
            vector_store.add_documents(documents)
            print(f"成功添加文件: {file_path} 到集合: {collection_name}")
            
        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {str(e)}")
            raise

    def process_directory(
        self,
        directory_path: str,
        file_extensions: list = None,
        collection_name: str = "documents",
    ):
        """处理整个目录的文档"""
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"目录不存在: {directory_path}")
            
        if not os.path.isdir(directory_path):
            raise ValueError(f"路径不是目录: {directory_path}")
        
        if file_extensions is None:
            file_extensions = [".pdf", ".txt", ".csv", ".docx"]

        all_documents = []

        for ext in file_extensions:
            pattern = f"**/*{ext}"
            loader_class = self._get_loader_class(ext)

            try:
                # 加载文档
                if loader_class == PyPDFLoader:
                    loader = DirectoryLoader(
                        directory_path, glob=pattern, loader_cls=loader_class
                    )
                elif loader_class == TextLoader:
                    loader = DirectoryLoader(
                        directory_path,
                        glob=pattern,
                        loader_cls=loader_class,
                        loader_kwargs={"encoding": "utf-8"},
                    )
                elif loader_class == CSVLoader:
                    loader = DirectoryLoader(
                        directory_path, glob=pattern, loader_cls=loader_class
                    )
                elif loader_class == Docx2txtLoader:
                    loader = DirectoryLoader(
                        directory_path, glob=pattern, loader_cls=loader_class
                    )
                else:
                    # UnstructuredFileLoader
                    loader = DirectoryLoader(
                        directory_path, glob=pattern, loader_cls=loader_class
                    )

                documents = loader.load()
                all_documents.extend(documents)
                print(f"从模式 {pattern} 加载了 {len(documents)} 个文档")
            except Exception as e:
                print(f"处理模式 {pattern} 时出错: {str(e)}")
                continue

        if not all_documents:
            print("未找到任何匹配的文档")
            return

        # 分割文本
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # chunk size (characters)
            chunk_overlap=200,  # chunk overlap (characters)
            add_start_index=True,  # track index in original document
        )
        docs = text_splitter.split_documents(all_documents)

        # 存储到 Milvus
        vector_store = self._get_vector_store(collection_name)
        vector_store.add_documents(docs)

        print(f"成功处理 {len(docs)} 个文档块到集合: {collection_name}")

    def search(self, query: str, collection_name: str = "documents", k: int = 5):
        """搜索文档"""
        try:
            vector_store = self._get_vector_store(collection_name)
            results = vector_store.similarity_search(query, k=k)
            return results
        except Exception as e:
            print(f"搜索时出错: {str(e)}")
            return []

    def list_collections(self):
        """列出所有 collections"""
        try:
            from pymilvus import connections, utility

            # 连接到Milvus
            connections.connect(alias="default", uri=self.milvus_url)
            collections = utility.list_collections()
            connections.disconnect(alias="default")
            return collections
        except Exception as e:
            print(f"列出collections时出错: {str(e)}")
            return []

    def delete_collection(self, collection_name: str):
        """删除指定的 collection"""
        try:
            from pymilvus import connections, utility

            # 连接到Milvus
            connections.connect(alias="default", uri=self.milvus_url)
            if utility.has_collection(collection_name):
                utility.drop_collection(collection_name)
                print(f"已删除 collection: {collection_name}")
            else:
                print(f"Collection {collection_name} 不存在")
            connections.disconnect(alias="default")
        except Exception as e:
            print(f"删除collection时出错: {str(e)}")


# 创建默认实例
RAG = RAGSystem()