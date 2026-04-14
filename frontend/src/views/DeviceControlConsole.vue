<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Monitor, Refresh, Setting, SwitchButton } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { toggleDeviceStatus } from '@/api/device'
import {
  getDeviceMonitorControlLogs,
  getDeviceMonitorOverview,
  type DeviceControlLog,
  type MonitorOverview,
} from '@/api/deviceMonitor'
import {
  getCompensationCapacitorBankControlProfile,
  writeCompensationCapacitorBankControlProfile,
  type CompensationCapacitorBankControlProfile,
} from '@/api/compensation'
import { resolveCompensationSubtype } from '@/shared/compensationDevices'
import { usePermissions } from '@/shared/composables/usePermissions'
import {
  capacitorBankEditableParameterMeta,
  capacitorBankControlGroupLabels,
  getCapacitorBankControlEditableValue,
  getCapacitorBankEditableParameterMeta,
  getCapacitorBankControlParameterMeta,
  capacitorBankControlParameterMeta,
  formatCapacitorBankControlValue,
} from '@/features/device-control/capacitorBankControlProfile'

const route = useRoute()
const router = useRouter()
const { canManageDevices, canControlDevices, isAdmin } = usePermissions()

const deviceId = computed(() => Number(route.params.id))
const loading = ref(false)
const toggleSubmitting = ref(false)
const writeSubmitting = ref(false)
const writeDialogVisible = ref(false)
const overview = ref<MonitorOverview | null>(null)
const controlProfile = ref<CompensationCapacitorBankControlProfile | null>(null)
const controlLogs = ref<DeviceControlLog[]>([])
const loadError = ref('')
const selectedParameterKey = ref('')
const writeForm = ref<{
  parameter_key: string
  target_value: string | number | boolean | null
  reason: string
}>({
  parameter_key: '',
  target_value: null,
  reason: '',
})

const archive = computed(() => overview.value?.archive)
const runtimeStatus = computed(() => overview.value?.runtime_status)
const compensationSubtype = computed(() => resolveCompensationSubtype(
  archive.value?.device_type,
  archive.value?.device_subtype,
) || '')
const isCapacitorBankController = computed(() => compensationSubtype.value === 'capacitor_bank_controller')
const controlCapabilities = computed(() => controlProfile.value?.capabilities)
const canToggleRemotely = computed(() =>
  Boolean(canControlDevices.value)
  && runtimeStatus.value?.is_online !== false
  && controlCapabilities.value?.supports_remote_control === true,
)
const canWriteParameters = computed(() =>
  Boolean(isAdmin.value)
  && runtimeStatus.value?.is_online !== false
  && controlCapabilities.value?.supports_write === true
  && ['fresh', 'stale'].includes(controlProfile.value?.source_status || ''),
)
const deviceActive = computed(() => runtimeStatus.value?.is_active ?? false)
const latestControlLog = computed(() => controlLogs.value[0] || null)
const selectedWriteMeta = computed(() => (
  selectedParameterKey.value ? getCapacitorBankEditableParameterMeta(selectedParameterKey.value) || null : null
))
const writeDisabledReason = computed(() => {
  if (!isAdmin.value) return '仅管理员可执行参数写入。'
  if (runtimeStatus.value?.is_online === false) return '当前设备离线，暂不开放参数写入。'
  if (controlCapabilities.value?.supports_write !== true) {
    return controlCapabilities.value?.write_status_message || '参数写入能力未开通。'
  }
  if (!['fresh', 'stale'].includes(controlProfile.value?.source_status || '')) {
    return '当前设备尚未完成真实参数回读，暂不允许下发参数写入。'
  }
  return ''
})

const overviewItems = computed(() => [
  { label: '设备名称', value: archive.value?.name || '--' },
  { label: '设备编码', value: archive.value?.sn || '--' },
  { label: '在线状态', value: runtimeStatus.value?.is_online ? '在线' : '离线' },
  { label: '最近通讯时间', value: formatDateTime(runtimeStatus.value?.last_message_at) },
  { label: '参数回读状态', value: sourceStatusText(controlProfile.value?.source_status) },
  { label: '当前告警摘要', value: `${runtimeStatus.value?.unresolved_alarm_count ?? 0} 条未处理` },
])

const groupedParameters = computed(() => {
  const groups = new Map<string, typeof capacitorBankControlParameterMeta>()
  for (const item of capacitorBankControlParameterMeta) {
    const existing = groups.get(item.group)
    if (existing) {
      existing.push(item)
    } else {
      groups.set(item.group, [item])
    }
  }
  return Array.from(groups.entries()).map(([key, items]) => ({
    key,
    label: capacitorBankControlGroupLabels[key as keyof typeof capacitorBankControlGroupLabels],
    items,
  }))
})

const editableParameterCards = computed(() =>
  capacitorBankEditableParameterMeta.map((item) => ({
    ...item,
    currentValue: formatCapacitorBankControlValue(controlProfile.value, item),
  })),
)

const actionCards = computed(() => [
  {
    title: '启停 / 使能',
    icon: SwitchButton,
    hint: canToggleRemotely.value
      ? `当前设备${deviceActive.value ? '运行中，可执行停用' : '已停用，可执行启用'}`
      : controlCapabilities.value?.remote_control_status_message || '远程控制能力待接入',
    actionLabel: deviceActive.value ? '停用设备' : '启用设备',
    enabled: canToggleRemotely.value,
    handler: handleToggleDevice,
  },
  {
    title: '手动投切测试',
    icon: Setting,
    hint: controlCapabilities.value?.remote_control_status_message || '远程控制能力待接入',
    actionLabel: '待开通',
    enabled: false,
  },
  {
    title: '报警复位',
    icon: Refresh,
    hint: controlCapabilities.value?.remote_control_status_message || '远程控制能力待接入',
    actionLabel: '待开通',
    enabled: false,
  },
  {
    title: '控制模式切换',
    icon: Setting,
    hint: controlCapabilities.value?.remote_control_status_message || '远程控制能力待接入',
    actionLabel: '待开通',
    enabled: false,
  },
])

const summaryItems = computed(() =>
  capacitorBankControlParameterMeta
    .filter((item) => item.summary)
    .map((item) => ({
      label: item.label,
      value: formatCapacitorBankControlValue(controlProfile.value, item),
    })),
)

const writeLogs = computed(() => controlLogs.value)

async function loadPage() {
  if (!deviceId.value) return
  loading.value = true
  loadError.value = ''
  try {
    const [overviewResponse, profileResponse] = await Promise.all([
      getDeviceMonitorOverview(deviceId.value),
      getCompensationCapacitorBankControlProfile(deviceId.value),
    ])
    overview.value = overviewResponse
    controlProfile.value = profileResponse
    const logs = await getDeviceMonitorControlLogs(deviceId.value, { limit: 10, hours: 168 })
    controlLogs.value = logs.items
    if (resolveCompensationSubtype(
      overviewResponse.archive?.device_type,
      overviewResponse.archive?.device_subtype,
    ) !== 'capacitor_bank_controller') {
      loadError.value = '当前设备不是电容补偿控制器，暂不支持进入控制台。'
    }
  } catch {
    loadError.value = '控制台数据加载失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

async function handleToggleDevice() {
  if (!deviceId.value || !canToggleRemotely.value) return
  const nextActive = !deviceActive.value
  const actionLabel = nextActive ? '启用' : '停用'
  try {
    await ElMessageBox.confirm(
      `确定要对 ${archive.value?.name || '当前设备'} 执行【${actionLabel}】指令吗？`,
      '远程控制确认',
      {
        confirmButtonText: `立即${actionLabel}`,
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
  } catch {
    return
  }

  toggleSubmitting.value = true
  try {
    await toggleDeviceStatus(deviceId.value, nextActive, `控制台${actionLabel}设备`)
    ElMessage.success(`已发送${actionLabel}指令`)
    await loadPage()
  } catch {
    ElMessage.error(`${actionLabel}指令发送失败，请稍后重试`)
  } finally {
    toggleSubmitting.value = false
  }
}

function openWriteDialog(parameterKey: string) {
  if (!canWriteParameters.value) {
    ElMessage.warning(writeDisabledReason.value || '当前暂不允许执行参数写入')
    return
  }
  const meta = getCapacitorBankEditableParameterMeta(parameterKey)
  if (!meta) {
    ElMessage.error('未找到对应参数配置')
    return
  }
  selectedParameterKey.value = parameterKey
  writeForm.value = {
    parameter_key: parameterKey,
    target_value: getCapacitorBankControlEditableValue(controlProfile.value, meta),
    reason: '',
  }
  writeDialogVisible.value = true
}

async function submitParameterWrite() {
  const meta = selectedWriteMeta.value
  if (!meta) return
  const normalizedTargetValue = normalizeWriteTargetValue(meta)
  if (normalizedTargetValue === null) return

  const previousValue = formatCapacitorBankControlValue(controlProfile.value, meta)
  const nextValueText = formatWriteTargetValue(meta, normalizedTargetValue)
  if (previousValue === nextValueText) {
    ElMessage.warning('目标值与当前快照一致，无需重复下发')
    return
  }

  try {
    await ElMessageBox.confirm(
      [
        `确定要写入参数【${meta.label}】吗？`,
        `当前值：${previousValue}`,
        `目标值：${nextValueText}`,
        '接口当前只表示 accepted 入队，不代表设备端已执行成功。',
      ].join('\n'),
      '参数写入确认',
      {
        confirmButtonText: '确认写入',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
  } catch {
    return
  }

  writeSubmitting.value = true
  try {
    const response = await writeCompensationCapacitorBankControlProfile(deviceId.value, {
      parameter_key: writeForm.value.parameter_key,
      target_value: normalizedTargetValue,
      reason: writeForm.value.reason.trim() || undefined,
    })
    ElMessage.success(response.message || '参数写入指令已入队')
    writeDialogVisible.value = false
    await loadPage()
  } catch (error) {
    ElMessage.error(extractErrorMessage(error, '参数写入失败，请稍后重试'))
  } finally {
    writeSubmitting.value = false
  }
}

function goMonitor() {
  router.push(`/devices/${deviceId.value}/monitor`)
}

function sourceStatusText(status?: string) {
  if (status === 'fresh') return '最新参数'
  if (status === 'stale') return '参数可能过期'
  if (status === 'empty') return '暂无参数'
  return '状态未知'
}

function formatDateTime(value?: string | null) {
  if (!value) return '暂无记录'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const pad = (num: number) => String(num).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

function formatWriteTargetValue(meta: NonNullable<typeof selectedWriteMeta.value>, value: string | number | boolean) {
  if (typeof value === 'boolean') {
    return value ? '开启' : '关闭'
  }
  return meta.unit ? `${value} ${meta.unit}` : String(value)
}

function normalizeWriteTargetValue(meta: NonNullable<typeof selectedWriteMeta.value>) {
  const value = writeForm.value.target_value
  if (meta.inputKind === 'boolean') {
    if (typeof value !== 'boolean') {
      ElMessage.warning(`请确认 ${meta.label} 的开关状态`)
      return null
    }
    return value
  }
  if (typeof value === 'string') {
    const trimmed = value.trim()
    if (!trimmed) {
      ElMessage.warning(`请填写 ${meta.label}`)
      return null
    }
    return trimmed
  }
  if (typeof value !== 'number' || Number.isNaN(value)) {
    ElMessage.warning(`请填写有效的 ${meta.label}`)
    return null
  }
  return value
}

function resolveLogTitle(log: DeviceControlLog) {
  if (log.action === 'start') return '启用设备'
  if (log.action === 'stop') return '停用设备'
  if (log.action.startsWith('write:')) {
    const meta = getCapacitorBankControlParameterMeta(log.action.slice(6))
    return meta ? `参数写入 · ${meta.label}` : `参数写入 · ${log.action.slice(6)}`
  }
  return log.action
}

function resolveLogTagType(log: DeviceControlLog) {
  if (log.result === 'success') return 'success'
  if (log.result === 'accepted') return 'warning'
  if (log.result === 'failed' || log.result === 'error') return 'danger'
  return 'info'
}

function extractErrorMessage(error: unknown, fallback: string) {
  if (
    typeof error === 'object'
    && error
    && 'response' in error
    && typeof error.response === 'object'
    && error.response
    && 'data' in error.response
  ) {
    const responseData = error.response.data as { detail?: string; message?: string }
    if (typeof responseData.detail === 'string' && responseData.detail) return responseData.detail
    if (typeof responseData.message === 'string' && responseData.message) return responseData.message
  }
  if (error instanceof Error && error.message) return error.message
  return fallback
}

watch(() => route.params.id, () => {
  void loadPage()
})

onMounted(() => {
  void loadPage()
})
</script>

<template>
  <div
    v-loading="loading"
    class="console-page"
  >
    <div class="console-head">
      <div class="console-head__left">
        <el-button
          :icon="ArrowLeft"
          text
          @click="router.push('/devices')"
        >
          返回设备台账
        </el-button>
        <div>
          <h2>{{ archive?.name || '补偿控制台' }}</h2>
          <p>{{ archive?.sn || '--' }} · {{ archive?.location || '未配置安装位置' }}</p>
        </div>
      </div>
      <div class="console-head__actions">
        <el-button
          :icon="Monitor"
          @click="goMonitor"
        >
          前往监控页
        </el-button>
        <el-button
          :icon="Refresh"
          @click="loadPage"
        >
          刷新
        </el-button>
      </div>
    </div>

    <div
      v-if="loadError"
      class="console-alert"
    >
      <strong>控制台暂不可用</strong>
      <span>{{ loadError }}</span>
    </div>

    <template v-else-if="isCapacitorBankController">
      <section class="console-panel">
        <div class="console-panel__head">
          <h3>设备概览</h3>
          <span>确认设备身份、在线状态与最新通讯情况后再进行控制或参数核对。</span>
        </div>
        <div class="overview-grid">
          <div
            v-for="item in overviewItems"
            :key="item.label"
            class="overview-card"
          >
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </div>
        </div>
      </section>

      <section class="console-panel">
        <div class="console-panel__head">
          <h3>远程控制</h3>
          <span>{{ controlCapabilities?.remote_control_status_message || '远程控制链路尚未接入。' }}</span>
        </div>
        <div class="remote-actions">
          <button
            v-for="card in actionCards"
            :key="card.title"
            class="remote-card"
            :class="{ 'remote-card--enabled': card.enabled }"
            type="button"
            :disabled="!card.enabled || toggleSubmitting"
            @click="card.handler?.()"
          >
            <component :is="card.icon" class="remote-card__icon" />
            <strong>{{ card.title }}</strong>
            <span>{{ card.hint }}</span>
            <em>{{ card.actionLabel }}</em>
          </button>
        </div>
        <div class="capability-note">
          <el-tag
            :type="controlCapabilities?.supports_remote_control ? 'success' : 'info'"
            effect="dark"
          >
            {{ controlCapabilities?.supports_remote_control ? '已开通远程控制' : '远程控制待开通' }}
          </el-tag>
          <small>
            当前账号控制权限：{{ canControlDevices ? '具备设备控制权限' : '无设备控制权限' }}
            · 最近结果：{{ latestControlLog ? `${latestControlLog.action} / ${latestControlLog.result || 'success'} / ${formatDateTime(latestControlLog.created_at)}` : '暂无记录' }}
          </small>
        </div>
      </section>

      <section class="console-panel">
        <div class="console-panel__head">
          <h3>参数管理</h3>
          <span>{{ controlCapabilities?.write_status_message || '当前仅开放只读参数展示。' }}</span>
        </div>
        <div class="summary-strip">
          <div
            v-for="item in summaryItems"
            :key="item.label"
            class="summary-chip"
          >
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </div>
        </div>
        <div class="capability-note">
          <el-tag
            :type="controlProfile?.source_status === 'fresh' ? 'success' : controlProfile?.source_status === 'stale' ? 'warning' : 'info'"
            effect="dark"
          >
            {{ sourceStatusText(controlProfile?.source_status) }}
          </el-tag>
          <small>
            来源：{{ controlProfile?.source || '未上报' }}
            · 快照时间：{{ formatDateTime(controlProfile?.snapshot_timestamp || controlProfile?.updated_at) }}
          </small>
        </div>

        <div class="param-groups">
          <section
            v-for="group in groupedParameters"
            :key="group.key"
            class="param-group"
          >
            <header class="param-group__head">
              <h4>{{ group.label }}</h4>
              <span>协议参数只读快照</span>
            </header>
            <div class="param-table">
              <div class="param-table__row param-table__row--head">
                <span>参数</span>
                <span>当前值</span>
                <span>寄存器</span>
                <span>读写属性</span>
                <span>最后更新时间</span>
              </div>
              <div
                v-for="item in group.items"
                :key="item.key"
                class="param-table__row"
              >
                <div>
                  <strong>{{ item.label }}</strong>
                  <small>{{ item.description }}</small>
                </div>
                <span>{{ formatCapacitorBankControlValue(controlProfile, item) }}</span>
                <span>{{ item.register }}</span>
                <span>{{ item.readWrite }}</span>
                <span>{{ formatDateTime(controlProfile?.snapshot_timestamp || controlProfile?.updated_at) }}</span>
              </div>
            </div>
          </section>
        </div>
        <div class="capability-note">
          <el-tag
            :type="controlCapabilities?.supports_write ? 'success' : 'info'"
            effect="dark"
          >
            {{ controlCapabilities?.supports_write ? '支持参数写入' : '参数写入待开通' }}
          </el-tag>
          <small>当前账号参数权限：{{ isAdmin ? '管理员，可发起受控写入' : canManageDevices ? '可查看档案，不可写入' : '仅查看' }}</small>
        </div>

        <div class="write-panel">
          <div class="write-panel__head">
            <div>
              <strong>受控写入入口</strong>
              <span>仅开放低风险参数，提交前需二次确认；设备端结果仍需等待回读或回执核对。</span>
            </div>
            <el-tag
              :type="canWriteParameters ? 'success' : 'warning'"
              effect="dark"
            >
              {{ canWriteParameters ? '当前允许写入' : '当前禁止写入' }}
            </el-tag>
          </div>
          <div
            v-if="writeDisabledReason"
            class="console-inline-alert"
          >
            <strong>写入入口已锁定</strong>
            <span>{{ writeDisabledReason }}</span>
          </div>
          <div class="editable-grid">
            <button
              v-for="item in editableParameterCards"
              :key="item.key"
              class="editable-card"
              type="button"
              :disabled="!canWriteParameters"
              @click="openWriteDialog(String(item.key))"
            >
              <span>{{ item.label }}</span>
              <strong>{{ item.currentValue }}</strong>
              <small>{{ item.description }}</small>
              <em>{{ canWriteParameters ? '修改参数' : '当前不可写入' }}</em>
            </button>
          </div>
        </div>
      </section>

      <section class="console-panel">
        <div class="console-panel__head">
          <h3>写入日志 / 结果</h3>
          <span>当前展示最近控制记录；参数下发开通后也会复用同一区域追踪结果。</span>
        </div>
        <div
          v-if="!writeLogs.length"
          class="empty-box"
        >
          <strong>暂无写入日志</strong>
          <span>当前还没有控制记录，可先尝试启用/停用设备验证远程控制链路。</span>
        </div>
        <div
          v-else
          class="log-list"
        >
          <div
            v-for="log in writeLogs"
            :key="log.id"
            class="log-row"
          >
            <div>
              <strong>{{ resolveLogTitle(log) }}</strong>
              <span>{{ formatDateTime(log.created_at) }} · {{ log.operator || '未知操作人' }}</span>
              <small v-if="log.reason">{{ log.reason }}</small>
            </div>
            <div class="log-meta">
              <el-tag :type="resolveLogTagType(log)" effect="dark">
                {{ log.result || 'success' }}
              </el-tag>
              <small>{{ log.command_source || 'api' }}</small>
            </div>
          </div>
        </div>
      </section>
    </template>

    <el-dialog
      v-model="writeDialogVisible"
      width="560px"
      :close-on-click-modal="false"
      title="参数写入"
    >
      <template v-if="selectedWriteMeta">
        <div class="dialog-intro">
          <strong>{{ selectedWriteMeta.label }}</strong>
          <span>{{ selectedWriteMeta.description }}</span>
        </div>
        <div class="dialog-current">
          <span>当前快照值</span>
          <strong>{{ formatCapacitorBankControlValue(controlProfile, selectedWriteMeta) }}</strong>
        </div>
        <el-form label-position="top">
          <el-form-item label="目标值">
            <el-switch
              v-if="selectedWriteMeta.inputKind === 'boolean'"
              v-model="writeForm.target_value"
              inline-prompt
              active-text="开启"
              inactive-text="关闭"
            />
            <el-input-number
              v-else
              v-model="writeForm.target_value"
              :min="selectedWriteMeta.min"
              :max="selectedWriteMeta.max"
              :step="selectedWriteMeta.step || 1"
              :precision="selectedWriteMeta.step && selectedWriteMeta.step < 1 ? 2 : 0"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="写入说明（选填）">
            <el-input
              v-model="writeForm.reason"
              type="textarea"
              :rows="3"
              maxlength="120"
              show-word-limit
              placeholder="例如：联调验证 / 现场调优 / 告警阈值收敛"
            />
          </el-form-item>
        </el-form>
        <div class="console-inline-alert console-inline-alert--soft">
          <strong>风险提示</strong>
          <span>接口当前仅表示 accepted 入队；提交后请结合设备回读、控制日志与现场反馈确认实际执行结果。</span>
        </div>
      </template>
      <template #footer>
        <div class="dialog-actions">
          <el-button @click="writeDialogVisible = false">取消</el-button>
          <el-button
            type="warning"
            :loading="writeSubmitting"
            @click="submitParameterWrite"
          >
            确认写入
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.console-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  color: #dbe5f4;
}

.console-head,
.console-panel,
.console-alert {
  border-radius: 18px;
  border: 1px solid rgba(52, 72, 99, 0.88);
  background: linear-gradient(180deg, rgba(18, 31, 49, 0.98), rgba(11, 21, 35, 0.98));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
}

.console-head {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: center;
  padding: 18px 20px;
}

.console-head__left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.console-head__left h2 {
  margin: 0;
  font-size: 22px;
  color: #f7fbff;
}

.console-head__left p {
  margin: 6px 0 0;
  color: #8ea5c1;
  font-size: 13px;
}

.console-head__actions {
  display: flex;
  gap: 12px;
}

.console-alert,
.console-panel {
  padding: 18px 20px;
}

.console-alert {
  display: flex;
  flex-direction: column;
  gap: 6px;
  border-color: rgba(196, 88, 88, 0.55);
}

.console-alert strong {
  color: #ffd5d5;
}

.console-alert span {
  color: #ffb4b4;
  font-size: 13px;
}

.console-panel__head {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.console-panel__head h3,
.param-group__head h4 {
  margin: 0;
  color: #f3f7fb;
}

.console-panel__head span,
.param-group__head span {
  color: #8ca0ba;
  font-size: 12px;
  line-height: 1.5;
}

.overview-grid,
.summary-strip,
.remote-actions {
  display: grid;
  gap: 14px;
}

.overview-grid {
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
}

.overview-card,
.summary-chip,
.remote-card {
  border-radius: 14px;
  border: 1px solid rgba(48, 70, 95, 0.82);
  background: rgba(19, 34, 53, 0.88);
}

.overview-card,
.summary-chip {
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.overview-card span,
.summary-chip span {
  color: #91a5c2;
  font-size: 12px;
}

.overview-card strong,
.summary-chip strong {
  color: #f7fbff;
  line-height: 1.5;
}

.remote-actions {
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.remote-card {
  min-height: 128px;
  padding: 16px;
  text-align: left;
  color: #a7b7cb;
  cursor: not-allowed;
  opacity: 0.72;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.remote-card--enabled {
  cursor: pointer;
  opacity: 1;
  border-color: rgba(245, 158, 11, 0.48);
  box-shadow: inset 0 0 0 1px rgba(245, 158, 11, 0.1);
}

.remote-card__icon {
  width: 18px;
  height: 18px;
}

.remote-card strong {
  color: #e8f0fb;
}

.remote-card span {
  font-size: 12px;
  line-height: 1.6;
}

.remote-card em {
  margin-top: auto;
  font-style: normal;
  color: #fbbf24;
  font-size: 12px;
}

.capability-note {
  margin-top: 14px;
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.capability-note small {
  color: #8ca0ba;
}

.write-panel {
  margin-top: 18px;
  padding: 16px;
  border-radius: 14px;
  border: 1px solid rgba(58, 78, 104, 0.82);
  background: rgba(16, 28, 45, 0.76);
}

.write-panel__head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.write-panel__head strong {
  display: block;
  color: #f3f7fb;
}

.write-panel__head span {
  display: block;
  margin-top: 6px;
  color: #8ca0ba;
  font-size: 12px;
  line-height: 1.6;
}

.console-inline-alert {
  margin-top: 14px;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid rgba(170, 122, 36, 0.42);
  background: rgba(73, 48, 14, 0.24);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.console-inline-alert strong {
  color: #fcd34d;
}

.console-inline-alert span {
  color: #d8c08a;
  font-size: 12px;
  line-height: 1.6;
}

.console-inline-alert--soft {
  margin-top: 0;
}

.editable-grid {
  margin-top: 14px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}

.editable-card {
  padding: 14px;
  border-radius: 14px;
  border: 1px solid rgba(48, 70, 95, 0.82);
  background: rgba(19, 34, 53, 0.88);
  color: #dbe5f4;
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 8px;
  cursor: pointer;
}

.editable-card:disabled {
  cursor: not-allowed;
  opacity: 0.68;
}

.editable-card span {
  color: #91a5c2;
  font-size: 12px;
}

.editable-card strong {
  color: #f8fbff;
}

.editable-card small {
  color: #87a0bc;
  line-height: 1.5;
}

.editable-card em {
  margin-top: auto;
  font-style: normal;
  color: #fbbf24;
  font-size: 12px;
}

.param-groups {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 14px;
}

.param-group {
  border: 1px solid rgba(44, 65, 89, 0.78);
  border-radius: 14px;
  background: rgba(14, 26, 42, 0.8);
  overflow: hidden;
}

.param-group__head {
  padding: 14px 16px;
  border-bottom: 1px solid rgba(44, 65, 89, 0.78);
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.param-table {
  display: flex;
  flex-direction: column;
}

.param-table__row {
  display: grid;
  grid-template-columns: minmax(220px, 2fr) minmax(120px, 1.2fr) 100px 100px 180px;
  gap: 12px;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(33, 52, 74, 0.78);
  align-items: center;
}

.param-table__row:last-child {
  border-bottom: none;
}

.param-table__row--head {
  background: rgba(22, 39, 60, 0.95);
  color: #8ca0ba;
  font-size: 12px;
}

.param-table__row div {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.param-table__row strong {
  color: #eef5ff;
}

.param-table__row small {
  color: #87a0bc;
  line-height: 1.5;
}

.param-table__row > span {
  color: #dbe5f4;
  line-height: 1.5;
}

.empty-box {
  min-height: 120px;
  border-radius: 14px;
  border: 1px dashed rgba(70, 91, 117, 0.72);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 8px;
  color: #90a4c2;
  text-align: center;
  padding: 12px;
}

.empty-box strong {
  color: #f3f7fb;
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.log-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(19, 34, 53, 0.88);
  border: 1px solid rgba(48, 70, 95, 0.82);
}

.log-row strong {
  color: #eef5ff;
}

.log-row span,
.log-row small,
.log-meta small {
  display: block;
  margin-top: 4px;
  color: #8ca0ba;
  font-size: 12px;
}

.log-meta {
  text-align: right;
}

.dialog-intro,
.dialog-current {
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid rgba(48, 70, 95, 0.82);
  background: rgba(19, 34, 53, 0.88);
  margin-bottom: 14px;
}

.dialog-intro strong,
.dialog-current strong {
  display: block;
  color: #eef5ff;
}

.dialog-intro span,
.dialog-current span {
  display: block;
  margin-top: 6px;
  color: #8ca0ba;
  font-size: 12px;
  line-height: 1.6;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 1100px) {
  .console-head,
  .console-panel__head,
  .capability-note,
  .write-panel__head {
    flex-direction: column;
    align-items: flex-start;
  }

  .param-table__row,
  .param-table__row--head {
    grid-template-columns: 1fr;
  }
}
</style>
