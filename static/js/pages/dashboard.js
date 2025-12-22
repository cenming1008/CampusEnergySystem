import { getDevices } from '../api/device.js';
import { getLatestTelemetry, getHistory } from '../api/telemetry.js';
import { getDualAxisOption } from '../components/charts.js';

let mainChart = null;
let currentDeviceId = 1;
let ws = null; // WebSocket 实例

export async function renderDashboard(container) {
    // 1. 渲染 HTML (保持不变)
    container.innerHTML = `
        <div class="grid-cards">
            <div class="info-card">
                <div class="card-top">
                    <span class="card-title">实时负荷</span>
                    <span id="dev-status" class="trend up">初始化...</span>
                </div>
                <div class="card-middle">
                    <h2 id="val-power">--</h2>
                    <span class="unit">kW</span>
                </div>
                <div class="card-bottom">
                    <div class="progress-bar"><div class="fill" style="width: 0%"></div></div>
                </div>
            </div>
            <div class="info-card">
                 <div class="card-top"><span class="card-title">今日用电</span></div>
                 <div class="card-middle"><h2 id="val-today">--</h2><span class="unit">kWh</span></div>
            </div>
            <div class="info-card">
                 <div class="card-top"><span class="card-title">A相电流</span></div>
                 <div class="card-middle"><h2 id="val-current">--</h2><span class="unit">A</span></div>
            </div>
            <div class="info-card">
                 <div class="card-top"><span class="card-title">母线电压</span></div>
                 <div class="card-middle"><h2 id="val-voltage">--</h2><span class="unit">V</span></div>
            </div>
        </div>

        <div class="grid-charts">
            <div class="panel">
                <div class="panel-header"><h3><i class="ri-pulse-line"></i> 负荷趋势分析 (实时推送)</h3></div>
                <div id="main-chart" class="chart-box" style="height:320px;"></div>
            </div>
        </div>
    `;

    // 2. 初始化图表
    mainChart = echarts.init(document.getElementById('main-chart'));
    window.addEventListener('resize', () => mainChart && mainChart.resize());

    // 3. 加载下拉框并获取初始数据
    await initDeviceSelector();
    await loadInitialData(); // 先加载一次历史数据填满图表

    // 4. 建立 WebSocket 连接
    connectWebSocket();
}

export function destroyDashboard() {
    // 离开页面时断开连接，节省资源
    if (ws) {
        ws.close();
        ws = null;
    }
}

async function initDeviceSelector() {
    // (保持原有的下拉框逻辑不变)
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
        
        selector.value = currentDeviceId;
        selector.onchange = (e) => {
            currentDeviceId = parseInt(e.target.value); // 确保是数字
            loadInitialData(); // 切换设备时，重载历史图表
        };
    } catch(e) { console.error(e); }
}

// 加载初始状态（因为 WebSocket 只推新数据，不推历史）
async function loadInitialData() {
    try {
        // 刷新数值面板
        const data = await getLatestTelemetry(currentDeviceId);
        updateDashboardValues(data);

        // 刷新图表历史
        const history = await getHistory(currentDeviceId);
        if (history.length > 0) {
            const times = history.map(i => i.timestamp.substring(11, 19));
            const powers = history.map(i => i.power);
            const currents = history.map(i => i.current);
            mainChart.setOption(getDualAxisOption(powers, currents, times));
        }
    } catch (e) { console.error("加载初始数据失败", e); }
}

function connectWebSocket() {
    // 自动判断协议 (ws:// 或 wss://)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log("✅ WebSocket 连接成功");
    };

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        
        // 只处理遥测更新，并且只处理当前选中的设备
        if (msg.type === 'telemetry_update' && msg.data.device_id === currentDeviceId) {
            handleRealtimeUpdate(msg.data);
        }
    };

    ws.onclose = () => {
        console.log("❌ WebSocket 连接断开");
    };
}

function handleRealtimeUpdate(data) {
    // 1. 更新卡片数值
    // 注意：WebSocket 推送的数据里可能没有 'today_energy' (看你的后端实现是否计算了)
    // 这里简单直接更新电压电流功率
    if (document.getElementById('val-power')) document.getElementById('val-power').innerText = data.power;
    if (document.getElementById('val-voltage')) document.getElementById('val-voltage').innerText = data.voltage;
    if (document.getElementById('val-current')) document.getElementById('val-current').innerText = data.current;
    
    // 更新状态灯
    const statusBadge = document.getElementById('dev-status');
    if(statusBadge) {
        statusBadge.innerHTML = '<i class="ri-pulse-line"></i> 实时接收';
        statusBadge.className = 'trend up';
        statusBadge.style.color = '#10b981';
    }

    // 2. 动态更新图表 (ECharts 动态追加)
    if (mainChart) {
        const option = mainChart.getOption();
        
        // 只有当图表已经有数据时才追加
        if (option.series && option.series.length > 0) {
            // 取出当前的 X轴 和 Y轴 数据
            const times = option.xAxis[0].data;
            const powers = option.series[0].data;
            const currents = option.series[1].data;

            // 追加新数据
            times.push(data.timestamp.substring(11, 19)); // 只取时分秒
            powers.push(data.power);
            currents.push(data.current);

            // 保持数据窗口固定（比如只显示最近 50 个点），移除最旧的
            if (times.length > 50) {
                times.shift();
                powers.shift();
                currents.shift();
            }

            // 重新设置数据，ECharts 会自动做平滑动画
            mainChart.setOption({
                xAxis: { data: times },
                series: [
                    { data: powers },
                    { data: currents }
                ]
            });
        }
    }
}

// 提取一个更新数值的辅助函数，供初始加载使用
function updateDashboardValues(data) {
    if(!data) return;
    document.getElementById('val-power').innerText = data.current_power || data.power || '--';
    document.getElementById('val-today').innerText = data.today_energy || '--';
    document.getElementById('val-voltage').innerText = data.voltage || '--';
    document.getElementById('val-current').innerText = data.current || '--';
}