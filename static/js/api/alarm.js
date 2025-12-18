// static/js/api/device.js
import { authFetch } from '../utils/request.js'; // 👈 导入新工具

export async function getAlarms() {
    const res = await authFetch('/alarms/?limit=20');
    return await res.json();
}

export async function resolveAllAlarms() {
    return await authFetch('/alarms/resolve-all', { method: 'POST' });
}