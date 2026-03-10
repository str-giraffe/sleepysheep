/* 基础样式 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: #333;
    background: #f5f5f5;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

/* 导航栏 */
.navbar {
    background: white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    padding: 1rem 0;
}

.nav-container {
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 20px;
}

.nav-brand {
    font-size: 1.5rem;
    font-weight: bold;
    color: #4CAF50;
    text-decoration: none;
}

.nav-menu {
    display: flex;
    align-items: center;
    gap: 20px;
}

.nav-welcome {
    color: #666;
}

.nav-link {
    color: #333;
    text-decoration: none;
    padding: 8px 12px;
    border-radius: 4px;
    transition: background 0.3s;
}

.nav-link:hover {
    background: #f0f0f0;
}

/* 登录页面 */
.login-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 80vh;
}

.login-box {
    background: white;
    padding: 40px;
    border-radius: 10px;
    box-shadow: 0 2px 20px rgba(0,0,0,0.1);
    width: 100%;
    max-width: 400px;
}

.login-box h1 {
    text-align: center;
    margin-bottom: 30px;
    color: #333;
}

.login-form {
    margin-bottom: 20px;
}

.form-group {
    margin-bottom: 20px;
}

.form-input {
    width: 100%;
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 16px;
}

.btn {
    padding: 12px 24px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 16px;
    transition: background 0.3s;
}

.btn-primary {
    background: #4CAF50;
    color: white;
}

.btn-primary:hover {
    background: #45a049;
}

.btn-block {
    width: 100%;
}

.btn-danger {
    background: #dc3545;
    color: white;
}

.btn-danger:hover {
    background: #c82333;
}

/* 提示框 */
.alert {
    padding: 12px;
    border-radius: 6px;
    margin-bottom: 20px;
}

.alert-error {
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

/* 管理面板 */
.admin-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin: 20px 0;
}

.stat-card {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    text-align: center;
}

.stat-number {
    font-size: 2rem;
    font-weight: bold;
    color: #4CAF50;
    margin: 10px 0;
}

.stat-label {
    color: #666;
    font-size: 0.9rem;
}

/* 表格 */
.table {
    width: 100%;
    background: white;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin: 20px 0;
}

.table th,
.table td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid #eee;
}

.table th {
    background: #f8f9fa;
    font-weight: bold;
}

.table tr:hover {
    background: #f5f5f5;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .nav-container {
        flex-direction: column;
        gap: 10px;
    }
    
    .nav-menu {
        width: 100%;
        justify-content: center;
        flex-wrap: wrap;
    }
    
    .admin-stats {
        grid-template-columns: 1fr;
    }
}