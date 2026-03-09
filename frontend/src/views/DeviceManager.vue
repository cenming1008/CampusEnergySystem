<script setup lang="ts">
    import { ref, reactive, onMounted, computed } from 'vue'
    import { 
      getDevices, createDevice, updateDevice, deleteDevice, toggleDeviceStatus,
      getDeviceTypes,
      type Device, type DeviceTypeConfig 
    } from '@/api/device'
    import { ElMessage, ElMessageBox } from 'element-plus'
    import { Plus, Search, Refresh, Delete, Edit } from '@element-plus/icons-vue'
    
    // --- 状态定义 ---
    const loading = ref(false)
    const tableData = ref<Device[]>([])
    const dialogVisible = ref(false)
    const dialogTitle = ref('新增设备')
    const formLoading = ref(false)
    const formRef = ref()
    
    // 设备类型列表（从后端动态获取）
    const deviceTypes = ref<DeviceTypeConfig[]>([])
    
    // 设备类型映射 (用于表格展示，动态计算)
    const deviceTypeMap = computed(() => {
      const map: Record<string, string> = {}
      deviceTypes.value.forEach(t => {
        map[t.device_type] = `${t.icon} ${t.name_zh}`
      })
      return map
    })
    
    // 表单数据模型
    const formData = reactive<Device>({
      name: '',
      sn: '',
      device_type: 'load', // 默认值：用电设备
      location: '',
      is_active: true,
      description: ''
    })
    
    // 表单校验规则
    const rules = {
      name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
      sn: [{ required: true, message: '请输入唯一序列号', trigger: 'blur' }],
      device_type: [{ required: true, message: '请选择设备类型', trigger: 'change' }],
      location: [{ required: true, message: '请输入安装位置', trigger: 'blur' }]
    }
    
    // --- 1. 获取设备列表 ---
    const fetchData = async () => {
      loading.value = true
      try {
        const res = await getDevices()
        // 按 ID 排序
        tableData.value = res.sort((a, b) => (a.id || 0) - (b.id || 0))
      } catch (e) {
        console.error(e)
      } finally {
        loading.value = false
      }
    }
    
    // --- 2. 新增 / 编辑 ---
    const openDialog = (row?: Device) => {
      if (row) {
        dialogTitle.value = '编辑设备'
        // 复制数据到表单 (注意深拷贝或 Object.assign)
        Object.assign(formData, row)
      } else {
        dialogTitle.value = '新增设备'
        // 重置表单
        formData.id = undefined
        formData.name = ''
        formData.sn = ''
        formData.device_type = deviceTypes.value.length > 0 ? deviceTypes.value[0].device_type : 'load'
        formData.location = ''
        formData.is_active = true
        formData.description = ''
      }
      dialogVisible.value = true
    }
    
    const handleSubmit = async () => {
      if (!formRef.value) return
      
      await formRef.value.validate(async (valid: boolean) => {
        if (valid) {
          formLoading.value = true
          try {
            if (formData.id) {
              // 编辑模式
              await updateDevice(formData.id, formData)
              ElMessage.success('设备更新成功')
            } else {
              // 新增模式
              await createDevice(formData)
              ElMessage.success('设备创建成功')
            }
            dialogVisible.value = false
            fetchData() // 刷新列表
          } catch (e) {
            console.error(e)
          } finally {
            formLoading.value = false
          }
        }
      })
    }
    
    // --- 3. 删除设备 ---
    const handleDelete = (row: Device) => {
      ElMessageBox.confirm(
        `确定要删除设备 "${row.name}" 吗？此操作不可恢复。`,
        '高危操作警告',
        {
          confirmButtonText: '确定删除',
          cancelButtonText: '取消',
          type: 'warning',
        }
      ).then(async () => {
        try {
          if (row.id) {
            await deleteDevice(row.id)
            ElMessage.success('删除成功')
            fetchData()
          }
        } catch (e) {
          console.error(e)
        }
      })
    }
    
    // --- 4. 核心：远程启停控制 (Switch) ---
    // 使用 before-change 钩子处理异步请求
    const handleStatusChange = (newVal: boolean, row: Device) => {
      return new Promise<boolean>((resolve, reject) => {
        const actionName = newVal ? '启动' : '停机'
        const color = newVal ? '#10b981' : '#ef4444'
        
        // 二次确认
        ElMessageBox.confirm(
          `确定要对 ${row.name} 执行【${actionName}】指令吗？`,
          '远程控制确认',
          {
            confirmButtonText: `立即${actionName}`,
            cancelButtonText: '取消',
            confirmButtonClass: newVal ? 'el-button--success' : 'el-button--danger',
            type: 'warning'
          }
        ).then(async () => {
          try {
            if (row.id) {
              // 调用 API
              await toggleDeviceStatus(row.id, newVal)
              ElMessage({
                message: `指令下发成功: 设备已${actionName}`,
                type: 'success',
              })
              resolve(true) // 允许 Switch 切换状态
            } else {
              reject()
            }
          } catch (e) {
            ElMessage.error('指令发送失败或超时')
            reject(e) // 阻止 Switch 切换状态
          }
        }).catch(() => {
          reject() // 用户取消
        })
      })
    }
    
    // --- 获取设备类型列表 ---
    const fetchDeviceTypes = async () => {
      try {
        const res = await getDeviceTypes()
        if (res.data) {
          deviceTypes.value = res.data
        }
      } catch (e) {
        console.error('获取设备类型失败:', e)
        // 降级：使用默认类型
        deviceTypes.value = [
          { device_type: 'load', name_zh: '用电设备', icon: '⚡', category: 'load', energy_type: 'electricity', name_en: 'Load', unit: 'kW', default_capacity: 100, required_fields: [], optional_fields: [], color: '#FF9800' },
          { device_type: 'solar', name_zh: '光伏发电', icon: '☀️', category: 'solar', energy_type: 'electricity', name_en: 'Solar', unit: 'kW', default_capacity: 50, required_fields: [], optional_fields: [], color: '#FFC107' },
          { device_type: 'water_meter', name_zh: '水表', icon: '💧', category: 'water_meter', energy_type: 'water', name_en: 'Water Meter', unit: 'm³/h', default_capacity: 50, required_fields: [], optional_fields: [], color: '#2196F3' },
          { device_type: 'gas_meter', name_zh: '燃气表', icon: '🔥', category: 'gas_meter', energy_type: 'gas', name_en: 'Gas Meter', unit: 'm³/h', default_capacity: 30, required_fields: [], optional_fields: [], color: '#FF5722' },
        ]
      }
    }
    
    // --- 生命周期 ---
    onMounted(async () => {
      await fetchDeviceTypes()
      fetchData()
    })
    </script>
    
    <template>
      <div class="device-container">
        <div class="toolbar">
          <div class="left">
            <h2 class="page-title">设备全生命周期台账</h2>
          </div>
          <div class="right">
            <el-button :icon="Refresh" circle @click="fetchData" />
            <el-button type="primary" :icon="Plus" @click="openDialog(undefined)">
              新增设备
            </el-button>
          </div>
        </div>
    
        <el-table 
          v-loading="loading" 
          :data="tableData" 
          style="width: 100%" 
          class="custom-table"
          :header-cell-style="{ background: '#1e293b', color: '#94a3b8', borderBottom: '1px solid #334155' }"
          :cell-style="{ background: '#1e293b', color: '#cbd5e1', borderBottom: '1px solid #334155' }"
        >
          <el-table-column prop="id" label="ID" width="80" align="center" />
          
          <el-table-column label="设备名称" min-width="180">
            <template #default="{ row }">
              <div class="device-name-cell">
                <span class="name">{{ row.name }}</span>
                <el-tag size="small" type="info" effect="dark" class="sn-tag">{{ row.sn }}</el-tag>
              </div>
            </template>
          </el-table-column>
    
          <el-table-column prop="device_type" label="设备类型" width="140">
            <template #default="{ row }">
              {{ deviceTypeMap[row.device_type] || row.device_type }}
            </template>
          </el-table-column>
    
          <el-table-column prop="location" label="安装位置" width="150" />
    
          <el-table-column label="运行状态 (远程控制)" width="200">
            <template #default="{ row }">
              <el-switch
                v-model="row.is_active"
                inline-prompt
                active-text="运行中"
                inactive-text="已停机"
                style="--el-switch-on-color: #10b981; --el-switch-off-color: #ef4444"
                :before-change="() => handleStatusChange(!row.is_active, row)"
              />
            </template>
          </el-table-column>
    
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" :icon="Edit" @click="openDialog(row)">编辑</el-button>
              <el-button link type="danger" :icon="Delete" @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
    
        <el-dialog
          v-model="dialogVisible"
          :title="dialogTitle"
          width="500px"
          class="custom-dialog"
        >
          <el-form ref="formRef" :model="formData" :rules="rules" label-width="100px" status-icon>
            <el-form-item label="设备名称" prop="name">
              <el-input v-model="formData.name" placeholder="例如: 智能电表" />
            </el-form-item>
            
            <el-form-item label="序列号 SN" prop="sn">
              <el-input v-model="formData.sn" placeholder="例如: METER-001" :disabled="!!formData.id"/>
            </el-form-item>
    
            <el-form-item label="设备类型" prop="device_type">
              <el-select v-model="formData.device_type" placeholder="请选择设备类型" style="width:100%">
                <el-option 
                  v-for="t in deviceTypes" 
                  :key="t.device_type" 
                  :label="`${t.icon} ${t.name_zh} (${t.unit})`" 
                  :value="t.device_type"
                >
                  <span style="float: left">{{ t.icon }} {{ t.name_zh }}</span>
                  <span style="float: right; color: #8492a6; font-size: 12px">{{ t.energy_type }} | {{ t.unit }}</span>
                </el-option>
              </el-select>
            </el-form-item>
    
            <el-form-item label="安装位置" prop="location">
              <el-input v-model="formData.location" placeholder="例如: 总配电室" />
            </el-form-item>
            
            <el-form-item label="描述备注" prop="description">
              <el-input v-model="formData.description" type="textarea" />
            </el-form-item>
          </el-form>
          
          <template #footer>
            <span class="dialog-footer">
              <el-button @click="dialogVisible = false">取消</el-button>
              <el-button type="primary" :loading="formLoading" @click="handleSubmit">
                确认提交
              </el-button>
            </span>
          </template>
        </el-dialog>
      </div>
    </template>
    
    <style scoped>
    .device-container {
      background: var(--bg-sidebar);
      padding: 20px;
      border-radius: 12px;
      border: 1px solid var(--border-color);
      min-height: 85vh;
      width: 100%;
      box-sizing: border-box;
    }
    
    .toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
    }
    .page-title { margin: 0; font-size: 18px; border-left: 4px solid var(--brand-color); padding-left: 10px; color: #fff; }
    
    /* 表格内样式微调 */
    .device-name-cell {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .name { font-weight: 600; color: #fff; }
    .sn-tag { width: fit-content; font-size: 10px; height: 20px; line-height: 18px; }
    
    /* 覆盖 Element Dialog 样式以适配暗黑主题 (通常建议在全局 css 中做，这里为了单文件演示) */
    :deep(.el-table__inner-wrapper::before) {
      background-color: #334155;
    }
    :deep(.el-table--enable-row-hover .el-table__body tr:hover > td) {
      background-color: rgba(255, 255, 255, 0.05) !important;
    }
    </style>