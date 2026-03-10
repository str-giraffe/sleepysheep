# migrate_to_db.py
import sqlite3
import json
from datetime import datetime

def migrate_to_database():
    """将内存数据迁移到数据库"""
    print("开始数据迁移...")
    
    # 源数据（从内存中）
    users = {
        'admin': {'id': 1, 'password': 'admin123', 'role': 'admin', 'email': 'admin@example.com'},
        'user1': {'id': 2, 'password': 'user123', 'role': 'user', 'email': 'user1@example.com'},
        'user2': {'id': 3, 'password': 'user123', 'role': 'user', 'email': 'user2@example.com'}
    }
    
    policies = [
        {'id': 1, 'title': '高新技术企业认定', 'content': '享受15%企业所得税优惠。', 'category': '税收', 'source': '科技部'},
        {'id': 2, 'title': '研发费用加计扣除', 'content': '研发费用100%税前加计扣除。', 'category': '税收', 'source': '税务总局'},
        {'id': 3, 'title': '小微企业税收优惠', 'content': '实际税负5%。', 'category': '税收', 'source': '财政部'}
    ]
    
    # 目标数据库
    db_file = 'policy_migrated.db'
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # 创建表
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash TEXT,
            email TEXT,
            role TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE policies (
            id INTEGER PRIMARY KEY,
            policy_title TEXT,
            policy_content TEXT,
            category TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 迁移用户
    for username, user_data in users.items():
        cursor.execute("""
            INSERT INTO users (id, username, password_hash, email, role)
            VALUES (?, ?, ?, ?, ?)
        """, (user_data['id'], username, user_data['password'], 
              user_data['email'], user_data['role']))
        print(f"✓ 迁移用户: {username}")
    
    # 迁移政策
    for policy in policies:
        cursor.execute("""
            INSERT INTO policies (id, policy_title, policy_content, category, source)
            VALUES (?, ?, ?, ?, ?)
        """, (policy['id'], policy['title'], policy['content'], 
              policy['category'], policy['source']))
        print(f"✓ 迁移政策: {policy['title']}")
    
    conn.commit()
    
    # 验证
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM policies")
    policy_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT username, password_hash FROM users WHERE username='admin'")
    admin = cursor.fetchone()
    
    print(f"\n✓ 迁移完成!")
    print(f"用户数: {user_count}")
    print(f"政策数: {policy_count}")
    print(f"管理员验证: {admin[0]} -> '{admin[1]}'")
    
    cursor.close()
    conn.close()
    
    return db_file

if __name__ == "__main__":
    db_file = migrate_to_database()
    print(f"\n数据库文件: {db_file}")
    print("可以修改 app_success_based.py 中的 use_database=True 来启用数据库")