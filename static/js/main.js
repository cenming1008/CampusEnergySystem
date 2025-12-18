import { initRouter } from './utils/router.js';
import { setupNavbar } from './components/navbar.js';
import { renderDashboard, destroyDashboard } from './pages/dashboard.js';
import { renderDeviceManager } from './pages/deviceManager.js';
import { renderFDD } from './pages/fdd.js';
import { renderReports } from './pages/report.js';

// ==============================================
// 👇 新增功能 1：路由守卫 (安全检查)
// ==============================================
// 这是一个"立即执行函数"，在页面加载 JS 的瞬间就会运行
(function checkAuth() {
    const token = localStorage.getItem('access_token');
    // 如果本地没有 Token，说明未登录或已过期，强制跳转到登录页
    if (!token) {
        // 使用 replace 而不是 href，这样用户点击浏览器“后退”按钮回不到这里，体验更好
        window.location.replace('/view/login.html');
    }
})();

document.addEventListener('DOMContentLoaded', () => {
    
    // 1. 初始化全局导航栏 (报警铃铛等)
    setupNavbar();

    // ==============================================
    // 👇 新增功能 2：显示当前登录用户名
    // ==============================================
    const userDisplay = document.querySelector('.user-info .name');
    const roleDisplay = document.querySelector('.user-info .role');
    
    if (userDisplay) {
        // 从 localStorage 获取登录时存入的用户名，默认为 Admin
        const username = localStorage.getItem('username') || 'Admin';
        userDisplay.innerText = username;
        // 如果是 admin 账号，显示管理员角色，否则显示操作员
        if (roleDisplay) {
            roleDisplay.innerText = (username === 'admin') ? '系统管理员' : '在线操作员';
        }
    }

    // 2. 获取主容器
    const appContainer = document.getElementById('app-container');

    // 3. 定义路由表
    // key 对应 index.html 里的 data-page 属性
    // value 是对应的渲染函数
    const routes = {
        'dashboard': async () => {
            await renderDashboard(appContainer);
        },
        'devices': async () => {
            destroyDashboard(); // 切走时停止轮询
            await renderDeviceManager(appContainer);
        },
        'fdd': async () => {
            destroyDashboard();
            await renderFDD(appContainer);
        },
        'report': async () => {
            destroyDashboard();
            renderReports(appContainer);
        }
    };

    // 4. 启动路由监听
    initRouter(routes);

    // 5. 默认进入首页
    renderDashboard(appContainer);
});