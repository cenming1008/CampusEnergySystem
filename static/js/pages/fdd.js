import { getFDDStats } from '../api/fdd.js';
import { getFddChartOption } from '../components/charts.js';

let chartInstance = null;

export async function renderFDD(container) {
    container.innerHTML = `
        <div class="panel">
            <div class="panel-header"><h3><i class="ri-pulse-fill"></i> 设备健康度排行榜 (FDD)</h3></div>
            <div id="fdd-chart" style="width: 100%; height: 400px;"></div>
        </div>
    `;

    const data = await getFDDStats();
    const names = data.map(i => i.device_name);
    const scores = data.map(i => i.health_score);
    const alarms = data.map(i => i.alarm_count);

    const dom = document.getElementById('fdd-chart');
    if (chartInstance) chartInstance.dispose();
    chartInstance = echarts.init(dom);
    chartInstance.setOption(getFddChartOption(names, scores, alarms));
    
    window.addEventListener('resize', () => chartInstance.resize());
}