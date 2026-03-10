# setup_simple_project.py
import sqlite3
import bcrypt
import os
import secrets

def setup_simple_project():
    """一键设置项目（使用 SQLite）"""
    
    print("=" * 60)
    print("快速项目设置工具（使用 SQLite）")
    print("=" * 60)
    
    # 1. 创建必要目录
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # 2. 创建 .env 文件
    env_content = f"""# 数据库配置 (使用 SQLite)
DB_TYPE=sqlite
DB_FILE=policy_rag.db

# Flask 密钥
SECRET_KEY={secrets.token_hex(32)}

# 阿里云 API
APIKEY=sk-your-aliyun-api-key-here

# 应用配置
DEBUG=True
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    print("✓ 创建 .env 配置文件")
    
    # 3. 创建 SQLite 数据库
    conn = sqlite3.connect('policy_rag.db')
    cursor = conn.cursor()
    
    # 创建表
    tables = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS policies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            policy_title TEXT NOT NULL,
            policy_content TEXT NOT NULL,
            category TEXT,
            source TEXT,
            publish_date DATE,
            vector_embedding TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS user_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            question TEXT NOT NULL,
            answer TEXT,
            status TEXT DEFAULT 'answered',
            similar_docs TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            resource TEXT,
            details TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    ]
    
    for sql in tables:
        cursor.execute(sql)
    
    # 添加默认用户
    users = [
        ('admin', 'admin123', 'admin@example.com', 'admin'),
        ('user1', 'user123', 'user1@example.com', 'user'),
        ('user2', 'user123', 'user2@example.com', 'user')
    ]
    
    for username, password, email, role in users:
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute(
            "INSERT OR IGNORE INTO users (username, password_hash, email, role) VALUES (?, ?, ?, ?)",
            (username, hashed, email, role)
        )
    
    conn.commit()
    conn.close()
    print("✓ 创建 SQLite 数据库")
    
    # 4. 创建简单的 Flask 应用
    app_content = '''from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
import bcrypt
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(os.getenv('DB_FILE', 'policy_rag.db'))
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    
    if user_data:
        return User(user_data[0], user_data[1], user_data[2])
    return None

def get_db():
    conn = sqlite3.connect(os.getenv('DB_FILE', 'policy_rag.db'))
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('index.html', username=current_user.username)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            user_obj = User(user['id'], user['username'], user['role'])
            login_user(user_obj)
            return redirect(url_for('index'))
        
        return render_template('login.html', error='用户名或密码错误')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/ask', methods=['POST'])
@login_required
def ask_question():
    data = request.get_json()
    question = data.get('question')
    
    if not question:
        return jsonify({'error': '问题不能为空'}), 400
    
    # 这里实现 RAG 逻辑
    answer = f"这是针对'{question}'的模拟回答。实际应调用 RAG 系统。"
    
    # 记录查询
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_queries (user_id, question, answer) VALUES (?, ?, ?)",
        (current_user.id, question, answer)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'question': question, 'answer': answer})

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.username, q.question, q.answer, q.created_at 
        FROM user_queries q 
        JOIN users u ON q.user_id = u.id 
        ORDER BY q.created_at DESC
    """)
    queries = cursor.fetchall()
    conn.close()
    
    return render_template('admin.html', queries=queries, username=current_user.username)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
'''

    with open('app_simple.py', 'w', encoding='utf-8') as f:
        f.write(app_content)
    print("✓ 创建 Flask 应用文件")
    
    # 5. 创建 HTML 模板
    templates = {
        'login.html': '''<!DOCTYPE html>
<html>
<head>
    <title>登录</title>
    <style>
        body { font-family: Arial; margin: 0; padding: 20px; background: #f5f5f5; }
        .login-box { max-width: 400px; margin: 100px auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { text-align: center; color: #333; margin-bottom: 30px; }
        input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
        button:hover { background: #45a049; }
        .error { color: #f44336; text-align: center; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>政策解读系统</h1>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="用户名" required>
            <input type="password" name="password" placeholder="密码" required>
            <button type="submit">登录</button>
        </form>
        <div style="text-align: center; margin-top: 20px; color: #666;">
            <p>测试账号:</p>
            <p>管理员: admin / admin123</p>
            <p>普通用户: user1 / user123</p>
        </div>
    </div>
</body>
</html>''',
        
        'index.html': '''<!DOCTYPE html>
<html>
<head>
    <title>政策解读助手</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial; margin: 0; padding: 0; background: #f5f5f5; }
        .header { background: white; padding: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); display: flex; justify-content: space-between; align-items: center; }
        .chat-container { max-width: 800px; margin: 20px auto; background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .message { margin: 10px 0; padding: 10px 15px; border-radius: 8px; max-width: 80%; }
        .user-message { background: #e3f2fd; margin-left: auto; }
        .bot-message { background: #f5f5f5; }
        .input-area { display: flex; margin-top: 20px; }
        #question { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 16px; }
        #ask-btn { padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 4px; margin-left: 10px; cursor: pointer; }
        #ask-btn:hover { background: #45a049; }
        .admin-link { margin-left: 20px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>政策解读助手</h1>
        <div>
            <span>欢迎, {{ username }}</span>
            {% if current_user.role == 'admin' %}
            <a href="{{ url_for('admin_dashboard') }}" class="admin-link">管理员面板</a>
            {% endif %}
            <a href="{{ url_for('logout') }}" style="margin-left: 20px;">退出</a>
        </div>
    </div>
    
    <div class="chat-container">
        <div id="chat"></div>
        
        <div class="input-area">
            <input type="text" id="question" placeholder="请输入关于政策的问题...">
            <button id="ask-btn">提问</button>
        </div>
    </div>
    
    <script>
        document.getElementById('ask-btn').addEventListener('click', askQuestion);
        document.getElementById('question').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') askQuestion();
        });
        
        function addMessage(text, isUser) {
            const chat = document.getElementById('chat');
            const msgDiv = document.createElement('div');
            msgDiv.className = isUser ? 'message user-message' : 'message bot-message';
            msgDiv.textContent = text;
            chat.appendChild(msgDiv);
            chat.scrollTop = chat.scrollHeight;
        }
        
        function askQuestion() {
            const input = document.getElementById('question');
            const question = input.value.trim();
            
            if (!question) return;
            
            addMessage(question, true);
            input.value = '';
            
            fetch('/ask', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ question: question })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    addMessage('错误: ' + data.error, false);
                } else {
                    addMessage(data.answer, false);
                }
            })
            .catch(error => {
                addMessage('请求失败: ' + error, false);
            });
        }
    </script>
</body>
</html>''',
        
        'admin.html': '''<!DOCTYPE html>
<html>
<head>
    <title>管理员面板</title>
    <style>
        body { font-family: Arial; margin: 0; padding: 20px; background: #f5f5f5; }
        .header { background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        table { width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f8f9fa; font-weight: bold; }
        .back-link { display: inline-block; margin-top: 20px; color: #4CAF50; text-decoration: none; }
    </style>
</head>
<body>
    <div class="header">
        <h1>管理员面板</h1>
        <p>用户: {{ username }}</p>
    </div>
    
    <h2>用户查询记录</h2>
    <table>
        <thead>
            <tr>
                <th>用户</th>
                <th>问题</th>
                <th>回答</th>
                <th>时间</th>
            </tr>
        </thead>
        <tbody>
            {% for query in queries %}
            <tr>
                <td>{{ query[0] }}</td>
                <td>{{ query[1] }}</td>
                <td>{{ query[2][:50] }}{% if query[2]|length > 50 %}...{% endif %}</td>
                <td>{{ query[3] }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <a href="{{ url_for('index') }}" class="back-link">返回首页</a>
</body>
</html>'''
    }
    
    for filename, content in templates.items():
        with open(f'templates/{filename}', 'w', encoding='utf-8') as f:
            f.write(content)
    
    print("✓ 创建 HTML 模板文件")
    
    # 6. 创建 requirements.txt
    requirements = '''flask==2.3.3
flask-login==0.6.3
python-dotenv==1.0.0
bcrypt==4.0.1
'''
    
    with open('requirements.txt', 'w', encoding='utf-8') as f:
        f.write(requirements)
    print("✓ 创建 requirements.txt")
    
    print("\n" + "=" * 60)
    print("项目设置完成！")
    print("=" * 60)
    print("\n运行步骤:")
    print("1. 安装依赖: pip install -r requirements.txt")
    print("2. 运行应用: python app_simple.py")
    print("3. 访问: http://localhost:5000")
    print("\n测试账号:")
    print("  管理员: admin / admin123")
    print("  普通用户: user1 / user123")
    print("  普通用户: user2 / user123")
    print("=" * 60)

if __name__ == "__main__":
    setup_simple_project()