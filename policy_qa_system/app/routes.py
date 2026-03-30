from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from .models import init_db, add_policy, get_all_policies, get_policy_by_id, delete_policy, add_user, get_user_by_username, get_user_by_id, hash_password, get_all_categories, add_category, get_all_tags, add_tag, add_policy_tag, get_policy_tags, add_user_history, get_user_history, add_user_favorite, remove_user_favorite, get_user_favorites, is_favorite, get_all_users, update_user_role, get_statistics, update_user_nickname, get_unique_nickname, add_forum_topic, get_all_forum_topics, get_forum_topic_by_id, add_forum_reply, get_forum_replies, delete_forum_topic, delete_forum_reply, ban_user, unban_user
from .rag import create_rag_db, generate_answer, policy_interpretation, policy_recommendation, multi_turn_chat, policy_comparison
import os

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'), static_folder=os.path.join(BASE_DIR, 'css'))
app.secret_key = 'your-secret-key-here'  # 用于 session 管理

init_db()

# 静态文件路由
@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'css'), filename)

@app.route('/')
def index():
    if not is_logged_in():
        return redirect(url_for('login'))
    
    user = get_user_by_id(session['user_id'])
    user_info = {
        'username': user['username'],
        'nickname': user['nickname'],
        'role': user['role'],
        'region': user['region']
    }
    return render_template('index.html', user_info=user_info)

# 辅助函数
def is_logged_in():
    return 'user_id' in session

def is_admin():
    if not is_logged_in():
        return False
    user = get_user_by_id(session['user_id'])
    return user and user['role'] == 'admin'

# 登录相关路由
@app.route('/login')
def login():
    if is_logged_in():
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    
    user = get_user_by_username(username)
    if user and user['password'] == hash_password(password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['region'] = user['region']
        
        # 如果是管理员，跳转到管理后台
        if user['role'] == 'admin':
            return redirect(url_for('admin'))
        # 如果是普通用户，跳转到首页
        return redirect(url_for('index'))
    
    return render_template('login.html', error='用户名或密码错误')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if is_logged_in():
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        region = request.form.get('region')
        
        if not username or not password:
            return render_template('login.html', error='用户名和密码不能为空')
        
        user_id = add_user(username, password, 'user', region)
        if user_id:
            # 注册成功后自动登录
            user = get_user_by_id(user_id)
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['region'] = user['region']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='用户名已存在')
    
    return render_template('login.html', is_register=True)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    if not is_admin():
        return redirect(url_for('login'))
    
    user_info = {
        'username': session.get('username'),
        'role': session.get('role'),
        'region': session.get('region')
    }
    return render_template('admin.html', user_info=user_info)

@app.route('/api/policies', methods=['GET'])
def api_get_policies():
    policies = get_all_policies()
    return jsonify(policies)



@app.route('/api/policies/<int:policy_id>', methods=['GET'])
def api_get_policy(policy_id):
    policy = get_policy_by_id(policy_id)
    if policy:
        return jsonify(policy)
    return jsonify({'error': '政策未找到'}), 404

@app.route('/api/policies/<int:policy_id>', methods=['DELETE'])
def api_delete_policy(policy_id):
    delete_policy(policy_id)
    return jsonify({'message': '政策删除成功'})

@app.route('/api/rag/build', methods=['POST'])
def api_build_rag():
    try:
        count = create_rag_db()
        return jsonify({'message': f'RAG 数据库构建成功，共处理 {count} 个文本片段'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/qa', methods=['POST'])
def api_qa():
    if not is_logged_in():
        return jsonify({'error': '请先登录'}), 401
    
    data = request.json
    question = data.get('question')
    
    if not question:
        return jsonify({'error': '问题不能为空'}), 400
    
    answer, chunks = generate_answer(question)
    
    # 添加用户历史记录
    add_user_history(session['user_id'], question, answer)
    
    return jsonify({'answer': answer, 'chunks': chunks})

# 个人中心路由
@app.route('/profile')
def profile():
    if not is_logged_in():
        return redirect(url_for('login'))
    
    user_info = {
        'username': session.get('username'),
        'role': session.get('role'),
        'region': session.get('region')
    }
    
    # 获取用户历史记录
    history = get_user_history(session['user_id'])
    
    # 获取用户收藏
    favorites = get_user_favorites(session['user_id'])
    
    return render_template('profile.html', user_info=user_info, history=history, favorites=favorites)

# 收藏相关API
@app.route('/api/favorite', methods=['POST'])
def api_add_favorite():
    if not is_logged_in():
        return jsonify({'error': '请先登录'}), 401
    
    data = request.json
    policy_id = data.get('policy_id')
    
    if not policy_id:
        return jsonify({'error': '政策ID不能为空'}), 400
    
    success = add_user_favorite(session['user_id'], policy_id)
    return jsonify({'success': success, 'message': '收藏成功' if success else '已经收藏过'})

@app.route('/api/favorite/<int:policy_id>', methods=['DELETE'])
def api_remove_favorite(policy_id):
    if not is_logged_in():
        return jsonify({'error': '请先登录'}), 401
    
    remove_user_favorite(session['user_id'], policy_id)
    return jsonify({'success': True, 'message': '取消收藏成功'})

# 分类和标签相关API
@app.route('/api/categories', methods=['GET'])
def api_get_categories():
    categories = get_all_categories()
    return jsonify(categories)

@app.route('/api/categories', methods=['POST'])
def api_add_category():
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    data = request.json
    name = data.get('name')
    description = data.get('description')
    
    if not name:
        return jsonify({'error': '分类名称不能为空'}), 400
    
    category_id = add_category(name, description)
    if category_id:
        return jsonify({'success': True, 'id': category_id, 'message': '分类添加成功'})
    else:
        return jsonify({'error': '分类已存在'}), 400

@app.route('/api/tags', methods=['GET'])
def api_get_tags():
    tags = get_all_tags()
    return jsonify(tags)

@app.route('/api/tags', methods=['POST'])
def api_add_tag():
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    data = request.json
    name = data.get('name')
    
    if not name:
        return jsonify({'error': '标签名称不能为空'}), 400
    
    tag_id = add_tag(name)
    return jsonify({'success': True, 'id': tag_id, 'message': '标签添加成功'})

# 用户管理相关API
@app.route('/api/users', methods=['GET'])
def api_get_users():
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    users = get_all_users()
    return jsonify(users)

@app.route('/api/users/<int:user_id>/role', methods=['PUT'])
def api_update_user_role(user_id):
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    data = request.json
    role = data.get('role')
    
    if not role or role not in ['user', 'admin']:
        return jsonify({'error': '角色类型不正确'}), 400
    
    update_user_role(user_id, role)
    return jsonify({'success': True, 'message': '角色更新成功'})

# 数据统计相关API
@app.route('/api/statistics', methods=['GET'])
def api_get_statistics():
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    stats = get_statistics()
    return jsonify(stats)

# 修改添加政策API，支持分类和标签
@app.route('/api/policies', methods=['POST'])
def api_add_policy():
    data = request.json
    title = data.get('title')
    content = data.get('content')
    source_url = data.get('source_url')
    publish_date = data.get('publish_date')
    category_id = data.get('category_id')
    tags = data.get('tags', [])
    
    if not title or not content:
        return jsonify({'error': '标题和内容不能为空'}), 400
    
    policy_id = add_policy(title, content, source_url, publish_date, category_id)
    
    # 添加标签
    for tag_name in tags:
        if tag_name:
            tag_id = add_tag(tag_name)
            if tag_id:
                add_policy_tag(policy_id, tag_id)
    
    return jsonify({'id': policy_id, 'message': '政策添加成功'})

# 政策解读API
@app.route('/api/policy/interpretation/<int:policy_id>', methods=['GET'])
def api_policy_interpretation(policy_id):
    interpretation = policy_interpretation(policy_id)
    return jsonify({'interpretation': interpretation})

# 政策推荐API
@app.route('/api/policy/recommendation', methods=['GET'])
def api_policy_recommendation():
    user_id = session.get('user_id') if is_logged_in() else None
    region = session.get('region') if is_logged_in() else None
    recommendation = policy_recommendation(user_id, region)
    return jsonify({'recommendation': recommendation})

# 多轮对话API
@app.route('/api/chat/multi-turn', methods=['POST'])
def api_multi_turn_chat():
    data = request.json
    messages = data.get('messages', [])
    if not messages:
        return jsonify({'error': '消息不能为空'}), 400
    response = multi_turn_chat(messages)
    return jsonify({'response': response})

# 政策对比API
@app.route('/api/policy/comparison', methods=['POST'])
def api_policy_comparison():
    data = request.json
    policy_ids = data.get('policy_ids', [])
    if not policy_ids or len(policy_ids) < 2:
        return jsonify({'error': '至少需要两个政策进行对比'}), 400
    comparison = policy_comparison(policy_ids)
    return jsonify({'comparison': comparison})

# 昵称设置API
@app.route('/api/profile/nickname', methods=['PUT'])
def api_update_nickname():
    if not is_logged_in():
        return jsonify({'error': '请先登录'}), 401
    
    data = request.json
    nickname = data.get('nickname')
    
    if not nickname:
        return jsonify({'error': '昵称不能为空'}), 400
    
    update_user_nickname(session['user_id'], nickname)
    return jsonify({'success': True, 'message': '昵称更新成功'})

# 讨论广场路由
@app.route('/forum')
def forum():
    user_info = None
    if is_logged_in():
        user = get_user_by_id(session['user_id'])
        user_info = {
            'username': user['username'],
            'nickname': user['nickname'],
            'role': user['role'],
            'region': user['region'],
            'ban_until': user['ban_until'],
            'is_banned': user['is_banned']
        }
    
    # 获取所有讨论主题
    topics = get_all_forum_topics()
    
    return render_template('forum.html', user_info=user_info, topics=topics)

@app.route('/forum/topic/<int:topic_id>')
def forum_topic(topic_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    
    user = get_user_by_id(session['user_id'])
    user_info = {
        'username': user['username'],
        'nickname': user['nickname'],
        'role': user['role'],
        'region': user['region'],
        'ban_until': user['ban_until'],
        'is_banned': user['is_banned']
    }
    
    # 获取主题信息
    topic = get_forum_topic_by_id(topic_id)
    if not topic:
        return redirect(url_for('forum'))
    
    # 获取回复列表
    replies = get_forum_replies(topic_id)
    
    return render_template('forum_topic.html', user_info=user_info, topic=topic, replies=replies)

# 讨论广场API
@app.route('/api/forum/topics', methods=['POST'])
def api_add_forum_topic():
    if not is_logged_in():
        return jsonify({'error': '请先登录'}), 401
    
    user = get_user_by_id(session['user_id'])
    if user['is_banned'] or user['ban_until']:
        return jsonify({'error': '您已被封禁，无法发布内容'}), 403
    
    if not user['nickname']:
        # 自动生成昵称
        nickname = get_unique_nickname()
        update_user_nickname(session['user_id'], nickname)
    
    data = request.json
    title = data.get('title')
    content = data.get('content')
    
    if not title or not content:
        return jsonify({'error': '标题和内容不能为空'}), 400
    
    topic_id = add_forum_topic(session['user_id'], title, content)
    return jsonify({'success': True, 'topic_id': topic_id, 'message': '主题发布成功'})

@app.route('/api/forum/topics/<int:topic_id>/replies', methods=['POST'])
def api_add_forum_reply(topic_id):
    if not is_logged_in():
        return jsonify({'error': '请先登录'}), 401
    
    user = get_user_by_id(session['user_id'])
    if user['is_banned'] or user['ban_until']:
        return jsonify({'error': '您已被封禁，无法回复内容'}), 403
    
    if not user['nickname']:
        # 自动生成昵称
        nickname = get_unique_nickname()
        update_user_nickname(session['user_id'], nickname)
    
    data = request.json
    content = data.get('content')
    
    if not content:
        return jsonify({'error': '回复内容不能为空'}), 400
    
    reply_id = add_forum_reply(topic_id, session['user_id'], content)
    return jsonify({'success': True, 'reply_id': reply_id, 'message': '回复成功'})

# 讨论广场管理API
@app.route('/api/forum/topics/<int:topic_id>', methods=['DELETE'])
def api_delete_forum_topic(topic_id):
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    delete_forum_topic(topic_id)
    return jsonify({'success': True, 'message': '主题删除成功'})

@app.route('/api/forum/replies/<int:reply_id>', methods=['DELETE'])
def api_delete_forum_reply(reply_id):
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    delete_forum_reply(reply_id)
    return jsonify({'success': True, 'message': '回复删除成功'})

# 用户封禁API
@app.route('/api/users/<int:user_id>/ban', methods=['POST'])
def api_ban_user(user_id):
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    data = request.json
    ban_type = data.get('ban_type')  # 'temporary' 或 'permanent'
    ban_duration = data.get('ban_duration')  # 临时封禁时长（小时）
    
    if ban_type == 'permanent':
        ban_user(user_id, is_permanent=True)
        return jsonify({'success': True, 'message': '用户已被永久封禁'})
    else:
        # 计算封禁截止时间
        import datetime
        ban_until = (datetime.datetime.now() + datetime.timedelta(hours=ban_duration)).isoformat()
        ban_user(user_id, ban_until=ban_until)
        return jsonify({'success': True, 'message': f'用户已被封禁 {ban_duration} 小时'})

@app.route('/api/users/<int:user_id>/unban', methods=['POST'])
def api_unban_user(user_id):
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    unban_user(user_id)
    return jsonify({'success': True, 'message': '用户封禁已解除'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
