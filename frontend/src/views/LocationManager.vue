<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getLocations,
  getRootLocations,
  getLocationTypes,
  getLocationTree,
  createLocation,
  updateLocation,
  deleteLocation,
  getLocationDetail,
  getLocationDevices,
  getChildLocations,
  assignDeviceToLocation,
  getLocationStatistics,
  searchLocations,
  type Location,
  type LocationTreeNode,
  type LocationTypeInfo,
  type LocationCreateRequest,
  type LocationStatistics
} from '@/api/location'
import { getDevices, type Device } from '@/api/device'
import { usePermissions } from '@/shared/composables/usePermissions'

// --- 状态 ---
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
const searchKeyword = ref('')
const searchResults = ref<Location[]>([])
const rootsOnly = ref(false)
const { canManageLocations, hasScopedAccess } = usePermissions()

// 对话框状态
const dialogVisible = ref(false)
const dialogType = ref<'create' | 'edit'>('create')
const dialogTitle = computed(() => dialogType.value === 'create' ? '新建位置' : '编辑位置')

// 设备分配对话框
const assignDialogVisible = ref(false)
const selectedDeviceId = ref<number | null>(null)

// 表单数据
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

// 树形配置
const treeProps = {
  children: 'children',
  label: 'name'
}

// --- 计算属性 ---
const typeLabel = (type: string) => {
  const item = typeList.value.find(t => t.value === type)
  return item?.label || type
}

const typeIcon = (type: string) => {
  const map: Record<string, string> = {
    building: '🏢',
    unit: '🏠',
    floor: '📊',
    room: '🚪',
    workshop: '🏭',
    area: '📍',
    zone: '🗺️'
  }
  return map[type] || '📍'
}

// --- 方法 ---
const loadData = async () => {
  loading.value = true
  try {
    const [list, tree, types, roots] = await Promise.all([
      getLocations(),
      getLocationTree(),
      getLocationTypes(),
      getRootLocations()
    ])
    locationList.value = rootsOnly.value ? roots : list
    locationTree.value = rootsOnly.value ? (tree.data || []).filter((item) => item.parent_id == null) : (tree.data || [])
    rootLocations.value = roots
    typeList.value = types.data || []
  } catch {
    ElMessage.error('加载数据失败')
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

const handleNodeClick = async (data: LocationTreeNode) => {
  selectedLocation.value = await getLocationDetail(data.id)
  try {
    const [devices, stats, children] = await Promise.all([
      getLocationDevices(data.id),
      getLocationStatistics(data.id),
      getChildLocations(data.id)
    ])
    locationDevices.value = devices
    locationStats.value = stats.data || null
    childLocations.value = children
  } catch {
    // 由 axios 拦截器统一提示
  }
}

const handleSearch = async () => {
  if (!searchKeyword.value.trim()) {
    searchResults.value = []
    return
  }
  try {
    searchResults.value = await searchLocations(searchKeyword.value.trim())
  } catch (error) {
    ElMessage.error('搜索位置失败')
  }
}

const selectSearchResult = async (location: Location) => {
  await handleNodeClick({
    ...location,
    children: []
  })
  searchResults.value = []
}

const openCreateDialog = (parentId?: number) => {
  dialogType.value = 'create'
  formData.id = undefined
  formData.name = ''
  formData.location_type = 'building'
  formData.parent_id = parentId
  formData.code = ''
  formData.description = ''
  formData.area_sqm = undefined
  formData.manager = ''
  formData.contact = ''
  dialogVisible.value = true
}

const openEditDialog = (location: Location) => {
  dialogType.value = 'edit'
  formData.id = location.id
  formData.name = location.name
  formData.location_type = location.location_type
  formData.parent_id = location.parent_id
  formData.code = location.code || ''
  formData.description = location.description || ''
  formData.area_sqm = location.area_sqm
  formData.manager = location.manager || ''
  formData.contact = location.contact || ''
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formData.name) {
    ElMessage.warning('请输入位置名称')
    return
  }
  try {
    if (dialogType.value === 'create') {
      await createLocation(formData)
      ElMessage.success('创建成功')
    } else {
      await updateLocation(formData.id!, formData)
      ElMessage.success('更新成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (e) {
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
    selectedLocation.value = null
    locationDevices.value = []
    locationStats.value = null
    loadData()
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
    // 刷新设备列表
    const devices = await getLocationDevices(selectedLocation.value.id)
    locationDevices.value = devices
  } catch (e) {
    ElMessage.error('分配失败')
  }
}

// --- 生命周期 ---
onMounted(async () => {
  await loadData()
  await loadDevices()
})
</script>

<template>
  <div class="location-page">
    <div class="page-header">
      <div>
        <h2>位置管理</h2>
        <el-tag
          v-if="hasScopedAccess"
          size="small"
          type="warning"
          effect="dark"
        >
          当前视图受位置范围限制
        </el-tag>
      </div>
      <el-button
        v-if="canManageLocations"
        type="primary"
        @click="openCreateDialog()"
      >
        <el-icon><Plus /></el-icon>新建位置
      </el-button>
    </div>

    <div class="main-content">
      <!-- 左侧树形结构 -->
      <div class="tree-panel">
        <div class="panel-header">
          <span>位置层级</span>
          <div class="panel-tools">
            <el-switch
              v-model="rootsOnly"
              active-text="仅顶级"
              @change="loadData"
            />
            <el-button
              text
              size="small"
              @click="loadData"
            >
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
        </div>
        <div class="search-box">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索位置名称/编码"
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
          :data="locationTree"
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
              >({{ data.device_count }})</span>
            </span>
          </template>
        </el-tree>
        
        <div
          v-if="locationTree.length === 0 && !loading"
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
      </div>

      <!-- 右侧详情 -->
      <div class="detail-panel">
        <template v-if="selectedLocation">
          <!-- 位置信息卡片 -->
          <div class="info-card">
            <div class="card-header">
              <div class="location-title">
                <span class="icon">{{ typeIcon(selectedLocation.location_type) }}</span>
                <span class="name">{{ selectedLocation.name }}</span>
                <el-tag size="small">
                  {{ typeLabel(selectedLocation.location_type) }}
                </el-tag>
              </div>
              <div
                v-if="canManageLocations"
                class="actions"
              >
                <el-button
                  text
                  @click="openCreateDialog(selectedLocation.id)"
                >
                  <el-icon><Plus /></el-icon>添加子位置
                </el-button>
                <el-button
                  text
                  @click="openEditDialog(selectedLocation)"
                >
                  <el-icon><Edit /></el-icon>编辑
                </el-button>
                <el-button
                  text
                  type="danger"
                  @click="handleDelete(selectedLocation)"
                >
                  <el-icon><Delete /></el-icon>删除
                </el-button>
              </div>
            </div>
            
            <div class="info-grid">
              <div class="info-item">
                <label>编码</label>
                <span>{{ selectedLocation.code || '-' }}</span>
              </div>
              <div class="info-item">
                <label>面积</label>
                <span>{{ selectedLocation.area_sqm ? `${selectedLocation.area_sqm} m²` : '-' }}</span>
              </div>
              <div class="info-item">
                <label>负责人</label>
                <span>{{ selectedLocation.manager || '-' }}</span>
              </div>
              <div class="info-item">
                <label>联系方式</label>
                <span>{{ selectedLocation.contact || '-' }}</span>
              </div>
            </div>
            
            <div
              v-if="selectedLocation.description"
              class="description"
            >
              {{ selectedLocation.description }}
            </div>

            <div
              v-if="childLocations.length > 0"
              class="child-section"
            >
              <div class="child-title">
                下级位置
              </div>
              <div class="child-list">
                <button
                  v-for="child in childLocations"
                  :key="child.id"
                  class="child-chip"
                  type="button"
                  @click="selectSearchResult(child)"
                >
                  {{ child.name }}
                </button>
              </div>
            </div>
          </div>

          <!-- 统计卡片 -->
          <div
            v-if="locationStats"
            class="stats-row"
          >
            <div class="stat-item">
              <div class="stat-value">
                {{ locationStats.total_devices }}
              </div>
              <div class="stat-label">
                总设备数
              </div>
            </div>
            <div class="stat-item">
              <div class="stat-value success">
                {{ locationStats.active_devices }}
              </div>
              <div class="stat-label">
                在线设备
              </div>
            </div>
            <div class="stat-item">
              <div class="stat-value">
                {{ locationStats.sub_locations_count }}
              </div>
              <div class="stat-label">
                子位置数
              </div>
            </div>
          </div>

          <!-- 设备列表 -->
          <div class="device-list-card">
            <div class="card-header">
              <span>位置下设备</span>
              <el-button
                v-if="canManageLocations"
                type="primary"
                size="small"
                @click="openAssignDialog"
              >
                <el-icon><Plus /></el-icon>分配设备
              </el-button>
            </div>
            
            <el-table
              :data="locationDevices"
              stripe
              max-height="300"
            >
              <el-table-column
                prop="id"
                label="ID"
                width="60"
              />
              <el-table-column
                prop="name"
                label="设备名称"
              />
              <el-table-column
                prop="energy_type"
                label="能源类型"
                width="100"
              />
              <el-table-column
                prop="device_type"
                label="设备类型"
                width="100"
              />
              <el-table-column
                label="状态"
                width="80"
              >
                <template #default="{ row }">
                  <el-tag
                    :type="row.is_active ? 'success' : 'info'"
                    size="small"
                  >
                    {{ row.is_active ? '在线' : '离线' }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
            
            <el-empty
              v-if="locationDevices.length === 0"
              description="暂无设备"
              :image-size="60"
            />
          </div>
        </template>

        <template v-else>
          <div class="empty-detail">
            <el-empty
              description="请在左侧选择一个位置"
              :image-size="120"
            />
          </div>
        </template>
      </div>
    </div>

    <!-- 新建/编辑对话框 -->
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

    <!-- 设备分配对话框 -->
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
  padding: 10px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: var(--text-primary);
}

.main-content {
  flex: 1;
  display: flex;
  gap: 20px;
  min-height: 0;
}

.tree-panel {
  width: 300px;
  background: var(--bg-card);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  padding: 15px;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.panel-tools {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-box {
  margin-bottom: 12px;
}

.search-results {
  display: grid;
  gap: 6px;
  margin-top: 8px;
}

.search-result {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  padding: 8px 10px;
  text-align: left;
}

.search-result small {
  color: var(--text-secondary);
  margin-left: 8px;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
}

.node-icon {
  font-size: 16px;
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
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto;
}

.info-card, .device-list-card {
  background: var(--bg-card);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.location-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.location-title .icon {
  font-size: 24px;
}

.location-title .name {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.info-item label {
  font-size: 12px;
  color: var(--text-secondary);
}

.info-item span {
  color: var(--text-primary);
}

.description {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.child-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.child-title {
  color: var(--text-secondary);
  font-size: 12px;
  margin-bottom: 10px;
}

.child-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.child-chip {
  background: rgba(64, 158, 255, 0.1);
  border: 1px solid rgba(64, 158, 255, 0.3);
  color: var(--text-primary);
  border-radius: 999px;
  padding: 6px 10px;
}

.stats-row {
  display: flex;
  gap: 20px;
}

.stat-item {
  flex: 1;
  background: var(--bg-card);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  padding: 20px;
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-value.success {
  color: #67c23a;
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 5px;
}

.empty-detail {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-card);
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

:deep(.el-tree) {
  background: transparent;
}

:deep(.el-tree-node__content) {
  height: 36px;
}
</style>
