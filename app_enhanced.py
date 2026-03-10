# app_enhanced.py
from flask import Flask, render_template_string, request, jsonify, redirect, session
import json
import os
from datetime import datetime
import hashlib

app = Flask(__name__)
app.secret_key = 'enhanced-policy-system-key'

# 配置文件
CONFIG = {
    'data_file': 'policy_data.json',  # 使用JSON文件存储，避免数据库问题
    'debug': True
}

# 初始化用户数据
def init_users():
    return {
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

# 初始化政策数据
def init_policies():
    return [
        {
            'id': 1,
            'title': '高新技术企业认定管理办法',
            'content': '高新技术企业是指在《国家重点支持的高新技术领域》内，持续进行研究开发与技术成果转化，形成企业核心自主知识产权，并以此为基础开展经营活动，在中国境内注册一年以上的居民企业。认定后三年内可享受15%的企业所得税优惠税率。',
            'category': '科技创新',
            'source': '科技部',
            'publish_date': '2023-01-01',
            'keywords': ['高新技术', '税收优惠', '企业所得税', '15%'],
            'vector': [0.1, 0.2, 0.3, 0.4, 0.5]  # 简单向量表示
        },
        {
            'id': 2,
            'title': '研发费用加计扣除政策',
            'content': '企业为开发新技术、新产品、新工艺发生的研究开发费用，未形成无形资产计入当期损益的，在按照规定据实扣除的基础上，按照研究开发费用的100%加计扣除；形成无形资产的，按照无形资产成本的200%摊销。',
            'category': '税收优惠',
            'source': '税务总局',
            'publish_date': '2023-03-15',
            'keywords': ['研发费用', '加计扣除', '税收', '100%'],
            'vector': [0.2, 0.3, 0.4, 0.5, 0.6]
        },
        {
            'id': 3,
            'title': '小微企业普惠性税收减免政策',
            'content': '对月销售额10万元以下的增值税小规模纳税人，免征增值税。对小型微利企业年应纳税所得额不超过100万元的部分，减按25%计入应纳税所得额，按20%的税率缴纳企业所得税。',
            'category': '小微企业',
            'source': '财政部',
            'publish_date': '2023-02-01',
            'keywords': ['小微企业', '税收减免', '增值税', '企业所得税'],
            'vector': [0.3, 0.4, 0.5, 0.6, 0.7]
        },
        {
            'id': 4,
            'title': '人才引进补贴实施办法',
            'content': '对引进的高层次人才，给予一次性安家补贴50-200万元，提供人才公寓或租房补贴，协助解决配偶就业和子女入学问题。对创业人才给予最高500万元的创业启动资金支持。',
            'category': '人才政策',
            'source': '人社部',
            'publish_date': '2023-04-10',
            'keywords': ['人才引进', '补贴', '安家费', '创业资金'],
            'vector': [0.4, 0.5, 0.6, 0.7, 0.8]
        },
        {
            'id': 5,
            'title': '环境保护税收优惠政策',
            'content': '企业从事符合条件的环境保护、节能节水项目的所得，自项目取得第一笔生产经营收入所属纳税年度起，第一年至第三年免征企业所得税，第四年至第六年减半征收企业所得税。',
            'category': '环保',
            'source': '生态环境部',
            'publish_date': '2023-05-20',
            'keywords': ['环境保护', '税收优惠', '免征', '节能节水'],
            'vector': [0.5, 0.6, 0.7, 0.8, 0.9]
        },
        {
            'id': 6,
            'title': '创业投资税收优惠政策',
            'content': '创业投资企业采取股权投资方式投资于未上市的中小高新技术企业2年以上的，可以按照其投资额的70%在股权持有满2年的当年抵扣该创业投资企业的应纳税所得额。',
            'category': '创业投资',
            'source': '税务总局',
            'publish_date': '2023-06-15',
            'keywords': ['创业投资', '股权投资', '税收抵扣', '70%'],
            'vector': [0.6, 0.7, 0.8, 0.9, 1.0]
        },
        {
            'id': 7,
            'title': '软件和集成电路产业税收政策',
            'content': '国家鼓励的软件企业和集成电路设计企业，自获利年度起计算优惠期，第一年至第二年免征企业所得税，第三年至第五年按照25%的法定税率减半征收企业所得税。',
            'category': '信息技术',
            'source': '工信部',
            'publish_date': '2023-07-01',
            'keywords': ['软件', '集成电路', '企业所得税', '免征'],
            'vector': [0.7, 0.8, 0.9, 1.0, 0.1]
        }
    ]

class PolicyRAGSystem:
    """增强的RAG政策解读系统"""
    
    def __init__(self):
        self.users = init_users()
        self.policies = init_policies()
        self.queries = []
        self.load_data()
    
    def load_data(self):
        """从文件加载数据"""
        if os.path.exists(CONFIG['data_file']):
            try:
                with open(CONFIG['data_file'], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.queries = data.get('queries', [])
                    print(f"✓ 加载了 {len(self.queries)} 条历史查询")
            except Exception as e:
                print(f"⚠ 加载数据失败: {e}")
    
    def save_data(self):
        """保存数据到文件"""
        try:
            data = {
                'queries': self.queries[-100:],  # 只保存最近100条
                'saved_at': datetime.now().isoformat()
            }
            with open(CONFIG['data_file'], 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠ 保存数据失败: {e}")
    
    def verify_user(self, username, password):
        """验证用户"""
        if username in self.users and self.users[username]['password'] == password:
            return self.users[username]
        return None
    
    def simple_similarity(self, vec1, vec2):
        """计算简单相似度"""
        if len(vec1) != len(vec2):
            return 0
        return sum(a * b for a, b in zip(vec1, vec2)) / (
            (sum(a*a for a in vec1) ** 0.5) * (sum(b*b for b in vec2) ** 0.5) + 1e-10
        )
    
    def generate_query_vector(self, query):
        """为查询生成简单向量"""
        # 基于关键词匹配生成向量
        query = query.lower()
        vector = [0.0] * 5
        
        # 检查关键词
        keywords_mapping = {
            '税收': 0, '优惠': 0, '减免': 0,
            '人才': 1, '引进': 1, '补贴': 1,
            '研发': 2, '技术': 2, '创新': 2,
            '企业': 3, '创业': 3, '投资': 3,
            '环境': 4, '保护': 4, '节能': 4
        }
        
        for keyword, index in keywords_mapping.items():
            if keyword in query:
                vector[index] += 0.5
        
        # 归一化
        norm = (sum(v*v for v in vector) ** 0.5) or 1
        return [v/norm for v in vector]
    
    def search_policies_rag(self, query, limit=3):
        """RAG搜索：基于相似度的政策检索"""
        query_vector = self.generate_query_vector(query)
        query_keywords = query.lower()
        
        scored_policies = []
        
        for policy in self.policies:
            # 1. 向量相似度
            vector_sim = self.simple_similarity(query_vector, policy.get('vector', []))
            
            # 2. 关键词匹配
            keyword_score = 0
            for keyword in policy.get('keywords', []):
                if keyword in query_keywords:
                    keyword_score += 0.3
            
            # 3. 标题和内容匹配
            content_score = 0
            if any(word in query_keywords for word in policy['title'].lower().split()):
                content_score += 0.2
            if any(word in query_keywords for word in policy['content'].lower().split()[:10]):
                content_score += 0.1
            
            # 总分
            total_score = vector_sim + keyword_score + content_score
            
            if total_score > 0.1:  # 阈值
                scored_policies.append({
                    'policy': policy,
                    'score': total_score,
                    'vector_sim': vector_sim,
                    'keyword_score': keyword_score
                })
        
        # 按分数排序
        scored_policies.sort(key=lambda x: x['score'], reverse=True)
        
        return [item['policy'] for item in scored_policies[:limit]]
    
    def add_query(self, user_id, username, question, answer, policies_used=None):
        """添加查询记录"""
        query = {
            'id': len(self.queries) + 1,
            'user_id': user_id,
            'username': username,
            'question': question,
            'answer': answer,
            'policies_used': policies_used or [],
            'created_at': datetime.now().isoformat()
        }
        self.queries.append(query)
        self.save_data()  # 自动保存
        return query
    
    def get_user_queries(self, user_id, limit=10):
        """获取用户的查询记录"""
        return [q for q in self.queries if q.get('user_id') == user_id][-limit:][::-1]
    
    def get_recent_queries(self, limit=20):
        """获取最近的查询记录"""
        return self.queries[-limit:][::-1]
    
    def get_statistics(self):
        """获取统计数据"""
        return {
            'user_count': len(self.users),
            'policy_count': len(self.policies),
            'query_count': len(self.queries),
            'today_queries': len([q for q in self.queries 
                                 if datetime.fromisoformat(q['created_at']).date() == datetime.now().date()])
        }

# 初始化系统
rag_system = PolicyRAGSystem()

# HTML模板
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
            <h1 class="login-title">政策解读系统 v2.0</h1>
            
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

INDEX_HTML = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>政策解读系统 v2.0</title>
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
        .logo span { color: #666; font-size: 14px; margin-left: 5px; }
        .user-info { display: flex; align-items: center; gap: 20px; }
        .user-info a { color: #666; text-decoration: none; padding: 5px 10px; border-radius: 4px; }
        .user-info a:hover { background: #f5f5f5; }
        .container {
            max-width: 1200px;
            margin: 30px auto;
            padding: 0 20px;
        }
        .dashboard {
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 20px;
        }
        .sidebar {
            background: white;
            border-radius: 8px;
            padding: 20px;
        }
        .main-content {
            background: white;
            border-radius: 8px;
            padding: 20px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-number {
            font-size: 24px;
            font-weight: bold;
            color: #1890ff;
        }
        .chat-container {
            margin-top: 20px;
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
        .quick-questions {
            margin-top: 20px;
        }
        .quick-btn {
            margin: 0 8px 8px 0;
            padding: 6px 12px;
            background: #fafafa;
            border: 1px solid #d9d9d9;
            border-radius: 4px;
            cursor: pointer;
        }
        .policy-info {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="logo">政策解读系统 <span>v2.0</span></div>
        <div class="user-info">
            <span>欢迎, {{ username }}</span>
            {% if role == "admin" %}
            <a href="/admin">管理面板</a>
            {% endif %}
            <a href="/profile">个人中心</a>
            <a href="/stats">数据统计</a>
            <a href="/logout">退出</a>
        </div>
    </div>
    
    <div class="container">
        <div class="dashboard">
            <div class="sidebar">
                <h3>📊 系统概览</h3>
                <p>政策库: {{ stats.policy_count }} 条</p>
                <p>总查询: {{ stats.query_count }} 次</p>
                <p>今日查询: {{ stats.today_queries }} 次</p>
                
                <h3 style="margin-top: 20px;">🔍 热门搜索</h3>
                <div id="hot-searches">
                    <p>高新技术企业</p>
                    <p>研发费用</p>
                    <p>小微企业</p>
                </div>
            </div>
            
            <div class="main-content">
                <h2>政策问答助手</h2>
                
                <div class="stats-grid">
                    <div class="stat-card" style="background: #f0f7ff;">
                        <div class="stat-number">{{ stats.policy_count }}</div>
                        <div>政策总数</div>
                    </div>
                    <div class="stat-card" style="background: #f6ffed;">
                        <div class="stat-number">{{ stats.query_count }}</div>
                        <div>总查询数</div>
                    </div>
                    <div class="stat-card" style="background: #fff7e6;">
                        <div class="stat-number">{{ stats.today_queries }}</div>
                        <div>今日查询</div>
                    </div>
                </div>
                
                <div class="chat-container">
                    <div class="chat-box" id="chat-box">
                        <div class="message bot-message">
                            <strong>👋 您好！我是政策解读助手</strong><br>
                            我可以回答您关于各种政策的问题，包括：
                            <ul>
                                <li>税收优惠政策</li>
                                <li>人才引进政策</li>
                                <li>小微企业扶持</li>
                                <li>研发创新支持</li>
                            </ul>
                            请输入您的问题，我会从政策库中为您找到最相关的信息。
                        </div>
                    </div>
                    
                    <div class="input-area">
                        <input type="text" id="question-input" placeholder="请输入您的问题..." onkeypress="if(event.key=='Enter')sendQuestion()">
                        <button id="send-btn" onclick="sendQuestion()">提问</button>
                    </div>
                    
                    <div class="quick-questions">
                        <p>快捷提问：</p>
                        <button class="quick-btn" onclick="quickAsk('高新技术企业有什么税收优惠？')">高新技术企业</button>
                        <button class="quick-btn" onclick="quickAsk('研发费用如何加计扣除？')">研发费用</button>
                        <button class="quick-btn" onclick="quickAsk('小微企业有哪些税收政策？')">小微企业</button>
                        <button class="quick-btn" onclick="quickAsk('人才引进有什么补贴？')">人才引进</button>
                        <button class="quick-btn" onclick="quickAsk('环境保护税收优惠有哪些？')">环保税收</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
    function quickAsk(question) {
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
        userMsg.innerHTML = `<strong>您：</strong><br>${question}`;
        chatBox.appendChild(userMsg);
        
        input.value = '';
        
        // 显示加载状态
        const loadingMsg = document.createElement('div');
        loadingMsg.className = 'message bot-message';
        loadingMsg.innerHTML = '<em>正在搜索相关政策...</em>';
        chatBox.appendChild(loadingMsg);
        chatBox.scrollTop = chatBox.scrollHeight;
        
        fetch('/ask', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({question: question})
        })
        .then(res => res.json())
        .then(data => {
            // 移除加载消息
            chatBox.removeChild(loadingMsg);
            
            const botMsg = document.createElement('div');
            botMsg.className = 'message bot-message';
            
            let answerHTML = `<strong>政策解读：</strong><br>${data.answer}`;
            
            if (data.sources && data.sources.length > 0) {
                answerHTML += `<div class="policy-info"><br>📚 参考政策：`;
                data.sources.forEach((source, idx) => {
                    answerHTML += `<br>${idx+1}. 《${source.title}》 (${source.source})`;
                });
                answerHTML += `</div>`;
            }
            
            botMsg.innerHTML = answerHTML;
            chatBox.appendChild(botMsg);
            chatBox.scrollTop = chatBox.scrollHeight;
            
            // 更新统计
            if (data.stats) {
                updateStats(data.stats);
            }
        })
        .catch(error => {
            chatBox.removeChild(loadingMsg);
            const errorMsg = document.createElement('div');
            errorMsg.className = 'message bot-message';
            errorMsg.textContent = '抱歉，请求失败，请重试。';
            chatBox.appendChild(errorMsg);
        });
    }
    
    function updateStats(stats) {
        // 更新页面上的统计数字
        document.querySelectorAll('.stat-number')[0].textContent = stats.policy_count;
        document.querySelectorAll('.stat-number')[1].textContent = stats.query_count;
        document.querySelectorAll('.stat-number')[2].textContent = stats.today_queries;
    }
    </script>
</body>
</html>'''

@app.route('/')
def index():
    if 'username' in session and session['username'] in rag_system.users:
        user = rag_system.users[session['username']]
        stats = rag_system.get_statistics()
        return render_template_string(INDEX_HTML, 
                                    username=session['username'],
                                    role=user['role'],
                                    stats=stats)
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            return render_template_string(LOGIN_HTML, error='用户名和密码不能为空')
        
        user = rag_system.verify_user(username, password)
        
        if user:
            session['username'] = username
            session['user_id'] = user['id']
            session['role'] = user['role']
            return redirect('/')
        
        return render_template_string(LOGIN_HTML, error='用户名或密码错误')
    
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/ask', methods=['POST'])
def ask():
    if 'username' not in session:
        return jsonify({'error': '请先登录'}), 401
    
    data = request.get_json()
    question = data.get('question', '').strip()
    
    if not question:
        return jsonify({'error': '问题不能为空'}), 400
    
    # 使用RAG搜索
    policies = rag_system.search_policies_rag(question, limit=3)
    
    if not policies:
        answer = "未找到相关信息。"
        sources = []
    elif len(policies) == 1:
        policy = policies[0]
        answer = f"根据政策《{policy['title']}》（{policy['source']}）：\n{policy['content']}"
        sources = [{'title': policy['title'], 'source': policy['source']}]
    else:
        answer = "根据以下相关政策：\n"
        sources = []
        for i, policy in enumerate(policies, 1):
            answer += f"\n{i}. 《{policy['title']}》（{policy['source']}）\n"
            answer += f"   {policy['content'][:150]}...\n"
            sources.append({'title': policy['title'], 'source': policy['source']})
    
    # 记录查询
    rag_system.add_query(
        session['user_id'],
        session['username'],
        question,
        answer,
        [p['title'] for p in policies]
    )
    
    stats = rag_system.get_statistics()
    
    return jsonify({
        'answer': answer,
        'sources': sources,
        'stats': stats
    })

@app.route('/admin')
def admin():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect('/')
    
    stats = rag_system.get_statistics()
    recent_queries = rag_system.get_recent_queries(20)
    
    return f'''<!DOCTYPE html>
<html>
<head><title>管理面板</title>
<style>
body {{ font-family: Arial; padding: 20px; }}
.stats {{ display: flex; gap: 20px; margin: 20px 0; }}
.stat {{ padding: 20px; background: white; border-radius: 8px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
th, td {{ padding: 10px; border: 1px solid #ddd; text-align: left; }}
</style>
</head>
<body>
    <h1>管理面板</h1>
    <p>用户: {session['username']}</p>
    
    <div class="stats">
        <div class="stat">用户数: {stats['user_count']}</div>
        <div class="stat">政策数: {stats['policy_count']}</div>
        <div class="stat">总查询: {stats['query_count']}</div>
        <div class="stat">今日查询: {stats['today_queries']}</div>
    </div>
    
    <h3>最近查询记录</h3>
    <table>
        <tr><th>用户</th><th>问题</th><th>回答</th><th>时间</th></tr>
        {"".join(f'<tr><td>{q["username"]}</td><td>{q["question"]}</td><td>{q["answer"][:50]}...</td><td>{q["created_at"]}</td></tr>' for q in recent_queries)}
    </table>
    
    <p><a href="/">返回首页</a></p>
</body>
</html>'''

@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect('/login')
    
    user = rag_system.users.get(session['username'], {})
    user_queries = rag_system.get_user_queries(session['user_id'], 10)
    
    return f'''<!DOCTYPE html>
<html>
<head><title>个人中心</title>
<style>
body {{ font-family: Arial; padding: 20px; }}
.profile-card {{ max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
th, td {{ padding: 10px; border: 1px solid #ddd; }}
</style>
</head>
<body>
    <div class="profile-card">
        <h1>个人中心</h1>
        <p><strong>用户名:</strong> {session['username']}</p>
        <p><strong>邮箱:</strong> {user.get('email', '')}</p>
        <p><strong>角色:</strong> {user.get('role', '')}</p>
        
        <h3>我的查询记录（最近10条）</h3>
        <table>
            <tr><th>问题</th><th>回答摘要</th><th>时间</th></tr>
            {"".join(f'<tr><td>{q["question"]}</td><td>{q["answer"][:100]}...</td><td>{q["created_at"]}</td></tr>' for q in user_queries)}
        </table>
        
        <p><a href="/">返回首页</a></p>
    </div>
</body>
</html>'''

@app.route('/stats')
def stats():
    if 'username' not in session:
        return redirect('/login')
    
    stats = rag_system.get_statistics()
    recent_queries = rag_system.get_recent_queries(10)
    
    # 按类别统计
    categories = {}
    for policy in rag_system.policies:
        cat = policy['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    return f'''<!DOCTYPE html>
<html>
<head><title>数据统计</title>
<style>
body {{ font-family: Arial; padding: 20px; }}
.stats-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }}
.stat-box {{ background: white; padding: 20px; border-radius: 8px; }}
</style>
</head>
<body>
    <h1>数据统计</h1>
    
    <div class="stats-grid">
        <div class="stat-box">
            <h3>📊 系统统计</h3>
            <p>用户数: {stats['user_count']}</p>
            <p>政策数: {stats['policy_count']}</p>
            <p>总查询: {stats['query_count']}</p>
            <p>今日查询: {stats['today_queries']}</p>
        </div>
        
        <div class="stat-box">
            <h3>📁 政策分类</h3>
            {"".join(f'<p>{cat}: {count} 条</p>' for cat, count in categories.items())}
        </div>
        
        <div class="stat-box">
            <h3>🔍 最近查询</h3>
            {"".join(f'<p><small>{q["created_at"]}</small><br>{q["question"][:30]}...</p>' for q in recent_queries)}
        </div>
        
        <div class="stat-box">
            <h3>👥 用户列表</h3>
            {"".join(f'<p>{user} ({rag_system.users[user]["role"]})</p>' for user in rag_system.users)}
        </div>
    </div>
    
    <p><a href="/">返回首页</a></p>
</body>
</html>'''

@app.route('/health')
def health():
    stats = rag_system.get_statistics()
    return jsonify({
        'status': 'ok',
        'version': '2.0',
        'stats': stats,
        'logged_in': 'username' in session
    })

if __name__ == '__main__':
    print("=" * 60)
    print("政策解读系统 v2.0 - 增强版")
    print("=" * 60)
    print("🎯 功能特点:")
    print("1. 增强的RAG搜索算法")
    print("2. 7个完整政策文档")
    print("3. 数据持久化（JSON文件）")
    print("4. 完整的统计功能")
    print("5. 用户查询历史")
    print("6. 美观的管理界面")
    print("\n🔐 测试账号:")
    print("管理员: admin / admin123")
    print("普通用户: user1 / user123")
    print("\n🌐 访问地址: http://localhost:5010")
    print("📊 数据文件: policy_data.json")
    print("=" * 60)
    
    app.run(debug=True, port=5010, host='0.0.0.0')