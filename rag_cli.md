# RAG CLI 工具使用说明

这个命令行工具允许您轻松地将文档添加到RAG系统并进行搜索。

## 安装和设置

确保您已经安装了所有必要的依赖项：
```bash
pip install -r requirements.txt
```

确保Milvus服务正在运行。您可以使用docker-compose启动它：
```bash
docker-compose up -d
```

## 使用方法

### 处理单个文件

```bash
python rag_cli.py --file /path/to/document.pdf --collection my_collection
```

### 处理整个目录

```bash
python rag_cli.py --directory /path/to/documents --collection my_collection
```

### 指定文件类型

```bash
python rag_cli.py --directory /path/to/documents --extensions .pdf .txt --collection my_collection
```

### 参数说明

- `--file` 或 `-f`: 指定要处理的单个文件路径
- `--directory` 或 `-d`: 指定要处理的目录路径
- `--extensions` 或 `-e`: 指定要处理的文件扩展名列表（默认：.pdf .txt .csv .docx）
- `--collection` 或 `-c`: 指定Milvus集合名称（默认：documents）

## 支持的文件格式

- PDF (.pdf)
- 文本文件 (.txt)
- CSV文件 (.csv)
- Word文档 (.docx)
- 其他文件格式（使用通用加载器）

## 示例

```bash
# 处理单个PDF文件
python rag_cli.py --file ./documents/sample.pdf --collection water_resources

# 处理目录中的所有支持格式的文件
python rag_cli.py --directory ./documents --collection water_resources

# 只处理TXT和CSV文件
python rag_cli.py --directory ./documents --extensions .txt .csv --collection water_resources