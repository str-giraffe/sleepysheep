import sqlite3
import os
import hashlib
import random
import string

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'policy.db')

def hash_password(password):
    """密码哈希函数"""
    return hashlib.sha256(password.encode()).hexdigest()

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

def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 创建政策表
    cursor.execute('''
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            nickname TEXT,
            region TEXT,
            ban_until TIMESTAMP,
            is_banned INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建讨论主题表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS forum_topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            view_count INTEGER DEFAULT 0,
            reply_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # 创建讨论回复表
    cursor.execute('''
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
    
    # 创建政策分类表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建政策标签表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建政策-标签关联表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS policy_tags (
            policy_id INTEGER,
            tag_id INTEGER,
            PRIMARY KEY (policy_id, tag_id),
            FOREIGN KEY (policy_id) REFERENCES policies(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
        )
    ''')
    
    # 创建用户历史记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            question TEXT NOT NULL,
            answer TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # 创建用户收藏表
    cursor.execute('''
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
    
    # 创建默认管理员账号
    cursor.execute('SELECT COUNT(*) FROM users WHERE role = ?', ('admin',))
    if cursor.fetchone()[0] == 0:
        # 默认管理员账号：admin / admin123
        cursor.execute('''
            INSERT INTO users (username, password, role, region)
            VALUES (?, ?, ?, ?)
        ''', ('admin', hash_password('admin123'), 'admin', '系统'))
    
    # 创建默认政策分类
    default_categories = ['教育', '医疗', '就业', '住房', '社保', '税收', '创业', '其他']
    for category in default_categories:
        cursor.execute('SELECT COUNT(*) FROM categories WHERE name = ?', (category,))
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO categories (name) VALUES (?)', (category,))
    
    conn.commit()
    conn.close()

def add_policy(title, content, source_url=None, publish_date=None, category_id=None):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO policies (title, content, source_url, publish_date, category_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (title, content, source_url, publish_date, category_id))
    conn.commit()
    policy_id = cursor.lastrowid
    conn.close()
    return policy_id

def get_all_policies():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.id, p.title, p.content, p.source_url, p.publish_date, p.created_at, c.name as category
        FROM policies p
        LEFT JOIN categories c ON p.category_id = c.id
    ''')
    policies = cursor.fetchall()
    conn.close()
    return [{
        'id': p[0], 'title': p[1], 'content': p[2], 'source_url': p[3], 
        'publish_date': p[4], 'created_at': p[5], 'category': p[6]
    } for p in policies]

def get_policy_by_id(policy_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.id, p.title, p.content, p.source_url, p.publish_date, p.created_at, c.name as category
        FROM policies p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.id = ?
    ''', (policy_id,))
    policy = cursor.fetchone()
    conn.close()
    if policy:
        return {
            'id': policy[0], 'title': policy[1], 'content': policy[2], 
            'source_url': policy[3], 'publish_date': policy[4], 
            'created_at': policy[5], 'category': policy[6]
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
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (username, password, role, region)
            VALUES (?, ?, ?, ?)
        ''', (username, hash_password(password), role, region))
        conn.commit()
        user_id = cursor.lastrowid
        return user_id
    except sqlite3.IntegrityError:
        return None  # 用户名已存在
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
        SELECT p.id, p.title, p.content, p.source_url, p.publish_date, p.created_at, c.name as category
        FROM policies p
        JOIN user_favorites uf ON p.id = uf.policy_id
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE uf.user_id = ?
        ORDER BY uf.created_at DESC
    ''', (user_id,))
    favorites = cursor.fetchall()
    conn.close()
    return [{
        'id': f[0], 'title': f[1], 'content': f[2], 'source_url': f[3], 
        'publish_date': f[4], 'created_at': f[5], 'category': f[6]
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
    
    # 问答历史数量
    cursor.execute('SELECT COUNT(*) FROM user_history')
    history_count = cursor.fetchone()[0]
    
    # 收藏数量
    cursor.execute('SELECT COUNT(*) FROM user_favorites')
    favorite_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'policy_count': policy_count,
        'user_count': user_count,
        'admin_count': admin_count,
        'history_count': history_count,
        'favorite_count': favorite_count
    }

if __name__ == '__main__':
    init_db()
    print('数据库初始化完成')
