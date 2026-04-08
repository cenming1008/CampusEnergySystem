<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  assignDeviceToLocation,
  createLocation,
  deleteLocation,
  getCampusOverview,
  getChildLocations,
  getLocationDetail,
  getLocationDevices,
  getLocationStatistics,
  getLocationTree,
  getLocationTypes,
  getLocations,
  getRootLocations,
  searchLocations,
  updateLocation,
  type CampusOverview,
  type Location,
  type LocationCreateRequest,
  type LocationStatistics,
  type LocationTreeNode,
  type LocationTypeInfo,
} from '@/api/location'
import { getDevices, type Device } from '@/api/device'
import { usePermissions } from '@/shared/composables/usePermissions'
import { useCrudDialog } from '@/shared/composables/useCrudDialog'
import { useCrudSubmit } from '@/shared/composables/useCrudSubmit'

interface SummaryCard {
  label: string
  value: string
  caption: string
}

interface DistributionItem {
  key: string
  label: string
  count: number
}

const loading = ref(false)
const locationList = ref<Location[]>([])
const locationTree = ref<LocationTreeNode[]>([])
const rootLocations = ref<Location[]>([])
const typeList = ref<LocationTypeInfo[]>([])
const deviceList = ref<Device[]>([])
const selectedLocation = ref<Location | null>(null)
const locationDevices = ref<Device[]>([])
const locationStats = ref<LocationStatistics | null>(null)
const childLocations = ref<Location[]>([])
const campusOverview = ref<CampusOverview | null>(null)
const searchKeyword = ref('')
const searchResults = ref<Location[]>([])
const rootsOnly = ref(false)
const { canManageLocations, hasScopedAccess } = usePermissions()

const assignDialogVisible = ref(false)
const selectedDeviceId = ref<number | null>(null)

const formData = reactive<LocationCreateRequest & { id?: number }>({
  name: '',
  location_type: 'building',
  parent_id: undefined,
  code: '',
  description: '',
  area_sqm: undefined,
  manager: '',
  contact: ''
})

const treeProps = {
  children: 'children',
  label: 'name'
}

const typeIconMap: Record<string, string> = {
  park: '🌐',
  campus: '🏙️',
  site: '📍',
  building: '🏢',
  unit: '🏠',
  floor: '🧱',
  room: '🚪',
  workshop: '🏭',
  area: '🗺️',
  zone: '📌'
}

const energyLabelMap: Record<string, string> = {
  electricity: '电力',
  electric: '电力',
  water: '水务',
  gas: '燃气',
  cooling: '冷量',
  heat: '热力',
  heating: '热力',
  steam: '蒸汽'
}

function typeLabel(type: string) {
  const item = typeList.value.find((entry) => entry.value === type)
  return item?.label || type
}

function typeIcon(type: string) {
  return typeIconMap[type] || '📍'
}

function energyLabel(type: string) {
  return energyLabelMap[type] || type
}

function formatNumber(value: number | undefined | null, digits: number = 0) {
  if (value == null || Number.isNaN(value)) return '-'
  return Number(value).toFixed(digits)
}

function formatTimestamp(value?: string | null) {
  if (!value) return '暂无记录'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', {
    hour12: false,
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function flattenTree(nodes: LocationTreeNode[]): LocationTreeNode[] {
  return nodes.flatMap((node) => [node, ...flattenTree(node.children || [])])
}

function cloneAsRootOnly(nodes: LocationTreeNode[]) {
  return nodes.map((node) => ({ ...node, children: [] }))
}

const allTreeNodes = computed(() => flattenTree(locationTree.value))
const displayedTree = computed(() => (rootsOnly.value ? cloneAsRootOnly(locationTree.value) : locationTree.value))
const selectedPathSegments = computed(() => {
  if (!selectedLocation.value?.full_path) return []
  return selectedLocation.value.full_path.split('/').filter(Boolean)
})

const overviewSummaryCards = computed<SummaryCard[]>(() => {
  const summary = campusOverview.value?.analysis_summary
  const hierarchy = campusOverview.value?.hierarchy_summary
  if (!summary || !hierarchy) return []

  return [
    {
      label: '空间节点',
      value: String(allTreeNodes.value.length || hierarchy.location_counts.building || 0),
      caption: '当前可见的园区空间层级节点'
    },
    {
      label: '楼栋数量',
      value: String(summary.building_count),
      caption: '当前园区空间体系中的楼栋总数'
    },
    {
      label: '接入设备',
      value: String(summary.device_count),
      caption: `${hierarchy.active_device_count} 台在线，${summary.meter_count} 台表计`
    },
    {
      label: '实时负荷',
      value: formatNumber(summary.realtime_load, 1),
      caption: '园区空间体系当前汇总负荷'
    }
  ]
})

const locationTypeDistribution = computed<DistributionItem[]>(() => {
  const counts = new Map<string, number>()
  allTreeNodes.value.forEach((node) => {
    counts.set(node.location_type, (counts.get(node.location_type) || 0) + 1)
  })
  return Array.from(counts.entries())
    .map(([key, count]) => ({
      key,
      label: typeLabel(key),
      count
    }))
    .sort((left, right) => right.count - left.count)
})

const overviewTreeHighlights = computed(() => {
  return displayedTree.value.slice(0, 6).map((node) => ({
    id: node.id,
    name: node.name,
    label: typeLabel(node.location_type),
    deviceCount: node.device_count || 0,
    childCount: node.children?.length || 0,
    type: node.location_type
  }))
})

const selectedSummaryCards = computed<SummaryCard[]>(() => {
  if (!selectedLocation.value || !locationStats.value) return []
  return [
    {
      label: '关联设备',
      value: String(locationStats.value.total_devices),
      caption: `${locationStats.value.active_devices} 台在线设备`
    },
    {
      label: '子空间',
      value: String(locationStats.value.sub_locations_count),
      caption: '当前空间下的直接子位置数量'
    },
    {
      label: '面积',
      value: locationStats.value.area_sqm ? `${formatNumber(locationStats.value.area_sqm, 0)}` : '-',
      caption: '当前空间登记面积（m²）'
    },
    {
      label: '负责人',
      value: locationStats.value.manager || selectedLocation.value.manager || '-',
      caption: '当前空间运维责任人'
    }
  ]
})

const selectedEnergyDistribution = computed<DistributionItem[]>(() => {
  const source = locationStats.value?.by_energy_type || {}
  return Object.entries(source)
    .map(([key, count]) => ({
      key,
      label: energyLabel(key),
      count
    }))
    .sort((left, right) => right.count - left.count)
})

const selectedDeviceDistribution = computed<DistributionItem[]>(() => {
  const source = locationStats.value?.by_device_type || {}
  return Object.entries(source)
    .map(([key, count]) => ({
      key,
      label: key || '未分类设备',
      count
    }))
    .sort((left, right) => right.count - left.count)
})

const selectedDeviceHighlights = computed(() => locationDevices.value.slice(0, 6))
const topAreaRankings = computed(() => campusOverview.value?.location_rankings.areas || [])
const topBuildingRankings = computed(() => campusOverview.value?.location_rankings.buildings || [])
const energyCategories = computed(() => campusOverview.value?.energy_category_summary || [])
const latestAlarms = computed(() => campusOverview.value?.alarm_summary.latest || [])

const loadData = async () => {
  loading.value = true
  try {
    const [list, tree, types, roots, overview] = await Promise.all([
      getLocations(),
      getLocationTree(),
      getLocationTypes(),
      getRootLocations(),
      getCampusOverview()
    ])

    locationList.value = list
    locationTree.value = tree
    rootLocations.value = roots
    typeList.value = types
    campusOverview.value = overview
  } catch {
    ElMessage.error('加载园区空间数据失败')
  } finally {
    loading.value = false
  }
}

const loadDevices = async () => {
  try {
    deviceList.value = await getDevices()
  } catch {
    // 由 axios 拦截器统一提示
  }
}

const loadLocationFocus = async (locationId: number) => {
  const detail = await getLocationDetail(locationId)
  selectedLocation.value = detail

  try {
    const [devices, stats, children] = await Promise.all([
      getLocationDevices(locationId),
      getLocationStatistics(locationId),
      getChildLocations(locationId)
    ])
    locationDevices.value = devices
    locationStats.value = stats
    childLocations.value = children
  } catch {
    locationDevices.value = []
    locationStats.value = null
    childLocations.value = []
  }
}

const handleNodeClick = async (data: LocationTreeNode) => {
  await loadLocationFocus(data.id)
}

const handleSearch = async () => {
  if (!searchKeyword.value.trim()) {
    searchResults.value = []
    return
  }

  try {
    searchResults.value = await searchLocations(searchKeyword.value.trim())
  } catch {
    ElMessage.error('搜索位置失败')
  }
}

const selectSearchResult = async (location: Location) => {
  await loadLocationFocus(location.id)
  searchResults.value = []
}

const clearSelection = () => {
  selectedLocation.value = null
  locationDevices.value = []
  locationStats.value = null
  childLocations.value = []
}

const resetLocationForm = (parentId?: number) => {
  formData.id = undefined
  formData.name = ''
  formData.location_type = 'building'
  formData.parent_id = parentId
  formData.code = ''
  formData.description = ''
  formData.area_sqm = undefined
  formData.manager = ''
  formData.contact = ''
}

const fillLocationForm = (location: Location) => {
  formData.id = location.id
  formData.name = location.name
  formData.location_type = location.location_type
  formData.parent_id = location.parent_id
  formData.code = location.code || ''
  formData.description = location.description || ''
  formData.area_sqm = location.area_sqm
  formData.manager = location.manager || ''
  formData.contact = location.contact || ''
}

const {
  dialogVisible,
  dialogType,
  dialogTitle,
  openCreateDialog,
  openEditDialog
} = useCrudDialog<Location, [number?]>({
  createTitle: '新建位置',
  editTitle: '编辑位置',
  resetForm: resetLocationForm,
  fillForm: fillLocationForm
})

const { submit: submitLocationForm } = useCrudSubmit({
  dialogType,
  dialogVisible,
  createAction: async () => {
    await createLocation(formData)
    ElMessage.success('创建成功')
  },
  updateAction: async () => {
    await updateLocation(formData.id!, formData)
    ElMessage.success('更新成功')
  },
  onSuccess: async () => {
    await loadData()
    if (selectedLocation.value?.id) {
      await loadLocationFocus(selectedLocation.value.id)
    }
  }
})

const handleSubmit = async () => {
  if (!formData.name) {
    ElMessage.warning('请输入位置名称')
    return
  }
  try {
    await submitLocationForm()
  } catch {
    ElMessage.error('操作失败')
  }
}

const handleDelete = async (location: Location) => {
  try {
    await ElMessageBox.confirm(`确定删除位置 "${location.name}"？`, '提示', {
      type: 'warning'
    })
    await deleteLocation(location.id)
    ElMessage.success('删除成功')
    clearSelection()
    await loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败，可能存在子位置或关联设备')
    }
  }
}

const openAssignDialog = () => {
  selectedDeviceId.value = null
  assignDialogVisible.value = true
}

const handleAssignDevice = async () => {
  if (selectedDeviceId.value == null || !selectedLocation.value) {
    ElMessage.warning('请选择设备')
    return
  }
  try {
    await assignDeviceToLocation(selectedLocation.value.id, selectedDeviceId.value)
    ElMessage.success('设备分配成功')
    assignDialogVisible.value = false
    await loadLocationFocus(selectedLocation.value.id)
  } catch {
    ElMessage.error('分配失败')
  }
}

onMounted(async () => {
  await loadData()
  await loadDevices()
})
</script>

<template>
  <div class="location-page">
    <div class="page-header">
      <div class="header-copy">
        <h2>园区空间</h2>
        <p>围绕园区、区域、楼栋和房间建立空间主视图，管理动作退到次级入口，不再让 CRUD 主导页面节奏。</p>
        <el-tag
          v-if="hasScopedAccess"
          size="small"
          type="warning"
          effect="dark"
        >
          当前视图受位置范围限制
        </el-tag>
      </div>
      <div class="header-actions">
        <el-button
          v-if="canManageLocations"
          plain
          @click="openCreateDialog()"
        >
          <el-icon><Plus /></el-icon>新建位置
        </el-button>
        <el-button
          text
          @click="loadData"
        >
          <el-icon><Refresh /></el-icon>刷新视图
        </el-button>
      </div>
    </div>

    <div class="main-content">
      <aside class="tree-panel">
        <div class="panel-header">
          <span>空间层级</span>
          <div class="panel-tools">
            <el-switch
              v-model="rootsOnly"
              active-text="仅顶级"
            />
            <el-button
              text
              size="small"
              @click="clearSelection"
            >
              清空焦点
            </el-button>
          </div>
        </div>

        <div class="search-box">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索位置名称 / 编码"
            clearable
            @change="handleSearch"
          />
          <div
            v-if="searchResults.length > 0"
            class="search-results"
          >
            <button
              v-for="item in searchResults"
              :key="item.id"
              class="search-result"
              type="button"
              @click="selectSearchResult(item)"
            >
              <span>{{ item.name }}</span>
              <small>{{ typeLabel(item.location_type) }}</small>
            </button>
          </div>
        </div>

        <el-tree
          v-loading="loading"
          :data="displayedTree"
          :props="treeProps"
          node-key="id"
          default-expand-all
          highlight-current
          @node-click="handleNodeClick"
        >
          <template #default="{ node, data }">
            <span class="tree-node">
              <span class="node-icon">{{ typeIcon(data.location_type) }}</span>
              <span class="node-label">{{ node.label }}</span>
              <span
                v-if="data.device_count"
                class="node-count"
              >
                {{ data.device_count }} 台
              </span>
            </span>
          </template>
        </el-tree>

        <div
          v-if="displayedTree.length === 0 && !loading"
          class="empty-tree"
        >
          <el-empty
            description="暂无位置数据"
            :image-size="80"
          >
            <el-button
              v-if="canManageLocations"
              type="primary"
              size="small"
              @click="openCreateDialog()"
            >
              创建第一个位置
            </el-button>
          </el-empty>
        </div>
      </aside>

      <section class="detail-panel">
        <template v-if="selectedLocation">
          <div class="focus-hero">
            <div class="focus-header">
              <div>
                <div class="focus-breadcrumb">
                  <span
                    v-for="segment in selectedPathSegments"
                    :key="segment"
                    class="path-chip"
                  >
                    {{ segment }}
                  </span>
                </div>
                <div class="focus-title">
                  <span class="focus-icon">{{ typeIcon(selectedLocation.location_type) }}</span>
                  <div>
                    <h3>{{ selectedLocation.name }}</h3>
                    <p>{{ typeLabel(selectedLocation.location_type) }} · {{ selectedLocation.code || '未配置编码' }}</p>
                  </div>
                </div>
              </div>
              <div class="focus-actions">
                <el-button
                  v-if="canManageLocations"
                  plain
                  @click="openCreateDialog(selectedLocation.id)"
                >
                  添加子位置
                </el-button>
                <el-button
                  plain
                  @click="clearSelection"
                >
                  返回空间总览
                </el-button>
              </div>
            </div>

            <div class="summary-grid">
              <article
                v-for="card in selectedSummaryCards"
                :key="card.label"
                class="summary-card"
              >
                <span>{{ card.label }}</span>
                <strong>{{ card.value }}</strong>
                <small>{{ card.caption }}</small>
              </article>
            </div>
          </div>

          <div class="focus-grid">
            <article class="panel-card">
              <div class="card-header">
                <div>
                  <h4>子空间结构</h4>
                  <p>当前空间下的直接层级入口，便于继续向下聚焦。</p>
                </div>
              </div>
              <div
                v-if="childLocations.length"
                class="chip-grid"
              >
                <button
                  v-for="child in childLocations"
                  :key="child.id"
                  class="space-chip"
                  type="button"
                  @click="selectSearchResult(child)"
                >
                  <span>{{ typeIcon(child.location_type) }} {{ child.name }}</span>
                  <small>{{ typeLabel(child.location_type) }}</small>
                </button>
              </div>
              <el-empty
                v-else
                description="当前空间暂无直接子位置"
              />
            </article>

            <article class="panel-card">
              <div class="card-header">
                <div>
                  <h4>关联设备</h4>
                  <p>当前空间下的关键设备入口和状态摘要。</p>
                </div>
              </div>
              <div
                v-if="selectedDeviceHighlights.length"
                class="device-highlight-list"
              >
                <div
                  v-for="device in selectedDeviceHighlights"
                  :key="device.id"
                  class="device-highlight"
                >
                  <div>
                    <strong>{{ device.name }}</strong>
                    <span>{{ energyLabel(device.energy_type || 'unknown') }} · {{ device.device_category || device.device_type }}</span>
                  </div>
                  <el-tag
                    :type="device.is_active ? 'success' : 'info'"
                    size="small"
                  >
                    {{ device.is_active ? '在线' : '离线' }}
                  </el-tag>
                </div>
              </div>
              <el-empty
                v-else
                description="当前空间暂无关联设备"
              />
            </article>

            <article class="panel-card">
              <div class="card-header">
                <div>
                  <h4>核心结构信息</h4>
                  <p>保留空间关键上下文，但不再用纯详情表单占据主视觉。</p>
                </div>
              </div>
              <div class="structure-grid">
                <div class="structure-item">
                  <label>完整路径</label>
                  <span>{{ selectedLocation.full_path || '-' }}</span>
                </div>
                <div class="structure-item">
                  <label>顶级节点</label>
                  <span>{{ rootLocations.length }}</span>
                </div>
                <div class="structure-item">
                  <label>能源分布</label>
                  <span>{{ selectedEnergyDistribution.map((item) => `${item.label} ${item.count}`).join(' / ') || '-' }}</span>
                </div>
                <div class="structure-item">
                  <label>设备分类</label>
                  <span>{{ selectedDeviceDistribution.map((item) => `${item.label} ${item.count}`).join(' / ') || '-' }}</span>
                </div>
                <div class="structure-item structure-item--wide">
                  <label>空间说明</label>
                  <span>{{ selectedLocation.description || '当前空间暂无额外描述。' }}</span>
                </div>
              </div>
            </article>

            <article
              v-if="canManageLocations"
              class="panel-card panel-card--secondary"
            >
              <div class="card-header">
                <div>
                  <h4>次级管理入口</h4>
                  <p>编辑、新建子位置、设备分配与删除都保留，但不再抬到主视觉中心。</p>
                </div>
              </div>
              <div class="secondary-actions">
                <el-button @click="openEditDialog(selectedLocation)">
                  编辑空间
                </el-button>
                <el-button @click="openAssignDialog">
                  分配设备
                </el-button>
                <el-button @click="openCreateDialog(selectedLocation.id)">
                  新建子位置
                </el-button>
                <el-button
                  type="danger"
                  plain
                  @click="handleDelete(selectedLocation)"
                >
                  删除空间
                </el-button>
              </div>
            </article>
          </div>
        </template>

        <template v-else>
          <div class="overview-hero">
            <div class="overview-copy">
              <span class="overview-eyebrow">Campus Spatial View</span>
              <h3>园区空间总览</h3>
              <p>当前页面默认承接园区空间层级、分布和重点区域，不再让右侧保持空白等待选择。</p>
            </div>
            <div class="summary-grid">
              <article
                v-for="card in overviewSummaryCards"
                :key="card.label"
                class="summary-card"
              >
                <span>{{ card.label }}</span>
                <strong>{{ card.value }}</strong>
                <small>{{ card.caption }}</small>
              </article>
            </div>
          </div>

          <div class="overview-grid">
            <article class="panel-card">
              <div class="card-header">
                <div>
                  <h4>空间层级概览</h4>
                  <p>当前可见空间节点的类型、数量与树顶重点分布。</p>
                </div>
              </div>
              <div class="distribution-list">
                <div
                  v-for="item in locationTypeDistribution"
                  :key="item.key"
                  class="distribution-item"
                >
                  <div class="distribution-row">
                    <span>{{ typeIcon(item.key) }} {{ item.label }}</span>
                    <strong>{{ item.count }}</strong>
                  </div>
                  <div class="distribution-bar">
                    <span :style="{ width: `${Math.max((item.count / Math.max(allTreeNodes.length, 1)) * 100, 8)}%` }" />
                  </div>
                </div>
              </div>
            </article>

            <article class="panel-card">
              <div class="card-header">
                <div>
                  <h4>空间焦点入口</h4>
                  <p>从顶级节点快速进入空间焦点视图。</p>
                </div>
              </div>
              <div
                v-if="overviewTreeHighlights.length"
                class="chip-grid"
              >
                <button
                  v-for="item in overviewTreeHighlights"
                  :key="item.id"
                  class="space-chip"
                  type="button"
                  @click="loadLocationFocus(item.id)"
                >
                  <span>{{ typeIcon(item.type) }} {{ item.name }}</span>
                  <small>{{ item.label }} · {{ item.deviceCount }} 台设备 · {{ item.childCount }} 个子空间</small>
                </button>
              </div>
              <el-empty
                v-else
                description="当前暂无可聚焦的空间节点"
              />
            </article>

            <article class="panel-card">
              <div class="card-header">
                <div>
                  <h4>空间分布与能耗焦点</h4>
                  <p>复用现有园区聚合接口，增强未选中态的信息密度。</p>
                </div>
              </div>
              <div class="rank-column">
                <div class="rank-block">
                  <div class="rank-title">区域排行</div>
                  <div
                    v-for="item in topAreaRankings.slice(0, 4)"
                    :key="`area-${item.location_id}`"
                    class="rank-row"
                  >
                    <span>{{ item.name }}</span>
                    <strong>{{ formatNumber(item.total_consumption, 1) }}</strong>
                  </div>
                </div>
                <div class="rank-block">
                  <div class="rank-title">楼栋排行</div>
                  <div
                    v-for="item in topBuildingRankings.slice(0, 4)"
                    :key="`building-${item.location_id}`"
                    class="rank-row"
                  >
                    <span>{{ item.name }}</span>
                    <strong>{{ formatNumber(item.total_consumption, 1) }}</strong>
                  </div>
                </div>
              </div>
            </article>

            <article class="panel-card">
              <div class="card-header">
                <div>
                  <h4>能源与告警摘要</h4>
                  <p>当前园区空间下的能源分布和最近告警提示。</p>
                </div>
              </div>
              <div class="tag-list">
                <el-tag
                  v-for="item in energyCategories.slice(0, 5)"
                  :key="item.energy_category"
                  type="info"
                  effect="plain"
                >
                  {{ item.label }} {{ (item.ratio * 100).toFixed(1) }}%
                </el-tag>
              </div>
              <div class="alarm-summary">
                <div class="alarm-stat">
                  <span>未恢复告警</span>
                  <strong>{{ campusOverview?.alarm_summary.unresolved_count || 0 }}</strong>
                </div>
                <div class="alarm-stat">
                  <span>最近告警</span>
                  <strong>{{ latestAlarms.length }}</strong>
                </div>
              </div>
              <div
                v-if="latestAlarms.length"
                class="latest-alarm-list"
              >
                <div
                  v-for="alarm in latestAlarms.slice(0, 3)"
                  :key="alarm.id"
                  class="latest-alarm"
                >
                  <strong>{{ alarm.message }}</strong>
                  <span>{{ formatTimestamp(alarm.timestamp) }}</span>
                </div>
              </div>
            </article>
          </div>
        </template>
      </section>
    </div>

    <el-dialog
      v-if="canManageLocations"
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
    >
      <el-form label-width="100px">
        <el-form-item
          label="位置名称"
          required
        >
          <el-input
            v-model="formData.name"
            placeholder="请输入位置名称"
          />
        </el-form-item>
        <el-form-item
          label="位置类型"
          required
        >
          <el-select
            v-model="formData.location_type"
            style="width: 100%"
            teleported
            popper-class="app-select-popper"
          >
            <el-option
              v-for="t in typeList"
              :key="t.value"
              :label="t.label"
              :value="t.value"
            >
              <span>{{ typeIcon(t.value) }} {{ t.label }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="父级位置">
          <el-select
            v-model="formData.parent_id"
            placeholder="无（顶级位置）"
            clearable
            style="width: 100%"
            teleported
            popper-class="app-select-popper"
          >
            <el-option
              v-for="loc in locationList"
              :key="loc.id"
              :label="loc.name"
              :value="loc.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="位置编码">
          <el-input
            v-model="formData.code"
            placeholder="请输入编码"
          />
        </el-form-item>
        <el-form-item label="面积(m²)">
          <el-input-number
            v-model="formData.area_sqm"
            :min="0"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="负责人">
          <el-input
            v-model="formData.manager"
            placeholder="请输入负责人"
          />
        </el-form-item>
        <el-form-item label="联系方式">
          <el-input
            v-model="formData.contact"
            placeholder="请输入联系方式"
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
      v-if="canManageLocations"
      v-model="assignDialogVisible"
      title="分配设备"
      width="400px"
    >
      <el-form label-width="80px">
        <el-form-item label="选择设备">
          <el-select
            v-model="selectedDeviceId"
            placeholder="请选择设备"
            style="width: 100%"
            filterable
            teleported
            popper-class="app-select-popper"
          >
            <el-option
              v-for="d in deviceList"
              :key="d.id"
              :label="d.name"
              :value="d.id"
            >
              <span>{{ d.name }}</span>
              <span style="color: #999; margin-left: 10px">{{ d.energy_type }}</span>
            </el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="assignDialogVisible = false">
          取消
        </el-button>
        <el-button
          type="primary"
          @click="handleAssignDevice"
        >
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.location-page {
  min-height: 100%;
  padding: 10px;
  color: var(--text-primary);
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.header-copy {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.header-copy h2 {
  margin: 0;
}

.header-copy p {
  max-width: 720px;
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.6;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.main-content {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 20px;
  min-height: calc(100vh - 220px);
}

.tree-panel,
.focus-hero,
.overview-hero,
.panel-card {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(18, 31, 52, 0.96) 0%, rgba(9, 17, 32, 0.96) 100%);
  box-shadow: 0 20px 60px rgba(3, 10, 24, 0.22);
}

.tree-panel {
  display: flex;
  flex-direction: column;
  padding: 18px;
}

.panel-header,
.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.card-header h4,
.rank-title {
  margin: 0;
  font-size: 18px;
}

.card-header p {
  margin: 6px 0 0;
  color: var(--text-secondary);
  line-height: 1.6;
}

.panel-tools {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-box {
  margin-top: 16px;
  margin-bottom: 14px;
}

.search-results {
  display: grid;
  gap: 6px;
  margin-top: 8px;
}

.search-result,
.space-chip {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-primary);
  cursor: pointer;
}

.search-result {
  padding: 8px 10px;
  text-align: left;
}

.search-result small,
.space-chip small,
.device-highlight span,
.distribution-row,
.rank-row span,
.latest-alarm span,
.summary-card small,
.structure-item label {
  color: var(--text-secondary);
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
}

.node-count {
  color: var(--text-secondary);
  font-size: 12px;
}

.empty-tree {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.detail-panel {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.overview-hero,
.focus-hero {
  padding: 24px;
}

.overview-copy {
  margin-bottom: 18px;
}

.overview-eyebrow {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(73, 145, 255, 0.14);
  color: #8cb8ff;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.overview-copy h3,
.focus-title h3 {
  margin: 14px 0 8px;
  font-size: 30px;
}

.overview-copy p,
.focus-title p,
.distribution-item,
.structure-item span,
.alarm-stat span {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.6;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.summary-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
}

.summary-card strong {
  font-size: 28px;
}

.overview-grid,
.focus-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.panel-card {
  padding: 20px;
}

.panel-card--secondary {
  background: linear-gradient(180deg, rgba(12, 19, 32, 0.96) 0%, rgba(7, 12, 22, 0.96) 100%);
}

.distribution-list,
.rank-column,
.latest-alarm-list,
.device-highlight-list,
.secondary-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.distribution-item,
.rank-row,
.latest-alarm,
.device-highlight {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.04);
}

.distribution-row,
.rank-row,
.device-highlight {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.distribution-bar {
  height: 8px;
  margin-top: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
}

.distribution-bar span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #4a90ff 0%, #63d6ff 100%);
}

.rank-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.alarm-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}

.alarm-stat {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.04);
}

.alarm-stat strong {
  font-size: 24px;
}

.focus-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 18px;
}

.focus-breadcrumb {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.path-chip {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-secondary);
  font-size: 12px;
}

.focus-title {
  display: flex;
  align-items: center;
  gap: 14px;
}

.focus-icon {
  font-size: 34px;
}

.focus-actions {
  display: flex;
  gap: 12px;
}

.chip-grid {
  display: grid;
  gap: 10px;
}

.space-chip {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px 16px;
  text-align: left;
}

.structure-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.structure-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.04);
}

.structure-item--wide {
  grid-column: span 2;
}

.secondary-actions .el-button {
  justify-content: flex-start;
}

:deep(.el-tree) {
  background: transparent;
}

:deep(.el-tree-node__content) {
  height: 38px;
}

@media (max-width: 1280px) {
  .main-content {
    grid-template-columns: 300px minmax(0, 1fr);
  }

  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 1080px) {
  .main-content,
  .overview-grid,
  .focus-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .location-page {
    padding: 0;
  }

  .page-header,
  .focus-header,
  .header-actions,
  .focus-actions {
    flex-direction: column;
  }

  .summary-grid,
  .structure-grid,
  .alarm-summary {
    grid-template-columns: 1fr;
  }

  .structure-item--wide {
    grid-column: auto;
  }
}
</style>
