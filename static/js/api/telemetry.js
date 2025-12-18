// static/js/api/device.js
import { authFetch } from '../utils/request.js'; // 👈 导入新工具

export async function getLatestTelemetry(deviceId) {
    const res = await authFetch(`/analysis/${deviceId}`);
    return await res.json();
}

export async function getHistory(deviceId) {
    const res = await authFetch(`/telemetry/${deviceId}?limit=50`);
    return await res.json();
}