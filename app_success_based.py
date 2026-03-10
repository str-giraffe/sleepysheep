# app_success_based.py
from flask import Flask, render_template_string, request, jsonify, redirect, session
import sqlite3
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'success-based-system-key'

# 配置文件
CONFIG = {
    'db_file': 'policy_success.db',
    'use_database': False,  # 先禁用数据库，使用内存存储
    'debug': True
}

# 硬编码用户（从无数据库版本移植）
USERS = {
    'admin': {
        'id': 1,
        'password': 'admin123',
        'role': 'admin',
        'email': 'admin@example.com',
        'created_at': '2024-01-01'
    },
    'user1': {
        'id': 2,
        'password': 'user123',
        'role': 'user',
        'email': 'user1@example.com',
        'created_at': '2024-01-01'
    },
    'user2': {
        'id': 3,
        'password': 'user123',
        'role': 'user',
        'email': 'user2@example.com',
        'created_at': '2024-01-01'
    }
}

# 硬编码政策数据
POLICIES = [
    {
        'id': 1,
        'title': '高新技术企业认定管理办法',
        'content': '高新技术企业是指在《国家重点支持的高新技术领域》内，持续进行研究开发与技术成果转化，形成企业核心自主知识产权，并以此为基础开展经营活动，在中国境内（不包括港、澳、台地区）注册一年以上的居民企业。认定后三年内可享受15%的企业所得税优惠税率。',
        'category': '科技创新',
        'source': '科技部',
        'publish_date': '2023-01-01',
        'created_at': '2023-01-01'
    },
    {
        'id': 2,
        'title': '研发费用加计扣除政策',
        'content': '企业为开发新技术、新产品、新工艺发生的研究开发费用，未形成无形资产计入当期损益的，在按照规定据实扣除的基础上，按照研究开发费用的100%加计扣除；形成无形资产的，按照无形资产成本的200%摊销。',
        'category': '税收优惠',
        'source': '税务总局',
        'publish_date': '2023-03-15',
        'created_at': '2023-03-15'
    },
    {
        'id': 3,
        'title': '小微企业普惠性税收减免政策',
        'content': '对月销售额10万元以下（含本数）的增值税小规模纳税人，免征增值税。对小型微利企业年应纳税所得额不超过100万元的部分，减按25%计入应纳税所得额，按20%的税率缴纳企业所得税。',
        'category': '小微企业',
        'source': '财政部',
        'publish_date': '2023-02-01',
        'created_at': '2023-02-01'
    }
]

# 内存中的查询记录
USER_QUERIES = []

class HybridStorage:
    """混合存储：内存 + 数据库"""
    
    def __init__(self, use_db=False):
        self.use_db = use_db
        self.users = USERS.copy()
        self.policies = POLICIES.copy()
        self.queries = USER_QUERIES.copy()
        
        if use_db:
            self.init_database()
    
    def init_database(self):
        """初始化数据库（可选）"""
        if not self.use_db:
            return
        
        try:
            conn = sqlite3.connect(CONFIG['db_file'])
            cursor = conn.cursor()
            
            # 创建表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE,
                    password_hash TEXT,
                    email TEXT,
                    role TEXT,
                    created_at TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS policies (
                    id INTEGER PRIMARY KEY,
                    policy_title TEXT,
                    policy_content TEXT,
                    category TEXT,
                    source TEXT,
                    publish_date TEXT,
                    created_at TEXT
                )
            """)
            
            # 插入数据
            for user_id, user_data in self.users.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO users (id, username, password_hash, email, role, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_data['id'], user_id, user_data['password'], 
                      user_data['email'], user_data['role'], user_data['created_at']))
            
            for policy in self.policies:
                cursor.execute("""
                    INSERT OR REPLACE INTO policies (id, policy_title, policy_content, category, source, publish_date, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (policy['id'], policy['title'], policy['content'], 
                      policy['category'], policy['source'], policy['publish_date'], policy['created_at']))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"✓ 数据库初始化完成: {CONFIG['db_file']}")
            
        except Exception as e:
            print(f"⚠ 数据库初始化失败，使用内存存储: {e}")
            self.use_db = False
    
    def verify_user(self, username, password):
        """验证用户"""
        if username in self.users and self.users[username]['password'] == password:
            return self.users[username]
        return None
    
    def search_policies(self, query, limit=3):
        """搜索政策"""
        results = []
        for policy in self.policies:
            if (query.lower() in policy['title'].lower() or 
                query.lower() in policy['content'].lower() or
                query.lower() in policy['category'].lower()):
                results.append(policy)
        
        return results[:limit]
    
    def add_query(self, user_id, question, answer):
        """添加查询记录"""
        query = {
            'id': len(self.queries) + 1,
            'user_id': user_id,
            'question': question,
            'answer': answer,
            'created_at': datetime.now().isoformat()
        }
        self.queries.append(query)
        return query

# 初始化存储
storage = HybridStorage(use_db=CONFIG['use_database'])

# 登录页面
LOGIN_HTML = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>登录 - 政策解读系统</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .login-container {
            width: 100%;
            max-width: 400px;
            padding: 20px;
        }
        .login-box {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
        }
        .login-title {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
            font-size: 24px;
        }
        .error-message {
            background: #fff2f0;
            color: #ff4d4f;
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 20px;
            text-align: center;
            border: 1px solid #ffccc7;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-input {
            width: 100%;
            padding: 12px 15px;
            border: 1px solid #d9d9d9;
            border-radius: 6px;
            font-size: 16px;
        }
        .login-btn {
            width: 100%;
            padding: 12px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            cursor: pointer;
        }
        .test-accounts {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 6px;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-box">
            <h1 class="login-title">政策解读系统</h1>
            
            {% if error %}
            <div class="error-message">{{ error }}</div>
            {% endif %}
            
            <form method="POST">
                <div class="form-group">
                    <input type="text" name="username" placeholder="用户名" required class="form-input">
                </div>
                <div class="form-group">
                    <input type="password" name="password" placeholder="密码" required class="form-input">
                </div>
                <button type="submit" class="login-btn">登录</button>
            </form>
            
            <div class="test-accounts">
                <h3>测试账号</h3>
                <p>管理员: admin / admin123</p>
                <p>普通用户: user1 / user123</p>
            </div>
        </div>
    </div>
</body>
</html>'''

# 首页
INDEX_HTML = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>政策解读系统</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #f0f2f5; }
        .navbar {
            background: white;
            padding: 0 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .logo { font-size: 20px; font-weight: bold; color: #1890ff; }
        .user-info { display: flex; align-items: center; gap: 20px; }
        .user-info a { color: #666; text-decoration: none; }
        .user-info a:hover { color: #1890ff; }
        .container {
            max-width: 1000px;
            margin: 30px auto;
            padding: 0 20px;
        }
        .chat-container {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 24px;
        }
        .chat-title {
            font-size: 18px;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid #f0f0f0;
        }
        .chat-box {
            height: 400px;
            overflow-y: auto;
            padding: 20px;
            background: #fafafa;
            border-radius: 6px;
            margin-bottom: 20px;
        }
        .message {
            margin: 12px 0;
            padding: 12px 16px;
            border-radius: 6px;
            line-height: 1.5;
            max-width: 80%;
        }
        .user-message {
            background: #e6f7ff;
            margin-left: auto;
            border: 1px solid #91d5ff;
        }
        .bot-message {
            background: #f6ffed;
            border: 1px solid #b7eb8f;
        }
        .input-area {
            display: flex;
            gap: 10px;
        }
        #question-input {
            flex: 1;
            padding: 12px;
            border: 1px solid #d9d9d9;
            border-radius: 6px;
        }
        #send-btn {
            padding: 0 24px;
            background: #1890ff;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
        }
        .quick-btn {
            margin: 0 8px 8px 0;
            padding: 6px 12px;
            background: #fafafa;
            border: 1px solid #d9d9d9;
            border-radius: 4px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="logo">政策解读系统</div>
        <div class="user-info">
            <span>欢迎, {{ username }}</span>
            {% if role == "admin" %}
            <a href="/admin">管理面板</a>
            {% endif %}
            <a href="/profile">个人中心</a>
            <a href="/logout">退出</a>
        </div>
    </div>
    
    <div class="container">
        <div class="chat-container">
            <div class="chat-title">政策问答助手</div>
            
            <div class="chat-box" id="chat-box">
                <div class="message bot-message">您好！我是政策解读助手，可以回答您关于高新技术企业、税收优惠、人才政策等方面的问题。</div>
            </div>
            
            <div class="input-area">
                <input type="text" id="question-input" placeholder="请输入您的问题...">
                <button id="send-btn">提问</button>
            </div>
            
            <div style="margin-top: 20px;">
                <button class="quick-btn" onclick="askQuick('高新技术企业有什么税收优惠？')">高新技术企业</button>
                <button class="quick-btn" onclick="askQuick('研发费用如何加计扣除？')">研发费用</button>
                <button class="quick-btn" onclick="askQuick('小微企业有哪些税收政策？')">小微企业</button>
            </div>
        </div>
    </div>

    <script>
    function askQuick(question) {
        document.getElementById('question-input').value = question;
        sendQuestion();
    }
    
    function sendQuestion() {
        const input = document.getElementById('question-input');
        const question = input.value.trim();
        
        if (!question) return;
        
        const chatBox = document.getElementById('chat-box');
        const userMsg = document.createElement('div');
        userMsg.className = 'message user-message';
        userMsg.textContent = question;
        chatBox.appendChild(userMsg);
        
        input.value = '';
        
        fetch('/ask', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({question: question})
        })
        .then(res => res.json())
        .then(data => {
            const botMsg = document.createElement('div');
            botMsg.className = 'message bot-message';
            botMsg.textContent = data.answer;
            chatBox.appendChild(botMsg);
            chatBox.scrollTop = chatBox.scrollHeight;
        });
    }
    
    document.getElementById('send-btn').addEventListener('click', sendQuestion);
    document.getElementById('question-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') sendQuestion();
    });
    </script>
</body>
</html>'''

@app.route('/')
def index():
    if 'username' in session and session['username'] in USERS:
        user = USERS[session['username']]
        return render_template_string(INDEX_HTML, 
                                    username=session['username'],
                                    role=user['role'])
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        print(f"[登录] 用户: {username}, 密码: {password}")
        
        if not username or not password:
            return render_template_string(LOGIN_HTML, error='用户名和密码不能为空')
        
        user = storage.verify_user(username, password)
        
        if user:
            session['username'] = username
            session['user_id'] = user['id']
            session['role'] = user['role']
            print(f"[成功] 登录: {username}")
            return redirect('/')
        
        print(f"[失败] 登录: {username}")
        return render_template_string(LOGIN_HTML, error='用户名或密码错误')
    
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/ask', methods=['POST'])
def ask():
    if 'username' not in session:
        return jsonify({'answer': '请先登录'}), 401
    
    data = request.get_json()
    question = data.get('question', '').strip()
    
    if not question:
        return jsonify({'answer': '问题不能为空'}), 400
    
    # 搜索政策
    policies = storage.search_policies(question)
    
    if not policies:
        answer = "未找到相关信息。"
    elif len(policies) == 1:
        policy = policies[0]
        answer = f"根据政策《{policy['title']}》（{policy['source']}）：\n{policy['content']}"
    else:
        answer = "根据以下相关政策：\n"
        for i, policy in enumerate(policies, 1):
            answer += f"\n{i}. 《{policy['title']}》（{policy['source']}）\n"
            answer += f"   {policy['content'][:100]}...\n"
    
    # 记录查询
    if 'user_id' in session:
        storage.add_query(session['user_id'], question, answer)
    
    return jsonify({'answer': answer})

@app.route('/admin')
def admin():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect('/')
    
    return f'''<!DOCTYPE html>
<html>
<head><title>管理面板</title>
<style>
body {{ font-family: Arial; padding: 20px; }}
.stats {{ display: flex; gap: 20px; margin: 20px 0; }}
.stat {{ padding: 20px; background: white; border-radius: 8px; text-align: center; }}
</style>
</head>
<body>
    <h1>管理面板</h1>
    <p>用户: {session['username']}</p>
    
    <div class="stats">
        <div class="stat">用户数: {len(USERS)}</div>
        <div class="stat">政策数: {len(POLICIES)}</div>
        <div class="stat">查询数: {len(storage.queries)}</div>
    </div>
    
    <h3>最近查询</h3>
    <ul>
        {"".join(f'<li><b>{q["user_id"]}</b>: {q["question"]} - {q["created_at"]}</li>' for q in storage.queries[-10:])}
    </ul>
    
    <p><a href="/">返回首页</a></p>
</body>
</html>'''

@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect('/login')
    
    user = USERS.get(session['username'], {})
    user_queries = [q for q in storage.queries if q.get('user_id') == user.get('id')]
    
    return f'''<!DOCTYPE html>
<html>
<head><title>个人中心</title></head>
<body>
    <h1>个人中心</h1>
    <p>用户名: {session['username']}</p>
    <p>邮箱: {user.get('email', '')}</p>
    <p>角色: {user.get('role', '')}</p>
    
    <h3>我的查询记录</h3>
    <ul>
        {"".join(f'<li>{q["question"]} - {q["created_at"]}</li>' for q in user_queries[-5:])}
    </ul>
    
    <p><a href="/">返回首页</a></p>
</body>
</html>'''

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'users': len(USERS),
        'policies': len(POLICIES),
        'queries': len(storage.queries),
        'logged_in': 'username' in session
    })

if __name__ == '__main__':
    print("=" * 60)
    print("政策解读系统 - 基于成功版本构建")
    print("=" * 60)
    print("存储方式: 内存存储")
    print("数据库: 禁用（避免登录问题）")
    print("访问: http://localhost:5009")
    print("\n测试账号:")
    print("管理员: admin / admin123")
    print("普通用户: user1 / user123")
    print("\n特点:")
    print("1. 基于已验证的无数据库版本构建")
    print("2. 使用内存存储，避免数据库问题")
    print("3. 保留所有核心功能")
    print("=" * 60)
    
    app.run(debug=True, port=5009, host='0.0.0.0')