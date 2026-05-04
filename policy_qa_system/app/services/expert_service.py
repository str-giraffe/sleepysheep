# 专家解读服务
from app.models import (
    add_expert_interpretation, get_pending_interpretations, approve_interpretation, 
    reject_interpretation, get_approved_interpretations, get_interpretation_by_id, get_user_interpretations
)

class ExpertService:
    @staticmethod
    def create_interpretation(user_id, title, content):
        """创建专家解读"""
        return add_expert_interpretation(user_id, title, content)
    
    @staticmethod
    def get_pending_interpretations():
        """获取待审核的专家解读"""
        return get_pending_interpretations()
    
    @staticmethod
    def approve_interpretation(interpretation_id):
        """批准专家解读"""
        approve_interpretation(interpretation_id)
    
    @staticmethod
    def reject_interpretation(interpretation_id):
        """拒绝专家解读"""
        reject_interpretation(interpretation_id)
    
    @staticmethod
    def get_approved_interpretations(limit=10):
        """获取已批准的专家解读"""
        return get_approved_interpretations(limit)
    
    @staticmethod
    def get_interpretation_by_id(interpretation_id):
        """根据ID获取专家解读"""
        return get_interpretation_by_id(interpretation_id)
    
    @staticmethod
    def get_user_interpretations(user_id, limit=20):
        """获取用户的专家解读"""
        return get_user_interpretations(user_id, limit)
