# AI Chat Server

一个基于FastAPI和DeepSeek AI的智能聊天服务器，支持流式响应和对话历史管理。

## 功能特性

- 🚀 **FastAPI框架** - 高性能异步Web框架
- 💬 **智能对话** - 基于DeepSeek AI模型
- 📱 **流式响应** - 支持实时流式传输
- 🔄 **对话历史** - 内存中维护对话上下文
- 🌐 **CORS支持** - 跨域资源共享配置
- 🛠️ **专业领域** - 水利水电工程专业问答

## 技术栈

- **后端框架**: FastAPI
- **AI模型**: DeepSeek Chat
- **异步处理**: asyncio
- **对话管理**: LangChain
- **环境管理**: Python虚拟环境

## 项目结构

ai-chat-server/ ├── main.py # 主应用文件 ├── llm/ │ └── model.py # AI模型配置 ├── requirements.txt # 依赖包列表 ├── Makefile # 构建脚本 ├── .env.example # 环境变量示例 └── .gitignore # Git忽略文件


plainText

## 快速开始

### 环境要求

- Python 3.13+
- DeepSeek API密钥

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd ai-chat-server
```

2. **创建虚拟环境**
```bash
python -m venv ai-chat-server
source ai-chat-server/bin/activate  # Linux/Mac
# 或 ai-chat-server\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
make install
```

4. **配置环境变量**
复制`.env.example`为`.env`并配置你的API密钥：
```bash
cp .env.example .env
```
编辑`.env`文件：
```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_API_BASE=https://api.deepseek.com
```

5. **启动服务器**
```bash
make run
```

服务器将在 `http://localhost:8001` 启动。

## API文档

启动服务器后，访问以下地址查看API文档：
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

### 聊天接口

**POST** `/api/chat`

请求体：
```json
{
  "input": "你的问题"
}
```

响应：流式EventStream格式

## Makefile命令

```bash
make run        # 运行开发服务器（带热重载）
make install    # 安装依赖包
make freeze     # 生成requirements.txt
make format     # 格式化代码（使用black）
make clean      # 清理缓存文件
make check      # 代码风格检查（使用flake8）
make help       # 显示帮助信息
```

## 开发说明

### 模型配置

AI模型配置位于 `llm/model.py`，当前配置为：
- 模型：DeepSeek Chat
- 温度：0.3（控制回答的创造性）
- 流式：启用
- 专业领域：水利水电工程

### 自定义配置

要修改AI的专业领域，编辑 `llm/model.py` 中的系统提示：

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "你的自定义系统提示"),
    # ... 其他配置
])
```

## 部署

### 生产环境部署

使用uvicorn运行生产服务器：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Docker部署（可选）

创建Dockerfile：
```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```
