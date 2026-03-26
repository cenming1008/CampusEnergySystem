<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { getAlarms, resolveAlarm, resolveAllAlarms, type Alarm } from '@/api/alarm'
import { getDevices, type Device } from '@/api/device'

const loading = ref(false)
const resolving = ref<number | null>(null)
const bulkResolving = ref(false)
const alarms = ref<Alarm[]>([])
const deviceList = ref<Device[]>([])

const filters = reactive<{
  device_id?: number
  resolved?: boolean
  start_time?: string
  end_time?: string
  limit: number
}>({
  resolved: false,
  limit: 50,
})

const hasActiveAlarms = computed(() => alarms.value.some((item) => !item.is_resolved))

function resolveDeviceName(deviceId: number) {
  return deviceList.value.find((item) => item.id === deviceId)?.name || `设备 ${deviceId}`
}

function severityTagType(severity?: string) {
  if (severity === 'critical') return 'danger'
  if (severity === 'warning') return 'warning'
  return 'info'
}

async function loadDevices() {
  try {
    deviceList.value = await getDevices()
  } catch (error) {
    console.error('加载设备失败', error)
  }
}

async function loadAlarms() {
  loading.value = true
  try {
    alarms.value = await getAlarms({
      device_id: filters.device_id,
      resolved: filters.resolved,
      start_time: filters.start_time,
      end_time: filters.end_time,
      limit: filters.limit,
    })
  } finally {
    loading.value = false
  }
}

async function handleResolve(alarm: Alarm) {
  resolving.value = alarm.id
  try {
    await resolveAlarm(alarm.id)
    ElMessage.success('报警已处理')
    await loadAlarms()
  } finally {
    resolving.value = null
  }
}

async function handleResolveAll() {
  bulkResolving.value = true
  try {
    const response = await resolveAllAlarms()
    ElMessage.success(response.message || '报警已批量处理')
    await loadAlarms()
  } finally {
    bulkResolving.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadDevices(), loadAlarms()])
})
</script>

<template>
  <div class="alarm-center-page">
    <div class="hero">
      <div>
        <h2>告警中心</h2>
        <p>集中查看未处理、已恢复和历史告警，支持按设备与时间窗筛选。</p>
      </div>
      <el-button
        type="danger"
        :disabled="!hasActiveAlarms"
        :loading="bulkResolving"
        @click="handleResolveAll"
      >
        一键处理未恢复告警
      </el-button>
    </div>

    <el-card shadow="never">
      <div class="filters">
        <el-select
          v-model="filters.device_id"
          clearable
          filterable
          placeholder="全部设备"
          teleported
          popper-class="app-select-popper"
        >
          <el-option
            v-for="device in deviceList"
            :key="device.id"
            :label="device.name"
            :value="device.id"
          />
        </el-select>
        <el-select
          v-model="filters.resolved"
          clearable
          placeholder="报警状态"
          teleported
          popper-class="app-select-popper"
        >
          <el-option
            label="仅未恢复"
            :value="false"
          />
          <el-option
            label="仅已恢复"
            :value="true"
          />
        </el-select>
        <el-date-picker
          v-model="filters.start_time"
          type="datetime"
          value-format="YYYY-MM-DDTHH:mm:ss"
          placeholder="开始时间"
        />
        <el-date-picker
          v-model="filters.end_time"
          type="datetime"
          value-format="YYYY-MM-DDTHH:mm:ss"
          placeholder="结束时间"
        />
        <el-input-number
          v-model="filters.limit"
          :min="10"
          :max="100"
          :step="10"
        />
        <el-button
          type="primary"
          :loading="loading"
          @click="loadAlarms"
        >
          查询
        </el-button>
      </div>

      <el-table
        v-loading="loading"
        :data="alarms"
        class="table"
      >
        <el-table-column
          prop="timestamp"
          label="时间"
          min-width="180"
        />
        <el-table-column
          label="设备"
          min-width="160"
        >
          <template #default="{ row }">
            {{ resolveDeviceName(row.device_id) }}
          </template>
        </el-table-column>
        <el-table-column
          label="严重级别"
          width="120"
        >
          <template #default="{ row }">
            <el-tag :type="severityTagType(row.severity)">
              {{ row.severity || 'info' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="message"
          label="告警内容"
          min-width="260"
        />
        <el-table-column
          label="状态"
          width="120"
        >
          <template #default="{ row }">
            <el-tag :type="row.is_resolved ? 'success' : 'danger'">
              {{ row.is_resolved ? '已恢复' : '未恢复' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          label="处理信息"
          min-width="220"
        >
          <template #default="{ row }">
            <div class="stack-cell">
              <span>{{ row.resolved_by || '-' }}</span>
              <small>{{ row.handling_note || row.resolved_at || '待处理' }}</small>
            </div>
          </template>
        </el-table-column>
        <el-table-column
          label="操作"
          width="140"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button
              size="small"
              type="primary"
              :disabled="row.is_resolved"
              :loading="resolving === row.id"
              @click="handleResolve(row)"
            >
              处理
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.alarm-center-page {
  display: grid;
  gap: 16px;
}

.hero {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.hero h2,
.hero p {
  margin: 0;
}

.hero p {
  margin-top: 6px;
  color: #94a3b8;
}

.filters {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
  align-items: center;
}

.stack-cell {
  display: flex;
  flex-direction: column;
}

.stack-cell small {
  color: #94a3b8;
}
</style>
