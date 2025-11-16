from rag_system import RAGSystem

# 使用示例
def advanced_example():
    rag = RAGSystem()

    # 处理文档目录
    # rag.add_file("./documents/test.txt")

    # 搜索
    results = rag.search("水利对象是什么", k=3)

    for i, doc in enumerate(results):
        print(f"\n结果 {i+1}:")
        print(f"内容: {doc.page_content[:300]}...")
        print(f"来源: {doc.metadata.get('source', 'Unknown')}")


if __name__ == "__main__":
    advanced_example()
