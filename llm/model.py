# LangChain 相关导入
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory

# 环境变量处理
import os
from dotenv import load_dotenv

load_dotenv()

print(os.getenv("MODEL_API_KEY"))
# 初始化模型
model = ChatOpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_API_BASE"),
    model_name="deepseek-chat",
    streaming=True,
    temperature=0.3,
)

# 创建提示模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个专业的水利水电工程师，回答必须准确、简洁、使用中文。"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])

# 创建处理链
chain = prompt | model

# 创建内存存储（实际项目中应替换为 Redis/DB）
store = {}

def get_chat_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# 包装 chain 以支持消息历史
chain_with_history = RunnableWithMessageHistory(
    runnable=chain,
    get_session_history=get_chat_history,
    input_messages_key="question",
    history_messages_key="history",
)

# 固定会话ID（在实际应用中可能需要动态生成）
SESSION_ID = "123"
