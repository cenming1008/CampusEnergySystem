<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getDeviceGroups,
  getGroupTypes,
  getAllGroupStatistics,
  getGroupDetail,
  createGroup,
  updateGroup,
  deleteGroup,
  getGroupDevices,
  addDeviceToGroup,
  batchAddDevicesToGroup,
  removeDeviceFromGroup,
  getGroupDeviceCount as fetchGroupDeviceCount,
  getGroupStatistics,
  searchGroups,
  type DeviceGroup,
  type GroupTypeInfo,
  type GroupStatistics,
  type AllGroupStatistics,
  type GroupCreateRequest
} from '@/api/deviceGroup'
import { getDevices, type Device } from '@/api/device'
import { usePermissions } from '@/shared/composables/usePermissions'
import { useCrudDialog } from '@/shared/composables/useCrudDialog'
import { useCrudSubmit } from '@/shared/composables/useCrudSubmit'

// --- 状态 ---
const loading = ref(false)
const groupList = ref<DeviceGroup[]>([])
const typeList = ref<GroupTypeInfo[]>([])
const allStats = ref<AllGroupStatistics[]>([])
const deviceList = ref<Device[]>([])
const selectedGroup = ref<DeviceGroup | null>(null)
const groupDevices = ref<Device[]>([])
const groupStats = ref<GroupStatistics | null>(null)
const exactGroupDeviceCount = ref<number | null>(null)
const searchKeyword = ref('')
const { canManageGroups, hasScopedAccess } = usePermissions()

// 对话框状态
// 添加设备对话框
const addDeviceDialogVisible = ref(false)
const selectedDeviceIds = ref<number[]>([])

// 表单数据
const formData = reactive<GroupCreateRequest & { id?: number }>({
  name: '',
  code: '',
  description: '',
  group_type: 'production',
  parent_id: undefined,
  manager: '',
  contact: ''
})

// --- 计算属性 ---
const typeLabel = (type: string) => {
  const item = typeList.value.find(t => t.value === type)
  return item?.label || type
}

const typeColor = (type: string) => {
  const map: Record<string, string> = {
    production: '#409eff',
    office: '#67c23a',
    critical: '#e6a23c',
    backup: '#909399'
  }
  return map[type] || '#409eff'
}

// 可添加的设备（排除已在分组中的）
const availableDevices = computed(() => {
  const existingIds = new Set(groupDevices.value.map(d => d.id))
  return deviceList.value.filter(d => !existingIds.has(d.id))
})

// --- 方法 ---
const loadData = async () => {
  loading.value = true
  try {
    const [groups, types, stats] = await Promise.all([
      searchKeyword.value.trim() ? searchGroups(searchKeyword.value.trim()) : getDeviceGroups(),
      getGroupTypes(),
      getAllGroupStatistics()
    ])
    groupList.value = groups
    typeList.value = types.data || []
    allStats.value = stats.data || []
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

const getGroupDeviceCountLabel = (groupId: number) => {
  const stat = allStats.value.find(s => s.group_id === groupId)
  return stat?.device_count || 0
}

const selectGroup = async (group: DeviceGroup) => {
  selectedGroup.value = await getGroupDetail(group.id)
  try {
    const [devices, stats, count] = await Promise.all([
      getGroupDevices(group.id),
      getGroupStatistics(group.id),
      fetchGroupDeviceCount(group.id)
    ])
    groupDevices.value = devices
    groupStats.value = stats.data || null
    exactGroupDeviceCount.value = count.data?.count || 0
  } catch {
    // 由 axios 拦截器统一提示
  }
}

const handleSearch = () => {
  loadData()
}

const resetGroupForm = () => {
  formData.id = undefined
  formData.name = ''
  formData.code = ''
  formData.description = ''
  formData.group_type = 'production'
  formData.parent_id = undefined
  formData.manager = ''
  formData.contact = ''
}

const fillGroupForm = (group: DeviceGroup) => {
  formData.id = group.id
  formData.name = group.name
  formData.code = group.code || ''
  formData.description = group.description || ''
  formData.group_type = group.group_type || 'production'
  formData.parent_id = group.parent_id
  formData.manager = group.manager || ''
  formData.contact = group.contact || ''
}

const {
  dialogVisible,
  dialogType,
  dialogTitle,
  openCreateDialog,
  openEditDialog
} = useCrudDialog<DeviceGroup>({
  createTitle: '新建分组',
  editTitle: '编辑分组',
  resetForm: resetGroupForm,
  fillForm: fillGroupForm
})

const { submit: submitGroupForm } = useCrudSubmit({
  dialogType,
  dialogVisible,
  createAction: async () => {
    await createGroup(formData)
    ElMessage.success('创建成功')
  },
  updateAction: async () => {
    await updateGroup(formData.id!, formData)
    ElMessage.success('更新成功')
  },
  onSuccess: () => {
    loadData()
  }
})

const handleSubmit = async () => {
  if (!formData.name) {
    ElMessage.warning('请输入分组名称')
    return
  }
  try {
    await submitGroupForm()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const handleDelete = async (group: DeviceGroup) => {
  try {
    await ElMessageBox.confirm(`确定删除分组 "${group.name}"？`, '提示', {
      type: 'warning'
    })
    await deleteGroup(group.id)
    ElMessage.success('删除成功')
    if (selectedGroup.value?.id === group.id) {
      selectedGroup.value = null
      groupDevices.value = []
      groupStats.value = null
    }
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const openAddDeviceDialog = () => {
  selectedDeviceIds.value = []
  addDeviceDialogVisible.value = true
}

const handleAddDevices = async () => {
  if (!selectedGroup.value || selectedDeviceIds.value.length === 0) {
    ElMessage.warning('请选择设备')
    return
  }
  try {
    if (selectedDeviceIds.value.length === 1) {
      const targetDeviceId = selectedDeviceIds.value[0]
      if (targetDeviceId == null) return
      await addDeviceToGroup(selectedGroup.value.id, targetDeviceId)
    } else {
      await batchAddDevicesToGroup(selectedGroup.value.id, selectedDeviceIds.value)
    }
    ElMessage.success('添加成功')
    addDeviceDialogVisible.value = false
    // 刷新
    const devices = await getGroupDevices(selectedGroup.value.id)
    groupDevices.value = devices
    loadData() // 刷新统计
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

const handleRemoveDevice = async (device: Device) => {
  if (!selectedGroup.value) return
  try {
    await ElMessageBox.confirm(`确定将 "${device.name}" 从分组中移除？`, '提示', {
      type: 'warning'
    })
    if (device.id == null) return
    await removeDeviceFromGroup(selectedGroup.value.id, device.id)
    ElMessage.success('移除成功')
    const devices = await getGroupDevices(selectedGroup.value.id)
    groupDevices.value = devices
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('移除失败')
    }
  }
}

// --- 生命周期 ---
onMounted(async () => {
  await loadData()
  await loadDevices()
})
</script>

<template>
  <div class="groups-page">
    <div class="page-header">
      <div>
        <h2>设备分组</h2>
        <el-tag
          v-if="hasScopedAccess"
          size="small"
          type="warning"
          effect="dark"
        >
          当前分组与设备已按位置范围过滤
        </el-tag>
      </div>
      <el-button
        v-if="canManageGroups"
        type="primary"
        @click="openCreateDialog"
      >
        <el-icon><Plus /></el-icon>新建分组
      </el-button>
    </div>

    <div class="main-content">
      <!-- 左侧分组列表 -->
      <div class="group-list-panel">
        <div class="panel-header">
          <span>分组列表</span>
          <el-button
            text
            size="small"
            @click="loadData"
          >
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>
        <div class="search-box">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索分组名称/编码"
            clearable
            @change="handleSearch"
          />
        </div>
        
        <div
          v-loading="loading"
          class="group-list"
        >
          <div
            v-for="group in groupList"
            :key="group.id"
            class="group-item"
            :class="{ active: selectedGroup?.id === group.id }"
            @click="selectGroup(group)"
          >
            <div class="group-info">
              <div class="group-name">
                <span
                  class="color-dot"
                  :style="{ background: typeColor(group.group_type || '') }"
                />
                {{ group.name }}
              </div>
              <div class="group-meta">
                <el-tag
                  size="small"
                  :color="typeColor(group.group_type || '')"
                  effect="dark"
                >
                  {{ typeLabel(group.group_type || '') }}
                </el-tag>
                <span class="device-count">{{ getGroupDeviceCountLabel(group.id) }} 台设备</span>
              </div>
            </div>
            <div
              v-if="canManageGroups"
              class="group-actions"
              @click.stop
            >
              <el-button
                text
                size="small"
                @click="openEditDialog(group)"
              >
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button
                text
                size="small"
                type="danger"
                @click="handleDelete(group)"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
          
          <el-empty
            v-if="groupList.length === 0 && !loading"
            description="暂无分组"
            :image-size="60"
          >
            <el-button
              v-if="canManageGroups"
              type="primary"
              size="small"
              @click="openCreateDialog"
            >
              创建分组
            </el-button>
          </el-empty>
        </div>
      </div>

      <!-- 右侧详情 -->
      <div class="detail-panel">
        <template v-if="selectedGroup">
          <!-- 分组信息 -->
          <div class="info-card">
            <div class="card-header">
              <div class="group-title">
                <span
                  class="color-dot large"
                  :style="{ background: typeColor(selectedGroup.group_type || '') }"
                />
                <span class="name">{{ selectedGroup.name }}</span>
                <el-tag size="small">
                  {{ typeLabel(selectedGroup.group_type || '') }}
                </el-tag>
              </div>
            </div>
            
            <div class="info-grid">
              <div class="info-item">
                <label>分组编码</label>
                <span>{{ selectedGroup.code || '-' }}</span>
              </div>
              <div class="info-item">
                <label>负责人</label>
                <span>{{ selectedGroup.manager || '-' }}</span>
              </div>
              <div class="info-item">
                <label>联系方式</label>
                <span>{{ selectedGroup.contact || '-' }}</span>
              </div>
              <div class="info-item">
                <label>创建时间</label>
                <span>{{ selectedGroup.created_at ? new Date(selectedGroup.created_at).toLocaleDateString() : '-' }}</span>
              </div>
              <div class="info-item">
                <label>精确设备数</label>
                <span>{{ exactGroupDeviceCount ?? groupDevices.length }}</span>
              </div>
            </div>
            
            <div
              v-if="selectedGroup.description"
              class="description"
            >
              {{ selectedGroup.description }}
            </div>
          </div>

          <!-- 统计 -->
          <div
            v-if="groupStats"
            class="stats-row"
          >
            <div class="stat-item">
              <div class="stat-value">
                {{ groupStats.total_devices }}
              </div>
              <div class="stat-label">
                总设备数
              </div>
            </div>
            <div class="stat-item">
              <div class="stat-value success">
                {{ groupStats.active_devices }}
              </div>
              <div class="stat-label">
                在线设备
              </div>
            </div>
            <div
              v-for="(count, type) in groupStats.by_energy_type"
              :key="type"
              class="stat-item"
            >
              <div class="stat-value">
                {{ count }}
              </div>
              <div class="stat-label">
                {{ type }}
              </div>
            </div>
          </div>

          <!-- 设备列表 -->
          <div class="device-list-card">
            <div class="card-header">
              <span>分组设备</span>
              <el-button
                v-if="canManageGroups"
                type="primary"
                size="small"
                @click="openAddDeviceDialog"
              >
                <el-icon><Plus /></el-icon>添加设备
              </el-button>
            </div>
            
            <el-table
              :data="groupDevices"
              stripe
              max-height="400"
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
              <el-table-column
                v-if="canManageGroups"
                label="操作"
                width="80"
                fixed="right"
              >
                <template #default="{ row }">
                  <el-button
                    type="danger"
                    link
                    size="small"
                    @click="handleRemoveDevice(row)"
                  >
                    移除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            
            <el-empty
              v-if="groupDevices.length === 0"
              description="暂无设备"
              :image-size="60"
            />
          </div>
        </template>

        <template v-else>
          <div class="empty-detail">
            <el-empty
              description="请在左侧选择一个分组"
              :image-size="120"
            />
          </div>
        </template>
      </div>
    </div>

    <!-- 新建/编辑对话框 -->
    <el-dialog
      v-if="canManageGroups"
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
    >
      <el-form label-width="100px">
        <el-form-item
          label="分组名称"
          required
        >
          <el-input
            v-model="formData.name"
            placeholder="请输入分组名称"
          />
        </el-form-item>
        <el-form-item label="分组类型">
          <el-select
            v-model="formData.group_type"
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
              <span
                class="color-dot"
                :style="{ background: typeColor(t.value) }"
              />
              <span style="margin-left: 8px">{{ t.label }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="分组编码">
          <el-input
            v-model="formData.code"
            placeholder="请输入编码"
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

    <!-- 添加设备对话框 -->
    <el-dialog
      v-if="canManageGroups"
      v-model="addDeviceDialogVisible"
      title="添加设备到分组"
      width="500px"
    >
      <el-form label-width="80px">
        <el-form-item label="选择设备">
          <el-select
            v-model="selectedDeviceIds"
            placeholder="请选择设备（可多选）"
            style="width: 100%"
            multiple
            filterable
            teleported
            popper-class="app-select-popper"
          >
            <el-option
              v-for="d in availableDevices"
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
        <el-button @click="addDeviceDialogVisible = false">
          取消
        </el-button>
        <el-button
          type="primary"
          @click="handleAddDevices"
        >
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.groups-page {
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

.group-list-panel {
  width: 350px;
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

.search-box {
  margin-bottom: 12px;
}

.group-list {
  flex: 1;
  overflow-y: auto;
}

.group-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 8px;
  border: 1px solid transparent;
}

.group-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.group-item.active {
  background: rgba(64, 158, 255, 0.1);
  border-color: var(--brand-color);
}

.group-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: var(--text-primary);
}

.color-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.color-dot.large {
  width: 12px;
  height: 12px;
}

.group-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 5px;
}

.device-count {
  font-size: 12px;
  color: var(--text-secondary);
}

.group-actions {
  display: flex;
  gap: 5px;
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

.group-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.group-title .name {
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

.stats-row {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.stat-item {
  flex: 1;
  min-width: 100px;
  background: var(--bg-card);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  padding: 15px;
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-value.success {
  color: #67c23a;
}

.stat-label {
  font-size: 12px;
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
</style>
