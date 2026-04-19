# 用户历史和收藏服务
from app.models import (
    add_user_history, get_user_history, add_user_favorite, 
    remove_user_favorite, get_user_favorites, is_favorite
)

class UserHistoryService:
    @staticmethod
    def add_history(user_id, question, answer=None):
        """添加用户历史记录"""
        add_user_history(user_id, question, answer)
    
    @staticmethod
    def get_user_history(user_id, limit=20):
        """获取用户历史记录"""
        return get_user_history(user_id, limit)

class UserFavoriteService:
    @staticmethod
    def add_favorite(user_id, policy_id):
        """添加用户收藏"""
        return add_user_favorite(user_id, policy_id)
    
    @staticmethod
    def remove_favorite(user_id, policy_id):
        """移除用户收藏"""
        remove_user_favorite(user_id, policy_id)
    
    @staticmethod
    def get_user_favorites(user_id):
        """获取用户收藏"""
        return get_user_favorites(user_id)
    
    @staticmethod
    def is_favorite(user_id, policy_id):
        """检查是否已收藏"""
        return is_favorite(user_id, policy_id)
