# 安全相关功能
import bcrypt
import os
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('security')

# 密码哈希函数
def hash_password(password):
    """使用 bcrypt 进行密码哈希"""
    salt = bcrypt.gensalt(12)  # 12 轮哈希
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

# 密码验证函数
def verify_password(plain_password, hashed_password):
    """验证密码（支持旧的SHA-256和新的bcrypt格式）"""
    import hashlib
    
    # 检查是否是bcrypt格式（以$2b$开头）
    if hashed_password.startswith('$2b$'):
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except ValueError:
            # 如果bcrypt验证失败，尝试SHA-256
            pass
    
    # 尝试旧的SHA-256验证
    old_hash = hashlib.sha256(plain_password.encode()).hexdigest()
    return old_hash == hashed_password

# 输入验证函数
def validate_input(input_data, input_type):
    """验证输入数据"""
    if input_type == 'username':
        # 用户名验证：只允许字母、数字、下划线，长度 3-20
        if not isinstance(input_data, str):
            return False
        if len(input_data) < 3 or len(input_data) > 20:
            return False
        if not input_data.replace('_', '').isalnum():
            return False
        return True
    elif input_type == 'password':
        # 密码验证：至少 6 位
        if not isinstance(input_data, str):
            return False
        if len(input_data) < 6:
            return False
        return True
    elif input_type == 'email':
        # 简单的邮箱验证
        if not isinstance(input_data, str):
            return False
        if '@' not in input_data or '.' not in input_data:
            return False
        return True
    elif input_type == 'title':
        # 标题验证：长度 1-100
        if not isinstance(input_data, str):
            return False
        if len(input_data) < 1 or len(input_data) > 100:
            return False
        return True
    elif input_type == 'content':
        # 内容验证：长度 1-10000
        if not isinstance(input_data, str):
            return False
        if len(input_data) < 1 or len(input_data) > 10000:
            return False
        return True
    return False

# 审计日志函数
def log_audit(action, user_id, details=None):
    """记录审计日志"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'user_id': user_id,
        'details': details
    }
    logger.info(f"AUDIT: {log_entry}")

# 生成随机令牌
def generate_token(length=32):
    """生成随机令牌"""
    return os.urandom(length).hex()

# 检查权限
def check_permission(user_role, required_role):
    """检查用户权限"""
    role_hierarchy = {
        'user': 1,
        'expert': 2,
        'admin': 3
    }
    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role, 3)
    return user_level >= required_level
