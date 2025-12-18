// static/js/api/device.js
import { authFetch } from '../utils/request.js'; // 👈 导入新工具

export async function getFDDStats() {
    const res = await authFetch('/fdd/stats');
    return await res.json();
}