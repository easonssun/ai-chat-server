import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from bson.objectid import ObjectId
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MongoDBManager:
    """MongoDB数据库管理类"""

    def __init__(self, connection_string: str = None, db_name: str = "ai_chat_db"):
        """
        初始化MongoDB连接

        Args:
            connection_string: MongoDB连接字符串，如果为None则从环境变量读取
            db_name: 数据库名称
        """
        self.connection_string = connection_string or os.getenv(
            "MONGODB_URI", "mongodb://localhost:27017/"
        )
        self.db_name = db_name
        self.client = None
        self.db = None
        self._connect()

    def _connect(self):
        """连接到MongoDB数据库"""
        try:
            self.client = MongoClient(self.connection_string)
            # 测试连接
            self.client.admin.command("ping")
            self.db = self.client[self.db_name]
            logger.info(f"成功连接到MongoDB数据库: {self.db_name}")

            # 初始化集合和索引
            self._initialize_collections()

        except ConnectionFailure as e:
            logger.error(f"无法连接到MongoDB: {e}")
            raise

    def _initialize_collections(self):
        """初始化数据库集合和索引"""
        # 用户集合
        if "users" not in self.db.list_collection_names():
            self.db.create_collection("users")

        # 为用户集合创建索引
        self.db.users.create_index("username", unique=True)
        self.db.users.create_index("email", unique=True)

        # 聊天记录集合
        if "chat_history" not in self.db.list_collection_names():
            self.db.create_collection("chat_history")

        # 为聊天记录创建索引
        self.db.chat_history.create_index("user_id")
        self.db.chat_history.create_index([("user_id", 1), ("timestamp", -1)])

        # 会话集合
        if "sessions" not in self.db.list_collection_names():
            self.db.create_collection("sessions")

        self.db.sessions.create_index("session_id", unique=True)
        self.db.sessions.create_index([("user_id", 1), ("created_at", -1)])

        logger.info("数据库集合和索引初始化完成")

    def is_connected(self) -> bool:
        """检查数据库连接状态"""
        try:
            self.client.admin.command("ping")
            return True
        except:
            return False

    def close_connection(self):
        """关闭数据库连接"""
        if self.client:
            self.client.close()
            logger.info("MongoDB连接已关闭")

    # ========== 用户管理操作 ==========

    def create_user(self, user_data: Dict[str, Any]) -> Optional[str]:
        """
        创建新用户

        Args:
            user_data: 用户数据字典

        Returns:
            创建的用户ID，如果失败返回None
        """
        try:
            # 添加时间戳
            user_data["created_at"] = datetime.utcnow()
            user_data["updated_at"] = datetime.utcnow()

            result = self.db.users.insert_one(user_data)
            logger.info(f"用户创建成功: {result.inserted_id}")
            return str(result.inserted_id)

        except DuplicateKeyError as e:
            logger.error(f"用户创建失败，用户名或邮箱已存在: {e}")
            return None
        except Exception as e:
            logger.error(f"用户创建失败: {e}")
            return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取用户信息

        Args:
            user_id: 用户ID

        Returns:
            用户信息字典，如果不存在返回None
        """
        try:
            user = self.db.users.find_one({"_id": ObjectId(user_id)})
            if user:
                user["_id"] = str(user["_id"])  # 转换ObjectId为字符串
            return user
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        根据用户名获取用户信息

        Args:
            username: 用户名

        Returns:
            用户信息字典，如果不存在返回None
        """
        try:
            user = self.db.users.find_one({"username": username})
            if user:
                user["_id"] = str(user["_id"])
            return user
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return None

    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """
        更新用户信息

        Args:
            user_id: 用户ID
            update_data: 要更新的数据

        Returns:
            更新是否成功
        """
        try:
            update_data["updated_at"] = datetime.utcnow()
            result = self.db.users.update_one(
                {"_id": ObjectId(user_id)}, {"$set": update_data}
            )
            success = result.modified_count > 0
            if success:
                logger.info(f"用户信息更新成功: {user_id}")
            else:
                logger.warning(f"用户信息未更新: {user_id}")
            return success
        except Exception as e:
            logger.error(f"更新用户信息失败: {e}")
            return False

    def delete_user(self, user_id: str) -> bool:
        """
        删除用户

        Args:
            user_id: 用户ID

        Returns:
            删除是否成功
        """
        try:
            result = self.db.users.delete_one({"_id": ObjectId(user_id)})
            success = result.deleted_count > 0
            if success:
                logger.info(f"用户删除成功: {user_id}")
                # 同时删除该用户的聊天记录和会话
                self.db.chat_history.delete_many({"user_id": user_id})
                self.db.sessions.delete_many({"user_id": user_id})
            else:
                logger.warning(f"用户不存在: {user_id}")
            return success
        except Exception as e:
            logger.error(f"删除用户失败: {e}")
            return False

    # ========== 聊天记录操作 ==========

    def add_chat_message(self, chat_data: Dict[str, Any]) -> Optional[str]:
        """
        添加聊天记录

        Args:
            chat_data: 聊天数据

        Returns:
            聊天记录ID，如果失败返回None
        """
        try:
            chat_data["timestamp"] = datetime.utcnow()
            result = self.db.chat_history.insert_one(chat_data)
            logger.info(f"聊天记录添加成功: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"添加聊天记录失败: {e}")
            return None

    def get_chat_history(
        self, user_id: str, limit: int = 50, skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取用户的聊天历史记录

        Args:
            user_id: 用户ID
            limit: 返回记录数量限制
            skip: 跳过记录数量

        Returns:
            聊天记录列表
        """
        try:
            cursor = (
                self.db.chat_history.find({"user_id": user_id})
                .sort("timestamp", -1)
                .skip(skip)
                .limit(limit)
            )

            messages = []
            for msg in cursor:
                msg["_id"] = str(msg["_id"])
                messages.append(msg)

            return messages
        except Exception as e:
            logger.error(f"获取聊天记录失败: {e}")
            return []

    def get_recent_chats(self, user_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """
        获取用户最近指定小时内的聊天记录

        Args:
            user_id: 用户ID
            hours: 小时数

        Returns:
            聊天记录列表
        """
        try:
            time_threshold = datetime.utcnow() - timedelta(hours=hours)
            cursor = self.db.chat_history.find(
                {"user_id": user_id, "timestamp": {"$gte": time_threshold}}
            ).sort("timestamp", -1)

            messages = []
            for msg in cursor:
                msg["_id"] = str(msg["_id"])
                messages.append(msg)

            return messages
        except Exception as e:
            logger.error(f"获取最近聊天记录失败: {e}")
            return []

    def delete_chat_message(self, message_id: str) -> bool:
        """
        删除单条聊天记录

        Args:
            message_id: 聊天记录ID

        Returns:
            删除是否成功
        """
        try:
            result = self.db.chat_history.delete_one({"_id": ObjectId(message_id)})
            success = result.deleted_count > 0
            if success:
                logger.info(f"聊天记录删除成功: {message_id}")
            else:
                logger.warning(f"聊天记录不存在: {message_id}")
            return success
        except Exception as e:
            logger.error(f"删除聊天记录失败: {e}")
            return False

    def clear_user_chat_history(self, user_id: str) -> bool:
        """
        清空用户的聊天记录

        Args:
            user_id: 用户ID

        Returns:
            清空是否成功
        """
        try:
            result = self.db.chat_history.delete_many({"user_id": user_id})
            logger.info(
                f"清空用户聊天记录成功: {user_id}, 删除记录数: {result.deleted_count}"
            )
            return True
        except Exception as e:
            logger.error(f"清空聊天记录失败: {e}")
            return False

    # ========== 会话管理操作 ==========

    def create_session(self, session_data: Dict[str, Any]) -> Optional[str]:
        """
        创建新会话

        Args:
            session_data: 会话数据

        Returns:
            会话ID，如果失败返回None
        """
        try:
            session_data["created_at"] = datetime.utcnow()
            session_data["updated_at"] = datetime.utcnow()

            result = self.db.sessions.insert_one(session_data)
            logger.info(f"会话创建成功: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            return None

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话信息

        Args:
            session_id: 会话ID

        Returns:
            会话信息字典，如果不存在返回None
        """
        try:
            session = self.db.sessions.find_one({"session_id": session_id})
            if session:
                session["_id"] = str(session["_id"])
            return session
        except Exception as e:
            logger.error(f"获取会话信息失败: {e}")
            return None

    def update_session(self, session_id: str, update_data: Dict[str, Any]) -> bool:
        """
        更新会话信息

        Args:
            session_id: 会话ID
            update_data: 要更新的数据

        Returns:
            更新是否成功
        """
        try:
            update_data["updated_at"] = datetime.utcnow()
            result = self.db.sessions.update_one(
                {"session_id": session_id}, {"$set": update_data}
            )
            success = result.modified_count > 0
            if success:
                logger.info(f"会话信息更新成功: {session_id}")
            else:
                logger.warning(f"会话信息未更新: {session_id}")
            return success
        except Exception as e:
            logger.error(f"更新会话信息失败: {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        """
        删除会话

        Args:
            session_id: 会话ID

        Returns:
            删除是否成功
        """
        try:
            result = self.db.sessions.delete_one({"session_id": session_id})
            success = result.deleted_count > 0
            if success:
                logger.info(f"会话删除成功: {session_id}")
            else:
                logger.warning(f"会话不存在: {session_id}")
            return success
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            return False

    # ========== 统计和工具方法 ==========

    def get_user_count(self) -> int:
        """获取用户总数"""
        try:
            return self.db.users.count_documents({})
        except Exception as e:
            logger.error(f"获取用户总数失败: {e}")
            return 0

    def get_chat_message_count(self, user_id: str = None) -> int:
        """
        获取聊天记录总数

        Args:
            user_id: 用户ID，如果为None则获取所有记录

        Returns:
            聊天记录总数
        """
        try:
            query = {"user_id": user_id} if user_id else {}
            return self.db.chat_history.count_documents(query)
        except Exception as e:
            logger.error(f"获取聊天记录总数失败: {e}")
            return 0

    def get_active_sessions_count(self) -> int:
        """获取活跃会话数量"""
        try:
            # 假设活跃会话是最近24小时内更新的会话
            time_threshold = datetime.utcnow() - timedelta(hours=24)
            return self.db.sessions.count_documents(
                {"updated_at": {"$gte": time_threshold}}
            )
        except Exception as e:
            logger.error(f"获取活跃会话数量失败: {e}")
            return 0


# 创建全局数据库实例
db_manager = MongoDBManager()

# 使用示例
if __name__ == "__main__":
    # 测试数据库连接和基本操作
    try:
        # 测试连接
        print(f"数据库连接状态: {db_manager.is_connected()}")

        # 创建测试用户
        test_user = {
            "username": "test_user",
            "email": "test@example.com",
            "name": "测试用户",
        }
        user_id = db_manager.create_user(test_user)
        print(f"创建用户ID: {user_id}")

        # 获取用户信息
        user = db_manager.get_user_by_id(user_id)
        print(f"用户信息: {user}")

        # 添加聊天记录
        chat_message = {
            "user_id": user_id,
            "message": "你好，这是一个测试消息",
            "role": "user",  # user 或 assistant
            "session_id": "test_session",
        }
        message_id = db_manager.add_chat_message(chat_message)
        print(f"聊天记录ID: {message_id}")

        # 获取聊天历史
        history = db_manager.get_chat_history(user_id)
        print(f"聊天历史记录数: {len(history)}")

        # 关闭连接
        db_manager.close_connection()

    except Exception as e:
        print(f"测试过程中出现错误: {e}")
