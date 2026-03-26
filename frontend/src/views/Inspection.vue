<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Delete, Edit, Check, Clock, Warning, Location } from '@element-plus/icons-vue'
import {
  getRoutes, createRoute, updateRoute, deleteRoute, getRoutePoints,
  createPoint, updatePoint, deletePoint,
  getPlans, createPlan, updatePlan, deletePlan,
  getTasks, getTodayTasks, createTask, startTask, completeTask, getTaskRecords,
  submitRecord, getStatistics,
  type InspectionRoute, type InspectionPoint, type InspectionPlan,
  type InspectionTask, type InspectionRecord, type InspectionStatistics
} from '@/api/inspection'
import { getDevices, type Device } from '@/api/device'
import { usePermissions } from '@/shared/composables/usePermissions'

interface ApiErrorLike {
  response?: {
    status?: number
    data?: {
      detail?: string
    }
  }
}

const getErrorDetail = (error: unknown, fallback: string) => {
  const apiError = error as ApiErrorLike
  return apiError.response?.data?.detail || fallback
}

// ==================== 状态 ====================
const loading = ref(false)
const activeTab = ref('tasks')

// 数据
const routes = ref<InspectionRoute[]>([])
const points = ref<InspectionPoint[]>([])
const plans = ref<InspectionPlan[]>([])
const tasks = ref<InspectionTask[]>([])
const todayTasks = ref<InspectionTask[]>([])
const devices = ref<Device[]>([])
const statistics = ref<InspectionStatistics | null>(null)
const currentRecords = ref<InspectionRecord[]>([])
const { canManageInspection, canOperateInspection, hasScopedAccess } = usePermissions()

// 对话框
const routeDialogVisible = ref(false)
const pointDialogVisible = ref(false)
const planDialogVisible = ref(false)
const taskDialogVisible = ref(false)
const executeDialogVisible = ref(false)
const recordDialogVisible = ref(false)

// 编辑模式标志
const isEditingRoute = ref(false)
const isEditingPlan = ref(false)
const editingRouteId = ref<number | null>(null)
const editingPlanId = ref<number | null>(null)

// 当前选中
const selectedRoute = ref<InspectionRoute | null>(null)
const selectedTask = ref<InspectionTask | null>(null)
const selectedPoint = ref<InspectionPoint | null>(null)

// 表单数据
const routeForm = reactive({
  name: '',
  code: '',
  description: '',
  estimated_duration: 30
})

const pointForm = reactive({
  route_id: 0,
  name: '',
  device_id: undefined as number | undefined,
  location: '',
  sequence: 0,
  check_items: ['外观检查', '运行状态', '仪表读数'],
  qr_code: '',
  is_required: true
})

const planForm = reactive({
  route_id: 0,
  name: '',
  plan_type: 'daily',
  start_date: '',
  end_date: '',
  execution_time: '08:00',
  assigned_to: '',
  department: ''
})

const taskForm = reactive({
  route_id: 0,
  inspector: ''
})

const recordForm = reactive({
  task_id: 0,
  point_id: 0,
  result: 'normal',
  meter_reading: undefined as number | undefined,
  abnormal_description: '',
  abnormal_level: ''
})

// ==================== 计算属性 ====================
const statusTagType = (status: string) => {
  const map: Record<string, string> = {
    pending: 'info',
    in_progress: 'warning',
    completed: 'success',
    overdue: 'danger',
    cancelled: 'info'
  }
  return map[status] || 'info'
}

const statusLabel = (status: string) => {
  const map: Record<string, string> = {
    pending: '待执行',
    in_progress: '进行中',
    completed: '已完成',
    overdue: '已逾期',
    cancelled: '已取消'
  }
  return map[status] || status
}

const resultTagType = (result: string) => {
  const map: Record<string, string> = {
    normal: 'success',
    abnormal: 'warning',
    defect: 'danger',
    serious: 'danger'
  }
  return map[result] || 'info'
}

const resultLabel = (result: string) => {
  const map: Record<string, string> = {
    normal: '正常',
    abnormal: '异常',
    defect: '缺陷',
    serious: '严重'
  }
  return map[result] || result
}

const planTypeLabel = (type: string) => {
  const map: Record<string, string> = {
    daily: '每日巡检',
    weekly: '每周巡检',
    monthly: '每月巡检'
  }
  return map[type] || type
}

const deviceName = (deviceId?: number) => {
  if (!deviceId) return '-'
  const device = devices.value.find(d => d.id === deviceId)
  return device?.name || `设备${deviceId}`
}

// ==================== 方法 ====================

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const [routesRes, plansRes, tasksRes, todayRes, devicesRes, statsRes] = await Promise.all([
      getRoutes(true),
      getPlans(true),
      getTasks({ limit: 50 }),
      getTodayTasks(),
      getDevices(),
      getStatistics()
    ])
    routes.value = routesRes
    plans.value = plansRes
    tasks.value = tasksRes
    todayTasks.value = todayRes
    devices.value = devicesRes
    if (statsRes) {
      statistics.value = statsRes
    }
  } catch (e) {
    console.error('加载数据失败:', e)
  } finally {
    loading.value = false
  }
}

// 路线相关
const openRouteDialog = (route?: InspectionRoute) => {
  if (route) {
    // 编辑模式
    isEditingRoute.value = true
    editingRouteId.value = route.id!
    routeForm.name = route.name
    routeForm.code = route.code || ''
    routeForm.description = route.description || ''
    routeForm.estimated_duration = route.estimated_duration
  } else {
    // 新建模式
    isEditingRoute.value = false
    editingRouteId.value = null
    routeForm.name = ''
    routeForm.code = ''
    routeForm.description = ''
    routeForm.estimated_duration = 30
  }
  routeDialogVisible.value = true
}

const submitRoute = async () => {
  try {
    if (isEditingRoute.value && editingRouteId.value) {
      await updateRoute(editingRouteId.value, routeForm)
      ElMessage.success('更新成功')
    } else {
      await createRoute(routeForm)
      ElMessage.success('创建成功')
    }
    routeDialogVisible.value = false
    loadData()
  } catch (error) {
    const msg = getErrorDetail(error, isEditingRoute.value ? '更新失败' : '创建失败')
    ElMessage.error(msg)
  }
}

const handleDeleteRoute = (route: InspectionRoute) => {
  ElMessageBox.confirm(`确定要删除路线「${route.name}」吗？`, '确认删除', {
    type: 'warning'
  }).then(async () => {
    try {
      await deleteRoute(route.id!)
      ElMessage.success('删除成功')
      loadData()
    } catch (error) {
      const apiError = error as ApiErrorLike
      const detail = apiError.response?.data?.detail || ''
      // 如果是因为有关联数据，询问是否强制删除
      if (apiError.response?.status === 409 && detail.includes('无法删除')) {
        ElMessageBox.confirm(
          `${detail}\n\n是否强制删除（将同时删除所有关联数据）？`,
          '存在关联数据',
          { type: 'warning', confirmButtonText: '强制删除', cancelButtonText: '取消' }
        ).then(async () => {
          try {
            await deleteRoute(route.id!, true)
            ElMessage.success('删除成功')
            loadData()
          } catch (forceDeleteError) {
            ElMessage.error(getErrorDetail(forceDeleteError, '删除失败'))
          }
        }).catch(() => {})
      } else {
        ElMessage.error(detail || '删除失败')
      }
    }
  }).catch(() => {})
}

const viewRoutePoints = async (route: InspectionRoute) => {
  selectedRoute.value = route
  try {
    points.value = await getRoutePoints(route.id!)
  } catch (e) {
    console.error(e)
  }
}

// 巡检点相关
const openPointDialog = (route: InspectionRoute) => {
  selectedRoute.value = route
  pointForm.route_id = route.id!
  pointForm.name = ''
  pointForm.device_id = undefined
  pointForm.location = ''
  pointForm.sequence = points.value.length + 1
  pointForm.check_items = ['外观检查', '运行状态', '仪表读数']
  pointForm.qr_code = ''
  pointForm.is_required = true
  pointDialogVisible.value = true
}

const submitPoint = async () => {
  try {
    await createPoint({
      ...pointForm,
      check_items: pointForm.check_items
    })
    ElMessage.success('添加成功')
    pointDialogVisible.value = false
    if (selectedRoute.value) {
      viewRoutePoints(selectedRoute.value)
    }
    loadData()
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

const handleDeletePoint = (point: InspectionPoint) => {
  ElMessageBox.confirm(`确定要删除巡检点「${point.name}」吗？`, '确认删除', {
    type: 'warning'
  }).then(async () => {
    await deletePoint(point.id!)
    ElMessage.success('删除成功')
    if (selectedRoute.value) {
      viewRoutePoints(selectedRoute.value)
    }
  })
}

// 计划相关
const openPlanDialog = (plan?: InspectionPlan) => {
  if (plan) {
    // 编辑模式
    isEditingPlan.value = true
    editingPlanId.value = plan.id!
    planForm.route_id = plan.route_id
    planForm.name = plan.name
    planForm.plan_type = plan.plan_type
    planForm.start_date = plan.start_date.split('T')[0]
    planForm.end_date = plan.end_date?.split('T')[0] || ''
    planForm.execution_time = plan.execution_time
    planForm.assigned_to = plan.assigned_to || ''
    planForm.department = plan.department || ''
  } else {
    // 新建模式
    isEditingPlan.value = false
    editingPlanId.value = null
    planForm.route_id = routes.value[0]?.id || 0
    planForm.name = ''
    planForm.plan_type = 'daily'
    planForm.start_date = new Date().toISOString().split('T')[0]
    planForm.end_date = ''
    planForm.execution_time = '08:00'
    planForm.assigned_to = ''
    planForm.department = ''
  }
  planDialogVisible.value = true
}

const submitPlan = async () => {
  try {
    const data = {
      ...planForm,
      start_date: new Date(planForm.start_date).toISOString(),
      end_date: planForm.end_date ? new Date(planForm.end_date).toISOString() : undefined
    }
    if (isEditingPlan.value && editingPlanId.value) {
      await updatePlan(editingPlanId.value, data)
      ElMessage.success('更新成功')
    } else {
      await createPlan(data)
      ElMessage.success('创建成功')
    }
    planDialogVisible.value = false
    loadData()
  } catch (error) {
    const msg = getErrorDetail(error, isEditingPlan.value ? '更新失败' : '创建失败')
    ElMessage.error(msg)
  }
}

const handleDeletePlan = (plan: InspectionPlan) => {
  ElMessageBox.confirm(`确定要删除计划「${plan.name}」吗？`, '确认删除', {
    type: 'warning'
  }).then(async () => {
    try {
      await deletePlan(plan.id!)
      ElMessage.success('删除成功')
      loadData()
    } catch (error) {
      const apiError = error as ApiErrorLike
      const detail = apiError.response?.data?.detail || ''
      if (apiError.response?.status === 409 && detail.includes('无法删除')) {
        ElMessageBox.confirm(
          `${detail}\n\n是否强制删除？`,
          '存在关联数据',
          { type: 'warning', confirmButtonText: '强制删除', cancelButtonText: '取消' }
        ).then(async () => {
          try {
            await deletePlan(plan.id!, true)
            ElMessage.success('删除成功')
            loadData()
          } catch (forceDeleteError) {
            ElMessage.error(getErrorDetail(forceDeleteError, '删除失败'))
          }
        }).catch(() => {})
      } else {
        ElMessage.error(detail || '删除失败')
      }
    }
  }).catch(() => {})
}

// 任务相关
const openTaskDialog = () => {
  taskForm.route_id = routes.value[0]?.id || 0
  taskForm.inspector = ''
  taskDialogVisible.value = true
}

const submitTask = async () => {
  try {
    await createTask(taskForm)
    ElMessage.success('创建成功')
    taskDialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error('创建失败')
  }
}

const handleStartTask = async (task: InspectionTask) => {
  ElMessageBox.prompt('请输入巡检员姓名', '开始巡检', {
    confirmButtonText: '开始',
    cancelButtonText: '取消',
    inputPattern: /.+/,
    inputErrorMessage: '请输入巡检员姓名'
  }).then(async ({ value }) => {
    try {
      await startTask(task.id!, value)
      ElMessage.success('巡检任务已开始')
      loadData()
    } catch (error) {
      const msg = getErrorDetail(error, '开始任务失败')
      ElMessage.error(msg)
    }
  }).catch(() => {})
}

const handleCompleteTask = async (task: InspectionTask) => {
  ElMessageBox.confirm('确认完成此巡检任务？', '完成巡检', {
    type: 'success'
  }).then(async () => {
    try {
      await completeTask(task.id!)
      ElMessage.success('巡检任务已完成')
      loadData()
    } catch (error) {
      const msg = getErrorDetail(error, '完成任务失败')
      ElMessage.error(msg)
    }
  }).catch(() => {})
}

const openExecuteDialog = async (task: InspectionTask) => {
  selectedTask.value = task
  try {
    points.value = await getRoutePoints(task.route_id)
    currentRecords.value = await getTaskRecords(task.id!)
    executeDialogVisible.value = true
  } catch (e) {
    console.error(e)
  }
}

// 记录相关
const openRecordDialog = (point: InspectionPoint) => {
  selectedPoint.value = point
  recordForm.task_id = selectedTask.value!.id!
  recordForm.point_id = point.id!
  recordForm.result = 'normal'
  recordForm.meter_reading = undefined
  recordForm.abnormal_description = ''
  recordForm.abnormal_level = ''
  recordDialogVisible.value = true
}

const submitRecordForm = async () => {
  try {
    await submitRecord({
      task_id: recordForm.task_id,
      point_id: recordForm.point_id,
      result: recordForm.result,
      meter_reading: recordForm.meter_reading,
      abnormal_description: recordForm.abnormal_description || undefined,
      abnormal_level: recordForm.abnormal_level || undefined,
      inspector: selectedTask.value?.inspector
    })
    ElMessage.success('提交成功')
    recordDialogVisible.value = false
    // 刷新记录
    currentRecords.value = await getTaskRecords(selectedTask.value!.id!)
    loadData()
  } catch (error) {
    const msg = getErrorDetail(error, '提交失败')
    ElMessage.error(msg)
  }
}

const isPointChecked = (pointId: number) => {
  return currentRecords.value.some(r => r.point_id === pointId)
}

const getPointRecord = (pointId: number) => {
  return currentRecords.value.find(r => r.point_id === pointId)
}

// 生命周期
onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="inspection-container">
    <!-- 头部统计卡片 -->
    <div
      v-if="statistics"
      class="stats-row"
    >
      <div class="stat-card">
        <div
          class="stat-icon"
          style="background: #3b82f6;"
        >
          <el-icon><Clock /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">
            {{ statistics.tasks.total }}
          </div>
          <div class="stat-label">
            总任务数
          </div>
        </div>
      </div>
      <div class="stat-card">
        <div
          class="stat-icon"
          style="background: #10b981;"
        >
          <el-icon><Check /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">
            {{ statistics.tasks.completion_rate }}%
          </div>
          <div class="stat-label">
            完成率
          </div>
        </div>
      </div>
      <div class="stat-card">
        <div
          class="stat-icon"
          style="background: #f59e0b;"
        >
          <el-icon><Warning /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">
            {{ statistics.abnormal.count }}
          </div>
          <div class="stat-label">
            异常数
          </div>
        </div>
      </div>
      <div class="stat-card">
        <div
          class="stat-icon"
          style="background: #8b5cf6;"
        >
          <el-icon><Location /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">
            {{ statistics.points.completed }}
          </div>
          <div class="stat-label">
            已检查点
          </div>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <el-tabs
      v-model="activeTab"
      class="main-tabs"
    >
      <!-- 巡检任务 Tab -->
      <el-tab-pane
        label="巡检任务"
        name="tasks"
      >
        <div class="tab-toolbar">
          <el-button
            v-if="canManageInspection"
            type="primary"
            :icon="Plus"
            @click="openTaskDialog"
          >
            新建任务
          </el-button>
          <el-button
            :icon="Refresh"
            @click="loadData"
          >
            刷新
          </el-button>
        </div>
        <el-alert
          v-if="hasScopedAccess"
          type="warning"
          :closable="false"
          show-icon
          style="margin-bottom: 12px;"
        >
          当前巡检任务与路线已按位置范围过滤
        </el-alert>

        <!-- 今日任务 -->
        <div class="section-title">
          今日任务
        </div>
        <el-table
          v-loading="loading"
          :data="todayTasks"
          class="custom-table"
        >
          <el-table-column
            prop="task_no"
            label="任务编号"
            width="160"
          />
          <el-table-column
            label="巡检路线"
            min-width="150"
          >
            <template #default="{ row }">
              {{ routes.find(r => r.id === row.route_id)?.name || '-' }}
            </template>
          </el-table-column>
          <el-table-column
            prop="inspector"
            label="巡检员"
            width="100"
          />
          <el-table-column
            label="进度"
            width="150"
          >
            <template #default="{ row }">
              <el-progress 
                :percentage="row.total_points > 0 ? Math.round(row.completed_points / row.total_points * 100) : 0"
                :status="row.status === 'completed' ? 'success' : ''"
              />
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
            label="操作"
            width="200"
            fixed="right"
          >
            <template #default="{ row }">
              <el-button 
                v-if="canOperateInspection && row.status === 'pending'" 
                link
                type="success" 
                @click="handleStartTask(row)"
              >
                开始
              </el-button>
              <el-button 
                v-if="canOperateInspection && row.status === 'in_progress'" 
                link
                type="primary" 
                @click="openExecuteDialog(row)"
              >
                执行
              </el-button>
              <el-button 
                v-if="canOperateInspection && row.status === 'in_progress'" 
                link
                type="success" 
                @click="handleCompleteTask(row)"
              >
                完成
              </el-button>
              <el-button 
                v-if="row.status === 'completed'" 
                link
                type="info" 
                @click="openExecuteDialog(row)"
              >
                查看
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 历史任务 -->
        <div
          class="section-title"
          style="margin-top: 20px;"
        >
          历史任务
        </div>
        <el-table
          v-loading="loading"
          :data="tasks"
          class="custom-table"
        >
          <el-table-column
            prop="task_no"
            label="任务编号"
            width="160"
          />
          <el-table-column
            label="巡检路线"
            min-width="150"
          >
            <template #default="{ row }">
              {{ routes.find(r => r.id === row.route_id)?.name || '-' }}
            </template>
          </el-table-column>
          <el-table-column
            prop="task_date"
            label="任务日期"
            width="180"
          >
            <template #default="{ row }">
              {{ new Date(row.task_date).toLocaleString() }}
            </template>
          </el-table-column>
          <el-table-column
            prop="inspector"
            label="巡检员"
            width="100"
          />
          <el-table-column
            label="异常"
            width="80"
          >
            <template #default="{ row }">
              <el-tag
                v-if="row.abnormal_count > 0"
                type="danger"
                size="small"
              >
                {{ row.abnormal_count }}
              </el-tag>
              <span v-else>-</span>
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
        </el-table>
      </el-tab-pane>

      <!-- 巡检路线 Tab -->
      <el-tab-pane
        label="巡检路线"
        name="routes"
      >
        <div class="tab-toolbar">
          <el-button
            v-if="canManageInspection"
            type="primary"
            :icon="Plus"
            @click="openRouteDialog"
          >
            新建路线
          </el-button>
          <el-button
            :icon="Refresh"
            @click="loadData"
          >
            刷新
          </el-button>
        </div>

        <div class="routes-grid">
          <div 
            v-for="route in routes" 
            :key="route.id" 
            class="route-card"
            @click="viewRoutePoints(route)"
          >
            <div class="route-header">
              <span class="route-name">{{ route.name }}</span>
              <el-tag size="small">
                {{ route.device_count }} 个巡检点
              </el-tag>
            </div>
            <div class="route-info">
              <span>预计耗时: {{ route.estimated_duration }} 分钟</span>
              <span v-if="route.code">编码: {{ route.code }}</span>
            </div>
            <div
              v-if="route.description"
              class="route-desc"
            >
              {{ route.description }}
            </div>
            <div
              v-if="canManageInspection"
              class="route-actions"
            >
              <el-button
                size="small"
                @click.stop="openPointDialog(route)"
              >
                添加巡检点
              </el-button>
              <el-button
                size="small"
                type="primary"
                @click.stop="openRouteDialog(route)"
              >
                编辑
              </el-button>
              <el-button
                size="small"
                type="danger"
                @click.stop="handleDeleteRoute(route)"
              >
                删除
              </el-button>
            </div>
          </div>
        </div>

        <!-- 巡检点列表 -->
        <div
          v-if="selectedRoute"
          class="points-section"
        >
          <div class="section-title">
            {{ selectedRoute.name }} - 巡检点列表
          </div>
          <el-table
            :data="points"
            class="custom-table"
          >
            <el-table-column
              prop="sequence"
              label="顺序"
              width="80"
            />
            <el-table-column
              prop="name"
              label="巡检点名称"
              min-width="150"
            />
            <el-table-column
              label="关联设备"
              min-width="150"
            >
              <template #default="{ row }">
                {{ deviceName(row.device_id) }}
              </template>
            </el-table-column>
            <el-table-column
              prop="location"
              label="位置"
              width="150"
            />
            <el-table-column
              label="必检"
              width="80"
            >
              <template #default="{ row }">
                <el-tag
                  :type="row.is_required ? 'danger' : 'info'"
                  size="small"
                >
                  {{ row.is_required ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column
              v-if="canManageInspection"
              label="操作"
              width="100"
            >
              <template #default="{ row }">
                <el-button
                  link
                  type="danger"
                  @click="handleDeletePoint(row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- 巡检计划 Tab -->
      <el-tab-pane
        label="巡检计划"
        name="plans"
      >
        <div class="tab-toolbar">
          <el-button
            v-if="canManageInspection"
            type="primary"
            :icon="Plus"
            @click="openPlanDialog"
          >
            新建计划
          </el-button>
          <el-button
            :icon="Refresh"
            @click="loadData"
          >
            刷新
          </el-button>
        </div>

        <el-table
          v-loading="loading"
          :data="plans"
          class="custom-table"
        >
          <el-table-column
            prop="name"
            label="计划名称"
            min-width="150"
          />
          <el-table-column
            label="巡检路线"
            min-width="150"
          >
            <template #default="{ row }">
              {{ routes.find(r => r.id === row.route_id)?.name || '-' }}
            </template>
          </el-table-column>
          <el-table-column
            label="计划类型"
            width="120"
          >
            <template #default="{ row }">
              <el-tag size="small">
                {{ planTypeLabel(row.plan_type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            prop="execution_time"
            label="执行时间"
            width="100"
          />
          <el-table-column
            prop="assigned_to"
            label="负责人"
            width="100"
          />
          <el-table-column
            prop="department"
            label="部门"
            width="120"
          />
          <el-table-column
            v-if="canManageInspection"
            label="操作"
            width="150"
            fixed="right"
          >
            <template #default="{ row }">
              <el-button
                link
                type="primary"
                @click="openPlanDialog(row)"
              >
                编辑
              </el-button>
              <el-button
                link
                type="danger"
                @click="handleDeletePlan(row)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 新建/编辑路线对话框 -->
    <el-dialog
      v-if="canManageInspection"
      v-model="routeDialogVisible"
      :title="isEditingRoute ? '编辑巡检路线' : '新建巡检路线'"
      width="500px"
    >
      <el-form
        :model="routeForm"
        label-width="100px"
      >
        <el-form-item
          label="路线名称"
          required
        >
          <el-input
            v-model="routeForm.name"
            placeholder="如：配电室日常巡检"
          />
        </el-form-item>
        <el-form-item label="路线编码">
          <el-input
            v-model="routeForm.code"
            placeholder="如：PDR-001"
          />
        </el-form-item>
        <el-form-item label="预计耗时">
          <el-input-number
            v-model="routeForm.estimated_duration"
            :min="5"
            :max="480"
          />
          <span style="margin-left: 10px;">分钟</span>
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="routeForm.description"
            type="textarea"
            rows="3"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="routeDialogVisible = false">
          取消
        </el-button>
        <el-button
          type="primary"
          @click="submitRoute"
        >
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 添加巡检点对话框 -->
    <el-dialog
      v-if="canManageInspection"
      v-model="pointDialogVisible"
      title="添加巡检点"
      width="500px"
    >
      <el-form
        :model="pointForm"
        label-width="100px"
      >
        <el-form-item
          label="巡检点名称"
          required
        >
          <el-input
            v-model="pointForm.name"
            placeholder="如：1号配电柜"
          />
        </el-form-item>
        <el-form-item label="关联设备">
          <el-select
            v-model="pointForm.device_id"
            placeholder="选择设备"
            clearable
            style="width: 100%"
            teleported
            popper-class="app-select-popper"
          >
            <el-option 
              v-for="d in devices" 
              :key="d.id" 
              :label="d.name" 
              :value="d.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="位置描述">
          <el-input
            v-model="pointForm.location"
            placeholder="如：配电室A区"
          />
        </el-form-item>
        <el-form-item label="巡检顺序">
          <el-input-number
            v-model="pointForm.sequence"
            :min="1"
          />
        </el-form-item>
        <el-form-item label="是否必检">
          <el-switch v-model="pointForm.is_required" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pointDialogVisible = false">
          取消
        </el-button>
        <el-button
          type="primary"
          @click="submitPoint"
        >
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 新建/编辑计划对话框 -->
    <el-dialog
      v-if="canManageInspection"
      v-model="planDialogVisible"
      :title="isEditingPlan ? '编辑巡检计划' : '新建巡检计划'"
      width="500px"
    >
      <el-form
        :model="planForm"
        label-width="100px"
      >
        <el-form-item
          label="计划名称"
          required
        >
          <el-input
            v-model="planForm.name"
            placeholder="如：配电室每日巡检"
          />
        </el-form-item>
        <el-form-item
          label="巡检路线"
          required
        >
          <el-select
            v-model="planForm.route_id"
            style="width: 100%"
          >
            <el-option 
              v-for="r in routes" 
              :key="r.id" 
              :label="r.name" 
              :value="r.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="计划类型">
          <el-select
            v-model="planForm.plan_type"
            style="width: 100%"
          >
            <el-option
              label="每日巡检"
              value="daily"
            />
            <el-option
              label="每周巡检"
              value="weekly"
            />
            <el-option
              label="每月巡检"
              value="monthly"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="执行时间">
          <el-time-select
            v-model="planForm.execution_time"
            start="00:00"
            step="00:30"
            end="23:30"
            placeholder="选择时间"
          />
        </el-form-item>
        <el-form-item
          label="开始日期"
          required
        >
          <el-date-picker 
            v-model="planForm.start_date" 
            type="date" 
            placeholder="选择日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="负责人">
          <el-input v-model="planForm.assigned_to" />
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="planForm.department" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="planDialogVisible = false">
          取消
        </el-button>
        <el-button
          type="primary"
          @click="submitPlan"
        >
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 新建任务对话框 -->
    <el-dialog
      v-if="canManageInspection"
      v-model="taskDialogVisible"
      title="新建巡检任务"
      width="400px"
    >
      <el-form
        :model="taskForm"
        label-width="100px"
      >
        <el-form-item
          label="巡检路线"
          required
        >
          <el-select
            v-model="taskForm.route_id"
            style="width: 100%"
          >
            <el-option 
              v-for="r in routes" 
              :key="r.id" 
              :label="r.name" 
              :value="r.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="巡检员">
          <el-input
            v-model="taskForm.inspector"
            placeholder="可在开始时填写"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="taskDialogVisible = false">
          取消
        </el-button>
        <el-button
          type="primary"
          @click="submitTask"
        >
          创建
        </el-button>
      </template>
    </el-dialog>

    <!-- 执行巡检对话框 -->
    <el-dialog 
      v-model="executeDialogVisible" 
      :title="`执行巡检 - ${selectedTask?.task_no || ''}`" 
      width="700px"
    >
      <div
        v-if="selectedTask"
        class="execute-info"
      >
        <span>巡检员: {{ selectedTask.inspector || '-' }}</span>
        <span>进度: {{ selectedTask.completed_points }} / {{ selectedTask.total_points }}</span>
        <span>
          状态: 
          <el-tag
            :type="statusTagType(selectedTask.status)"
            size="small"
          >
            {{ statusLabel(selectedTask.status) }}
          </el-tag>
        </span>
      </div>

      <el-table
        :data="points"
        class="custom-table"
      >
        <el-table-column
          prop="sequence"
          label="序号"
          width="70"
        />
        <el-table-column
          prop="name"
          label="巡检点"
          min-width="150"
        />
        <el-table-column
          label="关联设备"
          width="150"
        >
          <template #default="{ row }">
            {{ deviceName(row.device_id) }}
          </template>
        </el-table-column>
        <el-table-column
          label="检查结果"
          width="100"
        >
          <template #default="{ row }">
            <template v-if="isPointChecked(row.id)">
              <el-tag
                :type="resultTagType(getPointRecord(row.id)!.result)"
                size="small"
              >
                {{ resultLabel(getPointRecord(row.id)!.result) }}
              </el-tag>
            </template>
            <span
              v-else
              style="color: #909399;"
            >未检查</span>
          </template>
        </el-table-column>
        <el-table-column
          label="操作"
          width="120"
        >
          <template #default="{ row }">
            <el-button 
              v-if="!isPointChecked(row.id) && selectedTask?.status === 'in_progress'"
              link
              type="primary" 
              @click="openRecordDialog(row)"
            >
              检查
            </el-button>
            <el-tag
              v-else-if="isPointChecked(row.id)"
              type="success"
              size="small"
            >
              已完成
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 提交检查记录对话框 -->
    <el-dialog
      v-model="recordDialogVisible"
      :title="`检查 - ${selectedPoint?.name || ''}`"
      width="450px"
    >
      <el-form
        :model="recordForm"
        label-width="100px"
      >
        <el-form-item
          label="检查结果"
          required
        >
          <el-radio-group v-model="recordForm.result">
            <el-radio value="normal">
              正常
            </el-radio>
            <el-radio value="abnormal">
              异常
            </el-radio>
            <el-radio value="defect">
              缺陷
            </el-radio>
            <el-radio value="serious">
              严重
            </el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="仪表读数">
          <el-input-number
            v-model="recordForm.meter_reading"
            :precision="2"
          />
        </el-form-item>
        <el-form-item
          v-if="recordForm.result !== 'normal'"
          label="异常等级"
        >
          <el-select
            v-model="recordForm.abnormal_level"
            style="width: 100%"
          >
            <el-option
              label="轻微"
              value="minor"
            />
            <el-option
              label="一般"
              value="medium"
            />
            <el-option
              label="严重"
              value="major"
            />
            <el-option
              label="紧急"
              value="critical"
            />
          </el-select>
        </el-form-item>
        <el-form-item
          v-if="recordForm.result !== 'normal'"
          label="异常描述"
        >
          <el-input
            v-model="recordForm.abnormal_description"
            type="textarea"
            rows="3"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="recordDialogVisible = false">
          取消
        </el-button>
        <el-button
          type="primary"
          @click="submitRecordForm"
        >
          提交
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.inspection-container {
  padding: 20px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  background: var(--bg-sidebar, #1e293b);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  border: 1px solid var(--border-color, #334155);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #fff;
}

.stat-label {
  color: #94a3b8;
  font-size: 14px;
}

.main-tabs {
  background: var(--bg-sidebar, #1e293b);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--border-color, #334155);
}

.tab-toolbar {
  margin-bottom: 16px;
  display: flex;
  gap: 10px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 12px;
  padding-left: 10px;
  border-left: 4px solid var(--brand-color, #3b82f6);
}

.routes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.route-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.route-card:hover {
  border-color: var(--brand-color, #3b82f6);
  background: rgba(59, 130, 246, 0.1);
}

.route-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.route-name {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
}

.route-info {
  display: flex;
  gap: 20px;
  color: #94a3b8;
  font-size: 13px;
  margin-bottom: 8px;
}

.route-desc {
  color: #64748b;
  font-size: 13px;
  margin-bottom: 12px;
}

.route-actions {
  display: flex;
  gap: 8px;
}

.points-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--border-color, #334155);
}

.execute-info {
  display: flex;
  gap: 30px;
  margin-bottom: 16px;
  color: #94a3b8;
}

.custom-table {
  --el-table-bg-color: transparent;
  --el-table-header-bg-color: rgba(255, 255, 255, 0.05);
  --el-table-tr-bg-color: transparent;
  --el-table-row-hover-bg-color: rgba(255, 255, 255, 0.05);
  --el-table-border-color: var(--border-color, #334155);
  --el-table-text-color: #cbd5e1;
  --el-table-header-text-color: #94a3b8;
}

:deep(.el-tabs__item) {
  color: #94a3b8;
}

:deep(.el-tabs__item.is-active) {
  color: var(--brand-color, #3b82f6);
}

:deep(.el-dialog) {
  --el-dialog-bg-color: #1e293b;
  --el-dialog-title-font-size: 16px;
}

:deep(.el-dialog__title) {
  color: #fff;
}

:deep(.el-form-item__label) {
  color: #94a3b8;
}
</style>
