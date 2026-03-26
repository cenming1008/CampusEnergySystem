<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getMaintenanceDetail,
  getMaintenanceList,
  getMaintenanceTypes,
  getMaintenanceStatuses,
  createMaintenance,
  startMaintenance,
  completeMaintenance,
  cancelMaintenance,
  deleteMaintenance,
  getUpcomingMaintenance,
  getOverdueMaintenance,
  getMaintenanceStatistics,
  getDeviceMaintenanceHistory,
  updateMaintenance,
  type MaintenanceRecord,
  type MaintenanceTypeInfo,
  type MaintenanceStatusInfo,
  type MaintenanceCreateRequest,
  type MaintenanceCompleteRequest,
  type MaintenanceUpdateRequest,
  type MaintenanceStatistics
} from '@/api/maintenance'
import { getDevices, type Device } from '@/api/device'
import { usePermissions } from '@/shared/composables/usePermissions'

const isPromptCancelled = (error: unknown) => error === 'cancel' || error === 'close'

// --- 状态 ---
const loading = ref(false)
const maintenanceList = ref<MaintenanceRecord[]>([])
const upcomingList = ref<MaintenanceRecord[]>([])
const overdueList = ref<MaintenanceRecord[]>([])
const deviceList = ref<Device[]>([])
const typeList = ref<MaintenanceTypeInfo[]>([])
const statusList = ref<MaintenanceStatusInfo[]>([])
const statistics = ref<MaintenanceStatistics | null>(null)

// 筛选条件
const filters = reactive({
  device_id: undefined as number | undefined,
  maintenance_type: '',
  status: ''
})

// 对话框状态
const dialogVisible = ref(false)
const detailDialogVisible = ref(false)
const historyDialogVisible = ref(false)
const dialogType = ref<'create' | 'edit' | 'complete'>('create')
const dialogTitle = computed(() => {
  if (dialogType.value === 'create') return '新建维护计划'
  if (dialogType.value === 'edit') return '编辑维护计划'
  return '完成维护'
})
const detailRecord = ref<MaintenanceRecord | null>(null)
const historyRecords = ref<MaintenanceRecord[]>([])

// 表单数据
const formData = reactive<MaintenanceCreateRequest>({
  device_id: 0,
  maintenance_type: 'routine',
  scheduled_time: '',
  title: '',
  description: '',
  operator: ''
})

const editFormData = reactive<MaintenanceUpdateRequest & { id: number }>({
  id: 0,
  scheduled_time: '',
  title: '',
  description: '',
  operator: '',
})

const completeFormData = reactive<MaintenanceCompleteRequest & { id: number }>({
  id: 0,
  result: '',
  cost: undefined,
  parts_replaced: '',
  next_maintenance_date: ''
})

// 当前选中的Tab
const activeTab = ref('all')
const { canManageMaintenance, canOperateMaintenance, hasScopedAccess } = usePermissions()

// --- 计算属性 ---
const statusTagType = (status: string) => {
  const map: Record<string, string> = {
    scheduled: 'info',
    in_progress: 'warning',
    completed: 'success',
    cancelled: 'danger'
  }
  return map[status] || 'info'
}

const statusLabel = (status: string) => {
  const item = statusList.value.find(s => s.value === status)
  return item?.label || status
}

const typeLabel = (type: string) => {
  const item = typeList.value.find(t => t.value === type)
  return item?.label || type
}

const deviceName = (deviceId: number) => {
  const device = deviceList.value.find(d => d.id === deviceId)
  return device?.name || `设备 ${deviceId}`
}

const statsByStatus = computed(() => statistics.value?.by_status || {})
const completedCount = computed(() => statistics.value?.completed_count || 0)

// --- 方法 ---
const loadData = async () => {
  loading.value = true
  try {
    const [list, upcoming, overdue, stats] = await Promise.all([
      getMaintenanceList({
        device_id: filters.device_id,
        maintenance_type: filters.maintenance_type || undefined,
        status: filters.status || undefined,
        limit: 100
      }),
      getUpcomingMaintenance(7),
      getOverdueMaintenance(),
      getMaintenanceStatistics()
    ])
    maintenanceList.value = list
    upcomingList.value = upcoming
    overdueList.value = overdue
    statistics.value = stats.data || null
  } catch (e) {
    console.error('加载维护数据失败:', e)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const loadBaseData = async () => {
  try {
    const [devices, types, statuses] = await Promise.all([
      getDevices(),
      getMaintenanceTypes(),
      getMaintenanceStatuses()
    ])
    deviceList.value = devices
    typeList.value = types.data || []
    statusList.value = statuses.data || []
  } catch (e) {
    console.error('加载基础数据失败:', e)
  }
}

const handleFilter = () => {
  loadData()
}

const resetFilters = () => {
  filters.device_id = undefined
  filters.maintenance_type = ''
  filters.status = ''
  loadData()
}

const openCreateDialog = () => {
  dialogType.value = 'create'
  formData.device_id = deviceList.value[0]?.id || 0
  formData.maintenance_type = 'routine'
  formData.scheduled_time = ''
  formData.title = ''
  formData.description = ''
  formData.operator = ''
  dialogVisible.value = true
}

const openEditDialog = async (record: MaintenanceRecord) => {
  dialogType.value = 'edit'
  const detail = await getMaintenanceDetail(record.id)
  editFormData.id = detail.id
  editFormData.scheduled_time = detail.scheduled_time
  editFormData.title = detail.title
  editFormData.description = detail.description || ''
  editFormData.operator = detail.operator || ''
  dialogVisible.value = true
}

const openCompleteDialog = (record: MaintenanceRecord) => {
  dialogType.value = 'complete'
  completeFormData.id = record.id
  completeFormData.result = ''
  completeFormData.cost = undefined
  completeFormData.parts_replaced = ''
  completeFormData.next_maintenance_date = ''
  dialogVisible.value = true
}

const openDetailDialog = async (record: MaintenanceRecord) => {
  detailRecord.value = await getMaintenanceDetail(record.id)
  detailDialogVisible.value = true
}

const openHistoryDialog = async (record: MaintenanceRecord) => {
  historyRecords.value = await getDeviceMaintenanceHistory(record.device_id, 20)
  historyDialogVisible.value = true
}

const handleSubmit = async () => {
  if (dialogType.value === 'create') {
    if (formData.device_id == null || formData.device_id === 0 || !formData.title || !formData.scheduled_time) {
      ElMessage.warning('请填写必要信息')
      return
    }
    try {
      await createMaintenance(formData)
      ElMessage.success('维护计划创建成功')
      dialogVisible.value = false
      loadData()
    } catch (e) {
      ElMessage.error('创建失败')
    }
  } else if (dialogType.value === 'edit') {
    try {
      await updateMaintenance(editFormData.id, {
        scheduled_time: editFormData.scheduled_time,
        title: editFormData.title,
        description: editFormData.description,
        operator: editFormData.operator
      })
      ElMessage.success('维护计划已更新')
      dialogVisible.value = false
      loadData()
    } catch (e) {
      ElMessage.error('更新失败')
    }
  } else {
    try {
      await completeMaintenance(completeFormData.id, {
        result: completeFormData.result,
        cost: completeFormData.cost,
        parts_replaced: completeFormData.parts_replaced,
        next_maintenance_date: completeFormData.next_maintenance_date || undefined
      })
      ElMessage.success('维护已完成')
      dialogVisible.value = false
      loadData()
    } catch (e) {
      ElMessage.error('操作失败')
    }
  }
}

const handleStart = async (record: MaintenanceRecord) => {
  try {
    await startMaintenance(record.id)
    ElMessage.success('维护已开始')
    loadData()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const handleCancel = async (record: MaintenanceRecord) => {
  try {
    await ElMessageBox.prompt('请输入取消原因', '取消维护', {
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    })
    await cancelMaintenance(record.id, '用户取消')
    ElMessage.success('维护已取消')
    loadData()
  } catch (error) {
    if (!isPromptCancelled(error)) {
      ElMessage.error('操作失败')
    }
  }
}

const handleDelete = async (record: MaintenanceRecord) => {
  try {
    await ElMessageBox.confirm('确定删除此维护记录？', '提示', {
      type: 'warning'
    })
    await deleteMaintenance(record.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (!isPromptCancelled(error)) {
      ElMessage.error('删除失败')
    }
  }
}

const formatDateTime = (dt: string) => {
  if (!dt) return '-'
  return new Date(dt).toLocaleString('zh-CN')
}

// --- 生命周期 ---
onMounted(async () => {
  await loadBaseData()
  await loadData()
})
</script>

<template>
  <div class="maintenance-page">
    <!-- 统计卡片 -->
    <div class="stat-cards">
      <div class="stat-card">
        <div class="stat-icon scheduled">
          <el-icon><Calendar /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">
            {{ statsByStatus.scheduled || 0 }}
          </div>
          <div class="stat-label">
            计划中
          </div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon in-progress">
          <el-icon><Loading /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">
            {{ statsByStatus.in_progress || 0 }}
          </div>
          <div class="stat-label">
            进行中
          </div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon completed">
          <el-icon><CircleCheck /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">
            {{ completedCount }}
          </div>
          <div class="stat-label">
            已完成
          </div>
        </div>
      </div>
      <div class="stat-card warning">
        <div class="stat-icon overdue">
          <el-icon><Warning /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">
            {{ overdueList.length }}
          </div>
          <div class="stat-label">
            逾期
          </div>
        </div>
      </div>
    </div>

    <!-- 操作栏 -->
    <div class="toolbar">
      <div class="filters">
        <el-tag
          v-if="hasScopedAccess"
          size="small"
          type="warning"
          effect="dark"
        >
          维护记录已按位置范围过滤
        </el-tag>
        <el-select
          v-model="filters.device_id"
          placeholder="选择设备"
          clearable
          style="width: 180px"
          teleported
          popper-class="app-select-popper"
        >
          <el-option
            v-for="d in deviceList"
            :key="d.id"
            :label="d.name"
            :value="d.id"
          />
        </el-select>
        <el-select
          v-model="filters.maintenance_type"
          placeholder="维护类型"
          clearable
          style="width: 140px"
          teleported
          popper-class="app-select-popper"
        >
          <el-option
            v-for="t in typeList"
            :key="t.value"
            :label="t.label"
            :value="t.value"
          />
        </el-select>
        <el-select
          v-model="filters.status"
          placeholder="状态"
          clearable
          style="width: 120px"
          teleported
          popper-class="app-select-popper"
        >
          <el-option
            v-for="s in statusList"
            :key="s.value"
            :label="s.label"
            :value="s.value"
          />
        </el-select>
        <el-button
          type="primary"
          @click="handleFilter"
        >
          查询
        </el-button>
        <el-button @click="resetFilters">
          重置
        </el-button>
      </div>
      <el-button
        v-if="canManageMaintenance"
        type="primary"
        @click="openCreateDialog"
      >
        <el-icon><Plus /></el-icon>新建维护
      </el-button>
    </div>

    <!-- Tab切换 -->
    <el-tabs
      v-model="activeTab"
      class="maintenance-tabs"
    >
      <el-tab-pane
        label="全部记录"
        name="all"
      >
        <el-table
          v-loading="loading"
          :data="maintenanceList"
          stripe
        >
          <el-table-column
            prop="id"
            label="ID"
            width="60"
          />
          <el-table-column
            label="设备"
            width="150"
          >
            <template #default="{ row }">
              {{ deviceName(row.device_id) }}
            </template>
          </el-table-column>
          <el-table-column
            prop="title"
            label="维护标题"
            min-width="150"
          />
          <el-table-column
            label="类型"
            width="100"
          >
            <template #default="{ row }">
              <el-tag size="small">
                {{ typeLabel(row.maintenance_type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            label="状态"
            width="100"
          >
            <template #default="{ row }">
              <el-tag
                :type="statusTagType(row.status)"
                size="small"
              >
                {{ statusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            label="计划时间"
            width="160"
          >
            <template #default="{ row }">
              {{ formatDateTime(row.scheduled_time) }}
            </template>
          </el-table-column>
          <el-table-column
            prop="operator"
            label="维护人员"
            width="100"
          />
          <el-table-column
            label="操作"
            width="320"
            fixed="right"
          >
            <template #default="{ row }">
              <el-button 
                type="info"
                link
                size="small" 
                @click="openDetailDialog(row)"
              >
                详情
              </el-button>
              <el-button 
                type="info"
                link
                size="small" 
                @click="openHistoryDialog(row)"
              >
                历史
              </el-button>
              <el-button 
                v-if="canManageMaintenance && row.status === 'scheduled'"
                type="primary"
                link
                size="small" 
                @click="openEditDialog(row)"
              >
                编辑
              </el-button>
              <el-button 
                v-if="canOperateMaintenance && row.status === 'scheduled'" 
                type="primary"
                link
                size="small" 
                @click="handleStart(row)"
              >
                开始
              </el-button>
              <el-button 
                v-if="canOperateMaintenance && row.status === 'in_progress'" 
                type="success"
                link
                size="small" 
                @click="openCompleteDialog(row)"
              >
                完成
              </el-button>
              <el-button 
                v-if="canOperateMaintenance && (row.status === 'scheduled' || row.status === 'in_progress')" 
                type="warning"
                link
                size="small" 
                @click="handleCancel(row)"
              >
                取消
              </el-button>
              <el-button 
                v-if="canManageMaintenance"
                type="danger"
                link
                size="small" 
                @click="handleDelete(row)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane
        :label="`即将到期 (${upcomingList.length})`"
        name="upcoming"
      >
        <el-table
          :data="upcomingList"
          stripe
        >
          <el-table-column
            prop="id"
            label="ID"
            width="60"
          />
          <el-table-column
            label="设备"
            width="150"
          >
            <template #default="{ row }">
              {{ deviceName(row.device_id) }}
            </template>
          </el-table-column>
          <el-table-column
            prop="title"
            label="维护标题"
            min-width="150"
          />
          <el-table-column
            label="类型"
            width="100"
          >
            <template #default="{ row }">
              <el-tag size="small">
                {{ typeLabel(row.maintenance_type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            label="计划时间"
            width="160"
          >
            <template #default="{ row }">
              {{ formatDateTime(row.scheduled_time) }}
            </template>
          </el-table-column>
          <el-table-column
            prop="operator"
            label="维护人员"
            width="100"
          />
          <el-table-column
            label="操作"
            width="120"
            fixed="right"
          >
            <template #default="{ row }">
              <el-button
                v-if="canOperateMaintenance"
                type="primary"
                link
                size="small"
                @click="handleStart(row)"
              >
                开始
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane
        :label="`逾期未完成 (${overdueList.length})`"
        name="overdue"
      >
        <el-alert
          v-if="overdueList.length > 0"
          type="warning"
          :closable="false"
          show-icon
        >
          有 {{ overdueList.length }} 条维护计划已逾期，请尽快处理！
        </el-alert>
        <el-table
          :data="overdueList"
          stripe
          style="margin-top: 15px"
        >
          <el-table-column
            prop="id"
            label="ID"
            width="60"
          />
          <el-table-column
            label="设备"
            width="150"
          >
            <template #default="{ row }">
              {{ deviceName(row.device_id) }}
            </template>
          </el-table-column>
          <el-table-column
            prop="title"
            label="维护标题"
            min-width="150"
          />
          <el-table-column
            label="计划时间"
            width="160"
          >
            <template #default="{ row }">
              <span style="color: #f56c6c">{{ formatDateTime(row.scheduled_time) }}</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="operator"
            label="维护人员"
            width="100"
          />
          <el-table-column
            label="操作"
            width="150"
            fixed="right"
          >
            <template #default="{ row }">
              <el-button
                v-if="canOperateMaintenance"
                type="primary"
                link
                size="small"
                @click="handleStart(row)"
              >
                立即处理
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 新建/完成对话框 -->
    <el-dialog
      v-if="canOperateMaintenance"
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
    >
      <!-- 新建表单 -->
      <el-form
        v-if="dialogType === 'create'"
        label-width="100px"
      >
        <el-form-item
          label="设备"
          required
        >
          <el-select
            v-model="formData.device_id"
            placeholder="选择设备"
            style="width: 100%"
            teleported
            popper-class="app-select-popper"
          >
            <el-option
              v-for="d in deviceList"
              :key="d.id"
              :label="d.name"
              :value="d.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item
          label="维护类型"
          required
        >
          <el-select
            v-model="formData.maintenance_type"
            style="width: 100%"
            teleported
            popper-class="app-select-popper"
          >
            <el-option
              v-for="t in typeList"
              :key="t.value"
              :label="t.label"
              :value="t.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item
          label="维护标题"
          required
        >
          <el-input
            v-model="formData.title"
            placeholder="请输入维护标题"
          />
        </el-form-item>
        <el-form-item
          label="计划时间"
          required
        >
          <el-date-picker
            v-model="formData.scheduled_time"
            type="datetime"
            placeholder="选择时间"
            style="width: 100%"
            value-format="YYYY-MM-DDTHH:mm:ss"
          />
        </el-form-item>
        <el-form-item label="维护人员">
          <el-input
            v-model="formData.operator"
            placeholder="请输入维护人员"
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入描述"
          />
        </el-form-item>
      </el-form>

      <el-form
        v-else-if="dialogType === 'edit'"
        label-width="100px"
      >
        <el-form-item
          label="维护标题"
          required
        >
          <el-input v-model="editFormData.title" />
        </el-form-item>
        <el-form-item
          label="计划时间"
          required
        >
          <el-date-picker
            v-model="editFormData.scheduled_time"
            type="datetime"
            style="width: 100%"
            value-format="YYYY-MM-DDTHH:mm:ss"
          />
        </el-form-item>
        <el-form-item label="维护人员">
          <el-input v-model="editFormData.operator" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="editFormData.description"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
      </el-form>

      <!-- 完成表单 -->
      <el-form
        v-else
        label-width="100px"
      >
        <el-form-item label="维护结果">
          <el-input
            v-model="completeFormData.result"
            type="textarea"
            :rows="3"
            placeholder="请输入维护结果"
          />
        </el-form-item>
        <el-form-item label="维护成本">
          <el-input-number
            v-model="completeFormData.cost"
            :min="0"
            :precision="2"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="更换部件">
          <el-input
            v-model="completeFormData.parts_replaced"
            placeholder="请输入更换的部件"
          />
        </el-form-item>
        <el-form-item label="下次维护">
          <el-date-picker
            v-model="completeFormData.next_maintenance_date"
            type="datetime"
            placeholder="建议下次维护时间"
            style="width: 100%"
            value-format="YYYY-MM-DDTHH:mm:ss"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">
          取消
        </el-button>
        <el-button
          type="primary"
          @click="handleSubmit"
        >
          确定
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="detailDialogVisible"
      title="维护详情"
      width="560px"
    >
      <div
        v-if="detailRecord"
        class="detail-grid"
      >
        <div class="detail-item">
          <label>设备</label>
          <span>{{ deviceName(detailRecord.device_id) }}</span>
        </div>
        <div class="detail-item">
          <label>状态</label>
          <span>{{ statusLabel(detailRecord.status) }}</span>
        </div>
        <div class="detail-item">
          <label>类型</label>
          <span>{{ typeLabel(detailRecord.maintenance_type) }}</span>
        </div>
        <div class="detail-item">
          <label>计划时间</label>
          <span>{{ formatDateTime(detailRecord.scheduled_time) }}</span>
        </div>
        <div class="detail-item">
          <label>开始时间</label>
          <span>{{ formatDateTime(detailRecord.start_time || '') }}</span>
        </div>
        <div class="detail-item">
          <label>结束时间</label>
          <span>{{ formatDateTime(detailRecord.end_time || '') }}</span>
        </div>
        <div class="detail-item full">
          <label>标题</label>
          <span>{{ detailRecord.title }}</span>
        </div>
        <div class="detail-item full">
          <label>描述</label>
          <span>{{ detailRecord.description || '-' }}</span>
        </div>
        <div class="detail-item full">
          <label>结果</label>
          <span>{{ detailRecord.result || '-' }}</span>
        </div>
      </div>
    </el-dialog>

    <el-dialog
      v-model="historyDialogVisible"
      title="设备维护历史"
      width="760px"
    >
      <el-table
        :data="historyRecords"
        size="small"
        max-height="420"
      >
        <el-table-column
          prop="id"
          label="ID"
          width="60"
        />
        <el-table-column
          prop="title"
          label="标题"
          min-width="180"
        />
        <el-table-column
          label="状态"
          width="120"
        >
          <template #default="{ row }">
            {{ statusLabel(row.status) }}
          </template>
        </el-table-column>
        <el-table-column
          label="计划时间"
          min-width="160"
        >
          <template #default="{ row }">
            {{ formatDateTime(row.scheduled_time) }}
          </template>
        </el-table-column>
        <el-table-column
          prop="operator"
          label="维护人员"
          width="120"
        />
      </el-table>
    </el-dialog>
  </div>
</template>

<style scoped>
.maintenance-page {
  padding: 10px;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  border: 1px solid var(--border-color);
}

.stat-card.warning {
  border-color: #f56c6c;
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-icon.scheduled { background: rgba(64, 158, 255, 0.1); color: #409eff; }
.stat-icon.in-progress { background: rgba(230, 162, 60, 0.1); color: #e6a23c; }
.stat-icon.completed { background: rgba(103, 194, 58, 0.1); color: #67c23a; }
.stat-icon.overdue { background: rgba(245, 108, 108, 0.1); color: #f56c6c; }

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  background: var(--bg-card);
  padding: 15px 20px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

.filters {
  display: flex;
  gap: 10px;
  align-items: center;
}

.maintenance-tabs {
  background: var(--bg-card);
  padding: 20px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

:deep(.el-tabs__header) {
  margin-bottom: 20px;
}

:deep(.el-table) {
  background: transparent;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-item.full {
  grid-column: 1 / -1;
}

.detail-item label {
  color: var(--text-secondary);
  font-size: 12px;
}
</style>
