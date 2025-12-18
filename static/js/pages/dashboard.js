import { getDevices } from '../api/device.js';
import { getLatestTelemetry, getHistory } from '../api/telemetry.js';
import { getDualAxisOption } from '../components/charts.js';

let mainChart = null;
let pollInterval = null;
let currentDeviceId = 1;

export async function renderDashboard(container) {
    // 1. 渲染 HTML (包含最新的电费卡片结构)
    container.innerHTML = `
        <div class="grid-cards">
            <div class="info-card">
                <div class="card-top">
                    <span class="card-title">实时负荷</span>
                    <span id="dev-status" class="trend up">运行中</span>
                    <span class="trend up">2.4%</span>
                </div>
                <div class="card-middle">
                    <h2 id="val-power">--</h2>
                    <span class="unit">kW</span>
                </div>
                <div class="card-bottom">
                    <div class="progress-bar"><div class="fill" style="width: 65%"></div></div>
                </div>
            </div>

            <div class="info-card">
                <div class="card-top">
                    <span class="card-title">今日用电</span>
                    <span class="trend up" style="color: #f59e0b; font-weight: bold;">
                        ¥ <span id="val-cost">--</span>
                    </span>
                </div>
                <div class="card-middle">
                    <h2 id="val-today">--</h2>
                    <span class="unit">kWh</span>
                </div>
                <div class="card-bottom">
                    <span style="color: #64748b; font-size: 12px;">单价: 0.85元/度</span>
                </div>
            </div>

            <div class="info-card">
                <div class="card-top"><span class="card-title">A相电流</span></div>
                <div class="card-middle">
                    <h2 id="val-current">--</h2>
                    <span class="unit">A</span>
                </div>
                <div class="card-bottom">
                    <div class="progress-bar orange"><div class="fill" style="width: 80%"></div></div>
                </div>
            </div>

            <div class="info-card">
                <div class="card-top"><span class="card-title">母线电压</span></div>
                <div class="card-middle">
                    <h2 id="val-voltage">--</h2>
                    <span class="unit">V</span>
                </div>
                <div class="card-bottom">
                    <div class="progress-bar purple"><div class="fill" style="width: 95%"></div></div>
                </div>
            </div>
        </div>

        <div class="grid-charts">
            <div class="panel">
                <div class="panel-header"><h3><i class="ri-pulse-line"></i> 负荷趋势分析</h3></div>
                <div id="main-chart" class="chart-box" style="height:320px;"></div>
            </div>
        </div>
    `;

    // 2. 初始化图表
    mainChart = echarts.init(document.getElementById('main-chart'));
    window.addEventListener('resize', () => mainChart && mainChart.resize());

    // 3. 加载下拉框
    await initDeviceSelector();

    // 4. 启动轮询
    refreshData();
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(refreshData, 2000);
}

// 停止轮询（切出页面时调用）
export function destroyDashboard() {
    if (pollInterval) clearInterval(pollInterval);
}

async function initDeviceSelector() {
    try {
        const devices = await getDevices();
        const selector = document.getElementById('device-selector');
        if (!selector) return;

        selector.innerHTML = '';
        devices.forEach(d => {
            const opt = document.createElement('option');
            opt.value = d.id;
            opt.text = `${d.id}. ${d.name}`;
            selector.appendChild(opt);
        });
        
        // 保持选中状态
        selector.value = currentDeviceId;
        
        selector.onchange = (e) => {
            currentDeviceId = e.target.value;
            refreshData();
        };
    } catch(e) { console.error(e); }
}

async function refreshData() {
    try {
        // 1. 获取分析数据
        const data = await getLatestTelemetry(currentDeviceId);
        
        // --- 👇 状态显示逻辑 ---
        const statusBadge = document.getElementById('dev-status');
        if (statusBadge) {
            if (data.is_active) {
                statusBadge.innerHTML = '<i class="ri-pulse-line"></i> 运行中';
                statusBadge.className = 'trend up'; // 绿色
                statusBadge.style.color = '#10b981';
            } else {
                statusBadge.innerHTML = '<i class="ri-pause-circle-line"></i> 已暂停';
                statusBadge.className = 'trend';    // 灰色/默认色
                statusBadge.style.color = '#64748b'; // 灰色
            }
        }
        // ----------------------

        // 2. 填入数值 (此时后端返回的是最后一次的数值，不是0，所以会显示暂停前的值)
        document.getElementById('val-power').innerText = data.current_power;
        document.getElementById('val-today').innerText = data.today_energy;
        document.getElementById('val-cost').innerText = data.today_cost !== undefined ? data.today_cost : '0.00';
        document.getElementById('val-voltage').innerText = data.voltage;
        document.getElementById('val-current').innerText = data.current;

        // 3. 更新图表
        // 关键原理：因为模拟器停了，数据库没有新数据。
        // getHistory 拿到的永远是相同的 50 条旧数据。
        // ECharts 收到相同的数据，图表就会看起来“静止不动”，实现暂停效果。
        const history = await getHistory(currentDeviceId);
        if (history.length > 0) {
            const times = history.map(i => i.timestamp.substring(11, 19));
            const powers = history.map(i => i.power);
            const currents = history.map(i => i.current);
            
            mainChart.setOption(getDualAxisOption(powers, currents, times));
        }
    } catch(e) { console.error(e); }
}