from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import BASE_DIR, SECRET_KEY
from app.models import init_db
from app.rag import create_rag_db, generate_answer, policy_interpretation, policy_recommendation, multi_turn_chat, policy_comparison

# 服务层
from app.services.user_service import UserService
from app.services.policy_service import PolicyService
from app.services.forum_service import ForumService
from app.services.user_history_service import UserHistoryService, UserFavoriteService
from app.services.expert_service import ExpertService
from app.services.public_voice_service import PublicVoiceService
from app.services.statistics_service import StatisticsService

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'), static_folder=os.path.join(BASE_DIR, 'css'))
app.secret_key = SECRET_KEY  # 用于 session 管理

init_db()

# 静态文件路由
@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'css'), filename)

@app.route('/')
def index():
    user_info = None
    if is_logged_in():
        user = UserService.get_user_by_id(session['user_id'])
        user_info = {
            'username': user['username'],
            'nickname': user['nickname'],
            'role': user['role'],
            'region': user['region'],
            'is_expert': user['is_expert']
        }
    
    # 获取最新政策（最多10条）
    policies = PolicyService.get_all_policies()[:10]
    
    # 获取已批准的专家解读（最多10条）
    interpretations = ExpertService.get_approved_interpretations(limit=10)
    
    # 获取民声内容（最多10条）
    voices = PublicVoiceService.get_public_voices(limit=10)
    
    return render_template('index.html', user_info=user_info, policies=policies, interpretations=interpretations, voices=voices)

# 辅助函数
def is_logged_in():
    return 'user_id' in session

def is_admin():
    if not is_logged_in():
        return False
    user = UserService.get_user_by_id(session['user_id'])
    return user and user['role'] == 'admin'

# 登录相关路由
@app.route('/login')
def login():
    if is_logged_in():
        redirect_url = request.args.get('redirect', '/')
        return redirect(redirect_url)
    redirect_url = request.args.get('redirect', '/')
    return render_template('login.html', redirect_url=redirect_url)



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
        
        user_id = UserService.create_user(username, password, 'user', region)
        if user_id:
            # 注册成功后自动登录
            user = UserService.get_user_by_id(user_id)
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['region'] = user['region']
            session['is_expert'] = user['is_expert']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='用户名已存在')
    
    return render_template('login.html', is_register=True)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/search')
def search():
    if not is_logged_in():
        return redirect(url_for('login', redirect='/search'))
    
    query = request.args.get('q', '').strip()
    user_info = None
    if is_logged_in():
        user = UserService.get_user_by_id(session['user_id'])
        user_info = {
            'username': user['username'],
            'nickname': user['nickname'],
            'role': user['role'],
            'region': user['region'],
            'is_expert': user['is_expert']
        }
    
    results = []
    if query:
        # 获取所有政策
        policies = PolicyService.get_all_policies()
        
        # 简单的搜索逻辑：计算匹配度并排序
        for policy in policies:
            # 计算匹配度
            title_match = 0
            content_match = 0
            
            if query.lower() in policy['title'].lower():
                title_match = 1.0
            
            if query.lower() in policy['content'].lower():
                content_match = 0.5
            
            # 综合得分 = 匹配度 * 0.7 + 浏览量权重 * 0.3
            view_count = policy.get('view_count', 0)
            max_view = max([p.get('view_count', 0) for p in policies]) if policies else 1
            view_score = view_count / max_view if max_view > 0 else 0
            
            score = (title_match + content_match) * 0.7 + view_score * 0.3
            
            if score > 0:
                # 生成摘要，高亮关键词
                summary = policy['content'][:200]
                if query.lower() in summary.lower():
                    summary = summary.replace(query, f'<span class="highlight">{query}</span>', 1)
                
                results.append({
                    'id': policy['id'],
                    'title': policy['title'],
                    'content': policy['content'],
                    'publish_date': policy.get('publish_date'),
                    'view_count': view_count,
                    'score': score * 100,
                    'summary': summary
                })
        
        # 按得分从高到低排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # 记录搜索历史
        from app.models import add_user_search_history
        add_user_search_history(session['user_id'], query, len(results))
    
    return render_template('search.html', user_info=user_info, query=query, results=results)

@app.route('/admin')
def admin():
    if not is_admin():
        return redirect(url_for('login'))
    
    user_info = {
        'username': session.get('username'),
        'role': session.get('role'),
        'region': session.get('region')
    }
    return render_template('admin_index.html', user_info=user_info)

@app.route('/admin/policies')
def admin_policies():
    if not is_admin():
        return redirect(url_for('login'))
    
    user_info = {
        'username': session.get('username'),
        'role': session.get('role'),
        'region': session.get('region')
    }
    return render_template('admin_policies.html', user_info=user_info)

@app.route('/admin/categories')
def admin_categories():
    if not is_admin():
        return redirect(url_for('login'))
    
    user_info = {
        'username': session.get('username'),
        'role': session.get('role'),
        'region': session.get('region')
    }
    return render_template('admin_categories.html', user_info=user_info)

@app.route('/admin/tags')
def admin_tags():
    if not is_admin():
        return redirect(url_for('login'))
    
    user_info = {
        'username': session.get('username'),
        'role': session.get('role'),
        'region': session.get('region')
    }
    return render_template('admin_tags.html', user_info=user_info)

@app.route('/admin/users')
def admin_users():
    if not is_admin():
        return redirect(url_for('login'))
    
    user_info = {
        'username': session.get('username'),
        'role': session.get('role'),
        'region': session.get('region')
    }
    return render_template('admin_users.html', user_info=user_info)

@app.route('/admin/experts')
def admin_experts():
    if not is_admin():
        return redirect(url_for('login'))
    
    user_info = {
        'username': session.get('username'),
        'role': session.get('role'),
        'region': session.get('region')
    }
    return render_template('admin_experts.html', user_info=user_info)

@app.route('/admin/interpretations')
def admin_interpretations():
    if not is_admin():
        return redirect(url_for('login'))
    
    user_info = {
        'username': session.get('username'),
        'role': session.get('role'),
        'region': session.get('region')
    }
    return render_template('admin_interpretations.html', user_info=user_info)

@app.route('/admin/public-voice')
def admin_public_voice():
    if not is_admin():
        return redirect(url_for('login'))
    
    user_info = {
        'username': session.get('username'),
        'role': session.get('role'),
        'region': session.get('region')
    }
    return render_template('admin_public_voice.html', user_info=user_info)

@app.route('/admin/statistics')
def admin_statistics():
    if not is_admin():
        return redirect(url_for('login'))
    
    user_info = {
        'username': session.get('username'),
        'role': session.get('role'),
        'region': session.get('region')
    }
    return render_template('admin_statistics.html', user_info=user_info)

@app.route('/admin/rag')
def admin_rag():
    if not is_admin():
        return redirect(url_for('login'))
    
    user_info = {
        'username': session.get('username'),
        'role': session.get('role'),
        'region': session.get('region')
    }
    return render_template('admin_rag.html', user_info=user_info)

@app.route('/api/policies', methods=['GET'])
def api_get_policies():
    from datetime import datetime, timedelta
    
    policies = PolicyService.get_all_policies()
    
    category_id = request.args.get('category_id')
    time_filter = request.args.get('time_filter')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 确保分页参数有效
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 10
    
    if category_id:
        policies = [p for p in policies if str(p.get('category_id', '')) == category_id]
    
    if time_filter:
        now = datetime.now()
        if time_filter == 'today':
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_filter == 'week':
            start = now - timedelta(days=7)
        elif time_filter == 'month':
            start = now - timedelta(days=30)
        elif time_filter == 'quarter':
            start = now - timedelta(days=90)
        elif time_filter == 'year':
            start = now - timedelta(days=365)
        else:
            start = None
        
        if start:
            filtered = []
            for p in policies:
                try:
                    created = datetime.fromisoformat(p['created_at'])
                    if created >= start:
                        filtered.append(p)
                except:
                    pass
            policies = filtered
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            filtered = []
            for p in policies:
                try:
                    created = datetime.fromisoformat(p['created_at'])
                    if created >= start_dt:
                        filtered.append(p)
                except:
                    pass
            policies = filtered
        except:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date) + timedelta(days=1)
            filtered = []
            for p in policies:
                try:
                    created = datetime.fromisoformat(p['created_at'])
                    if created < end_dt:
                        filtered.append(p)
                except:
                    pass
            policies = filtered
        except:
            pass
    
    # 计算总页数
    total = len(policies)
    total_pages = (total + per_page - 1) // per_page
    
    # 分页
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_policies = policies[start_idx:end_idx]
    
    return jsonify({
        'policies': paginated_policies,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages
        }
    })




@app.route('/api/policies/<int:policy_id>', methods=['GET'])
def api_get_policy(policy_id):
    policy = PolicyService.get_policy_by_id(policy_id)
    if policy:
        return jsonify(policy)
    return jsonify({'error': '政策未找到'}), 404

@app.route('/api/policies/<int:policy_id>', methods=['DELETE'])
def api_delete_policy(policy_id):
    PolicyService.delete_policy(policy_id)
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
    history = UserHistoryService.get_user_history(session['user_id'])
    
    # 获取用户收藏
    favorites = UserFavoriteService.get_user_favorites(session['user_id'])
    
    # 获取用户搜索历史
    from app.models import get_user_search_history
    search_history = get_user_search_history(session['user_id'])
    
    # 获取用户在讨论广场发布的主题
    from app.models import get_user_forum_topics
    forum_topics = get_user_forum_topics(session['user_id'])
    
    # 获取用户在讨论广场发布的回复
    from app.models import get_user_forum_replies
    forum_replies = get_user_forum_replies(session['user_id'])
    
    return render_template('profile.html', user_info=user_info, history=history, favorites=favorites, 
                          search_history=search_history, forum_topics=forum_topics, forum_replies=forum_replies)

# 收藏相关API
@app.route('/api/favorite', methods=['POST'])
def api_add_favorite():
    if not is_logged_in():
        return jsonify({'error': '请先登录'}), 401
    
    data = request.json
    policy_id = data.get('policy_id')
    
    if not policy_id:
        return jsonify({'error': '政策ID不能为空'}), 400
    
    success = UserFavoriteService.add_favorite(session['user_id'], policy_id)
    return jsonify({'success': success, 'message': '收藏成功' if success else '已经收藏过'})

@app.route('/api/favorite/<int:policy_id>', methods=['DELETE'])
def api_remove_favorite(policy_id):
    if not is_logged_in():
        return jsonify({'error': '请先登录'}), 401
    
    UserFavoriteService.remove_favorite(session['user_id'], policy_id)
    return jsonify({'success': True, 'message': '取消收藏成功'})

# 分类和标签相关API
@app.route('/api/categories', methods=['GET'])
def api_get_categories():
    categories = PolicyService.get_all_categories()
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
    
    category_id = PolicyService.create_category(name, description)
    if category_id:
        return jsonify({'success': True, 'id': category_id, 'message': '分类添加成功'})
    else:
        return jsonify({'error': '分类已存在'}), 400

@app.route('/api/tags', methods=['GET'])
def api_get_tags():
    tags = PolicyService.get_all_tags()
    return jsonify(tags)

@app.route('/api/tags', methods=['POST'])
def api_add_tag():
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    data = request.json
    name = data.get('name')
    
    if not name:
        return jsonify({'error': '标签名称不能为空'}), 400
    
    tag_id = PolicyService.create_tag(name)
    return jsonify({'success': True, 'id': tag_id, 'message': '标签添加成功'})

# 用户管理相关API
@app.route('/api/users', methods=['GET'])
def api_get_users():
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    users = UserService.get_all_users()
    return jsonify(users)

@app.route('/api/users/<int:user_id>/role', methods=['PUT'])
def api_update_user_role(user_id):
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    data = request.json
    role = data.get('role')
    
    if not role or role not in ['user', 'admin']:
        return jsonify({'error': '角色类型不正确'}), 400
    
    UserService.update_user_role(user_id, role)
    return jsonify({'success': True, 'message': '角色更新成功'})

# 数据统计相关API
@app.route('/api/statistics', methods=['GET'])
def api_get_statistics():
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    stats = StatisticsService.get_statistics()
    return jsonify(stats)

# 修改添加政策API，支持分类和标签
@app.route('/api/policies', methods=['POST'])
def api_add_policy():
    data = request.json
    title = data.get('title')
    content = data.get('content')
    source = data.get('source')
    publish_date = data.get('publish_date')
    category_id = data.get('category_id')
    tags = data.get('tags', [])
    
    if not title or not content:
        return jsonify({'error': '标题和内容不能为空'}), 400
    
    policy_id = PolicyService.create_policy(title, content, source, publish_date, category_id)
    
    # 添加标签
    for tag_name in tags:
        if tag_name:
            tag_id = PolicyService.create_tag(tag_name)
            if tag_id:
                PolicyService.add_policy_tag(policy_id, tag_id)
    
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
    
    UserService.update_nickname(session['user_id'], nickname)
    return jsonify({'success': True, 'message': '昵称更新成功'})

# 讨论广场路由
@app.route('/forum')
def forum():
    user_info = None
    if is_logged_in():
        user = UserService.get_user_by_id(session['user_id'])
        user_info = {
            'username': user['username'],
            'nickname': user['nickname'],
            'role': user['role'],
            'region': user['region'],
            'ban_until': user['ban_until'],
            'is_banned': user['is_banned']
        }
    
    # 获取所有讨论主题
    topics = ForumService.get_all_topics()
    
    return render_template('forum.html', user_info=user_info, topics=topics)

@app.route('/forum/topic/<int:topic_id>')
def forum_topic(topic_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    
    user = UserService.get_user_by_id(session['user_id'])
    user_info = {
        'username': user['username'],
        'nickname': user['nickname'],
        'role': user['role'],
        'region': user['region'],
        'ban_until': user['ban_until'],
        'is_banned': user['is_banned']
    }
    
    # 获取主题信息
    topic = ForumService.get_topic_by_id(topic_id)
    if not topic:
        return redirect(url_for('forum'))
    
    # 获取回复列表
    replies = ForumService.get_topic_replies(topic_id)
    
    return render_template('forum_topic.html', user_info=user_info, topic=topic, replies=replies)

# 讨论广场API
@app.route('/api/forum/topics', methods=['GET'])
def api_get_forum_topics():
    topics = ForumService.get_all_topics()
    return jsonify({'success': True, 'topics': topics})

@app.route('/api/forum/topics', methods=['POST'])
def api_add_forum_topic():
    if not is_logged_in():
        return jsonify({'error': '请先登录'}), 401
    
    user = UserService.get_user_by_id(session['user_id'])
    if user['is_banned'] or user['ban_until']:
        return jsonify({'error': '您已被封禁，无法发布内容'}), 403
    
    if not user['nickname']:
        # 自动生成昵称
        nickname = UserService.get_unique_nickname()
        UserService.update_nickname(session['user_id'], nickname)
    
    data = request.json
    title = data.get('title')
    content = data.get('content')
    
    if not title or not content:
        return jsonify({'error': '标题和内容不能为空'}), 400
    
    topic_id = ForumService.create_topic(session['user_id'], title, content)
    return jsonify({'success': True, 'topic_id': topic_id, 'message': '主题发布成功'})

@app.route('/api/forum/topics/<int:topic_id>/replies', methods=['POST'])
def api_add_forum_reply(topic_id):
    if not is_logged_in():
        return jsonify({'error': '请先登录'}), 401
    
    user = UserService.get_user_by_id(session['user_id'])
    if user['is_banned'] or user['ban_until']:
        return jsonify({'error': '您已被封禁，无法回复内容'}), 403
    
    if not user['nickname']:
        # 自动生成昵称
        nickname = UserService.get_unique_nickname()
        UserService.update_nickname(session['user_id'], nickname)
    
    data = request.json
    content = data.get('content')
    
    if not content:
        return jsonify({'error': '回复内容不能为空'}), 400
    
    reply_id = ForumService.create_reply(topic_id, session['user_id'], content)
    return jsonify({'success': True, 'reply_id': reply_id, 'message': '回复成功'})

# 讨论广场管理API
@app.route('/api/forum/topics/<int:topic_id>', methods=['DELETE'])
def api_delete_forum_topic(topic_id):
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    ForumService.delete_topic(topic_id)
    return jsonify({'success': True, 'message': '主题删除成功'})

@app.route('/api/forum/replies/<int:reply_id>', methods=['DELETE'])
def api_delete_forum_reply(reply_id):
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    ForumService.delete_reply(reply_id)
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
        UserService.ban_user(user_id, is_permanent=True)
        return jsonify({'success': True, 'message': '用户已被永久封禁'})
    else:
        # 计算封禁截止时间
        import datetime
        ban_until = (datetime.datetime.now() + datetime.timedelta(hours=ban_duration)).isoformat()
        UserService.ban_user(user_id, ban_until=ban_until)
        return jsonify({'success': True, 'message': f'用户已被封禁 {ban_duration} 小时'})

@app.route('/api/users/<int:user_id>/unban', methods=['POST'])
def api_unban_user(user_id):
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    UserService.unban_user(user_id)
    return jsonify({'success': True, 'message': '用户封禁已解除'})

# 专家认证相关API
@app.route('/api/expert/application', methods=['POST'])
def api_submit_expert_application():
    if not is_logged_in():
        return jsonify({'error': '请先登录'}), 401
    
    data = request.json
    application = data.get('application')
    
    if not application:
        return jsonify({'error': '申请内容不能为空'}), 400
    
    UserService.submit_expert_application(session['user_id'], application)
    return jsonify({'success': True, 'message': '专家申请已提交，请等待管理员审核'})

@app.route('/api/expert/status', methods=['GET'])
def api_get_expert_status():
    if not is_logged_in():
        return jsonify({'error': '请先登录'}), 401
    
    status = UserService.get_expert_status(session['user_id'])
    return jsonify(status)

@app.route('/api/admin/expert/applications', methods=['GET'])
def api_get_expert_applications():
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    applications = UserService.get_expert_applications()
    return jsonify(applications)

@app.route('/api/admin/expert/applications/<int:user_id>/approve', methods=['POST'])
def api_approve_expert(user_id):
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    UserService.approve_expert(user_id)
    return jsonify({'success': True, 'message': '专家认证已批准'})

@app.route('/api/admin/expert/applications/<int:user_id>/reject', methods=['POST'])
def api_reject_expert(user_id):
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    UserService.reject_expert(user_id)
    return jsonify({'success': True, 'message': '专家认证已拒绝'})

# 专家解读相关API
@app.route('/api/expert/interpretations', methods=['POST'])
def api_add_expert_interpretation():
    if not is_logged_in():
        return jsonify({'error': '请先登录'}), 401
    
    user = UserService.get_user_by_id(session['user_id'])
    if not user['is_expert']:
        return jsonify({'error': '只有专家才能发布解读'}), 403
    
    data = request.json
    title = data.get('title')
    content = data.get('content')
    
    if not title or not content:
        return jsonify({'error': '标题和内容不能为空'}), 400
    
    interpretation_id = ExpertService.create_interpretation(session['user_id'], title, content)
    return jsonify({'success': True, 'interpretation_id': interpretation_id, 'message': '解读已提交，请等待管理员审核'})

@app.route('/api/admin/interpretations/pending', methods=['GET'])
def api_get_pending_interpretations():
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    interpretations = ExpertService.get_pending_interpretations()
    return jsonify(interpretations)

@app.route('/api/admin/interpretations/<int:interpretation_id>/approve', methods=['POST'])
def api_approve_interpretation(interpretation_id):
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    ExpertService.approve_interpretation(interpretation_id)
    return jsonify({'success': True, 'message': '解读已批准'})

@app.route('/api/admin/interpretations/<int:interpretation_id>/reject', methods=['POST'])
def api_reject_interpretation(interpretation_id):
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    ExpertService.reject_interpretation(interpretation_id)
    return jsonify({'success': True, 'message': '解读已拒绝'})

@app.route('/api/interpretations', methods=['GET'])
def api_get_approved_interpretations():
    interpretations = ExpertService.get_approved_interpretations()
    return jsonify(interpretations)

@app.route('/api/interpretations/<int:interpretation_id>', methods=['GET'])
def api_get_interpretation(interpretation_id):
    interpretation = ExpertService.get_interpretation_by_id(interpretation_id)
    if interpretation:
        # 检查用户是否登录
        if not is_logged_in():
            return jsonify({'error': '请先登录查看内容'}), 401
        return jsonify(interpretation)
    return jsonify({'error': '解读未找到'}), 404

@app.route('/api/user/interpretations', methods=['GET'])
def api_get_user_interpretations():
    if not is_logged_in():
        return jsonify({'error': '请先登录'}), 401
    
    interpretations = ExpertService.get_user_interpretations(session['user_id'])
    return jsonify(interpretations)

# 解读详情页面路由
@app.route('/interpretation/<int:interpretation_id>')
def interpretation_detail(interpretation_id):
    if not is_logged_in():
        # 记录当前页面，登录后跳转回来
        session['next_url'] = url_for('interpretation_detail', interpretation_id=interpretation_id)
        return redirect(url_for('login'))
    
    interpretation = ExpertService.get_interpretation_by_id(interpretation_id)
    if not interpretation:
        return redirect(url_for('index'))
    
    user = UserService.get_user_by_id(session['user_id'])
    user_info = {
        'username': user['username'],
        'nickname': user['nickname'],
        'role': user['role'],
        'region': user['region'],
        'is_expert': user['is_expert']
    }
    
    return render_template('interpretation_detail.html', user_info=user_info, interpretation=interpretation)

# 政策详情页面路由
@app.route('/policy/<int:policy_id>')
def policy_detail(policy_id):
    if not is_logged_in():
        # 记录当前页面，登录后跳转回来
        session['next_url'] = url_for('policy_detail', policy_id=policy_id)
        return redirect(url_for('login'))
    
    policy = PolicyService.get_policy_by_id(policy_id)
    if not policy:
        return redirect(url_for('index'))
    
    user = UserService.get_user_by_id(session['user_id'])
    user_info = {
        'username': user['username'],
        'nickname': user['nickname'],
        'role': user['role'],
        'region': user['region'],
        'is_expert': user['is_expert']
    }
    
    # 获取政策标签
    tags = PolicyService.get_policy_tags(policy_id)
    
    return render_template('policy_detail.html', user_info=user_info, policy=policy, tags=tags)

# 更新登录后跳转逻辑
@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    redirect_url = request.form.get('redirect_url', '/')
    
    user = UserService.get_user_by_username(username)
    if user and UserService.verify_password(password, user['password']):
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['region'] = user['region']
        session['is_expert'] = user['is_expert']
        
        # 如果有跳转目标，跳转到该目标
        if redirect_url:
            return redirect(redirect_url)
        
        # 如果是管理员，跳转到管理后台
        if user['role'] == 'admin':
            return redirect(url_for('admin'))
        # 如果是普通用户，跳转到首页
        return redirect(url_for('index'))
    
    return render_template('login.html', error='用户名或密码错误', redirect_url=redirect_url)

# 讨论广场点赞API
@app.route('/api/forum/topics/<int:topic_id>/like', methods=['POST'])
def api_like_forum_topic(topic_id):
    if not is_logged_in():
        return jsonify({'error': '请先登录'}), 401
    
    try:
        success = ForumService.like_topic(session['user_id'], topic_id)
        if success:
            return jsonify({'success': True, 'message': '点赞成功'})
        else:
            return jsonify({'success': False, 'message': '已经点过赞了'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 民声相关API
@app.route('/api/public-voice/settings', methods=['GET'])
def api_get_public_voice_settings():
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    settings = PublicVoiceService.get_settings()
    return jsonify(settings)

@app.route('/api/public-voice/settings', methods=['PUT'])
def api_update_public_voice_settings():
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    data = request.json
    min_view_count = data.get('min_view_count')
    min_like_count = data.get('min_like_count')
    
    if min_view_count is None or min_like_count is None:
        return jsonify({'error': '缺少必要参数'}), 400
    
    try:
        PublicVoiceService.update_settings(session['user_id'], min_view_count, min_like_count)
        return jsonify({'success': True, 'message': '设置更新成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/public-voice/setting-changes', methods=['GET'])
def api_get_public_voice_setting_changes():
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    changes = PublicVoiceService.get_setting_changes()
    return jsonify(changes)

@app.route('/api/public-voice/endorseable-topics', methods=['GET'])
def api_get_endorseable_topics():
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    topics = PublicVoiceService.get_endorseable_topics()
    return jsonify(topics)

@app.route('/api/public-voice/endorsements/<int:topic_id>', methods=['POST'])
def api_add_admin_endorsement(topic_id):
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    data = request.json
    endorsement = data.get('endorsement', 0)
    
    try:
        success = PublicVoiceService.add_endorsement(topic_id, session['user_id'], endorsement)
        if success:
            # 检查是否达到发布条件
            endorsements = PublicVoiceService.get_endorsements(topic_id)
            positive_endorsements = sum(1 for e in endorsements if e['endorsement'] == 1)
            negative_endorsements = sum(1 for e in endorsements if e['endorsement'] == -1)
            
            # 发布条件：至少2个管理员推举，且没有反对意见，或者3个管理员中有多数同意
            if (positive_endorsements >= 2 and negative_endorsements == 0) or (len(endorsements) >= 3 and positive_endorsements > negative_endorsements):
                voice_id = PublicVoiceService.add_public_voice(topic_id)
                if voice_id:
                    return jsonify({'success': True, 'message': '推举成功，该主题已发布到民声'}), 201
            
            return jsonify({'success': True, 'message': '推举成功'}), 200
        else:
            return jsonify({'error': '推举失败'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/public-voice/endorsements/<int:topic_id>', methods=['GET'])
def api_get_admin_endorsements(topic_id):
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    endorsements = PublicVoiceService.get_endorsements(topic_id)
    return jsonify(endorsements)

@app.route('/api/public-voice/voices', methods=['GET'])
def api_get_public_voices():
    voices = PublicVoiceService.get_public_voices()
    return jsonify(voices)

# 民声详情页面路由
@app.route('/public-voice/<int:voice_id>')
def public_voice_detail(voice_id):
    if not is_logged_in():
        # 记录当前页面，登录后跳转回来
        session['next_url'] = url_for('public_voice_detail', voice_id=voice_id)
        return redirect(url_for('login'))
    
    # 获取民声详情
    voices = PublicVoiceService.get_public_voices()
    voice = next((v for v in voices if v['id'] == voice_id), None)
    if not voice:
        return redirect(url_for('index'))
    
    user = UserService.get_user_by_id(session['user_id'])
    user_info = {
        'username': user['username'],
        'nickname': user['nickname'],
        'role': user['role'],
        'region': user['region'],
        'is_expert': user['is_expert']
    }
    
    return render_template('public_voice_detail.html', user_info=user_info, voice=voice)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
