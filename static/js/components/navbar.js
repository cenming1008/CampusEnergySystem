import { getAlarms, resolveAllAlarms } from '../api/alarm.js';

export function setupNavbar() {
    // 铃铛弹窗逻辑
    const btn = document.getElementById('alarm-btn');
    const dropdown = document.getElementById('alarm-dropdown');
    const clearBtn = document.querySelector('.clear-all');

    if(btn) {
        btn.onclick = (e) => {
            e.stopPropagation();
            dropdown.classList.toggle('show');
        };
        document.addEventListener('click', () => dropdown.classList.remove('show'));
        dropdown.onclick = (e) => e.stopPropagation();
    }

    // 全部清除按钮
    if (clearBtn) {
        clearBtn.onclick = async () => {
            await resolveAllAlarms();
            await refreshAlarmBadge(); // 刷新角标
            dropdown.classList.remove('show');
        };
    }

    // 定时刷新报警角标
    refreshAlarmBadge();
    setInterval(refreshAlarmBadge, 5000);
}

export async function refreshAlarmBadge() {
    try {
        const alarms = await getAlarms();
        const badge = document.getElementById('alarm-badge');
        const content = document.getElementById('dropdown-content');
        const btn = document.getElementById('alarm-btn');

        if (!badge) return;

        if (alarms.length > 0) {
            btn.classList.add('has-alarm');
            badge.style.display = 'block';
            badge.innerText = alarms.length;
            content.innerHTML = alarms.map(a => `
                <div class="alarm-item">
                    <i class="ri-alarm-warning-fill alarm-icon"></i>
                    <div class="alarm-info">
                        <div class="alarm-time">${a.timestamp.substring(11, 19)} | ID:${a.device_id}</div>
                        <div class="alarm-msg">${a.message}</div>
                    </div>
                </div>
            `).join('');
        } else {
            btn.classList.remove('has-alarm');
            badge.style.display = 'none';
            content.innerHTML = '<div style="padding:15px; text-align:center; color:#64748b">🎉 系统运行正常</div>';
        }
    } catch(e) { console.error(e); }
}