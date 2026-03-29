import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'policy.db')

def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS policies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            source_url TEXT,
            publish_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def add_policy(title, content, source_url=None, publish_date=None):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO policies (title, content, source_url, publish_date)
        VALUES (?, ?, ?, ?)
    ''', (title, content, source_url, publish_date))
    conn.commit()
    policy_id = cursor.lastrowid
    conn.close()
    return policy_id

def get_all_policies():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, content, source_url, publish_date, created_at FROM policies')
    policies = cursor.fetchall()
    conn.close()
    return [{'id': p[0], 'title': p[1], 'content': p[2], 'source_url': p[3], 'publish_date': p[4], 'created_at': p[5]} for p in policies]

def get_policy_by_id(policy_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, content, source_url, publish_date, created_at FROM policies WHERE id = ?', (policy_id,))
    policy = cursor.fetchone()
    conn.close()
    if policy:
        return {'id': policy[0], 'title': policy[1], 'content': policy[2], 'source_url': policy[3], 'publish_date': policy[4], 'created_at': policy[5]}
    return None

def delete_policy(policy_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM policies WHERE id = ?', (policy_id,))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print('数据库初始化完成')
