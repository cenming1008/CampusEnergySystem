<script setup lang="ts">
    import { ref } from 'vue'
    import { downloadReport } from '@/api/report' // 之前定义的api
    import { ElMessage } from 'element-plus'
    import { Download, Document } from '@element-plus/icons-vue'
    
    const downloading = ref(false)
    
    const handleDownload = async () => {
      downloading.value = true
      try {
        // 1. 请求二进制流 (Blob)
        const blob = await downloadReport()
        
        // 2. 创建临时下载链接
        const url = window.URL.createObjectURL(new Blob([blob as any]))
        const link = document.createElement('a')
        link.href = url
        
        // 3. 设置文件名 (可以加时间戳)
        const fileName = `Energy_Report_${new Date().toISOString().slice(0,10)}.csv`
        link.setAttribute('download', fileName)
        
        // 4. 触发点击并清理
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        
        ElMessage.success('报表下载成功')
      } catch (e) {
        console.error(e)
        ElMessage.error('下载失败，请检查网络')
      } finally {
        downloading.value = false
      }
    }
    </script>
    
    <template>
      <div class="report-container">
        <div class="report-card">
          <el-icon class="icon" :size="80" color="#3b82f6"><Document /></el-icon>
          <h2>历史数据导出</h2>
          <p>生成并下载全矿设备的历史运行数据 (CSV格式)，包含电压、电流、功率及能耗记录。</p>
          
          <el-button 
            type="primary" 
            size="large" 
            :icon="Download" 
            :loading="downloading"
            @click="handleDownload"
            class="download-btn"
          >
            {{ downloading ? '正在生成报表...' : '立即下载 CSV 报表' }}
          </el-button>
        </div>
      </div>
    </template>
    
    <style scoped>
    .report-container {
      height: 85vh;
      display: flex;
      justify-content: center;
      align-items: center;
    }
    
    .report-card {
      background: var(--bg-sidebar);
      border: 1px solid var(--border-color);
      border-radius: 16px;
      padding: 60px;
      text-align: center;
      width: 400px;
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
    }
    
    .icon { margin-bottom: 20px; }
    
    h2 { color: #fff; margin: 10px 0; }
    
    p { color: var(--text-secondary); line-height: 1.6; margin-bottom: 40px; font-size: 14px; }
    
    .download-btn { width: 100%; padding: 12px; font-weight: bold; }
    </style>