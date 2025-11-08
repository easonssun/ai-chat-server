# LangChain 相关导入
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory

from llm.chat_history import MongoDBChatMessageHistory

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

system_prompt = """
你是一个专业的水利行业智能客服助手，由水利部门或相关机构部署，旨在为公众、工作人员或相关单位提供准确、权威、及时的水利信息咨询服务。

你的职责包括但不限于：
- 解答关于水资源管理、防汛抗旱、水利工程、水文监测、河湖治理、用水政策等方面的问题；
- 提供与国家及地方最新水利法规、技术标准、应急预案相关的解释；
- 在面对不确定或超出知识范围的问题时，明确说明“该问题超出我的知识范围”或“建议咨询当地水利主管部门”，切勿编造答案；
- 对涉及生命安全（如洪水预警、堤防险情等）的问题，务必强调“请立即联系当地应急管理部门或拨打110/119求助”；
- 回答需简洁清晰、语言通俗，避免过度使用专业术语；若必须使用，请附带简要解释；
- 严格遵守中国法律法规，不讨论政治、宗教、色情、暴力等相关话题；
- 所有回答必须基于可靠、公开、官方的信息源，不得传播未经证实的消息。

请始终以服务公众安全和水利公共利益为首要原则。
"""

# 创建提示模板
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ]
)

# 创建处理链
chain = prompt | model


# 创建内存存储（实际项目中应替换为 Redis/DB）
# 替换原来的 store = {}
def get_chat_history(session_id: str):
    chat_message_history = MongoDBChatMessageHistory(
        session_id=session_id,
        connection_string=os.getenv(
            "MONGODB_URI", "mongodb://localhost:27017/"
        ),  # 替换为你的连接字符串
        database_name=os.getenv("MONGODB_DB_NAME", "ai_chat_db"),  # 替换为你的数据库名
        collection_name="chat_histories",  # 替换为你的集合名
    )
    return chat_message_history


# 包装 chain 以支持消息历史
chain_with_history = RunnableWithMessageHistory(
    runnable=chain,
    get_session_history=get_chat_history,
    input_messages_key="question",
    history_messages_key="history",
)

# 固定会话ID（在实际应用中可能需要动态生成）
SESSION_ID = "123"
