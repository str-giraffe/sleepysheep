/**
 * 政策问答系统 - 主 JavaScript 文件
 * 包含所有页面共享的交互功能
 */

// ==================== 通知系统 ====================
function showNotification(message, type = 'info') {
    const colors = {
        success: '#27ae60',
        error: '#e74c3c',
        warning: '#f39c12',
        info: '#3498db'
    };

    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        border-radius: 12px;
        color: white;
        font-weight: 500;
        font-size: 14px;
        z-index: 9999;
        animation: slideInRight 0.3s ease;
        background: ${colors[type] || colors.info};
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        display: flex;
        align-items: center;
        gap: 10px;
        max-width: 400px;
        word-wrap: break-word;
    `;

    const icon = type === 'success' ? '✓' : type === 'error' ? '✗' : type === 'warning' ? '⚠' : 'ℹ';
    notification.innerHTML = `<span style="font-size: 18px;">${icon}</span><span>${message}</span>`;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ==================== 侧边栏管理 ====================
const SidebarManager = {
    timeout: null,

    init() {
        const sidebar = document.getElementById('sidebar');
        if (!sidebar) return;

        // 鼠标进入侧边栏
        sidebar.addEventListener('mouseenter', () => {
            clearTimeout(this.timeout);
            this.show();
        });

        // 鼠标离开侧边栏
        sidebar.addEventListener('mouseleave', () => {
            this.timeout = setTimeout(() => this.hide(), 300);
        });

        // 点击页面其他区域
        document.addEventListener('click', (e) => {
            if (!sidebar.contains(e.target) && !e.target.matches('.sidebar-toggle')) {
                this.hide();
            }
        });

        // ESC 键关闭
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hide();
            }
        });
    },

    toggle() {
        const sidebar = document.getElementById('sidebar');
        const toggle = document.getElementById('sidebarToggle');
        if (!sidebar || !toggle) return;

        sidebar.classList.toggle('active');
        toggle.classList.toggle('active');
    },

    show() {
        const sidebar = document.getElementById('sidebar');
        const toggle = document.getElementById('sidebarToggle');
        if (!sidebar || !toggle) return;

        sidebar.classList.add('active');
        toggle.classList.add('active');
    },

    hide() {
        const sidebar = document.getElementById('sidebar');
        const toggle = document.getElementById('sidebarToggle');
        if (!sidebar || !toggle) return;

        sidebar.classList.remove('active');
        toggle.classList.remove('active');
    }
};

// ==================== 模态框管理 ====================
const ModalManager = {
    open(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;

        modal.classList.add('active');
        document.body.style.overflow = 'hidden';

        // 点击外部关闭
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.close(modalId);
            }
        });
    },

    close(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;

        modal.classList.remove('active');
        document.body.style.overflow = '';

        // 重置表单
        const form = modal.querySelector('form');
        if (form) {
            form.reset();
        }
    }
};

// ==================== 加载动画 ====================
const LoadingManager = {
    show(element) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (!element) return;

        element.classList.add('loading');
        element.style.position = 'relative';

        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner';
        spinner.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 40px;
            height: 40px;
            border: 3px solid rgba(139, 0, 0, 0.1);
            border-top-color: var(--primary-color);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        `;

        element.appendChild(spinner);
    },

    hide(element) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (!element) return;

        element.classList.remove('loading');
        const spinner = element.querySelector('.loading-spinner');
        if (spinner) {
            spinner.remove();
        }
    }
};

// ==================== API 请求封装 ====================
const API = {
    async request(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            }
        };

        try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('API请求失败:', error);
            throw error;
        }
    },

    // 收藏相关
    async addFavorite(policyId) {
        return this.request(`/api/policy/${policyId}/favorite`, { method: 'POST' });
    },

    async removeFavorite(policyId) {
        return this.request(`/api/profile/favorite/${policyId}`, { method: 'DELETE' });
    },

    // 主题相关
    async createTopic(data) {
        return this.request('/api/forum/topics', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async deleteTopic(topicId) {
        return this.request(`/api/forum/topics/${topicId}`, { method: 'DELETE' });
    },

    async likeTopic(topicId) {
        return this.request(`/api/forum/topics/${topicId}/like`, { method: 'POST' });
    },

    async getTopics() {
        return this.request('/api/forum/topics');
    },

    // 用户相关
    async updateNickname(nickname) {
        return this.request('/api/profile/nickname', {
            method: 'PUT',
            body: JSON.stringify({ nickname })
        });
    }
};

// ==================== 工具函数 ====================
const Utils = {
    // 防抖
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // 节流
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    // 格式化日期
    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;

        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (minutes < 1) return '刚刚';
        if (minutes < 60) return `${minutes}分钟前`;
        if (hours < 24) return `${hours}小时前`;
        if (days < 7) return `${days}天前`;

        return date.toLocaleDateString('zh-CN');
    },

    // 截断文本
    truncateText(text, maxLength) {
        if (!text || text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    },

    // 复制到剪贴板
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            showNotification('已复制到剪贴板', 'success');
        } catch (err) {
            showNotification('复制失败', 'error');
        }
    }
};

// ==================== 动画效果 ====================
const Animations = {
    // 淡入
    fadeIn(element, duration = 300) {
        element.style.opacity = '0';
        element.style.display = 'block';
        element.style.transition = `opacity ${duration}ms ease`;

        requestAnimationFrame(() => {
            element.style.opacity = '1';
        });
    },

    // 淡出
    fadeOut(element, duration = 300) {
        element.style.transition = `opacity ${duration}ms ease`;
        element.style.opacity = '0';

        setTimeout(() => {
            element.style.display = 'none';
        }, duration);
    },

    // 滑动进入
    slideIn(element, direction = 'up', duration = 300) {
        const transforms = {
            up: 'translateY(20px)',
            down: 'translateY(-20px)',
            left: 'translateX(20px)',
            right: 'translateX(-20px)'
        };

        element.style.opacity = '0';
        element.style.transform = transforms[direction];
        element.style.transition = `all ${duration}ms ease`;

        requestAnimationFrame(() => {
            element.style.opacity = '1';
            element.style.transform = 'translate(0)';
        });
    },

    // 计数动画
    countUp(element, target, duration = 1000) {
        const start = 0;
        const increment = target / (duration / 16);
        let current = start;

        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                element.textContent = target;
                clearInterval(timer);
            } else {
                element.textContent = Math.floor(current);
            }
        }, 16);
    }
};

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', function() {
    // 初始化侧边栏
    SidebarManager.init();

    // 添加全局动画样式
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(100px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        @keyframes slideOutRight {
            from {
                opacity: 1;
                transform: translateX(0);
            }
            to {
                opacity: 0;
                transform: translateX(100px);
            }
        }

        @keyframes spin {
            to {
                transform: translate(-50%, -50%) rotate(360deg);
            }
        }

        .loading {
            pointer-events: none;
            opacity: 0.7;
        }
    `;
    document.head.appendChild(style);

    // 添加平滑滚动
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // 输入框焦点效果
    document.querySelectorAll('input, textarea').forEach(input => {
        input.addEventListener('focus', function() {
            this.closest('.form-group')?.classList.add('focused');
        });
        input.addEventListener('blur', function() {
            this.closest('.form-group')?.classList.remove('focused');
        });
    });
});

// 暴露全局函数
window.showNotification = showNotification;
window.toggleSidebar = () => SidebarManager.toggle();
window.ModalManager = ModalManager;
window.LoadingManager = LoadingManager;
window.API = API;
window.Utils = Utils;
window.Animations = Animations;
