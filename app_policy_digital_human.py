# app_policy_digital_human_fixed.py
from flask import Flask, render_template_string, request, jsonify, session, redirect, send_file
import os
import tempfile
import shutil
import uuid
from datetime import datetime
import time

# 检查核心依赖
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("⚠ pyttsx3 未安装，语音功能将不可用")

app = Flask(__name__)
app.secret_key = 'policy-digital-human-optimized-2024'

# 用户数据
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

# 政策数据
POLICIES = [
    {
        'id': 1,
        'title': '高新技术企业认定管理办法',
        'content': '高新技术企业是指在《国家重点支持的高新技术领域》内，持续进行研究开发与技术成果转化，形成企业核心自主知识产权，并以此为基础开展经营活动，在中国境内注册一年以上的居民企业。认定后三年内可享受15%的企业所得税优惠税率。',
        'category': '科技创新',
        'source': '科技部',
        'publish_date': '2023-01-01',
        'keywords': ['高新技术', '税收优惠', '企业所得税', '15%']
    },
    {
        'id': 2,
        'title': '研发费用加计扣除政策',
        'content': '企业为开发新技术、新产品、新工艺发生的研究开发费用，未形成无形资产计入当期损益的，在按照规定据实扣除的基础上，按照研究开发费用的100%加计扣除；形成无形资产的，按照无形资产成本的200%摊销。',
        'category': '税收优惠',
        'source': '税务总局',
        'publish_date': '2023-03-15',
        'keywords': ['研发费用', '加计扣除', '税收', '100%']
    },
    {
        'id': 3,
        'title': '小微企业普惠性税收减免政策',
        'content': '对月销售额10万元以下的增值税小规模纳税人，免征增值税。对小型微利企业年应纳税所得额不超过100万元的部分，减按25%计入应纳税所得额，按20%的税率缴纳企业所得税。',
        'category': '小微企业',
        'source': '财政部',
        'publish_date': '2023-02-01',
        'keywords': ['小微企业', '税收减免', '增值税', '企业所得税']
    }
]

class SimpleDigitalHuman:
    """简易数字人类 - 优化版"""
    
    def __init__(self):
        self.tts_engine = None
        if TTS_AVAILABLE:
            self.init_tts()
        self.audio_files = {}  # 存储音频文件路径
    
    def init_tts(self):
        """初始化TTS引擎"""
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)  # 语速
            self.tts_engine.setProperty('volume', 0.9)  # 音量
            print("✓ TTS引擎初始化成功")
        except Exception as e:
            print(f"⚠ TTS初始化失败: {e}")
            self.tts_engine = None
    
    def speak_text(self, text, output_file=None):
        """文本转语音"""
        if not self.tts_engine:
            return None
        
        try:
            if not output_file:
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                    output_file = tmp.name
            
            self.tts_engine.save_to_file(text, output_file)
            self.tts_engine.runAndWait()
            
            return output_file
        except Exception as e:
            print(f"⚠ 语音合成失败: {e}")
            return None

class PolicySystem:
    """政策解读系统"""
    
    def __init__(self):
        self.users = USERS
        self.policies = POLICIES
        self.queries = []
        self.digital_human = SimpleDigitalHuman()
    
    def verify_user(self, username, password):
        """验证用户"""
        if username in self.users and self.users[username]['password'] == password:
            return self.users[username]
        return None
    
    def search_policies(self, query, limit=3):
        """搜索政策"""
        query_lower = query.lower()
        scored_policies = []
        
        for policy in self.policies:
            score = 0
            
            # 关键词匹配
            for keyword in policy.get('keywords', []):
                if keyword.lower() in query_lower:
                    score += 2
            
            # 标题匹配
            if any(word in query_lower for word in policy['title'].lower().split()):
                score += 1.5
            
            # 内容匹配
            if any(word in query_lower for word in policy['content'].lower().split()[:20]):
                score += 1
            
            if score > 0:
                scored_policies.append({'policy': policy, 'score': score})
        
        scored_policies.sort(key=lambda x: x['score'], reverse=True)
        return [r['policy'] for r in scored_policies[:limit]]
    
    def answer_question(self, question, username="用户"):
        """回答问题"""
        policies = self.search_policies(question)
        
        if not policies:
            answer = f"{username}，您好！关于您的问题，信息库中暂时没有找到相关政策信息。\n\n您可以尝试询问以下方面：\n1. 高新技术企业税收优惠\n2. 研发费用加计扣除\n3. 小微企业税收政策"
            return answer, []
        
        if len(policies) == 1:
            policy = policies[0]
            answer = f"{username}，您好！根据政策《{policy['title']}》（{policy['source']}）：\n\n{policy['content']}"
        else:
            answer = f"{username}，您好！根据相关政策，我为您找到以下信息：\n"
            for i, policy in enumerate(policies, 1):
                answer += f"\n{i}. 《{policy['title']}》（{policy['source']}）\n"
                answer += f"   {policy['content'][:100]}...\n"
        
        # 记录查询
        query_record = {
            'id': len(self.queries) + 1,
            'username': username,
            'question': question,
            'answer': answer,
            'policies_used': [p['title'] for p in policies],
            'created_at': datetime.now().isoformat()
        }
        self.queries.append(query_record)
        
        return answer, [p['title'] for p in policies]
    
    def get_statistics(self):
        """获取统计数据"""
        return {
            'user_count': len(self.users),
            'policy_count': len(self.policies),
            'query_count': len(self.queries)
        }

# 初始化系统
policy_system = PolicySystem()

# 创建必要的目录
temp_dir = os.path.join('static', 'temp')
os.makedirs(temp_dir, exist_ok=True)
print(f"✓ 音频缓存目录: {temp_dir}")

# ========== HTML 模板 ==========

# 登录页面模板
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
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
                <p>普通用户: user2 / user123</p>
            </div>
        </div>
    </div>
</body>
</html>
'''

# 首页模板
INDEX_TEMPLATE = '''
<!DOCTYPE html>
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
        .user-info a { color: #666; text-decoration: none; padding: 5px 10px; border-radius: 4px; }
        .user-info a:hover { background: #f5f5f5; }
        .container {
            max-width: 1200px;
            margin: 30px auto;
            padding: 0 20px;
        }
        .welcome-box {
            background: white;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 30px;
        }
        .features {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
        }
        .feature-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .feature-card h3 {
            color: #1890ff;
            margin-bottom: 10px;
        }
        .feature-card a {
            display: inline-block;
            margin-top: 10px;
            padding: 8px 16px;
            background: #1890ff;
            color: white;
            text-decoration: none;
            border-radius: 4px;
        }
        .stats {
            margin-top: 20px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="logo">政策解读系统</div>
        <div class="user-info">
            <span>欢迎, {{ username }}</span>
            <a href="/digital_human">🤖 数字人助手</a>
            {% if role == "admin" %}
            <a href="/admin">管理面板</a>
            {% endif %}
            <a href="/logout">退出</a>
        </div>
    </div>
    
    <div class="container">
        <div class="welcome-box">
            <h1>欢迎使用政策解读系统！</h1>
            <p>为您提供专业的政策咨询服务</p>
        </div>
        
        <div class="features">
            <div class="feature-card">
                <h3>🤖 数字人助手</h3>
                <p>与智能数字人对话，获取政策解读</p>
                <a href="/digital_human">开始对话</a>
            </div>
            
            <div class="feature-card">
                <h3>📚 政策查询</h3>
                <p>快速查找相关政策信息</p>
                <div class="stats">
                    政策库: {{ stats.policy_count }} 条<br>
                    覆盖3大领域
                </div>
            </div>
            
            <div class="feature-card">
                <h3>📊 系统统计</h3>
                <div class="stats">
                    用户数: {{ stats.user_count }}<br>
                    查询数: {{ stats.query_count }}<br>
                    语音支持: {{ tts_status }}
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

# 数字人页面模板
DIGITAL_HUMAN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>政策数字人助手</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            display: flex;
            gap: 30px;
            max-width: 1200px;
            width: 100%;
        }
        
        /* 左侧：数字人 */
        .avatar-section {
            flex: 1;
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        
        .avatar-container {
            width: 300px;
            height: 400px;
            position: relative;
            margin-bottom: 20px;
        }
        
        .avatar {
            width: 100%;
            height: 100%;
            object-fit: contain;
            border-radius: 10px;
            background: #f5f5f5;
            transition: all 0.3s;
        }
        
        .speech-bubble {
            position: absolute;
            top: -80px;
            left: 50%;
            transform: translateX(-50%);
            background: white;
            padding: 15px 20px;
            border-radius: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            max-width: 300px;
            min-width: 200px;
            display: none;
        }
        
        .speech-bubble::after {
            content: '';
            position: absolute;
            top: 100%;
            left: 50%;
            transform: translateX(-50%);
            border: 10px solid transparent;
            border-top-color: white;
        }
        
        .avatar-status {
            margin-top: 20px;
            padding: 10px 20px;
            background: #e3f2fd;
            border-radius: 20px;
            font-size: 14px;
            color: #1976d2;
        }
        
        /* 右侧：问答区域 */
        .qa-section {
            flex: 1;
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        
        .chat-container {
            height: 400px;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        
        .message {
            margin: 10px 0;
            padding: 12px 16px;
            border-radius: 10px;
            max-width: 80%;
            line-height: 1.5;
        }
        
        .user-message {
            background: #e3f2fd;
            margin-left: auto;
            text-align: right;
        }
        
        .bot-message {
            background: #f5f5f5;
        }
        
        .input-area {
            display: flex;
            gap: 10px;
        }
        
        #question-input {
            flex: 1;
            padding: 12px 15px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
        }
        
        #send-btn {
            padding: 12px 24px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
        }
        
        .quick-questions {
            margin-top: 20px;
        }
        
        .quick-btn {
            margin: 5px;
            padding: 8px 16px;
            background: #f0f0f0;
            border: 1px solid #ddd;
            border-radius: 6px;
            cursor: pointer;
        }
        
        .control-panel {
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        
        .nav-back {
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 6px;
        }
        
        @keyframes talk {
            0% { transform: translateY(0); }
            50% { transform: translateY(-5px); }
            100% { transform: translateY(0); }
        }
        
        @keyframes nod {
            0% { transform: rotate(0deg); }
            50% { transform: rotate(5deg); }
            100% { transform: rotate(0deg); }
        }
        
        @keyframes shake {
            0% { transform: rotate(0deg); }
            33% { transform: rotate(-5deg); }
            66% { transform: rotate(5deg); }
            100% { transform: rotate(0deg); }
        }
        
        .talking { animation: talk 0.5s infinite; }
        .nodding { animation: nod 0.5s; }
        .shaking { animation: shake 0.5s; }
    </style>
</head>
<body>
    <div class="container">
        <!-- 左侧：数字人 -->
        <div class="avatar-section">
            <h2>🤖 政策数字人助手</h2>
            <div class="avatar-container">
                <div id="speech-bubble" class="speech-bubble">
                    <p id="speech-text">您好！请问有什么政策问题？</p>
                </div>
                <img id="avatar" src="https://placehold.co/300x400/667eea/ffffff?text=政策助手" 
                     alt="数字人助手" class="avatar">
            </div>
            <div class="avatar-status" id="avatar-status">状态: 待命中</div>
            
            <div class="control-panel">
                <h4>表情控制</h4>
                <button class="quick-btn" onclick="animateAvatar('nod')">点头</button>
                <button class="quick-btn" onclick="animateAvatar('shake')">摇头</button>
                <button class="quick-btn" onclick="animateAvatar('talking')">说话</button>
                <button class="quick-btn" onclick="animateAvatar('thinking')">思考</button>
            </div>
        </div>
        
        <!-- 右侧：问答区域 -->
        <div class="qa-section">
            <h2>💬 政策问答</h2>
            
            <div class="chat-container" id="chat-container">
                <div class="message bot-message">
                    <strong>数字人助手：</strong><br>
                    您好！我是政策解读数字人助手，可以为您提供专业的政策咨询服务。
                </div>
            </div>
            
            <div class="input-area">
                <input type="text" id="question-input" placeholder="请输入您的问题...">
                <button id="send-btn" onclick="sendQuestion()">发送</button>
            </div>
            
            <div class="quick-questions">
                <p>快捷提问：</p>
                <button class="quick-btn" onclick="quickAsk('高新技术企业有什么税收优惠？')">高新技术企业</button>
                <button class="quick-btn" onclick="quickAsk('研发费用如何加计扣除？')">研发费用</button>
                <button class="quick-btn" onclick="quickAsk('小微企业有哪些税收政策？')">小微企业</button>
            </div>
            
            <a href="/" class="nav-back">返回主页</a>
        </div>
    </div>

    <script>
        // 数字人状态
        let avatarState = 'idle';
        let currentAudio = null;
        let audioFiles = {}; // 存储已生成的音频
        
        // 获取DOM元素
        const avatar = document.getElementById('avatar');
        const speechBubble = document.getElementById('speech-bubble');
        const speechText = document.getElementById('speech-text');
        const avatarStatus = document.getElementById('avatar-status');
        const chatContainer = document.getElementById('chat-container');
        
        // 更新数字人状态
        function updateAvatarStatus(status, message = '') {
            avatarState = status;
            const statusMessages = {
                'idle': '待命中',
                'talking': '正在说话',
                'thinking': '正在思考',
                'listening': '正在聆听'
            };
            
            avatarStatus.textContent = `状态: ${statusMessages[status] || status}`;
            
            if (message) {
                speechText.textContent = message;
                speechBubble.style.display = 'block';
                
                // 5秒后隐藏气泡
                setTimeout(() => {
                    if (avatarState === 'talking') return;
                    speechBubble.style.display = 'none';
                }, 5000);
            }
        }
        
        // 数字人动画
        function animateAvatar(animation) {
            avatar.className = 'avatar';
            
            switch(animation) {
                case 'talking':
                    avatar.classList.add('talking');
                    updateAvatarStatus('talking');
                    break;
                case 'thinking':
                    avatar.classList.add('nodding');
                    updateAvatarStatus('thinking');
                    setTimeout(() => avatar.classList.remove('nodding'), 500);
                    break;
                case 'nod':
                    avatar.classList.add('nodding');
                    setTimeout(() => avatar.classList.remove('nodding'), 500);
                    break;
                case 'shake':
                    avatar.classList.add('shaking');
                    setTimeout(() => avatar.classList.remove('shaking'), 500);
                    break;
                default:
                    avatar.classList.remove('talking', 'nodding', 'shaking');
                    updateAvatarStatus('idle');
            }
        }
        
        // 播放语音
        function playSpeech(text) {
            // 停止当前语音
            if (currentAudio) {
                currentAudio.pause();
                currentAudio = null;
            }
            
            // 更新数字人状态
            updateAvatarStatus('talking', text);
            animateAvatar('talking');
            
            // 发送到后端生成语音
            fetch('/api/digital_human/speak', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text: text})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success && data.audio_url) {
                    console.log('音频URL:', data.audio_url);
                    
                    // 播放音频
                    currentAudio = new Audio(data.audio_url);
                    currentAudio.play().catch(error => {
                        console.log('音频播放失败:', error);
                        // 如果播放失败，3秒后停止动画
                        setTimeout(() => {
                            animateAvatar('idle');
                            updateAvatarStatus('idle');
                        }, 3000);
                    });
                    
                    // 音频播放结束
                    currentAudio.onended = () => {
                        animateAvatar('idle');
                        updateAvatarStatus('idle');
                        currentAudio = null;
                    };
                    
                    // 音频播放错误处理
                    currentAudio.onerror = (error) => {
                        console.log('音频播放错误:', error);
                        animateAvatar('idle');
                        updateAvatarStatus('idle');
                        currentAudio = null;
                    };
                } else {
                    console.log('语音生成失败，使用文本显示');
                    // 如果没有语音，3秒后停止说话动画
                    setTimeout(() => {
                        animateAvatar('idle');
                        updateAvatarStatus('idle');
                    }, 3000);
                }
            })
            .catch(error => {
                console.error('请求语音失败:', error);
                // 出错时3秒后停止动画
                setTimeout(() => {
                    animateAvatar('idle');
                    updateAvatarStatus('idle');
                }, 3000);
            });
        }
        
        // 添加消息到聊天框
        function addMessage(text, isUser) {
            const messageDiv = document.createElement('div');
            messageDiv.className = isUser ? 'message user-message' : 'message bot-message';
            messageDiv.innerHTML = `<strong>${isUser ? '您' : '数字人助手'}：</strong><br>${text}`;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        // 快速提问
        function quickAsk(question) {
            document.getElementById('question-input').value = question;
            sendQuestion();
        }
        
        // 发送问题
        function sendQuestion() {
            const input = document.getElementById('question-input');
            const question = input.value.trim();
            
            if (!question) return;
            
            // 添加到聊天框
            addMessage(question, true);
            input.value = '';
            
            // 显示思考状态
            updateAvatarStatus('thinking', '正在思考中...');
            animateAvatar('thinking');
            
            // 发送到后端
            fetch('/ask', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({question: question})
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    addMessage('错误: ' + data.error, false);
                    animateAvatar('idle');
                } else {
                    // 显示回答
                    addMessage(data.answer, false);
                    
                    // 让数字人说话
                    playSpeech(data.answer);
                }
            })
            .catch(error => {
                addMessage('请求失败，请重试', false);
                animateAvatar('idle');
            });
        }
        
        // 初始状态
        updateAvatarStatus('idle', '您好！请问有什么政策问题？');
        
        // 监听回车键
        document.getElementById('question-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendQuestion();
        });
        
        // 页面卸载时清理
        window.addEventListener('beforeunload', function() {
            if (currentAudio) {
                currentAudio.pause();
            }
        });
    </script>
</body>
</html>
'''

# 管理面板模板
ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>管理面板</title>
    <style>
        body { font-family: Arial; padding: 20px; }
        .stats { display: flex; gap: 20px; margin: 20px 0; }
        .stat { padding: 20px; background: white; border-radius: 8px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
        th { background: #f5f5f5; }
    </style>
</head>
<body>
    <h1>管理面板</h1>
    <p>用户: {{ username }}</p>
    
    <div class="stats">
        <div class="stat">用户数: {{ stats.user_count }}</div>
        <div class="stat">政策数: {{ stats.policy_count }}</div>
        <div class="stat">总查询: {{ stats.query_count }}</div>
    </div>
    
    <h3>最近查询记录</h3>
    <table>
        <tr><th>用户</th><th>问题</th><th>回答摘要</th><th>时间</th></tr>
        {% for query in queries %}
        <tr>
            <td>{{ query.username }}</td>
            <td>{{ query.question[:50] }}{% if query.question|length > 50 %}...{% endif %}</td>
            <td>{{ query.answer[:50] }}{% if query.answer|length > 50 %}...{% endif %}</td>
            <td>{{ query.created_at[:19] }}</td>
        </tr>
        {% endfor %}
    </table>
    
    <p><a href="/">返回首页</a></p>
</body>
</html>
'''

# ========== 路由定义 ==========

# 首页
@app.route('/')
def index():
    if 'username' not in session:
        return redirect('/login')
    
    user = policy_system.users.get(session['username'], {})
    stats = policy_system.get_statistics()
    tts_status = '已启用' if TTS_AVAILABLE else '未启用'
    
    return render_template_string(
        INDEX_TEMPLATE,
        username=session['username'],
        role=user.get('role', 'user'),
        stats=stats,
        tts_status=tts_status
    )

# 数字人页面
@app.route('/digital_human')
def digital_human_page():
    if 'username' not in session:
        return redirect('/login')
    
    return render_template_string(DIGITAL_HUMAN_TEMPLATE)

# 登录页面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            return render_template_string(LOGIN_TEMPLATE, error='用户名和密码不能为空')
        
        user = policy_system.verify_user(username, password)
        if user:
            session['username'] = username
            session['user_id'] = user['id']
            session['role'] = user['role']
            return redirect('/')
        
        return render_template_string(LOGIN_TEMPLATE, error='用户名或密码错误')
    
    return render_template_string(LOGIN_TEMPLATE)

# 退出登录
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# 问答接口
@app.route('/ask', methods=['POST'])
def ask():
    if 'username' not in session:
        return jsonify({'error': '请先登录'}), 401
    
    data = request.get_json()
    question = data.get('question', '').strip()
    
    if not question:
        return jsonify({'error': '问题不能为空'}), 400
    
    answer, policies_used = policy_system.answer_question(question, session['username'])
    
    return jsonify({
        'success': True,
        'answer': answer,
        'policies_used': policies_used
    })

# 数字人语音接口
@app.route('/api/digital_human/speak', methods=['POST'])
def digital_human_speak():
    """数字人说话接口"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': '文本不能为空'}), 400
    
    # 生成语音文件
    if TTS_AVAILABLE and policy_system.digital_human.tts_engine:
        try:
            # 创建临时文件
            filename = f"{uuid.uuid4().hex}.mp3"
            temp_audio_path = os.path.join(tempfile.gettempdir(), filename)
            
            # 生成语音
            result = policy_system.digital_human.speak_text(text, temp_audio_path)
            
            if result and os.path.exists(result):
                # 目标路径
                target_path = os.path.join(temp_dir, filename)
                
                # 确保目录存在
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                
                # 复制到静态目录
                try:
                    shutil.copy2(result, target_path)
                except Exception as copy_error:
                    print(f"复制文件失败: {copy_error}")
                    # 如果复制失败，使用原始文件
                    target_path = result
                
                # 返回正确的URL
                audio_url = f'/static/temp/{filename}'
                
                return jsonify({
                    'success': True,
                    'text': text,
                    'audio_url': audio_url,
                    'timestamp': datetime.now().isoformat()
                })
        except Exception as e:
            print(f"语音生成异常: {e}")
    
    return jsonify({
        'success': False,
        'text': text,
        'message': '语音生成失败，使用文本显示',
        'timestamp': datetime.now().isoformat()
    })

# 静态文件服务
@app.route('/static/temp/<filename>')
def serve_audio(filename):
    """提供生成的音频文件"""
    try:
        # 正确构建路径
        filepath = os.path.join(temp_dir, filename)
        
        # 确保路径存在
        if os.path.exists(filepath):
            return send_file(filepath, mimetype='audio/mpeg')
        
        # 如果在temp目录中找不到，尝试在系统temp中找
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        if os.path.exists(temp_path):
            return send_file(temp_path, mimetype='audio/mpeg')
        
        print(f"音频文件不存在: {filepath}")
        return '音频文件不存在', 404
    except Exception as e:
        print(f"提供音频文件时出错: {e}")
        return f'服务器错误: {str(e)}', 500

# 清理临时音频文件
def cleanup_temp_audio(hours_old=1):
    """清理旧的音频文件"""
    try:
        current_time = time.time()
        for filename in os.listdir(temp_dir):
            filepath = os.path.join(temp_dir, filename)
            if os.path.isfile(filepath) and filepath.endswith('.mp3'):
                # 获取文件修改时间
                file_mtime = os.path.getmtime(filepath)
                # 如果文件超过指定小时，删除
                if current_time - file_mtime > hours_old * 3600:
                    try:
                        os.remove(filepath)
                        print(f"清理旧文件: {filename}")
                    except Exception as e:
                        print(f"清理文件失败 {filename}: {e}")
    except Exception as e:
        print(f"清理临时文件时出错: {e}")

# 管理面板
@app.route('/admin')
def admin():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect('/')
    
    stats = policy_system.get_statistics()
    recent_queries = policy_system.queries[-20:][::-1]
    
    return render_template_string(
        ADMIN_TEMPLATE,
        username=session['username'],
        stats=stats,
        queries=recent_queries
    )

# 主函数
if __name__ == '__main__':
    print("=" * 60)
    print("政策数字人解读系统 - 修复版")
    print("=" * 60)
    print("🎯 系统功能:")
    print("1. ✓ 政策问答系统 (3个政策领域)")
    print("2. ✓ 用户登录认证 (3个测试账号)")
    print("3. ✓ 数字人交互界面 (动画+语音)")
    print("4. ✓ 语音合成功能" if TTS_AVAILABLE else "4. ⚠ 语音功能未启用")
    print("5. ✓ 管理面板")
    print("\n🔐 测试账号:")
    print("管理员: admin / admin123")
    print("普通用户: user1 / user123")
    print("普通用户: user2 / user123")
    print("\n📚 政策库:")
    for policy in POLICIES:
        print(f"- {policy['title']} ({policy['source']})")
    print("\n🌐 访问地址:")
    print("主页: http://localhost:5015")
    print("数字人: http://localhost:5015/digital_human")
    print("登录页: http://localhost:5015/login")
    print("\n💡 使用说明:")
    print("1. 访问登录页面输入账号密码")
    print("2. 进入主页后点击'数字人助手'")
    print("3. 输入问题或使用快捷提问")
    print("4. 数字人将语音回答并显示文字")
    print("\n🔧 修复内容:")
    print("- 修复Windows路径分隔符问题")
    print("- 优化音频文件处理")
    print("- 增加错误处理机制")
    print("=" * 60)
    
    # 启动时清理旧的临时文件
    cleanup_temp_audio()
    
    app.run(debug=True, port=5015, host='0.0.0.0')