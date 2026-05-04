# 初始化文件
from flask import Flask
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import BASE_DIR, SECRET_KEY

# 创建Flask应用实例
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'), static_folder=os.path.join(BASE_DIR, 'css'), static_url_path='/css')
app.secret_key = SECRET_KEY  # 用于 session 管理

# 导入路由和API
from app import routes
from app import api_doc