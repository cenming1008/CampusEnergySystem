// static/js/pages/deviceManager.js
import { getDevices, deleteDevice, toggleDeviceStatus } from '../api/device.js';

export async function renderDeviceManager(container) {
    container.innerHTML = `
        <div class="panel">
            <div class="panel-header">
                <h3><i class="ri-server-line"></i> 设备全生命周期台账</h3>
                <button class="panel-actions tag active">+ 新增设备</button>
            </div>
            <div style="overflow-x: auto; margin-top: 15px;">
                <table style="width: 100%; border-collapse: collapse; color: #cbd5e1; font-size: 14px;">
                    <thead>
                        <tr style="border-bottom: 1px solid #334155; text-align: left;">
                            <th style="padding: 12px;">ID</th>
                            <th style="padding: 12px;">设备名称</th>
                            <th style="padding: 12px;">序列号 (SN)</th>
                            <th style="padding: 12px;">安装位置/状态</th>
                            <th style="padding: 12px;">操作</th>
                        </tr>
                    </thead>
                    <tbody id="device-table-body">
                        <tr><td colspan="5" style="text-align:center;">加载中...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;

    // --- 全局函数绑定 ---
    
    window.handleDelete = async (id) => {
        if(confirm(`删除设备 ${id}?`)) {
            await deleteDevice(id);
            renderDeviceManager(container);
        }
    };

    /**
     * ✅ 修正后的启停函数
     */
    window.toggleDevice = async (id, targetStatus) => {
        try {
            // 调用 api/device.js 中封装好的 toggleDeviceStatus
            const res = await toggleDeviceStatus(id, targetStatus);
            
            if (res && res.ok) {
                // 操作成功，模拟点击侧边栏“设备台账”菜单刷新页面
                document.querySelector('[data-page="devices"]').click();
            } else {
                // 如果返回 401 或其他错误，res 会是 null 或 ok 为 false
                alert("操作失败：登录过期或权限不足 (401)");
            }
        } catch(e) { 
            console.error("请求异常:", e);
            alert("系统错误，请检查网络");
        }
    };

    // --- 数据渲染 ---
    const devices = await getDevices();
    const tbody = document.getElementById('device-table-body');
    tbody.innerHTML = devices.map(d => `
        <tr style="border-bottom: 1px solid rgba(255,255,255,0.05); opacity: ${d.is_active ? 1 : 0.6}">
            <td style="padding:12px;">#${d.id}</td>
            <td style="padding:12px; font-weight:bold;">${d.name}</td>
            <td style="padding:12px;">${d.sn}</td>
            <td style="padding:12px;">
                <span style="background: ${d.is_active ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}; 
                             color: ${d.is_active ? '#10b981' : '#ef4444'};
                             padding: 4px 8px; border-radius: 4px; font-size: 12px;">
                    ${d.is_active ? '运行中' : '已停机'}
                </span>
            </td>
            <td style="padding:12px; display: flex; gap: 10px;">
                <button onclick="toggleDevice(${d.id}, ${!d.is_active})" style="cursor:pointer; border:1px solid #334155; background:transparent; color:#fff; padding:4px 8px; border-radius:4px;">
                    ${d.is_active ? '🛑 停机' : '▶️ 启动'}
                </button>
                <button onclick="handleDelete(${d.id})" style="color:#ef4444; background:none; border:none; cursor:pointer;">删除</button>
            </td>
        </tr>
    `).join('');
}