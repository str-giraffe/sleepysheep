# app_no_db_fixed.py
from flask import Flask, render_template_string, request, redirect, session, jsonify

app = Flask(__name__)
app.secret_key = 'no-database-required-key'

# 硬编码用户
USERS = {
    'admin': {
        'password': 'admin123',
        'role': 'admin',
        'email': 'admin@example.com'
    },
    'user1': {
        'password': 'user123',
        'role': 'user',
        'email': 'user1@example.com'
    },
    'user2': {
        'password': 'user123',
        'role': 'user',
        'email': 'user2@example.com'
    }
}

# 硬编码政策
POLICIES = [
    {
        'title': '高新技术企业认定',
        'content': '高新技术企业享受15%企业所得税优惠税率，认定有效期三年。',
        'category': '税收',
        'source': '科技部'
    },
    {
        'title': '研发费用加计扣除',
        'content': '企业研发费用可按100%比例在税前加计扣除。',
        'category': '税收',
        'source': '税务总局'
    },
    {
        'title': '小微企业税收优惠',
        'content': '小微企业年应纳税所得额不超过100万元的部分，减按25%计入，按20%税率缴纳。',
        'category': '税收',
        'source': '财政部'
    }
]

# 首页模板
index_template = '''<!DOCTYPE html>
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
            font-size: 16px;
        }
        #question-input:focus {
            outline: none;
            border-color: #1890ff;
        }
        #send-btn {
            padding: 0 24px;
            background: #1890ff;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            cursor: pointer;
        }
        #send-btn:hover {
            background: #40a9ff;
        }
        .quick-questions {
            margin-top: 20px;
        }
        .quick-questions p {
            color: #666;
            margin-bottom: 10px;
        }
        .quick-btn {
            margin: 0 8px 8px 0;
            padding: 6px 12px;
            background: #fafafa;
            border: 1px solid #d9d9d9;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        .quick-btn:hover {
            background: #f5f5f5;
            border-color: #1890ff;
            color: #1890ff;
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
            
            <div class="quick-questions">
                <p>快捷提问：</p>
                <button class="quick-btn" onclick="askQuestion('高新技术企业有什么税收优惠？')">高新技术企业</button>
                <button class="quick-btn" onclick="askQuestion('研发费用如何加计扣除？')">研发费用</button>
                <button class="quick-btn" onclick="askQuestion('小微企业有哪些税收政策？')">小微企业</button>
                <button class="quick-btn" onclick="askQuestion('人才引进有什么补贴？')">人才引进</button>
            </div>
        </div>
    </div>

    <script>
        function addMessage(text, isUser) {
            const chatBox = document.getElementById('chat-box');
            const message = document.createElement('div');
            message.className = isUser ? 'message user-message' : 'message bot-message';
            message.textContent = text;
            chatBox.appendChild(message);
            chatBox.scrollTop = chatBox.scrollHeight;
        }
        
        function askQuestion(question) {
            if (!question) return;
            
            document.getElementById('question-input').value = question;
            sendQuestion();
        }
        
        function sendQuestion() {
            const input = document.getElementById('question-input');
            const question = input.value.trim();
            
            if (!question) return;
            
            addMessage(question, true);
            input.value = '';
            
            fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: question })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addMessage(data.answer, false);
                } else {
                    addMessage('错误: ' + data.error, false);
                }
            })
            .catch(error => {
                addMessage('请求失败，请重试', false);
            });
        }
        
        document.getElementById('send-btn').addEventListener('click', sendQuestion);
        document.getElementById('question-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendQuestion();
        });
    </script>
</body>
</html>'''

# 登录模板
login_template = '''<!DOCTYPE html>
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
            transition: all 0.3s;
        }
        .form-input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
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
            transition: background 0.3s;
        }
        .login-btn:hover {
            background: #5a67d8;
        }
        .test-accounts {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 6px;
        }
        .test-accounts h3 {
            color: #555;
            margin-bottom: 10px;
            font-size: 16px;
        }
        .test-accounts p {
            color: #666;
            margin: 5px 0;
            font-size: 14px;
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
                <p>普通用户: user2 / user123</p>
            </div>
        </div>
    </div>
</body>
</html>'''

@app.route('/')
def index():
    if 'username' in session and session['username'] in USERS:
        user = USERS[session['username']]
        return render_template_string(index_template, 
                                    username=session['username'],
                                    role=user['role'])
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        print(f"登录尝试: {username}/{password}")
        
        if username in USERS and USERS[username]['password'] == password:
            session['username'] = username
            print(f"登录成功: {username}")
            return redirect('/')
        
        print(f"登录失败: {username}")
        return render_template_string(login_template, error='用户名或密码错误')
    
    return render_template_string(login_template)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

@app.route('/ask', methods=['POST'])
def ask():
    if 'username' not in session or session['username'] not in USERS:
        return jsonify({'success': False, 'error': '请先登录'}), 401
    
    data = request.get_json()
    question = data.get('question', '')
    
    if not question:
        return jsonify({'success': False, 'error': '问题不能为空'}), 400
    
    # 简单搜索逻辑
    answer = "信息库未收录相关信息。"
    for policy in POLICIES:
        if any(keyword in question for keyword in ['税收', '优惠', '减免', '税率']):
            if policy['category'] == '税收':
                answer = f"根据政策《{policy['title']}》（来源：{policy['source']}）：\n{policy['content']}"
                break
    
    return jsonify({'success': True, 'answer': answer})

@app.route('/admin')
def admin():
    if 'username' not in session or session['username'] not in USERS:
        return redirect('/login')
    
    user = USERS[session['username']]
    if user['role'] != 'admin':
        return redirect('/')
    
    # 创建用户列表HTML
    users_html = '<ul>'
    for username, info in USERS.items():
        users_html += f'<li>{username} ({info["role"]}) - {info["email"]}</li>'
    users_html += '</ul>'
    
    return f'''<!DOCTYPE html>
<html>
<head>
    <title>管理面板</title>
    <style>
        body {{ font-family: Arial; padding: 20px; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat-card {{ padding: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center; }}
        .stat-number {{ font-size: 2rem; color: #1890ff; }}
    </style>
</head>
<body>
    <h1>管理面板</h1>
    <p>用户: {session['username']}</p>
    
    <div class="stats">
        <div class="stat-card">
            <div class="stat-number">{len(USERS)}</div>
            <div>用户数</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{len(POLICIES)}</div>
            <div>政策数</div>
        </div>
    </div>
    
    <h3>系统用户</h3>
    {users_html}
    
    <a href="/">返回首页</a>
</body>
</html>'''

@app.route('/profile')
def profile():
    if 'username' not in session or session['username'] not in USERS:
        return redirect('/login')
    
    user = USERS[session['username']]
    
    return f'''<!DOCTYPE html>
<html>
<head>
    <title>个人中心</title>
    <style>
        body {{ font-family: Arial; padding: 20px; }}
        .profile-card {{ max-width: 400px; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
    </style>
</head>
<body>
    <div class="profile-card">
        <h1>个人中心</h1>
        <p><strong>用户名:</strong> {session['username']}</p>
        <p><strong>邮箱:</strong> {user['email']}</p>
        <p><strong>角色:</strong> {user['role']}</p>
        <a href="/">返回首页</a>
    </div>
</body>
</html>'''

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'users': len(USERS), 'policies': len(POLICIES)})

if __name__ == '__main__':
    print("=" * 60)
    print("政策解读系统 - 无数据库版本 (已修复)")
    print("=" * 60)
    print("访问: http://localhost:5004")
    print("\n测试账号:")
    print("管理员: admin / admin123")
    print("普通用户: user1 / user123")
    print("普通用户: user2 / user123")
    print("\n无需数据库，所有数据硬编码在内存中")
    print("\n健康检查: http://localhost:5004/health")
    print("=" * 60)
    
    app.run(debug=True, port=5004, host='0.0.0.0')