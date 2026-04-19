import sqlite3

# 数据库连接
conn = sqlite3.connect('policy.db')
cursor = conn.cursor()

# 删除标题为"未知标题"的政策记录
cursor.execute('DELETE FROM policies WHERE title = ?', ('未知标题',))
conn.commit()
print(f"删除了 {cursor.rowcount} 条 '未知标题' 记录")

# 删除标题为"自然人电子税务局"的政策记录
cursor.execute('DELETE FROM policies WHERE title = ?', ('自然人电子税务局',))
conn.commit()
print(f"删除了 {cursor.rowcount} 条 '自然人电子税务局' 记录")

# 关闭数据库连接
conn.close()

print("清理完成!")
