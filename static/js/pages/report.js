export function renderReports(container) {
    container.innerHTML = `
        <div class="panel" style="text-align: center; padding: 60px;">
            <div style="font-size: 64px; color: #3b82f6; margin-bottom: 20px;"><i class="ri-file-excel-2-fill"></i></div>
            <h2 style="color: #fff;">历史数据导出</h2>
            <p style="color: #94a3b8; margin-bottom: 30px;">导出 CSV 格式分析报表</p>
            <a href="/reports/export_csv" target="_blank" style="background:#3b82f6; color:white; padding:12px 30px; border-radius:6px; text-decoration:none;">立即下载</a>
        </div>
    `;
}