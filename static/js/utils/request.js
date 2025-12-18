// static/js/utils/request.js

// 所有的 API 请求都应该用这个函数，而不是直接用 fetch
export async function authFetch(url, options = {}) {
    // 1. 获取本地存储的 Token
    const token = localStorage.getItem('access_token');
    
    // 2. 准备请求头
    const headers = options.headers || {};
    if (token) {
        // 🚨 关键：把 Token 放入 Authorization 头
        headers['Authorization'] = `Bearer ${token}`;
    }

    // 3. 发送请求
    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...headers
        }
    });

    // 4. 全局拦截 401 (未授权/Token过期)
    if (response.status === 401) {
        alert("登录已过期，请重新登录");
        logout(); // 踢出
        return null;
    }

    return response;
}

export function logout() {
    localStorage.removeItem('access_token');
    window.location.href = '/login.html'; // 跳转到登录页
}