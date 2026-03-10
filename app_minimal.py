# app_minimal.py
from flask import Flask, render_template_string, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'minimal-test-key'

# 硬编码用户（绕过数据库）
USERS = {
    'admin': 'admin123',
    'user1': 'user123',
    'user2': 'user123'
}

@app.route('/')
def index():
    if 'username' in session:
        return f'''
        <!DOCTYPE html>
        <html>
        <head><title>主页</title></head>
        <body>
            <h1>欢迎, {session['username']}!</h1>
            <p>登录成功！政策解读系统运行正常。</p>
            <p><a href="/logout">退出</a></p>
        </body>
        </html>
        '''
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in USERS and USERS[username] == password:
            session['username'] = username
            return redirect('/')
        
        return '''
        <h1>登录失败</h1>
        <p>用户名或密码错误</p>
        <a href="/login">返回</a>
        '''
    
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>登录</title></head>
    <body>
        <h1>登录测试</h1>
        <form method="POST">
            <input type="text" name="username" placeholder="用户名" required><br>
            <input type="password" name="password" placeholder="密码" required><br>
            <button type="submit">登录</button>
        </form>
        <p>测试: admin/admin123</p>
    </body>
    </html>
    '''

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

if __name__ == '__main__':
    print("=" * 60)
    print("最简登录测试")
    print("访问: http://localhost:5002")
    print("测试: admin/admin123")
    print("=" * 60)
    app.run(debug=True, port=5002)