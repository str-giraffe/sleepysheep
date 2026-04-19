# 数据库连接管理
import sqlite3
import os
import logging
from datetime import datetime
from app.config import DATABASE_PATH

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('database')

class DatabaseManager:
    """数据库连接管理器"""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """建立数据库连接"""
        try:
            # 确保数据库文件所在目录存在
            os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
            
            # 建立连接
            self.conn = sqlite3.connect(
                DATABASE_PATH,
                check_same_thread=False,
                timeout=30
            )
            
            # 设置PRAGMA选项
            self.cursor = self.conn.cursor()
            self._set_pragmas()
            
            logger.info("Database connection established")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            return False
    
    def _set_pragmas(self):
        """设置数据库PRAGMA选项"""
        try:
            # 启用外键约束
            self.cursor.execute('PRAGMA foreign_keys = ON')
            # 设置同步模式为NORMAL，平衡性能和安全性
            self.cursor.execute('PRAGMA synchronous = NORMAL')
            # 启用自动Vacuum
            self.cursor.execute('PRAGMA auto_vacuum = INCREMENTAL')
            # 设置缓存大小
            self.cursor.execute('PRAGMA cache_size = -10000')  # 10MB缓存
        except Exception as e:
            logger.error(f"Error setting pragmas: {str(e)}")
    
    def execute(self, query, params=None):
        """执行SQL查询"""
        if not self.conn or not self.cursor:
            if not self.connect():
                return None
        
        try:
            if params:
                result = self.cursor.execute(query, params)
            else:
                result = self.cursor.execute(query)
            return result
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            logger.error(f"Query: {query}")
            if params:
                logger.error(f"Params: {params}")
            return None
    
    def commit(self):
        """提交事务"""
        try:
            if self.conn:
                self.conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error committing transaction: {str(e)}")
        return False
    
    def rollback(self):
        """回滚事务"""
        try:
            if self.conn:
                self.conn.rollback()
                return True
        except Exception as e:
            logger.error(f"Error rolling back transaction: {str(e)}")
        return False
    
    def close(self):
        """关闭数据库连接"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}")
    
    def backup(self, backup_path=None):
        """备份数据库"""
        try:
            if not backup_path:
                # 生成备份文件名
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_dir = os.path.join(os.path.dirname(DATABASE_PATH), 'backups')
                os.makedirs(backup_dir, exist_ok=True)
                backup_path = os.path.join(backup_dir, f'policy_backup_{timestamp}.db')
            
            # 执行备份
            with sqlite3.connect(backup_path) as backup_conn:
                self.conn.backup(backup_conn)
            
            logger.info(f"Database backup created: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Error backing up database: {str(e)}")
            return None

# 创建全局数据库管理器实例
db_manager = DatabaseManager()

# 数据库初始化函数
def init_database():
    """初始化数据库"""
    if not db_manager.connect():
        logger.error("Failed to initialize database")
        return False
    
    try:
        # 这里可以放置数据库初始化代码
        # 例如创建表结构等
        logger.info("Database initialized successfully")
        return True
    finally:
        db_manager.close()
