// static/js/api/device.js
import { authFetch } from '../utils/request.js'; // 👈 导入新工具

export async function getDevices() {
    // 👇 把 fetch 改成 authFetch
    const res = await authFetch('/devices/'); 
    return await res.json();
}

export async function deleteDevice(id) {
    // 👇 把 fetch 改成 authFetch
    return await authFetch(`/devices/${id}`, { method: 'DELETE' });
}