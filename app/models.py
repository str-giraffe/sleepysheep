import sqlite3
import os
import random
import string
import logging

from app.config import DATABASE_PATH
from app.security import hash_password, validate_input, log_audit

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('models')

def generate_random_nickname():
    """生成随机昵称"""
    # 生成6位随机字符串，包含数字、大写字母、小写字母
    characters = string.ascii_letters + string.digits
    random_str = ''.join(random.choice(characters) for _ in range(6))
    return f"user{random_str}"

def get_unique_nickname():
    """生成唯一的随机昵称"""
    while True:
        nickname = generate_random_nickname()
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users WHERE nickname = ?', (nickname,))
        count = cursor.fetchone()[0]
        conn.close()
        if count == 0:
            return nickname

from app.database import db_manager

def init_db():
    """初始化数据库"""
    if not db_manager.connect():
        logger.error("Failed to connect to database for initialization")
        return
    
    try:
        # 创建政策表
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source_url TEXT,
                publish_date TEXT,
                category_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建用户表
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                nickname TEXT,
                region TEXT,
                ban_until TIMESTAMP,
                is_banned INTEGER DEFAULT 0,
                is_expert INTEGER DEFAULT 0,
                expert_application TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建讨论主题表
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS forum_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                view_count INTEGER DEFAULT 0,
                reply_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                has_image INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # 创建讨论回复表
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS forum_replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER,
                user_id INTEGER,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (topic_id) REFERENCES forum_topics(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # 创建点赞记录表
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS forum_likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                topic_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, topic_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (topic_id) REFERENCES forum_topics(id) ON DELETE CASCADE
            )
        ''')
        
        # 创建政策分类表
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建政策标签表
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建政策-标签关联表
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS policy_tags (
                policy_id INTEGER,
                tag_id INTEGER,
                PRIMARY KEY (policy_id, tag_id),
                FOREIGN KEY (policy_id) REFERENCES policies(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        ''')
        
        # 创建用户历史记录表
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS user_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                question TEXT NOT NULL,
                answer TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # 创建用户搜索历史表
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS user_search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                query TEXT NOT NULL,
                result_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # 创建用户收藏表
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS user_favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                policy_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, policy_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (policy_id) REFERENCES policies(id) ON DELETE CASCADE
            )
        ''')
        
        # 创建专家解读表
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS expert_interpretations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # 创建民声设置表
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS public_voice_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                min_view_count INTEGER DEFAULT 100,
                min_like_count INTEGER DEFAULT 50,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建管理员推举记录表
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS admin_endorsements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER,
                admin_id INTEGER,
                endorsement INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (topic_id) REFERENCES forum_topics(id) ON DELETE CASCADE,
                FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(topic_id, admin_id)
            )
        ''')
        
        # 创建民声内容表
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS public_voices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                has_image INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (topic_id) REFERENCES forum_topics(id) ON DELETE CASCADE
            )
        ''')
        
        # 创建民声设置更改记录表
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS public_voice_setting_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                old_min_view_count INTEGER,
                new_min_view_count INTEGER,
                old_min_like_count INTEGER,
                new_min_like_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # 创建默认管理员账号
        result = db_manager.execute('SELECT COUNT(*) FROM users WHERE role = ?', ('admin',))
        if result:
            count = result.fetchone()[0]
            if count == 0:
                # 默认管理员账号：admin / admin123
                db_manager.execute('''
                    INSERT INTO users (username, password, role, region)
                    VALUES (?, ?, ?, ?)
                ''', ('admin', hash_password('admin123'), 'admin', '系统'))
        
        # 创建默认政策分类
        default_categories = ['教育', '医疗', '就业', '住房', '社保', '税收', '创业', '其他']
        for category in default_categories:
            result = db_manager.execute('SELECT COUNT(*) FROM categories WHERE name = ?', (category,))
            if result:
                count = result.fetchone()[0]
                if count == 0:
                    db_manager.execute('INSERT INTO categories (name) VALUES (?)', (category,))
        
        # 创建默认民声设置
        result = db_manager.execute('SELECT COUNT(*) FROM public_voice_settings')
        if result:
            count = result.fetchone()[0]
            if count == 0:
                db_manager.execute('INSERT INTO public_voice_settings (min_view_count, min_like_count) VALUES (?, ?)', (100, 50))
        
        # 提交事务
        if not db_manager.commit():
            logger.error("Failed to commit database initialization")
            db_manager.rollback()
        else:
            logger.info("Database initialized successfully")
            
            # 创建初始备份
            backup_path = db_manager.backup()
            if backup_path:
                logger.info(f"Initial database backup created: {backup_path}")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        db_manager.rollback()
    finally:
        db_manager.close()

def add_policy(title, content, source_url=None, publish_date=None, category_id=None):
    """添加政策"""
    # 输入验证
    if not validate_input(title, 'title'):
        logger.warning(f"Invalid policy title")
        return None
    if not validate_input(content, 'content'):
        logger.warning(f"Invalid policy content")
        return None
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO policies (title, content, source_url, publish_date, category_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, content, source_url, publish_date, category_id))
        conn.commit()
        policy_id = cursor.lastrowid
        # 记录审计日志
        log_audit('policy_created', 0, {'policy_id': policy_id, 'title': title})
        return policy_id
    except Exception as e:
        logger.error(f"Error creating policy: {str(e)}")
        return None
    finally:
        conn.close()

def get_all_policies():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.id, p.title, p.content, p.source, p.publish_date, p.created_at, p.topic
        FROM policies p
    ''')
    policies = cursor.fetchall()
    conn.close()
    return [{
        'id': p[0], 'title': p[1], 'content': p[2], 'source': p[3], 
        'publish_date': p[4], 'created_at': p[5], 'topic': p[6]
    } for p in policies]

def get_policy_by_id(policy_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.id, p.title, p.content, p.source, p.publish_date, p.created_at, p.topic
        FROM policies p
        WHERE p.id = ?
    ''', (policy_id,))
    policy = cursor.fetchone()
    conn.close()
    if policy:
        return {
            'id': policy[0], 'title': policy[1], 'content': policy[2], 
            'source': policy[3], 'publish_date': policy[4], 
            'created_at': policy[5], 'topic': policy[6]
        }
    return None

def delete_policy(policy_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM policies WHERE id = ?', (policy_id,))
    conn.commit()
    conn.close()

# 用户相关函数
def add_user(username, password, role='user', region=None):
    """添加用户"""
    # 输入验证
    if not validate_input(username, 'username'):
        logger.warning(f"Invalid username: {username}")
        return None
    if not validate_input(password, 'password'):
        logger.warning(f"Invalid password for user: {username}")
        return None
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (username, password, role, region)
            VALUES (?, ?, ?, ?)
        ''', (username, hash_password(password), role, region))
        conn.commit()
        user_id = cursor.lastrowid
        # 记录审计日志
        log_audit('user_created', user_id, {'username': username, 'role': role})
        return user_id
    except sqlite3.IntegrityError:
        logger.warning(f"Username already exists: {username}")
        return None  # 用户名已存在
    except Exception as e:
        logger.error(f"Error creating user {username}: {str(e)}")
        return None
    finally:
        conn.close()

def get_user_by_username(username):
    """根据用户名获取用户"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, username, password, role, nickname, region, ban_until, is_banned, created_at
        FROM users WHERE username = ?
    ''', (username,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'password': user[2],
            'role': user[3],
            'nickname': user[4],
            'region': user[5],
            'ban_until': user[6],
            'is_banned': user[7],
            'created_at': user[8]
        }
    return None

def get_user_by_id(user_id):
    """根据ID获取用户"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, username, password, role, nickname, region, ban_until, is_banned, created_at
        FROM users WHERE id = ?
    ''', (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'password': user[2],
            'role': user[3],
            'nickname': user[4],
            'region': user[5],
            'ban_until': user[6],
            'is_banned': user[7],
            'created_at': user[8]
        }
    return None

def update_user_region(user_id, region):
    """更新用户地区"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET region = ? WHERE id = ?', (region, user_id))
    conn.commit()
    conn.close()

def update_user_nickname(user_id, nickname):
    """更新用户昵称"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET nickname = ? WHERE id = ?', (nickname, user_id))
    conn.commit()
    conn.close()

def ban_user(user_id, ban_until=None, is_permanent=False):
    """封禁用户"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    if is_permanent:
        cursor.execute('UPDATE users SET is_banned = 1 WHERE id = ?', (user_id,))
    else:
        cursor.execute('UPDATE users SET ban_until = ? WHERE id = ?', (ban_until, user_id))
    conn.commit()
    conn.close()

def unban_user(user_id):
    """解除用户封禁"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET ban_until = NULL, is_banned = 0 WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

# 讨论广场相关函数
def add_forum_topic(user_id, title, content):
    """添加讨论主题"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO forum_topics (user_id, title, content)
        VALUES (?, ?, ?)
    ''', (user_id, title, content))
    conn.commit()
    topic_id = cursor.lastrowid
    conn.close()
    return topic_id

def get_all_forum_topics():
    """获取所有讨论主题"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ft.id, ft.user_id, ft.title, ft.content, ft.view_count, ft.reply_count, ft.created_at, ft.updated_at, u.nickname
        FROM forum_topics ft
        JOIN users u ON ft.user_id = u.id
        ORDER BY ft.updated_at DESC
    ''')
    topics = cursor.fetchall()
    conn.close()
    return [{
        'id': t[0], 'user_id': t[1], 'title': t[2], 'content': t[3],
        'view_count': t[4], 'reply_count': t[5], 'created_at': t[6],
        'updated_at': t[7], 'nickname': t[8]
    } for t in topics]

def get_forum_topic_by_id(topic_id):
    """根据ID获取讨论主题"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    # 增加浏览次数
    cursor.execute('UPDATE forum_topics SET view_count = view_count + 1 WHERE id = ?', (topic_id,))
    conn.commit()
    # 获取主题信息
    cursor.execute('''
        SELECT ft.id, ft.user_id, ft.title, ft.content, ft.view_count, ft.reply_count, ft.created_at, ft.updated_at, u.nickname
        FROM forum_topics ft
        JOIN users u ON ft.user_id = u.id
        WHERE ft.id = ?
    ''', (topic_id,))
    topic = cursor.fetchone()
    conn.close()
    if topic:
        return {
            'id': topic[0], 'user_id': topic[1], 'title': topic[2], 'content': topic[3],
            'view_count': topic[4], 'reply_count': topic[5], 'created_at': topic[6],
            'updated_at': topic[7], 'nickname': topic[8]
        }
    return None

def add_forum_reply(topic_id, user_id, content):
    """添加讨论回复"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    # 添加回复
    cursor.execute('''
        INSERT INTO forum_replies (topic_id, user_id, content)
        VALUES (?, ?, ?)
    ''', (topic_id, user_id, content))
    # 更新主题回复数
    cursor.execute('UPDATE forum_topics SET reply_count = reply_count + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (topic_id,))
    conn.commit()
    reply_id = cursor.lastrowid
    conn.close()
    return reply_id

def get_forum_replies(topic_id):
    """获取讨论主题的回复"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT fr.id, fr.user_id, fr.content, fr.created_at, u.nickname
        FROM forum_replies fr
        JOIN users u ON fr.user_id = u.id
        WHERE fr.topic_id = ?
        ORDER BY fr.created_at ASC
    ''', (topic_id,))
    replies = cursor.fetchall()
    conn.close()
    return [{
        'id': r[0], 'user_id': r[1], 'content': r[2], 'created_at': r[3], 'nickname': r[4]
    } for r in replies]

def delete_forum_topic(topic_id):
    """删除讨论主题"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM forum_topics WHERE id = ?', (topic_id,))
    conn.commit()
    conn.close()

def delete_forum_reply(reply_id):
    """删除讨论回复"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    # 获取回复所属的主题ID
    cursor.execute('SELECT topic_id FROM forum_replies WHERE id = ?', (reply_id,))
    topic_id = cursor.fetchone()
    if topic_id:
        # 删除回复
        cursor.execute('DELETE FROM forum_replies WHERE id = ?', (reply_id,))
        # 更新主题回复数
        cursor.execute('UPDATE forum_topics SET reply_count = reply_count - 1 WHERE id = ?', (topic_id[0],))
        conn.commit()
    conn.close()

# 用户管理相关函数更新
def get_all_users():
    """获取所有用户"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, nickname, role, region, ban_until, is_banned, created_at FROM users')
    users = cursor.fetchall()
    conn.close()
    return [{
        'id': u[0], 'username': u[1], 'nickname': u[2], 'role': u[3], 'region': u[4],
        'ban_until': u[5], 'is_banned': u[6], 'created_at': u[7]
    } for u in users]

# 分类相关函数
def get_all_categories():
    """获取所有分类"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, description, created_at FROM categories')
    categories = cursor.fetchall()
    conn.close()
    return [{
        'id': c[0], 'name': c[1], 'description': c[2], 'created_at': c[3]
    } for c in categories]

def add_category(name, description=None):
    """添加分类"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO categories (name, description) VALUES (?, ?)', (name, description))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None  # 分类已存在
    finally:
        conn.close()

# 标签相关函数
def get_all_tags():
    """获取所有标签"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, created_at FROM tags')
    tags = cursor.fetchall()
    conn.close()
    return [{
        'id': t[0], 'name': t[1], 'created_at': t[2]
    } for t in tags]

def add_tag(name):
    """添加标签"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO tags (name) VALUES (?)', (name,))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        # 标签已存在，返回现有标签的ID
        cursor.execute('SELECT id FROM tags WHERE name = ?', (name,))
        tag = cursor.fetchone()
        return tag[0] if tag else None
    finally:
        conn.close()

def add_policy_tag(policy_id, tag_id):
    """添加政策标签关联"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO policy_tags (policy_id, tag_id) VALUES (?, ?)', (policy_id, tag_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # 关联已存在
    finally:
        conn.close()

def get_policy_tags(policy_id):
    """获取政策的标签"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT t.id, t.name
        FROM tags t
        JOIN policy_tags pt ON t.id = pt.tag_id
        WHERE pt.policy_id = ?
    ''', (policy_id,))
    tags = cursor.fetchall()
    conn.close()
    return [{'id': t[0], 'name': t[1]} for t in tags]

# 用户历史记录相关函数
def add_user_history(user_id, question, answer=None):
    """添加用户历史记录"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_history (user_id, question, answer)
        VALUES (?, ?, ?)
    ''', (user_id, question, answer))
    conn.commit()
    conn.close()

def get_user_history(user_id, limit=20):
    """获取用户历史记录"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, question, answer, created_at
        FROM user_history
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_id, limit))
    history = cursor.fetchall()
    conn.close()
    return [{
        'id': h[0], 'question': h[1], 'answer': h[2], 'created_at': h[3]
    } for h in history]

# 用户搜索历史相关函数
def add_user_search_history(user_id, query, result_count=0):
    """添加用户搜索历史"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO user_search_history (user_id, query, result_count)
            VALUES (?, ?, ?)
        ''', (user_id, query, result_count))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error adding search history: {str(e)}")
        return False
    finally:
        conn.close()

def get_user_search_history(user_id, limit=20):
    """获取用户搜索历史"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, query, result_count, created_at
        FROM user_search_history
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_id, limit))
    history = cursor.fetchall()
    conn.close()
    return [{
        'id': h[0], 'query': h[1], 'result_count': h[2], 'created_at': h[3]
    } for h in history]

def get_user_forum_topics(user_id, limit=20):
    """获取用户在讨论广场发布的主题"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, title, content, view_count, reply_count, like_count, created_at
        FROM forum_topics
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_id, limit))
    topics = cursor.fetchall()
    conn.close()
    return [{
        'id': t[0], 'title': t[1], 'content': t[2], 
        'view_count': t[3], 'reply_count': t[4], 'like_count': t[5], 'created_at': t[6]
    } for t in topics]

def get_user_forum_replies(user_id, limit=20):
    """获取用户在讨论广场发布的回复"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT fr.id, fr.topic_id, fr.content, fr.created_at, ft.title
        FROM forum_replies fr
        JOIN forum_topics ft ON fr.topic_id = ft.id
        WHERE fr.user_id = ?
        ORDER BY fr.created_at DESC
        LIMIT ?
    ''', (user_id, limit))
    replies = cursor.fetchall()
    conn.close()
    return [{
        'id': r[0], 'topic_id': r[1], 'content': r[2], 'created_at': r[3], 'topic_title': r[4]
    } for r in replies]

# 用户收藏相关函数
def add_user_favorite(user_id, policy_id):
    """添加用户收藏"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO user_favorites (user_id, policy_id)
            VALUES (?, ?)
        ''', (user_id, policy_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # 已经收藏过
    finally:
        conn.close()

def remove_user_favorite(user_id, policy_id):
    """移除用户收藏"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM user_favorites
        WHERE user_id = ? AND policy_id = ?
    ''', (user_id, policy_id))
    conn.commit()
    conn.close()

def get_user_favorites(user_id):
    """获取用户收藏"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.id, p.title, p.content, p.source, p.publish_date, p.created_at, p.topic
        FROM policies p
        JOIN user_favorites uf ON p.id = uf.policy_id
        WHERE uf.user_id = ?
        ORDER BY uf.created_at DESC
    ''', (user_id,))
    favorites = cursor.fetchall()
    conn.close()
    return [{
        'id': f[0], 'title': f[1], 'content': f[2], 'source': f[3], 
        'publish_date': f[4], 'created_at': f[5], 'topic': f[6]
    } for f in favorites]

def is_favorite(user_id, policy_id):
    """检查是否已收藏"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM user_favorites
        WHERE user_id = ? AND policy_id = ?
    ''', (user_id, policy_id))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0



def update_user_role(user_id, role):
    """更新用户角色"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET role = ? WHERE id = ?', (role, user_id))
    conn.commit()
    conn.close()

# 数据统计相关函数
def get_statistics():
    """获取系统统计数据"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 政策数量
    cursor.execute('SELECT COUNT(*) FROM policies')
    policy_count = cursor.fetchone()[0]
    
    # 用户数量
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    
    # 管理员数量
    cursor.execute('SELECT COUNT(*) FROM users WHERE role = ?', ('admin',))
    admin_count = cursor.fetchone()[0]
    
    # 专家数量
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_expert = ?', (1,))
    expert_count = cursor.fetchone()[0]
    
    # 问答历史数量
    cursor.execute('SELECT COUNT(*) FROM user_history')
    history_count = cursor.fetchone()[0]
    
    # 收藏数量
    cursor.execute('SELECT COUNT(*) FROM user_favorites')
    favorite_count = cursor.fetchone()[0]
    
    # 专家解读数量
    cursor.execute('SELECT COUNT(*) FROM expert_interpretations WHERE status = ?', ('approved',))
    interpretation_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'policy_count': policy_count,
        'user_count': user_count,
        'admin_count': admin_count,
        'expert_count': expert_count,
        'history_count': history_count,
        'favorite_count': favorite_count,
        'interpretation_count': interpretation_count
    }

# 专家认证相关函数
def submit_expert_application(user_id, application):
    """提交专家申请"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET expert_application = ? WHERE id = ?', (application, user_id))
    conn.commit()
    conn.close()


def get_expert_applications():
    """获取专家申请列表"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, username, nickname, region, expert_application, created_at
        FROM users
        WHERE expert_application IS NOT NULL AND is_expert = 0
    ''')
    applications = cursor.fetchall()
    conn.close()
    return [{
        'id': a[0], 'username': a[1], 'nickname': a[2], 'region': a[3],
        'application': a[4], 'created_at': a[5]
    } for a in applications]


def approve_expert(user_id):
    """批准专家申请"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET is_expert = 1, expert_application = NULL WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()


def reject_expert(user_id):
    """拒绝专家申请"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET expert_application = NULL WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()


def get_expert_status(user_id):
    """获取用户专家状态"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT is_expert, expert_application FROM users WHERE id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {
            'is_expert': result[0],
            'has_applied': result[1] is not None
        }
    return {'is_expert': 0, 'has_applied': False}

# 专家解读相关函数
def add_expert_interpretation(user_id, title, content):
    """添加专家解读"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO expert_interpretations (user_id, title, content)
        VALUES (?, ?, ?)
    ''', (user_id, title, content))
    conn.commit()
    interpretation_id = cursor.lastrowid
    conn.close()
    return interpretation_id


def get_pending_interpretations():
    """获取待审核的专家解读"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ei.id, ei.user_id, ei.title, ei.content, ei.created_at, u.username, u.nickname
        FROM expert_interpretations ei
        JOIN users u ON ei.user_id = u.id
        WHERE ei.status = ?
        ORDER BY ei.created_at DESC
    ''', ('pending',))
    interpretations = cursor.fetchall()
    conn.close()
    return [{
        'id': i[0], 'user_id': i[1], 'title': i[2], 'content': i[3],
        'created_at': i[4], 'username': i[5], 'nickname': i[6]
    } for i in interpretations]


def approve_interpretation(interpretation_id):
    """批准专家解读"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE expert_interpretations
        SET status = ?, approved_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', ('approved', interpretation_id))
    conn.commit()
    conn.close()


def reject_interpretation(interpretation_id):
    """拒绝专家解读"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE expert_interpretations SET status = ? WHERE id = ?', ('rejected', interpretation_id))
    conn.commit()
    conn.close()


def get_approved_interpretations(limit=10):
    """获取已批准的专家解读"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ei.id, ei.user_id, ei.title, ei.content, ei.created_at, ei.approved_at, u.username, u.nickname
        FROM expert_interpretations ei
        JOIN users u ON ei.user_id = u.id
        WHERE ei.status = ?
        ORDER BY ei.approved_at DESC
        LIMIT ?
    ''', ('approved', limit))
    interpretations = cursor.fetchall()
    conn.close()
    return [{
        'id': i[0], 'user_id': i[1], 'title': i[2], 'content': i[3],
        'created_at': i[4], 'approved_at': i[5], 'username': i[6], 'nickname': i[7]
    } for i in interpretations]


def get_interpretation_by_id(interpretation_id):
    """根据ID获取专家解读"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ei.id, ei.user_id, ei.title, ei.content, ei.status, ei.created_at, ei.approved_at, u.username, u.nickname
        FROM expert_interpretations ei
        JOIN users u ON ei.user_id = u.id
        WHERE ei.id = ?
    ''', (interpretation_id,))
    interpretation = cursor.fetchone()
    conn.close()
    if interpretation:
        return {
            'id': interpretation[0], 'user_id': interpretation[1], 'title': interpretation[2], 'content': interpretation[3],
            'status': interpretation[4], 'created_at': interpretation[5], 'approved_at': interpretation[6],
            'username': interpretation[7], 'nickname': interpretation[8]
        }
    return None


def get_user_interpretations(user_id, limit=20):
    """获取用户的专家解读"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, title, content, status, created_at, approved_at
        FROM expert_interpretations
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_id, limit))
    interpretations = cursor.fetchall()
    conn.close()
    return [{
        'id': i[0], 'title': i[1], 'content': i[2], 'status': i[3],
        'created_at': i[4], 'approved_at': i[5]
    } for i in interpretations]

# 更新用户相关函数，添加专家状态
def get_all_users():
    """获取所有用户"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, nickname, role, region, is_expert, ban_until, is_banned, created_at FROM users')
    users = cursor.fetchall()
    conn.close()
    return [{
        'id': u[0], 'username': u[1], 'nickname': u[2], 'role': u[3], 'region': u[4],
        'is_expert': u[5], 'ban_until': u[6], 'is_banned': u[7], 'created_at': u[8]
    } for u in users]


def get_user_by_id(user_id):
    """根据ID获取用户"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, username, password, role, nickname, region, is_expert, ban_until, is_banned, created_at
        FROM users WHERE id = ?
    ''', (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'password': user[2],
            'role': user[3],
            'nickname': user[4],
            'region': user[5],
            'is_expert': user[6],
            'ban_until': user[7],
            'is_banned': user[8],
            'created_at': user[9]
        }
    return None


def get_user_by_username(username):
    """根据用户名获取用户"""
    # 输入验证
    if not validate_input(username, 'username'):
        logger.warning(f"Invalid username: {username}")
        return None
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT id, username, password, role, nickname, region, is_expert, ban_until, is_banned, created_at
            FROM users WHERE username = ?
        ''', (username,))
        user = cursor.fetchone()
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'password': user[2],
                'role': user[3],
                'nickname': user[4],
                'region': user[5],
                'is_expert': user[6],
                'ban_until': user[7],
                'is_banned': user[8],
                'created_at': user[9]
            }
        return None
    except Exception as e:
        logger.error(f"Error getting user by username {username}: {str(e)}")
        return None
    finally:
        conn.close()

# 讨论广场相关函数更新
def add_forum_topic(user_id, title, content, has_image=0):
    """添加讨论主题"""
    # 输入验证
    if not validate_input(title, 'title'):
        logger.warning(f"Invalid topic title from user {user_id}")
        return None
    if not validate_input(content, 'content'):
        logger.warning(f"Invalid topic content from user {user_id}")
        return None
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO forum_topics (user_id, title, content, has_image)
            VALUES (?, ?, ?, ?)
        ''', (user_id, title, content, has_image))
        conn.commit()
        topic_id = cursor.lastrowid
        # 记录审计日志
        log_audit('topic_created', user_id, {'topic_id': topic_id, 'title': title})
        return topic_id
    except Exception as e:
        logger.error(f"Error creating topic from user {user_id}: {str(e)}")
        return None
    finally:
        conn.close()

def get_all_forum_topics():
    """获取所有讨论主题"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ft.id, ft.user_id, ft.title, ft.content, ft.view_count, ft.reply_count, ft.like_count, ft.has_image, ft.created_at, ft.updated_at, u.nickname
        FROM forum_topics ft
        JOIN users u ON ft.user_id = u.id
        ORDER BY ft.updated_at DESC
    ''')
    topics = cursor.fetchall()
    conn.close()
    return [{
        'id': t[0], 'user_id': t[1], 'title': t[2], 'content': t[3],
        'view_count': t[4], 'reply_count': t[5], 'like_count': t[6], 'has_image': t[7],
        'created_at': t[8], 'updated_at': t[9], 'nickname': t[10]
    } for t in topics]

def get_forum_topic_by_id(topic_id):
    """根据ID获取讨论主题"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    # 增加浏览次数
    cursor.execute('UPDATE forum_topics SET view_count = view_count + 1 WHERE id = ?', (topic_id,))
    conn.commit()
    # 获取主题信息
    cursor.execute('''
        SELECT ft.id, ft.user_id, ft.title, ft.content, ft.view_count, ft.reply_count, ft.like_count, ft.has_image, ft.created_at, ft.updated_at, u.nickname
        FROM forum_topics ft
        JOIN users u ON ft.user_id = u.id
        WHERE ft.id = ?
    ''', (topic_id,))
    topic = cursor.fetchone()
    conn.close()
    if topic:
        return {
            'id': topic[0], 'user_id': topic[1], 'title': topic[2], 'content': topic[3],
            'view_count': topic[4], 'reply_count': topic[5], 'like_count': topic[6], 'has_image': topic[7],
            'created_at': topic[8], 'updated_at': topic[9], 'nickname': topic[10]
        }
    return None

def like_forum_topic(user_id, topic_id):
    """点赞讨论主题（每个用户只能点赞一次）"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        # 检查用户是否已经点赞过
        cursor.execute('SELECT id FROM forum_likes WHERE user_id = ? AND topic_id = ?', (user_id, topic_id))
        if cursor.fetchone():
            return False  # 已经点赞过
        
        # 开始事务
        conn.execute('BEGIN TRANSACTION')
        
        # 添加点赞记录
        cursor.execute('INSERT INTO forum_likes (user_id, topic_id) VALUES (?, ?)', (user_id, topic_id))
        
        # 增加点赞数
        cursor.execute('UPDATE forum_topics SET like_count = like_count + 1 WHERE id = ?', (topic_id,))
        
        # 提交事务
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # 唯一约束冲突，说明已经点赞过
        conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Error liking topic: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

# 民声相关函数
def get_public_voice_settings():
    """获取民声设置"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT min_view_count, min_like_count FROM public_voice_settings ORDER BY id DESC LIMIT 1')
    settings = cursor.fetchone()
    conn.close()
    if settings:
        return {
            'min_view_count': settings[0],
            'min_like_count': settings[1]
        }
    return {'min_view_count': 100, 'min_like_count': 50}

def update_public_voice_settings(admin_id, min_view_count, min_like_count):
    """更新民声设置"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 获取当前设置
    cursor.execute('SELECT min_view_count, min_like_count FROM public_voice_settings ORDER BY id DESC LIMIT 1')
    current_settings = cursor.fetchone()
    old_min_view_count = current_settings[0] if current_settings else 100
    old_min_like_count = current_settings[1] if current_settings else 50
    
    # 更新设置
    cursor.execute('''
        UPDATE public_voice_settings
        SET min_view_count = ?, min_like_count = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = (SELECT id FROM public_voice_settings ORDER BY id DESC LIMIT 1)
    ''', (min_view_count, min_like_count))
    
    # 记录更改
    cursor.execute('''
        INSERT INTO public_voice_setting_changes (admin_id, old_min_view_count, new_min_view_count, old_min_like_count, new_min_like_count)
        VALUES (?, ?, ?, ?, ?)
    ''', (admin_id, old_min_view_count, min_view_count, old_min_like_count, min_like_count))
    
    conn.commit()
    conn.close()

def get_public_voice_setting_changes(limit=20):
    """获取民声设置更改记录"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT psc.id, psc.admin_id, u.username, psc.old_min_view_count, psc.new_min_view_count, psc.old_min_like_count, psc.new_min_like_count, psc.created_at
        FROM public_voice_setting_changes psc
        JOIN users u ON psc.admin_id = u.id
        ORDER BY psc.created_at DESC
        LIMIT ?
    ''', (limit,))
    changes = cursor.fetchall()
    conn.close()
    return [{
        'id': c[0], 'admin_id': c[1], 'admin_username': c[2],
        'old_min_view_count': c[3], 'new_min_view_count': c[4],
        'old_min_like_count': c[5], 'new_min_like_count': c[6],
        'created_at': c[7]
    } for c in changes]

def add_admin_endorsement(topic_id, admin_id, endorsement):
    """添加管理员推举"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO admin_endorsements (topic_id, admin_id, endorsement)
            VALUES (?, ?, ?)
        ''', (topic_id, admin_id, endorsement))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # 已存在推举记录，更新
        cursor.execute('''
            UPDATE admin_endorsements
            SET endorsement = ?
            WHERE topic_id = ? AND admin_id = ?
        ''', (endorsement, topic_id, admin_id))
        conn.commit()
        return True
    finally:
        conn.close()

def get_admin_endorsements(topic_id):
    """获取主题的管理员推举记录"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT admin_id, endorsement, created_at
        FROM admin_endorsements
        WHERE topic_id = ?
    ''', (topic_id,))
    endorsements = cursor.fetchall()
    conn.close()
    return [{
        'admin_id': e[0],
        'endorsement': e[1],
        'created_at': e[2]
    } for e in endorsements]

def get_endorseable_topics():
    """获取可推举的讨论主题"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    # 获取符合条件的主题：有一定的浏览量和点赞量
    settings = get_public_voice_settings()
    cursor.execute('''
        SELECT ft.id, ft.title, ft.content, ft.view_count, ft.like_count, ft.has_image, ft.created_at, u.nickname
        FROM forum_topics ft
        JOIN users u ON ft.user_id = u.id
        WHERE ft.view_count >= ? AND ft.like_count >= ?
        ORDER BY ft.updated_at DESC
    ''', (settings['min_view_count'], settings['min_like_count']))
    topics = cursor.fetchall()
    conn.close()
    return [{
        'id': t[0], 'title': t[1], 'content': t[2],
        'view_count': t[3], 'like_count': t[4], 'has_image': t[5],
        'created_at': t[6], 'nickname': t[7]
    } for t in topics]

def add_public_voice(topic_id):
    """添加民声内容"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 获取主题信息
    cursor.execute('SELECT title, content, has_image, view_count, like_count FROM forum_topics WHERE id = ?', (topic_id,))
    topic = cursor.fetchone()
    if not topic:
        conn.close()
        return None
    
    # 检查是否已存在
    cursor.execute('SELECT id FROM public_voices WHERE topic_id = ?', (topic_id,))
    if cursor.fetchone():
        conn.close()
        return None
    
    # 添加民声
    cursor.execute('''
        INSERT INTO public_voices (topic_id, title, content, has_image, view_count, like_count)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (topic_id, topic[0], topic[1], topic[2], topic[3], topic[4]))
    
    conn.commit()
    voice_id = cursor.lastrowid
    conn.close()
    return voice_id

def get_public_voices(limit=10):
    """获取民声内容"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, topic_id, title, content, has_image, view_count, like_count, published_at
        FROM public_voices
        ORDER BY published_at DESC
        LIMIT ?
    ''', (limit,))
    voices = cursor.fetchall()
    conn.close()
    return [{
        'id': v[0], 'topic_id': v[1], 'title': v[2], 'content': v[3],
        'has_image': v[4], 'view_count': v[5], 'like_count': v[6],
        'published_at': v[7]
    } for v in voices]

if __name__ == '__main__':
    init_db()
    print('数据库初始化完成')
