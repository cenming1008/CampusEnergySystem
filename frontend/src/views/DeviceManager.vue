<script setup lang="ts">
    import { ref, reactive, onMounted, computed, unref, watch } from 'vue'
    import { useRoute, useRouter } from 'vue-router'
    import { usePermissions } from '@/shared/composables/usePermissions'
    import { isCompensationDeviceIdentity, normalizeCompensationDevice, resolveCompensationSubtype } from '@/shared/compensationDevices'
    import { getDeviceCategoryLabel, getDeviceSubtypeLabel } from '@/shared/deviceTypeLabels'
    import { getCompensationSvgOperationsProfile } from '@/api/compensation'
    import { 
      getDevices, createDevice, updateDevice, deleteDevice, toggleDeviceStatus,
      FALLBACK_DEVICE_TYPE_CONFIGS, getDeviceTypes, notifyDevicesUpdated,
      type Device, type DeviceTypeConfig, type DeviceWritePayload
    } from '@/api/device'
    import { ElMessage, ElMessageBox } from 'element-plus'
    import { Plus, Search, Refresh, Delete, Edit, Monitor, Setting } from '@element-plus/icons-vue'
    
    // --- 状态定义 ---
    const loading = ref(false)
	    const router = useRouter()
	    const route = useRoute()
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

    const typeSummary = computed(() => {
      const summary = new Map<string, { key: string; label: string; count: number }>()
      for (const device of tableData.value) {
        const key = device.device_category || device.device_type || 'unknown'
        const current = summary.get(key) || {
          key,
          label: getCategoryLabel(key),
          count: 0,
        }
        current.count += 1
        summary.set(key, current)
      }
      return Array.from(summary.values())
        .sort((left, right) => right.count - left.count)
        .slice(0, 5)
    })

    const routeCategory = computed(() => String(route.query.category || '').trim())
    const categoryAliases: Record<string, string[]> = {
      electricity: ['load', 'electricity', 'charger', 'compensation'],
      elec: ['load', 'electricity', 'charger', 'compensation'],
      'pv-storage': ['pv', 'solar', 'storage'],
      'cool-heat': ['cooling', 'heat', 'cooling_meter', 'heat_meter'],
      'water-gas': ['water', 'gas', 'water_meter', 'gas_meter'],
    }
    const filteredTableData = computed(() => {
      const category = routeCategory.value
      if (!category) return tableData.value
      const accepted = categoryAliases[category] || [category]
      return tableData.value.filter((device) => accepted.some((key) => (
        device.device_category === key ||
        device.device_type === key ||
        device.energy_type === key
      )))
    })
    
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
      if (isCompensationDeviceIdentity(device)) {
        return COMPENSATION_TYPE_KEY
      }
      return device.device_type
    }

    const inferSubtypeSelection = (device: Pick<Device, 'device_type' | 'device_subtype' | 'device_category'>) => {
      return resolveCompensationSubtype(device.device_type, device.device_subtype) || ''
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
        const res = await getDevices({ silent: true })
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
        const normalizedRow = normalizeCompensationDevice(row)
        dialogTitle.value = '编辑设备'
        // 复制数据到表单 (注意深拷贝或 Object.assign)
        Object.assign(formData, normalizedRow)
        selectedTypeKey.value = inferTypeSelection(normalizedRow)
        selectedSubtypeKey.value = inferSubtypeSelection(normalizedRow)
        formData.device_type = selectedTypeKey.value
        formData.device_subtype = selectedSubtypeKey.value || undefined
        formData.device_category = selectedTypeKey.value === COMPENSATION_TYPE_KEY ? COMPENSATION_TYPE_KEY : normalizedRow.device_category
        if (selectedSubtypeKey.value === 'svg' && normalizedRow.id) {
          try {
            const profile = await getCompensationSvgOperationsProfile(normalizedRow.id)
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
    
    // --- 4. 核心：设备启用状态切换 (Switch) ---
    // 使用 before-change 钩子处理异步请求
    const handleStatusChange = (newVal: boolean, row: Device) => {
      return new Promise<boolean>((resolve, reject) => {
        const actionName = newVal ? '启用' : '停用'
        
        // 二次确认
        ElMessageBox.confirm(
          `确定要将 ${row.name} 标记为【${actionName}】吗？`,
          '管理状态确认',
          {
            confirmButtonText: `确认${actionName}`,
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
                message: `管理状态已更新：设备已${actionName}`,
                type: 'success',
              })
              resolve(true) // 允许 Switch 切换状态
            } else {
              reject()
            }
          } catch (e) {
            ElMessage.error('管理状态更新失败')
            reject(e) // 阻止 Switch 切换状态
          }
        }).catch(() => {
          reject() // 用户取消
        })
      })
    }

    const isCapacitorBankController = (row: Device) =>
      resolveCompensationSubtype(row.device_type, row.device_subtype) === 'capacitor_bank_controller'

    const isPendingArchiveDevice = (row: Device) => row.archive_status === 'pending'
    const pendingArchiveMessage = '请先补全设备档案后再进入监控或控制台'

    const openDeviceMonitor = (row: Device) => {
      if (!row.id) return
      if (isPendingArchiveDevice(row)) {
        ElMessage.warning(pendingArchiveMessage)
        return
      }
      router.push(`/devices/${row.id}/monitor`)
    }

    const openDeviceConsole = (row: Device) => {
      if (!row.id) return
      if (isPendingArchiveDevice(row)) {
        ElMessage.warning(pendingArchiveMessage)
        return
      }
      router.push(`/devices/${row.id}/monitor?tab=remote-control`)
    }
    
    // --- 获取设备类型列表 ---
    const fetchDeviceTypes = async () => {
      try {
        const res = await getDeviceTypes({ silent: true })
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
    <div class="device-noise" />

    <header class="device-header glass-panel">
      <div class="device-brand-block">
        <div class="device-brand-mark">
          <span class="device-brand-mark__dot" />
        </div>
        <div class="device-brand-text">
          <p class="device-eyebrow">Device Registry</p>
          <h1>设备与表计</h1>
          <p class="device-subtitle">维护园区设备、表计和补偿装置台账，进入实时监控与控制台。</p>
          <div class="device-tags">
            <span class="device-tag">全生命周期台账</span>
            <span
              v-if="hasScopedAccess"
              class="device-tag device-tag--warn"
            >
              位置范围过滤中
            </span>
          </div>
        </div>
      </div>
      <div class="device-header-actions">
        <el-button
          :icon="Refresh"
          @click="fetchData"
        >
          刷新列表
        </el-button>
        <el-button
          v-if="canManageDevicesValue"
          type="primary"
          :icon="Plus"
          @click="openDialog()"
        >
          新增设备
        </el-button>
      </div>
    </header>

    <section class="device-table-panel glass-panel">
      <div class="table-panel-head">
        <div>
          <p class="section-label">设备台账</p>
          <h2>资产列表</h2>
        </div>
        <div
          v-if="typeSummary.length"
          class="type-summary"
        >
          <span class="type-summary__label">类型覆盖</span>
          <span
            v-for="item in typeSummary"
            :key="item.key"
            class="type-chip"
          >
            {{ item.label }} · {{ item.count }}
          </span>
        </div>
      </div>

      <el-table
        v-loading="loading"
        :data="filteredTableData"
        style="width: 100%"
        class="custom-table"
        empty-text="暂无设备数据"
      >
        <el-table-column
          prop="id"
          label="ID"
          width="80"
          align="center"
        />

        <el-table-column
          label="设备名称"
          min-width="200"
        >
          <template #default="{ row }">
            <div class="device-name-cell">
              <span class="name">{{ row.name }}</span>
              <div class="device-meta-row">
                <el-tag
                  v-if="isPendingArchiveDevice(row)"
                  size="small"
                  type="warning"
                  effect="plain"
                >
                  待完善
                </el-tag>
                <el-tag
                  size="small"
                  type="info"
                  effect="plain"
                  class="sn-tag"
                >
                  {{ row.sn }}
                </el-tag>
              </div>
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
          label="管理状态"
          width="180"
        >
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              inline-prompt
              active-text="启用"
              inactive-text="停用"
              style="--el-switch-on-color: #10b981; --el-switch-off-color: #ef4444"
              :disabled="!canControlDevicesValue || isPendingArchiveDevice(row)"
              :before-change="() => handleStatusChange(!row.is_active, row)"
            />
          </template>
        </el-table-column>

        <el-table-column
          label="监控"
          width="90"
        >
          <template #default="{ row }">
            <el-button
              link
              type="success"
              :icon="Monitor"
              :disabled="isPendingArchiveDevice(row)"
              @click="openDeviceMonitor(row)"
            >
              监控
            </el-button>
          </template>
        </el-table-column>

        <el-table-column
          label="控制台"
          width="96"
        >
          <template #default="{ row }">
            <el-button
              v-if="isCapacitorBankController(row)"
              link
              type="warning"
              :icon="Setting"
              :disabled="isPendingArchiveDevice(row)"
              @click="openDeviceConsole(row)"
            >
              控制台
            </el-button>
            <span v-else class="empty-dash">--</span>
          </template>
        </el-table-column>

        <el-table-column
          v-if="canManageDevicesValue"
          label="操作"
          width="180"
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
    </section>
    
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
      position: relative;
      display: flex;
      flex-direction: column;
      gap: 12px;
      width: 100%;
      min-height: 100%;
      height: auto;
      padding: 16px;
      overflow-x: hidden;
      box-sizing: border-box;
      color: #f5f7fa;
      background:
        radial-gradient(circle at top left, rgba(96, 165, 250, 0.08), transparent 28%),
        radial-gradient(circle at bottom right, rgba(52, 211, 153, 0.05), transparent 26%),
        #090e17;
    }

    .device-noise {
      position: absolute;
      inset: 0;
      z-index: 0;
      pointer-events: none;
      background: linear-gradient(180deg, rgba(255,255,255,0.012), transparent 20%, transparent 80%, rgba(255,255,255,0.012));
      opacity: 0.3;
    }

    .glass-panel {
      position: relative;
      z-index: 1;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.04);
      backdrop-filter: blur(18px) saturate(145%);
      box-shadow: inset 0 0 0 1px rgba(255,255,255,0.06), 0 10px 28px rgba(0,0,0,0.18);
      overflow: hidden;
    }

    .device-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      min-height: 112px;
      padding: 22px;
      box-sizing: border-box;
    }

    .device-brand-block {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      min-width: 0;
    }

    .device-brand-mark {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 52px;
      height: 52px;
      margin-top: 2px;
      border-radius: 14px;
      flex-shrink: 0;
      background: rgba(52, 211, 153, 0.12);
      box-shadow: inset 0 0 0 1px rgba(255,255,255,0.08);
    }

    .device-brand-mark__dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: #34d399;
      box-shadow: 0 0 12px rgba(52, 211, 153, 0.58);
    }

    .device-brand-text {
      display: flex;
      flex-direction: column;
      gap: 2px;
      min-width: 0;
    }

    .device-eyebrow {
      margin: 0;
      font-size: 10px;
      font-weight: 600;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: rgba(255,255,255,0.46);
    }

    .device-brand-text h1 {
      margin: 0;
      font-size: 26px;
      font-weight: 700;
      line-height: 1.02;
      letter-spacing: 0;
      color: #f5f7fa;
    }

    .device-subtitle {
      margin: 0;
      max-width: 560px;
      font-size: 12px;
      line-height: 1.3;
      color: rgba(255,255,255,0.44);
    }

    .device-tags,
    .device-header-actions,
    .type-summary,
    .device-meta-row {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }

    .device-tags {
      margin-top: 8px;
    }

    .device-header-actions {
      justify-content: flex-end;
      flex-shrink: 0;
    }

    .device-tag {
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      padding: 3px 10px;
      border-radius: 999px;
      font-size: 11px;
      color: rgba(255,255,255,0.62);
      background: rgba(255,255,255,0.045);
      border: 1px solid rgba(255,255,255,0.08);
    }

    .device-tag--warn {
      color: #fdba74;
      border-color: rgba(251, 146, 60, 0.28);
      background: rgba(251, 146, 60, 0.08);
    }

    .device-table-panel {
      display: flex;
      flex-direction: column;
      gap: 14px;
      padding: 18px 20px 20px;
    }

    .table-panel-head {
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 16px;
      padding-bottom: 12px;
      border-bottom: 1px solid rgba(255,255,255,0.06);
    }

    .section-label {
      margin: 0 0 4px;
      font-size: 10px;
      font-weight: 600;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: rgba(255,255,255,0.4);
    }

    .table-panel-head h2 {
      margin: 0;
      font-size: 16px;
      font-weight: 700;
      letter-spacing: 0;
      color: #f0f6ff;
    }

    .type-summary {
      justify-content: flex-end;
      max-width: 760px;
    }

    .type-summary__label {
      font-size: 11px;
      color: rgba(255,255,255,0.38);
    }

    .type-chip {
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      padding: 3px 9px;
      border-radius: 999px;
      border: 1px solid rgba(255,255,255,0.08);
      background: rgba(255,255,255,0.04);
      color: rgba(226,232,240,0.66);
      font-size: 11px;
      white-space: nowrap;
    }

    .custom-table {
      --el-table-bg-color: transparent;
      --el-table-tr-bg-color: transparent;
      --el-table-header-bg-color: rgba(255,255,255,0.035);
      --el-table-row-hover-bg-color: rgba(255,255,255,0.055);
      --el-table-border-color: rgba(255,255,255,0.06);
      --el-table-text-color: rgba(255,255,255,0.8);
      --el-table-header-text-color: rgba(255,255,255,0.46);
      --el-bg-color: transparent;
      --el-fill-color-lighter: rgba(255,255,255,0.04);
      position: relative;
      z-index: 1;
      border-radius: 12px;
      overflow: hidden;
      background: transparent;
      color: rgba(255,255,255,0.8);
    }

    .custom-table :deep(.el-table),
    .custom-table :deep(.el-table__inner-wrapper),
    .custom-table :deep(.el-scrollbar),
    .custom-table :deep(.el-scrollbar__view),
    .custom-table :deep(.el-table__body-wrapper),
    .custom-table :deep(.el-table__header-wrapper) {
      background: transparent;
      color: rgba(255,255,255,0.8);
    }

    .custom-table :deep(.el-table__inner-wrapper::before),
    .custom-table :deep(.el-table::before),
    .custom-table :deep(.el-table__border-left-patch) {
      display: none;
    }

    .custom-table :deep(th.el-table__cell) {
      background: rgba(255,255,255,0.03) !important;
      color: rgba(255,255,255,0.46);
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      border-bottom-color: rgba(255,255,255,0.06);
    }

    .custom-table :deep(td.el-table__cell) {
      background: transparent !important;
      border-bottom-color: rgba(255,255,255,0.045);
      color: rgba(255,255,255,0.78);
      font-size: 13px;
    }

    .custom-table :deep(.el-table__row:hover > td.el-table__cell),
    .custom-table :deep(.el-table__body tr.hover-row > td.el-table__cell),
    .custom-table :deep(.el-table__body tr:hover > td.el-table__cell) {
      background: rgba(255,255,255,0.055) !important;
    }

    .custom-table :deep(.el-table-fixed-column--right),
    .custom-table :deep(.el-table-fixed-column--left) {
      background: #101827 !important;
    }

    .custom-table :deep(.el-table__empty-block) {
      background: transparent;
    }

    .custom-table :deep(.el-loading-mask) {
      background: rgba(9, 14, 23, 0.72);
    }

    .device-name-cell {
      display: flex;
      flex-direction: column;
      gap: 6px;
      min-width: 0;
    }

    .name {
      font-weight: 700;
      color: #f8fafc;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .sn-tag {
      width: fit-content;
      max-width: 100%;
      font-size: 10px;
      height: 20px;
      line-height: 18px;
    }

    .empty-dash {
      color: rgba(255,255,255,0.34);
    }

    :deep(.el-button) {
      min-height: 34px;
      border-radius: 20px;
      font-weight: 500;
    }

    :deep(.el-button--primary) {
      border-color: rgba(96, 165, 250, 0.34);
      background: linear-gradient(135deg, rgba(96, 165, 250, 0.9), rgba(103, 232, 249, 0.72));
      color: #06111f;
    }

    :deep(.el-button:not(.el-button--primary):not(.el-button--danger):not(.is-link)) {
      border-color: rgba(255,255,255,0.08);
      background: rgba(255,255,255,0.045);
      color: rgba(255,255,255,0.72);
    }

    :deep(.el-button.is-link) {
      min-height: 28px;
      padding: 0 4px;
      border-radius: 6px;
      border-color: transparent !important;
      background: transparent !important;
      box-shadow: none;
    }

    :deep(.el-button.is-link.el-button--primary) {
      color: #60a5fa;
    }

    :deep(.el-button.is-link.el-button--success) {
      color: #7ddc50;
    }

    :deep(.el-button.is-link.el-button--warning) {
      color: #fbbf24;
    }

    :deep(.el-button.is-link.el-button--danger) {
      color: #f87171;
    }

    :deep(.el-tag) {
      border-radius: 7px;
      border-color: rgba(255,255,255,0.12);
      background: rgba(255,255,255,0.06);
      color: rgba(226,232,240,0.76);
    }

    :deep(.el-tag.el-tag--info) {
      border-color: rgba(148, 163, 184, 0.18);
      background: rgba(148, 163, 184, 0.08);
      color: rgba(226,232,240,0.64);
    }

    :deep(.el-tag.el-tag--warning) {
      border-color: rgba(251, 146, 60, 0.3);
      background: rgba(251, 146, 60, 0.1);
      color: #fdba74;
    }

    :deep(.el-switch__core) {
      border-color: rgba(255,255,255,0.14);
    }

    :deep(.el-switch__action) {
      background: #dbeafe;
    }

    :global(.custom-dialog) {
      border-radius: 16px;
      overflow: hidden;
      background: #111827;
      box-shadow: 0 24px 80px rgba(0,0,0,0.42), inset 0 0 0 1px rgba(255,255,255,0.08);
    }

    :global(.custom-dialog .el-dialog__header) {
      margin: 0;
      padding: 18px 22px 14px;
      border-bottom: 1px solid rgba(255,255,255,0.06);
      background: rgba(255,255,255,0.035);
    }

    :global(.custom-dialog .el-dialog__title) {
      color: #f8fafc;
      font-weight: 700;
      letter-spacing: 0;
    }

    :global(.custom-dialog .el-dialog__body) {
      max-height: min(68vh, 680px);
      overflow: auto;
      padding: 20px 22px;
      background: #111827;
      color: rgba(226,232,240,0.76);
    }

    :global(.custom-dialog .el-dialog__footer) {
      padding: 14px 22px 18px;
      border-top: 1px solid rgba(255,255,255,0.06);
      background: #111827;
    }

    :global(.custom-dialog .el-form-item__label) {
      color: rgba(226,232,240,0.62);
      font-weight: 500;
    }

    :global(.custom-dialog .el-input__wrapper),
    :global(.custom-dialog .el-select__wrapper),
    :global(.custom-dialog .el-textarea__inner),
    :global(.custom-dialog .el-input-number .el-input__wrapper),
    :global(.custom-dialog .el-date-editor.el-input__wrapper) {
      min-height: 34px;
      border-radius: 8px;
      border: none;
      background: rgba(255,255,255,0.055);
      box-shadow: inset 0 0 0 1px rgba(255,255,255,0.08);
    }

    :global(.custom-dialog .el-input__inner),
    :global(.custom-dialog .el-select__selected-item),
    :global(.custom-dialog .el-textarea__inner) {
      color: rgba(255,255,255,0.84);
    }

    :global(.custom-dialog .el-input__inner::placeholder),
    :global(.custom-dialog .el-textarea__inner::placeholder) {
      color: rgba(255,255,255,0.3);
    }

    :global(.custom-dialog .el-input-number__decrease),
    :global(.custom-dialog .el-input-number__increase) {
      border-color: rgba(255,255,255,0.08);
      background: rgba(255,255,255,0.055);
      color: rgba(255,255,255,0.58);
    }

    :global(.custom-dialog .el-divider__text) {
      background: #111827;
      color: rgba(255,255,255,0.62);
    }

    :global(.custom-dialog .el-dialog__headerbtn .el-dialog__close) {
      color: rgba(255,255,255,0.58);
    }

    .dialog-footer {
      display: flex;
      justify-content: flex-end;
      gap: 10px;
    }

    @media (max-width: 1280px) {
      .table-panel-head {
        align-items: flex-start;
        flex-direction: column;
      }

      .type-summary {
        justify-content: flex-start;
      }
    }

    @media (max-width: 768px) {
      .device-container {
        padding: 12px;
        gap: 10px;
      }

      .device-header {
        flex-direction: column;
        align-items: flex-start;
        padding: 14px 16px;
      }

      .device-brand-text h1 {
        font-size: 22px;
      }

      .device-header-actions {
        justify-content: flex-start;
        width: 100%;
      }

      .device-table-panel {
        padding: 14px 16px;
      }
    }
    </style>
