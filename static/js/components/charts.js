export function getDualAxisOption(powerData, currentData, timeData) {
    return {
        backgroundColor: 'transparent',
        tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
        legend: { textStyle: { color: '#94a3b8' }, top: 0 },
        grid: { left: '3%', right: '3%', bottom: '0%', top: '15%', containLabel: true },
        // 双 Y 轴配置
        yAxis: [
            { 
                type: 'value', name: '功率 (kW)', position: 'left',
                splitLine: { lineStyle: { color: '#334155', type: 'dashed', opacity: 0.3 } },
                axisLabel: { color: '#94a3b8' }
            },
            { 
                type: 'value', name: '电流 (A)', position: 'right',
                splitLine: { show: false },
                axisLabel: { color: '#94a3b8' }
            }
        ],
        xAxis: { 
            type: 'category', data: timeData, 
            axisLine: { lineStyle: { color: '#475569' } },
            axisLabel: { color: '#94a3b8' }
        },
        series: [
            { name: '功率', type: 'line', data: powerData, yAxisIndex: 0, color: '#3b82f6', smooth: true, showSymbol: false, areaStyle: { opacity: 0.2 } },
            { name: '电流', type: 'line', data: currentData, yAxisIndex: 1, color: '#ef4444', smooth: true, showSymbol: false }
        ]
    };
}

export function getFddChartOption(names, scores, alarms) {
    return {
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        legend: { textStyle: { color: '#94a3b8' } },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: { type: 'value', splitLine: { show: false } },
        yAxis: { type: 'category', data: names, axisLabel: { color: '#fff' } },
        series: [
            {
                name: '健康评分', type: 'bar', data: scores,
                itemStyle: { color: params => params.value > 80 ? '#10b981' : (params.value > 60 ? '#f59e0b' : '#ef4444') }
            },
            {
                name: '报警次数', type: 'bar', data: alarms,
                itemStyle: { color: '#64748b' }
            }
        ]
    };
}