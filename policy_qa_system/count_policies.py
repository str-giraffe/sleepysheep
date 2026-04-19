import sqlite3

# 数据库连接
conn = sqlite3.connect('policy.db')
cursor = conn.cursor()

# 查询政策数量
cursor.execute('SELECT COUNT(*) FROM policies')
count = cursor.fetchone()[0]

print(f"数据库中共有 {count} 条政策")

# 关闭数据库连接
conn.close()
