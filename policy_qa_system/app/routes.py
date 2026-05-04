from flask import render_template, request, jsonify, session, redirect, url_for
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from app.config import BASE_DIR, SECRET_KEY
from app.models import init_db, add_user_history, add_user_feedback, get_all_feedback, update_feedback_status
from app.rag import create_rag_db, generate_answer, policy_interpretation, policy_recommendation, multi_turn_chat, policy_comparison

# 服务层
from app.services.user_service import UserService
from app.services.policy_service import PolicyService
from app.services.forum_service import ForumService
from app.services.user_history_service import UserHistoryService, UserFavoriteService
from app.services.expert_service import ExpertService
from app.services.public_voice_service import PublicVoiceService
from app.services.statistics_service import StatisticsService

init_db()

# 语言切换路由
@app.route('/set-language/<lang>')
def set_language(lang):
    if lang in ['zh', 'en']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))

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
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('login.html', error='用户名和密码不能为空')

        # 验证用户
        user = UserService.verify_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['region'] = user['region']
            session['is_expert'] = user['is_expert']

            # 检查是否有下一页面
            next_url = session.pop('next_url', None)
            if next_url:
                return redirect(next_url)
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='用户名或密码错误')

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
            if policy['content'] and query.lower() in policy['content'].lower():
                content_match = 0.5

            # 总匹配度
            match_score = title_match + content_match

            if match_score > 0:
                results.append({
                    'id': policy['id'],
                    'title': policy['title'],
                    'content': policy['content'][:100] + '...' if policy['content'] else '',
                    'publish_date': policy['publish_date'],
                    'department': policy['department'],
                    'match_score': match_score
                })

        # 按匹配度排序
        results.sort(key=lambda x: x['match_score'], reverse=True)

        # 限制结果数量
        results = results[:20]

    return render_template('search.html', user_info=user_info, query=query, results=results)

# 个人中心路由
@app.route('/profile')
def profile():
    if not is_logged_in():
        return redirect(url_for('login', redirect='/profile'))

    user = UserService.get_user_by_id(session['user_id'])
    user_info = {
        'username': user['username'],
        'nickname': user['nickname'],
        'role': user['role'],
        'region': user['region'],
        'is_expert': user['is_expert']
    }

    # 获取用户的搜索历史
    search_history = UserHistoryService.get_user_search_history(session['user_id'])

    # 获取用户的收藏政策
    favorites = UserFavoriteService.get_user_favorites(session['user_id'])

    # 获取用户在讨论广场发布的内容
    user_topics = ForumService.get_user_topics(session['user_id'])
    user_replies = ForumService.get_user_replies(session['user_id'])

    return render_template('profile.html', user_info=user_info, search_history=search_history, favorites=favorites, user_topics=user_topics, user_replies=user_replies)

# 政策详情路由
@app.route('/policy/<int:policy_id>')
def policy_detail(policy_id):
    policy = PolicyService.get_policy_by_id(policy_id)
    if not policy:
        return redirect(url_for('index'))

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

    # 检查用户是否收藏了该政策
    is_favorite = False
    if is_logged_in():
        is_favorite = UserFavoriteService.is_favorite(session['user_id'], policy_id)

    return render_template('policy_detail.html', user_info=user_info, policy=policy, is_favorite=is_favorite)

# 讨论广场路由
@app.route('/forum')
def forum():
    if not is_logged_in():
        return redirect(url_for('login', redirect='/forum'))

    user = UserService.get_user_by_id(session['user_id'])
    user_info = {
        'username': user['username'],
        'nickname': user['nickname'],
        'role': user['role'],
        'region': user['region'],
        'is_expert': user['is_expert']
    }

    # 获取所有讨论主题
    topics = ForumService.get_all_topics()

    return render_template('forum.html', user_info=user_info, topics=topics)

# 讨论主题详情路由
@app.route('/forum/topic/<int:topic_id>')
def forum_topic(topic_id):
    if not is_logged_in():
        return redirect(url_for('login', redirect=f'/forum/topic/{topic_id}'))

    topic = ForumService.get_topic_by_id(topic_id)
    if not topic:
        return redirect(url_for('forum'))

    user = UserService.get_user_by_id(session['user_id'])
    user_info = {
        'username': user['username'],
        'nickname': user['nickname'],
        'role': user['role'],
        'region': user['region'],
        'is_expert': user['is_expert']
    }

    # 获取主题的回复
    replies = ForumService.get_topic_replies(topic_id)

    return render_template('forum_topic.html', user_info=user_info, topic=topic, replies=replies)

# 民声详情页面路由
@app.route('/public-voice/<int:voice_id>')
def public_voice_detail(voice_id):
    if not is_logged_in():
        session['next_url'] = url_for('public_voice_detail', voice_id=voice_id)
        return redirect(url_for('login'))

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

# 专家解读详情页面路由
@app.route('/interpretation/<int:interpretation_id>')
def interpretation_detail(interpretation_id):
    if not is_logged_in():
        session['next_url'] = url_for('interpretation_detail', interpretation_id=interpretation_id)
        return redirect(url_for('login'))

    interpretations = ExpertService.get_approved_interpretations()
    interpretation = next((i for i in interpretations if i['id'] == interpretation_id), None)
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

# 管理后台路由
@app.route('/admin')
def admin():
    if not is_admin():
        return redirect(url_for('index'))

    user = UserService.get_user_by_id(session['user_id'])
    user_info = {
        'username': user['username'],
        'nickname': user['nickname'],
        'role': user['role'],
        'region': user['region'],
        'is_expert': user['is_expert']
    }

    stats = StatisticsService.get_system_statistics()

    return render_template('admin_index.html', user_info=user_info, stats=stats)

@app.route('/admin/policies')
def admin_policies():
    if not is_admin():
        return redirect(url_for('index'))

    user = UserService.get_user_by_id(session['user_id'])
    user_info = {
        'username': user['username'],
        'nickname': user['nickname'],
        'role': user['role'],
        'region': user['region'],
        'is_expert': user['is_expert']
    }

    policies = PolicyService.get_all_policies()

    return render_template('admin_policies.html', user_info=user_info, policies=policies)

@app.route('/admin/categories')
def admin_categories():
    if not is_admin():
        return redirect(url_for('index'))

    user = UserService.get_user_by_id(session['user_id'])
    user_info = {
        'username': user['username'],
        'nickname': user['nickname'],
        'role': user['role'],
        'region': user['region'],
        'is_expert': user['is_expert']
    }

    categories = ['教育', '医疗', '就业', '住房', '社保', '税收', '创业', '其他']

    return render_template('admin_categories.html', user_info=user_info, categories=categories)

@app.route('/admin/tags')
def admin_tags():
    if not is_admin():
        return redirect(url_for('index'))

    user = UserService.get_user_by_id(session['user_id'])
    user_info = {
        'username': user['username'],
        'nickname': user['nickname'],
        'role': user['role'],
        'region': user['region'],
        'is_expert': user['is_expert']
    }

    tags = ['补贴', '优惠', '政策', '措施', '方案', '计划', '通知', '办法']

    return render_template('admin_tags.html', user_info=user_info, tags=tags)

@app.route('/admin/users')
def admin_users():
    if not is_admin():
        return redirect(url_for('index'))

    user = UserService.get_user_by_id(session['user_id'])
    user_info = {
        'username': user['username'],
        'nickname': user['nickname'],
        'role': user['role'],
        'region': user['region'],
        'is_expert': user['is_expert']
    }

    users = UserService.get_all_users()

    return render_template('admin_users.html', user_info=user_info, users=users)

@app.route('/admin/experts')
def admin_experts():
    if not is_admin():
        return redirect(url_for('index'))

    user = UserService.get_user_by_id(session['user_id'])
    user_info = {
        'username': user['username'],
        'nickname': user['nickname'],
        'role': user['role'],
        'region': user['region'],
        'is_expert': user['is_expert']
    }

    experts = UserService.get_all_experts()

    return render_template('admin_experts.html', user_info=user_info, experts=experts)

@app.route('/admin/interpretations')
def admin_interpretations():
    if not is_admin():
        return redirect(url_for('index'))

    user = UserService.get_user_by_id(session['user_id'])
    user_info = {
        'username': user['username'],
        'nickname': user['nickname'],
        'role': user['role'],
        'region': user['region'],
        'is_expert': user['is_expert']
    }

    interpretations = ExpertService.get_all_interpretations()

    return render_template('admin_interpretations.html', user_info=user_info, interpretations=interpretations)

@app.route('/admin/public-voice')
def admin_public_voice():
    if not is_admin():
        return redirect(url_for('index'))

    user = UserService.get_user_by_id(session['user_id'])
    user_info = {
        'username': user['username'],
        'nickname': user['nickname'],
        'role': user['role'],
        'region': user['region'],
        'is_expert': user['is_expert']
    }

    voices = PublicVoiceService.get_public_voices()

    return render_template('admin_public_voice.html', user_info=user_info, voices=voices)

@app.route('/admin/statistics')
def admin_statistics():
    if not is_admin():
        return redirect(url_for('index'))

    user = UserService.get_user_by_id(session['user_id'])
    user_info = {
        'username': user['username'],
        'nickname': user['nickname'],
        'role': user['role'],
        'region': user['region'],
        'is_expert': user['is_expert']
    }

    stats = StatisticsService.get_system_statistics()

    return render_template('admin_statistics.html', user_info=user_info, stats=stats)

@app.route('/admin/rag')
def admin_rag():
    if not is_admin():
        return redirect(url_for('index'))

    user = UserService.get_user_by_id(session['user_id'])
    user_info = {
        'username': user['username'],
        'nickname': user['nickname'],
        'role': user['role'],
        'region': user['region'],
        'is_expert': user['is_expert']
    }

    return render_template('admin_rag.html', user_info=user_info)

# API 路由
@app.route('/api/policies', methods=['GET'])
def api_get_policies():
    policies = PolicyService.get_all_policies()
    return jsonify(policies)

@app.route('/api/policies/<int:policy_id>', methods=['GET'])
def api_get_policy(policy_id):
    policy = PolicyService.get_policy_by_id(policy_id)
    if policy:
        return jsonify(policy)
    else:
        return jsonify({'error': '政策不存在'}), 404

@app.route('/api/rag/build', methods=['POST'])
def api_build_rag():
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403

    try:
        result = create_rag_db()
        return jsonify(result)
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

    try:
        answer = generate_answer(question)
        add_user_history(session['user_id'], question, answer)
        return jsonify({'answer': answer})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/policy/interpretation', methods=['POST'])
def api_policy_interpretation():
    if not is_logged_in():
        return jsonify({'error': '请先登录'}), 401

    data = request.json
    policy_id = data.get('policy_id')

    if not policy_id:
        return jsonify({'error': '政策ID不能为空'}), 400

    try:
        policy = PolicyService.get_policy_by_id(policy_id)
        if not policy:
            return jsonify({'error': '政策不存在'}), 404

        interpretation = policy_interpretation(policy['content'])
        return jsonify({'interpretation': interpretation})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/policy/recommendation', methods=['POST'])
def api_policy_recommendation():
    if not is_logged_in():
        return jsonify({'error': '请先登录'}), 401

    data = request.json
    user_needs = data.get('user_needs')

    if not user_needs:
        return jsonify({'error': '用户需求不能为空'}), 400

    try:
        recommendations = policy_recommendation(user_needs)
        return jsonify({'recommendations': recommendations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/multi-turn-chat', methods=['POST'])
def api_multi_turn_chat():
    if not is_logged_in():
        return jsonify({'error': '请先登录'}), 401

    data = request.json
    messages = data.get('messages')

    if not messages:
        return jsonify({'error': '消息不能为空'}), 400

    try:
        response = multi_turn_chat(messages)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/policy/comparison', methods=['POST'])
def api_policy_comparison():
    if not is_logged_in():
        return jsonify({'error': '请先登录'}), 401

    data = request.json
    policy_ids = data.get('policy_ids')

    if not policy_ids or len(policy_ids) < 2:
        return jsonify({'error': '至少需要两个政策进行对比'}), 400

    try:
        comparison = policy_comparison(policy_ids)
        return jsonify({'comparison': comparison})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 论坛 API
@app.route('/api/forum/topics', methods=['GET'])
def api_get_topics():
    topics = ForumService.get_all_topics()
    return jsonify(topics)

@app.route('/api/forum/topics', methods=['POST'])
def api_create_topic():
    if not is_logged_in():
        return jsonify({'error': '请先登录'}), 401

    data = request.json
    title = data.get('title')
    content = data.get('content')

    if not title or not content:
        return jsonify({'error': '标题和内容不能为空'}), 400

    topic_id = ForumService.create_topic(session['user_id'], title, content)
    if topic_id:
        return jsonify({'topic_id': topic_id, 'message': '发布成功'})
    else:
        return jsonify({'error': '发布失败'}), 500

@app.route('/api/forum/topics/<int:topic_id>/replies', methods=['GET'])
def api_get_replies(topic_id):
    replies = ForumService.get_topic_replies(topic_id)
    return jsonify(replies)

@app.route('/api/forum/topics/<int:topic_id>/replies', methods=['POST'])
def api_add_reply(topic_id):
    if not is_logged_in():
        return jsonify({'error': '请先登录'}), 401

    data = request.json
    content = data.get('content')

    if not content:
        return jsonify({'error': '回复内容不能为空'}), 400

    reply_id = ForumService.create_reply(topic_id, session['user_id'], content)
    if reply_id:
        return jsonify({'reply_id': reply_id, 'message': '回复成功'})
    else:
        return jsonify({'error': '回复失败'}), 500

@app.route('/api/forum/topics/<int:topic_id>/like', methods=['POST'])
def api_like_topic(topic_id):
    if not is_logged_in():
        return jsonify({'error': '请先登录'}), 401

    success = ForumService.like_topic(session['user_id'], topic_id)
    if success:
        return jsonify({'message': '点赞成功'})
    else:
        return jsonify({'error': '您已经点赞过了'}), 400

@app.route('/api/forum/replies/<int:reply_id>', methods=['DELETE'])
def api_delete_reply(reply_id):
    if not is_logged_in():
        return jsonify({'error': '请先登录'}), 401

    try:
        ForumService.delete_reply(reply_id)
        return jsonify({'message': '删除成功'})
    except Exception as e:
        return jsonify({'error': '删除失败'}), 500

# 民声 API
@app.route('/api/public-voice', methods=['GET'])
def api_get_public_voices():
    voices = PublicVoiceService.get_public_voices()
    return jsonify(voices)

# 用户反馈API
@app.route('/api/feedback', methods=['POST'])
def api_add_feedback():
    if not is_logged_in():
        return jsonify({'error': '请先登录'}), 401

    data = request.json
    feedback_type = data.get('type')
    content = data.get('content')

    if not feedback_type or not content:
        return jsonify({'error': '反馈类型和内容不能为空'}), 400

    success = add_user_feedback(session['user_id'], feedback_type, content)
    if success:
        return jsonify({'success': True, 'message': '反馈提交成功'})
    else:
        return jsonify({'error': '反馈提交失败'}), 500

# 管理后台反馈管理API
@app.route('/api/admin/feedback', methods=['GET'])
def api_get_feedback():
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403

    feedbacks = get_all_feedback()
    return jsonify(feedbacks)

@app.route('/api/admin/feedback/<int:feedback_id>/status', methods=['PUT'])
def api_update_feedback_status(feedback_id):
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403

    data = request.json
    status = data.get('status')

    if not status:
        return jsonify({'error': '状态不能为空'}), 400

    success = update_feedback_status(feedback_id, status)
    if success:
        return jsonify({'success': True, 'message': '状态更新成功'})
    else:
        return jsonify({'error': '状态更新失败'}), 500

# 个人中心 API
@app.route('/api/profile/nickname', methods=['PUT'])
def api_update_nickname():
    if not is_logged_in():
        return jsonify({'error': '请先登录'}), 401

    data = request.json
    nickname = data.get('nickname')

    if not nickname:
        return jsonify({'error': '昵称不能为空'}), 400

    try:
        UserService.update_nickname(session['user_id'], nickname)
        # 更新 session 中的用户信息
        user = UserService.get_user_by_id(session['user_id'])
        return jsonify({'success': True, 'message': '昵称修改成功', 'nickname': nickname})
    except Exception as e:
        return jsonify({'error': '昵称修改失败'}), 500

@app.route('/api/profile/favorite/<int:policy_id>', methods=['POST'])
def api_add_favorite(policy_id):
    if not is_logged_in():
        return jsonify({'error': '请先登录'}), 401

    try:
        UserFavoriteService.add_favorite(session['user_id'], policy_id)
        return jsonify({'success': True, 'message': '收藏成功'})
    except Exception as e:
        return jsonify({'error': '收藏失败'}), 500

@app.route('/api/profile/favorite/<int:policy_id>', methods=['DELETE'])
def api_remove_favorite(policy_id):
    if not is_logged_in():
        return jsonify({'error': '请先登录'}), 401

    try:
        UserFavoriteService.remove_favorite(session['user_id'], policy_id)
        return jsonify({'success': True, 'message': '取消收藏成功'})
    except Exception as e:
        return jsonify({'error': '取消收藏失败'}), 500