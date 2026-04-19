# 政策服务
from app.models import (
    add_policy, get_all_policies, get_policy_by_id, delete_policy, 
    add_category, get_all_categories, add_tag, get_all_tags, add_policy_tag, get_policy_tags
)

class PolicyService:
    @staticmethod
    def create_policy(title, content, source=None, publish_date=None, category_id=None):
        """创建政策"""
        return add_policy(title, content, source, publish_date, category_id)
    
    @staticmethod
    def get_all_policies():
        """获取所有政策"""
        return get_all_policies()
    
    @staticmethod
    def get_policy_by_id(policy_id):
        """根据ID获取政策"""
        return get_policy_by_id(policy_id)
    
    @staticmethod
    def delete_policy(policy_id):
        """删除政策"""
        delete_policy(policy_id)
    
    @staticmethod
    def get_all_categories():
        """获取所有分类"""
        return get_all_categories()
    
    @staticmethod
    def create_category(name, description=None):
        """创建分类"""
        return add_category(name, description)
    
    @staticmethod
    def get_all_tags():
        """获取所有标签"""
        return get_all_tags()
    
    @staticmethod
    def create_tag(name):
        """创建标签"""
        return add_tag(name)
    
    @staticmethod
    def add_policy_tag(policy_id, tag_id):
        """添加政策标签关联"""
        return add_policy_tag(policy_id, tag_id)
    
    @staticmethod
    def get_policy_tags(policy_id):
        """获取政策的标签"""
        return get_policy_tags(policy_id)
