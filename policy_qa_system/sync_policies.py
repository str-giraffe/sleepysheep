#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步政策数据到主数据库
"""
import sqlite3
import shutil
from datetime import datetime

def sync_policies():
    """将real_policies.db的数据同步到policy.db"""
    
    # 备份主数据库
    backup_file = f"policy_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2('policy.db', backup_file)
    print(f"已备份主数据库: {backup_file}")
    
    # 连接源数据库（real_policies.db）
    source_conn = sqlite3.connect('real_policies.db')
    source_cursor = source_conn.cursor()
    
    # 连接目标数据库（policy.db）
    target_conn = sqlite3.connect('policy.db')
    target_cursor = target_conn.cursor()
    
    # 确保目标表存在
    target_cursor.execute('''
    CREATE TABLE IF NOT EXISTS policies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        publish_date TEXT,
        source TEXT,
        topic TEXT,
        view_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 检查并添加缺失的字段
    try:
        target_cursor.execute('ALTER TABLE policies ADD COLUMN summary TEXT')
    except:
        pass
    
    try:
        target_cursor.execute('ALTER TABLE policies ADD COLUMN province TEXT')
    except:
        pass
    
    try:
        target_cursor.execute('ALTER TABLE policies ADD COLUMN url TEXT')
    except:
        pass
    
    try:
        target_cursor.execute('ALTER TABLE policies ADD COLUMN doc_type TEXT')
    except:
        pass
    
    try:
        target_cursor.execute('ALTER TABLE policies ADD COLUMN keywords TEXT')
    except:
        pass
    
    try:
        target_cursor.execute('ALTER TABLE policies ADD COLUMN hash TEXT')
    except:
        pass
    
    target_conn.commit()
    
    # 清空现有数据
    target_cursor.execute('DELETE FROM policies')
    target_conn.commit()
    print("已清空policy.db中的现有政策数据")
    
    # 从源数据库获取所有政策
    source_cursor.execute('''
    SELECT title, content, summary, publish_date, source, topic, 
           province, url, doc_type, keywords, hash, view_count
    FROM policies
    ''')
    
    policies = source_cursor.fetchall()
    print(f"从real_policies.db读取了 {len(policies)} 条政策")
    
    # 插入到目标数据库
    inserted = 0
    skipped = 0
    
    for policy in policies:
        try:
            target_cursor.execute('''
            INSERT INTO policies (title, content, summary, publish_date, source, topic,
                                  province, url, doc_type, keywords, hash, view_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', policy)
            inserted += 1
        except sqlite3.IntegrityError:
            skipped += 1
        except Exception as e:
            print(f"插入失败: {e}")
            skipped += 1
    
    target_conn.commit()
    
    # 统计
    target_cursor.execute('SELECT COUNT(*) FROM policies')
    total = target_cursor.fetchone()[0]
    
    print(f"\n同步完成!")
    print(f"成功插入: {inserted} 条")
    print(f"跳过: {skipped} 条")
    print(f"policy.db 总政策数: {total} 条")
    
    # 按主题统计
    print("\n按主题统计:")
    target_cursor.execute('SELECT topic, COUNT(*) FROM policies GROUP BY topic ORDER BY COUNT(*) DESC')
    for topic, count in target_cursor.fetchall():
        print(f"  {topic}: {count} 条")
    
    # 按来源统计
    print("\n按来源统计 (前10):")
    target_cursor.execute('SELECT source, COUNT(*) FROM policies GROUP BY source ORDER BY COUNT(*) DESC LIMIT 10')
    for source, count in target_cursor.fetchall():
        print(f"  {source}: {count} 条")
    
    # 关闭连接
    source_conn.close()
    target_conn.close()
    
    print("\n数据同步完成! 网站现在使用新的政策数据。")

if __name__ == "__main__":
    sync_policies()
