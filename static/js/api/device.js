// static/js/api/device.js
import { authFetch } from '../utils/request.js';

export async function getDevices() {
    const res = await authFetch('/devices/'); 
    return await res.json();
}

export async function deleteDevice(id) {
    return await authFetch(`/devices/${id}`, { method: 'DELETE' });
}

/**
 * 💡 这是解决 401 错误的关键函数
 */
export async function toggleDeviceStatus(id, active) {
    // authFetch 会自动从 localStorage 读取 access_token 并放入 Header
    return await authFetch(`/devices/${id}/toggle?active=${active}`, { 
        method: 'POST' 
    });
}