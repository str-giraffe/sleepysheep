# 配置文件
import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 数据库配置
DATABASE_PATH = os.path.join(BASE_DIR, 'policy.db')

# 安全配置
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# API配置
API_PREFIX = '/api'

# 缓存配置
CACHE_EXPIRATION = 3600  # 缓存过期时间（秒）

# 上传配置
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# 应用配置
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', 5000))

# 日志配置
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# 初始化上传目录
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
