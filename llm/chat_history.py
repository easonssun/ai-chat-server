import datetime
from typing import List
from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    messages_from_dict,
)


def _message_to_dict(message: BaseMessage) -> dict:
    """将消息转换为字典格式"""
    return {
        "type": message.type,
        "data": message.dict(),
        "additional_kwargs": message.additional_kwargs,
    }


class MongoDBChatMessageHistory(BaseChatMessageHistory):
    """
    MongoDB聊天消息历史存储实现
    将聊天消息持久化到MongoDB数据库中
    """

    def __init__(
        self,
        session_id: str,
        connection_string: str,
        database_name: str = "chat_history",
        collection_name: str = "messages",
        **kwargs,
    ):
        """
        初始化MongoDB聊天历史存储

        Args:
            session_id: 会话ID，用于区分不同对话
            connection_string: MongoDB连接字符串
            database_name: 数据库名称
            collection_name: 集合名称
            **kwargs: 其他MongoClient参数
        """
        self.session_id = session_id

        # 连接MongoDB
        self.client = MongoClient(connection_string, **kwargs)
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]

        # 创建索引以提高查询性能
        self._create_indexes()

        # 消息缓存
        self._messages: List[BaseMessage] = []
        self._load_messages()

    def _create_indexes(self):
        """创建必要的数据库索引"""
        self.collection.create_index(
            [("session_id", ASCENDING), ("timestamp", ASCENDING)]
        )
        self.collection.create_index(
            [("session_id", ASCENDING), ("message_index", ASCENDING)]
        )

    def _load_messages(self):
        """从数据库加载消息到内存"""
        try:
            docs = self.collection.find({"session_id": self.session_id}).sort(
                "message_index", ASCENDING
            )

            message_dicts = []
            for doc in docs:
                message_dict = {
                    "type": doc["type"],
                    "data": doc["data"],
                    "additional_kwargs": doc.get("additional_kwargs", {}),
                }
                message_dicts.append(message_dict)

            if message_dicts:
                self._messages = messages_from_dict(message_dicts)
            else:
                self._messages = []

        except Exception as e:
            print(f"加载消息失败: {e}")
            self._messages = []

    @property
    def messages(self) -> List[BaseMessage]:
        """获取所有消息"""
        return self._messages

    def add_message(self, message: BaseMessage) -> None:
        """添加消息到历史记录"""
        # 添加到内存
        self._messages.append(message)

        # 持久化到数据库
        try:
            message_dict = _message_to_dict(message)
            message_index = len(self._messages) - 1

            document = {
                "session_id": self.session_id,
                "message_index": message_index,
                "type": message_dict["type"],
                "data": message_dict["data"],
                "additional_kwargs": message_dict.get("additional_kwargs", {}),
                "timestamp": datetime.datetime.now(),
                "created_at": datetime.datetime.now(),
            }

            self.collection.insert_one(document)

        except Exception as e:
            # 如果数据库操作失败，从内存中移除消息
            self._messages.pop()
            raise Exception(f"保存消息到数据库失败: {e}")

    def add_user_message(self, content: str, **kwargs) -> None:
        """添加用户消息"""
        message = HumanMessage(content=content, **kwargs)
        self.add_message(message)

    def add_ai_message(self, content: str, **kwargs) -> None:
        """添加AI消息"""
        message = AIMessage(content=content, **kwargs)
        self.add_message(message)

    def add_system_message(self, content: str, **kwargs) -> None:
        """添加系统消息"""
        message = SystemMessage(content=content, **kwargs)
        self.add_message(message)

    def clear(self) -> None:
        """清空当前会话的所有消息"""
        try:
            # 从数据库删除
            self.collection.delete_many({"session_id": self.session_id})
            # 清空内存缓存
            self._messages = []
        except Exception as e:
            raise Exception(f"清空消息失败: {e}")

    def get_message_count(self) -> int:
        """获取消息数量"""
        return len(self._messages)

    def get_recent_messages(self, count: int = 10) -> List[BaseMessage]:
        """获取最近的消息"""
        return self._messages[-count:] if self._messages else []

    def __len__(self) -> int:
        return len(self._messages)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
