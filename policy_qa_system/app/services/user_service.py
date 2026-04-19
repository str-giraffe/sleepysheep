# 用户服务
from app.models import (
    add_user, get_user_by_username, get_user_by_id, update_user_nickname, 
    get_unique_nickname, ban_user, unban_user, get_all_users, update_user_role,
    submit_expert_application, get_expert_applications, approve_expert, reject_expert, get_expert_status
)
from app.security import verify_password

class UserService:
    @staticmethod
    def create_user(username, password, role='user', region=None):
        """创建用户"""
        return add_user(username, password, role, region)
    
    @staticmethod
    def get_user_by_username(username):
        """根据用户名获取用户"""
        return get_user_by_username(username)
    
    @staticmethod
    def get_user_by_id(user_id):
        """根据ID获取用户"""
        return get_user_by_id(user_id)
    
    @staticmethod
    def verify_password(plain_password, hashed_password):
        """验证密码"""
        return verify_password(plain_password, hashed_password)
    
    @staticmethod
    def update_nickname(user_id, nickname):
        """更新用户昵称"""
        update_user_nickname(user_id, nickname)
    
    @staticmethod
    def get_unique_nickname():
        """生成唯一昵称"""
        return get_unique_nickname()
    
    @staticmethod
    def ban_user(user_id, ban_until=None, is_permanent=False):
        """封禁用户"""
        ban_user(user_id, ban_until, is_permanent)
    
    @staticmethod
    def unban_user(user_id):
        """解除用户封禁"""
        unban_user(user_id)
    
    @staticmethod
    def get_all_users():
        """获取所有用户"""
        return get_all_users()
    
    @staticmethod
    def update_user_role(user_id, role):
        """更新用户角色"""
        update_user_role(user_id, role)
    
    @staticmethod
    def submit_expert_application(user_id, application):
        """提交专家申请"""
        submit_expert_application(user_id, application)
    
    @staticmethod
    def get_expert_applications():
        """获取专家申请列表"""
        return get_expert_applications()
    
    @staticmethod
    def approve_expert(user_id):
        """批准专家申请"""
        approve_expert(user_id)
    
    @staticmethod
    def reject_expert(user_id):
        """拒绝专家申请"""
        reject_expert(user_id)
    
    @staticmethod
    def get_expert_status(user_id):
        """获取用户专家状态"""
        return get_expert_status(user_id)
