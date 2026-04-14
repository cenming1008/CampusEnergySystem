<script setup lang="ts">
    import { ref, reactive, onMounted, computed, unref, watch } from 'vue'
    import { useRouter } from 'vue-router'
    import { usePermissions } from '@/shared/composables/usePermissions'
    import { getDeviceCategoryLabel, getDeviceSubtypeLabel } from '@/shared/deviceTypeLabels'
    import { getSVGOperationsProfile } from '@/api/svg'
    import { 
      getDevices, createDevice, updateDevice, deleteDevice, toggleDeviceStatus,
      FALLBACK_DEVICE_TYPE_CONFIGS, getDeviceTypes, notifyDevicesUpdated,
      type Device, type DeviceTypeConfig, type DeviceWritePayload
    } from '@/api/device'
    import { ElMessage, ElMessageBox } from 'element-plus'
    import { Plus, Search, Refresh, Delete, Edit, Monitor } from '@element-plus/icons-vue'
    
    // --- 状态定义 ---
    const loading = ref(false)
	    const router = useRouter()
	    const { canManageDevices, canControlDevices, hasScopedAccess } = usePermissions()
    const canManageDevicesValue = computed(() => Boolean(unref(canManageDevices)))
    const canControlDevicesValue = computed(() => Boolean(unref(canControlDevices)))
    const tableData = ref<Device[]>([])
    const dialogVisible = ref(false)
    const dialogTitle = ref('新增设备')
    const formLoading = ref(false)
    const formRef = ref()
    
    // 设备类型列表（从后端动态获取）
    const deviceTypes = ref<DeviceTypeConfig[]>([])
    
    const getCategoryLabel = (category?: string | null) => {
      return getDeviceCategoryLabel(category, deviceTypes.value) || '未分类设备'
    }

    const getSubtypeLabel = (deviceType?: string | null) => {
      return getDeviceSubtypeLabel(deviceType, deviceTypes.value) || '未定义子类型'
    }

    const COMPENSATION_TYPE_KEY = 'compensation'

    interface TypeOption {
      key: string
      label: string
      unit: string
    }

    const getPrimaryTypeKey = (config: DeviceTypeConfig) =>
      config.category === COMPENSATION_TYPE_KEY ? COMPENSATION_TYPE_KEY : config.device_type

    const typeOptions = computed<TypeOption[]>(() => {
      const seen = new Set<string>()
      const options: TypeOption[] = []
      for (const config of deviceTypes.value) {
        const key = getPrimaryTypeKey(config)
        if (seen.has(key)) continue
        seen.add(key)
        options.push({
          key,
          label: key === COMPENSATION_TYPE_KEY ? getCategoryLabel(COMPENSATION_TYPE_KEY) : config.name_zh,
          unit: config.unit,
        })
      }
      return options
    })

    const selectedTypeKey = ref('load')
    const selectedSubtypeKey = ref('')

    const subtypeOptions = computed(() =>
      deviceTypes.value.filter((config) => config.category === selectedTypeKey.value && getPrimaryTypeKey(config) !== config.device_type)
    )

    const showSubtypeField = computed(() => subtypeOptions.value.length > 0)
    
    // 表单数据模型
    const formData = reactive<Device>({
      name: '',
      sn: '',
      device_type: 'load', // 默认值：用电设备
      device_subtype: undefined,
      device_category: 'load',
      location: '',
      is_active: true,
      description: ''
    })
    const svgOperations = reactive({
      model_number: '',
      rated_voltage: undefined as number | undefined,
      rated_frequency: undefined as number | undefined,
      comm_address: '',
      module_count: undefined as number | undefined,
      single_module_capacity: undefined as number | undefined,
      asset_number: '',
      distribution_room: '',
      distribution_cabinet: '',
      circuit: '',
      om_responsible: '',
      contact_phone: '',
      install_date: '',
      commission_date: '',
      device_alias: '',
      display_name: ''
    })
    const isSvgDeviceType = computed(() => selectedSubtypeKey.value === 'svg')
    
    // 表单校验规则
    const rules = {
      name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
      sn: [{ required: true, message: '请输入唯一序列号', trigger: 'blur' }],
      device_type: [{ required: true, message: '请选择设备类型', trigger: 'change' }],
      device_subtype: [{
        validator: (_rule: unknown, value: string, callback: (error?: Error) => void) => {
          if (!showSubtypeField.value) {
            callback()
            return
          }
          if (!value) {
            callback(new Error('请选择设备子类型'))
            return
          }
          callback()
        },
        trigger: 'change',
      }],
      location: [{ required: true, message: '请输入安装位置', trigger: 'blur' }]
    }

    const inferTypeSelection = (device: Pick<Device, 'device_type' | 'device_category' | 'device_subtype'>) => {
      if (device.device_category === COMPENSATION_TYPE_KEY || ['svg', 'capacitor_bank_controller', 'reactive_power_compensator'].includes(device.device_type)) {
        return COMPENSATION_TYPE_KEY
      }
      return device.device_type
    }

    const inferSubtypeSelection = (device: Pick<Device, 'device_type' | 'device_subtype' | 'device_category'>) => {
      if (device.device_subtype) return device.device_subtype
      if (device.device_category === COMPENSATION_TYPE_KEY || ['svg', 'capacitor_bank_controller', 'reactive_power_compensator'].includes(device.device_type)) {
        return device.device_type === 'reactive_power_compensator' ? 'capacitor_bank_controller' : device.device_type
      }
      return ''
    }

    const resetTypeSelection = () => {
      const defaultType = typeOptions.value[0]?.key || 'load'
      selectedTypeKey.value = defaultType
      selectedSubtypeKey.value = ''
      formData.device_type = defaultType
      formData.device_subtype = undefined
      formData.device_category = defaultType === COMPENSATION_TYPE_KEY ? COMPENSATION_TYPE_KEY : defaultType
    }

    watch(selectedTypeKey, (nextType) => {
      formData.device_type = nextType
      formData.device_category = nextType === COMPENSATION_TYPE_KEY ? COMPENSATION_TYPE_KEY : nextType
      if (!showSubtypeField.value) {
        selectedSubtypeKey.value = ''
        formData.device_subtype = undefined
        return
      }
      const allowedSubtypes = new Set(subtypeOptions.value.map((item) => item.device_type))
      if (!allowedSubtypes.has(selectedSubtypeKey.value)) {
        selectedSubtypeKey.value = ''
      }
      formData.device_subtype = selectedSubtypeKey.value || undefined
    })

    watch(selectedSubtypeKey, (nextSubtype) => {
      formData.device_subtype = nextSubtype || undefined
    })
    
    // --- 1. 获取设备列表 ---
    const fetchData = async () => {
      loading.value = true
      try {
        const res = await getDevices()
        // 按 ID 排序
        tableData.value = res.sort((a, b) => (a.id || 0) - (b.id || 0))
      } catch {
        // 由 axios 拦截器统一提示
      } finally {
        loading.value = false
      }
    }
    
    // --- 2. 新增 / 编辑 ---
    const resetSvgOperations = () => {
      svgOperations.model_number = ''
      svgOperations.rated_voltage = undefined
      svgOperations.rated_frequency = undefined
      svgOperations.comm_address = ''
      svgOperations.module_count = undefined
      svgOperations.single_module_capacity = undefined
      svgOperations.asset_number = ''
      svgOperations.distribution_room = ''
      svgOperations.distribution_cabinet = ''
      svgOperations.circuit = ''
      svgOperations.om_responsible = ''
      svgOperations.contact_phone = ''
      svgOperations.install_date = ''
      svgOperations.commission_date = ''
      svgOperations.device_alias = ''
      svgOperations.display_name = ''
    }

    const openDialog = async (row?: Device | null) => {
      if (!canManageDevicesValue.value) {
        ElMessage.warning('当前账号无权新增或编辑设备')
        return
      }
      resetSvgOperations()
      if (row && typeof row === 'object' && 'name' in row) {
        dialogTitle.value = '编辑设备'
        // 复制数据到表单 (注意深拷贝或 Object.assign)
        Object.assign(formData, row)
        selectedTypeKey.value = inferTypeSelection(row)
        selectedSubtypeKey.value = inferSubtypeSelection(row)
        formData.device_type = selectedTypeKey.value
        formData.device_subtype = selectedSubtypeKey.value || undefined
        formData.device_category = selectedTypeKey.value === COMPENSATION_TYPE_KEY ? COMPENSATION_TYPE_KEY : row.device_category
        if (selectedSubtypeKey.value === 'svg' && row.id) {
          try {
            const profile = await getSVGOperationsProfile(row.id)
            Object.assign(svgOperations, {
              model_number: profile.model_number || '',
              rated_voltage: profile.rated_voltage ?? undefined,
              rated_frequency: profile.rated_frequency ?? undefined,
              comm_address: profile.comm_address || '',
              module_count: profile.module_count ?? undefined,
              single_module_capacity: profile.single_module_capacity ?? undefined,
              asset_number: profile.asset_number || '',
              distribution_room: profile.distribution_room || '',
              distribution_cabinet: profile.distribution_cabinet || '',
              circuit: profile.circuit || '',
              om_responsible: profile.om_responsible || '',
              contact_phone: profile.contact_phone || '',
              install_date: profile.install_date || '',
              commission_date: profile.commission_date || '',
              device_alias: profile.device_alias || '',
              display_name: profile.display_name || '',
            })
          } catch {
            // 允许编辑设备主档时 SVG 运维档案为空
          }
        }
      } else {
        dialogTitle.value = '新增设备'
        // 重置表单
        formData.id = undefined
        formData.name = ''
        formData.sn = ''
        formData.location = ''
        formData.is_active = true
        formData.description = ''
        resetTypeSelection()
      }
      dialogVisible.value = true
    }
    
    const handleSubmit = async () => {
      if (!formRef.value) return
      
      await formRef.value.validate(async (valid: boolean) => {
        if (valid) {
          formLoading.value = true
          try {
            const payload: DeviceWritePayload = {
              ...formData,
            }
            if (selectedTypeKey.value === COMPENSATION_TYPE_KEY) {
              payload.device_type = COMPENSATION_TYPE_KEY
              payload.device_category = COMPENSATION_TYPE_KEY
              payload.device_subtype = selectedSubtypeKey.value || undefined
            } else {
              payload.device_type = selectedTypeKey.value
              payload.device_category = selectedTypeKey.value
              payload.device_subtype = undefined
            }
            if (isSvgDeviceType.value) {
              payload.svg_operations = Object.fromEntries(
                Object.entries(svgOperations).filter(([, value]) => value !== '' && value !== undefined && value !== null)
              )
            }
            if (formData.id) {
              // 编辑模式
              await updateDevice(formData.id, payload)
              ElMessage.success('设备更新成功')
              notifyDevicesUpdated({ source: 'device-manager', action: 'update', deviceId: formData.id })
            } else {
              // 新增模式
              const createdDevice = await createDevice(payload)
              ElMessage.success('设备创建成功')
              notifyDevicesUpdated({ source: 'device-manager', action: 'create', deviceId: createdDevice.id })
            }
            dialogVisible.value = false
            fetchData() // 刷新列表
          } catch {
            // 由 axios 拦截器统一提示
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
            notifyDevicesUpdated({ source: 'device-manager', action: 'delete', deviceId: row.id })
            fetchData()
          }
        } catch {
          // 由 axios 拦截器统一提示
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
              notifyDevicesUpdated({ source: 'device-manager', action: 'toggle', deviceId: row.id, active: newVal })
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
        if (res.length) {
          deviceTypes.value = res
        }
      } catch {
        deviceTypes.value = FALLBACK_DEVICE_TYPE_CONFIGS
      }
      if (!formData.id) {
        resetTypeSelection()
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
        <h2 class="page-title">
          设备全生命周期台账
        </h2>
        <el-tag
          v-if="hasScopedAccess"
          size="small"
          effect="dark"
          type="warning"
        >
          当前列表已按位置范围过滤
        </el-tag>
      </div>
      <div class="right">
        <el-button
          :icon="Refresh"
          circle
          @click="fetchData"
        />
        <el-button
          v-if="canManageDevicesValue"
          type="primary"
          :icon="Plus"
          @click="openDialog()"
        >
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
      <el-table-column
        prop="id"
        label="ID"
        width="80"
        align="center"
      />
          
      <el-table-column
        label="设备名称"
        min-width="180"
      >
        <template #default="{ row }">
          <div class="device-name-cell">
            <span class="name">{{ row.name }}</span>
            <el-tag
              size="small"
              type="info"
              effect="dark"
              class="sn-tag"
            >
              {{ row.sn }}
            </el-tag>
          </div>
        </template>
      </el-table-column>
    
      <el-table-column
        prop="device_type"
        label="设备类型"
        width="160"
      >
        <template #default="{ row }">
          <span>{{ getCategoryLabel(row.device_category) }}</span>
        </template>
      </el-table-column>

      <el-table-column
        label="设备子类型"
        width="160"
      >
        <template #default="{ row }">
          <span>{{ row.device_subtype ? getSubtypeLabel(row.device_subtype) : '--' }}</span>
        </template>
      </el-table-column>
    
      <el-table-column
        prop="location"
        label="安装位置"
        width="150"
      />
    
      <el-table-column
        label="运行状态 (远程控制)"
        width="200"
      >
        <template #default="{ row }">
          <el-switch
            v-model="row.is_active"
            inline-prompt
            active-text="运行中"
            inactive-text="已停机"
            style="--el-switch-on-color: #10b981; --el-switch-off-color: #ef4444"
            :disabled="!canControlDevicesValue"
            :before-change="() => handleStatusChange(!row.is_active, row)"
          />
        </template>
      </el-table-column>
    
      <el-table-column
        label="监控"
        width="90"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button
            link
            type="success"
            :icon="Monitor"
            @click="row.id && router.push(`/devices/${row.id}/monitor`)"
          >
            监控
          </el-button>
        </template>
      </el-table-column>

      <el-table-column
        v-if="canManageDevicesValue"
        label="操作"
        width="180"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            :icon="Edit"
            @click="openDialog(row)"
          >
            编辑
          </el-button>
          <el-button
            link
            type="danger"
            :icon="Delete"
            @click="handleDelete(row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
      class="custom-dialog"
      append-to-body
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="100px"
        status-icon
      >
        <el-form-item
          label="设备名称"
          prop="name"
        >
          <el-input
            v-model="formData.name"
            placeholder="例如: 智能电表"
          />
        </el-form-item>
            
        <el-form-item
          label="序列号 SN"
          prop="sn"
        >
          <el-input
            v-model="formData.sn"
            placeholder="例如: METER-001"
            :disabled="!!formData.id"
          />
        </el-form-item>
    
        <el-form-item
          label="设备类型"
          prop="device_type"
        >
          <el-select
            v-model="selectedTypeKey"
            placeholder="请选择设备类型"
            style="width:100%"
          >
            <el-option 
              v-for="option in typeOptions" 
              :key="option.key" 
              :label="`${option.label} (${option.unit})`" 
              :value="option.key"
            >
              <span style="float: left">{{ option.label }}</span>
              <span style="float: right; color: #8492a6; font-size: 12px">{{ option.unit }}</span>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item
          v-if="showSubtypeField"
          label="设备子类型"
          prop="device_subtype"
        >
          <el-select
            v-model="selectedSubtypeKey"
            placeholder="请选择设备子类型"
            style="width:100%"
          >
            <el-option
              v-for="option in subtypeOptions"
              :key="option.device_type"
              :label="`${getSubtypeLabel(option.device_type)} (${option.unit})`"
              :value="option.device_type"
            >
              <span style="float: left">{{ getSubtypeLabel(option.device_type) }}</span>
              <span style="float: right; color: #8492a6; font-size: 12px">{{ option.unit }}</span>
            </el-option>
          </el-select>
        </el-form-item>
    
        <el-form-item
          label="安装位置"
          prop="location"
        >
          <el-input
            v-model="formData.location"
            placeholder="例如: 总配电室"
          />
        </el-form-item>
            
        <el-form-item
          label="描述备注"
          prop="description"
        >
          <el-input
            v-model="formData.description"
            type="textarea"
          />
        </el-form-item>

        <template v-if="isSvgDeviceType">
          <el-divider content-position="left">SVG 运维档案</el-divider>
          <el-form-item label="设备型号">
            <el-input v-model="svgOperations.model_number" placeholder="例如: SVG-400/0.4" />
          </el-form-item>
          <el-form-item label="额定电压">
            <el-input-number v-model="svgOperations.rated_voltage" :min="0" :precision="1" style="width:100%" />
          </el-form-item>
          <el-form-item label="额定频率">
            <el-input-number v-model="svgOperations.rated_frequency" :min="0" :precision="2" style="width:100%" />
          </el-form-item>
          <el-form-item label="通信地址">
            <el-input v-model="svgOperations.comm_address" placeholder="例如: 01" />
          </el-form-item>
          <el-form-item label="模块数量">
            <el-input-number v-model="svgOperations.module_count" :min="0" style="width:100%" />
          </el-form-item>
          <el-form-item label="单模块容量">
            <el-input-number v-model="svgOperations.single_module_capacity" :min="0" :precision="1" style="width:100%" />
          </el-form-item>
          <el-form-item label="资产编号">
            <el-input v-model="svgOperations.asset_number" />
          </el-form-item>
          <el-form-item label="所属配电室">
            <el-input v-model="svgOperations.distribution_room" />
          </el-form-item>
          <el-form-item label="所属配电柜">
            <el-input v-model="svgOperations.distribution_cabinet" />
          </el-form-item>
          <el-form-item label="所属回路">
            <el-input v-model="svgOperations.circuit" />
          </el-form-item>
          <el-form-item label="运维负责人">
            <el-input v-model="svgOperations.om_responsible" />
          </el-form-item>
          <el-form-item label="联系电话">
            <el-input v-model="svgOperations.contact_phone" />
          </el-form-item>
          <el-form-item label="安装日期">
            <el-date-picker v-model="svgOperations.install_date" type="date" value-format="YYYY-MM-DD" placeholder="选择安装日期" style="width:100%" />
          </el-form-item>
          <el-form-item label="投运日期">
            <el-date-picker v-model="svgOperations.commission_date" type="date" value-format="YYYY-MM-DD" placeholder="选择投运日期" style="width:100%" />
          </el-form-item>
          <el-form-item label="设备别名">
            <el-input v-model="svgOperations.device_alias" />
          </el-form-item>
          <el-form-item label="上位机名称">
            <el-input v-model="svgOperations.display_name" />
          </el-form-item>
        </template>
      </el-form>
          
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            :loading="formLoading"
            @click="handleSubmit"
          >
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
      position: relative;
      overflow: visible;
    }
    
    .toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      position: relative;
      z-index: 20;
      pointer-events: auto;
    }
    .left,
    .right {
      position: relative;
      z-index: 21;
    }
    .right {
      display: flex;
      align-items: center;
      gap: 12px;
      pointer-events: auto;
    }
    .page-title { margin: 0; font-size: 18px; border-left: 4px solid var(--brand-color); padding-left: 10px; color: #fff; }
    .custom-table {
      position: relative;
      z-index: 1;
    }
    
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
    :deep(.el-table__fixed),
    :deep(.el-table__fixed-right) {
      z-index: 2;
    }
    </style>
