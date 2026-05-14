<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/useAuthStore'
import { useAlarmPolling } from '@/features/alarm/composables/useAlarmPolling'
import { useDashboardClock } from '@/features/dashboard/composables/useDashboardClock'
import { useDashboardOverview } from '@/features/dashboard/composables/useDashboardOverview'
import { resolveAlarm, type Alarm } from '@/api/alarm'
import type { DeviceIngestionHealthItem } from '@/api/deviceMonitor'

import DashboardStatusBar from '@/features/dashboard/components/DashboardStatusBar.vue'
import CriticalAlertBanner from '@/features/dashboard/components/CriticalAlertBanner.vue'
import KpiStrip, { type KpiItem } from '@/features/dashboard/components/KpiStrip.vue'
import StackedTrend, { type TrendSeries } from '@/features/dashboard/components/StackedTrend.vue'
import AlertTrack, { type AlertItem, type AlertSeverity } from '@/features/dashboard/components/AlertTrack.vue'
import DeviceMatrix, { type MatrixGroup, type MatrixStatus } from '@/features/dashboard/components/DeviceMatrix.vue'
import EnergyMixDonut, { type MixItem } from '@/features/dashboard/components/EnergyMixDonut.vue'
import Ranking, { type RankItem } from '@/features/dashboard/components/Ranking.vue'

const authStore = useAuthStore()
const { currentTime, currentDate } = useDashboardClock()
const { alarmList, fetchAlarms } = useAlarmPolling({ interval: 10000 })
const {
  overview,
  previousOverview,
  ingestionByDevice,
  perMediumTrend,
  rankings,
  prevRankingMap,
  deviceList,
  pvCurrentPower,
  storageSOC,
  samplingOnline,
  samplingTotal,
} = useDashboardOverview()

// session-scoped UI state
const bannerDismissedId = ref<number | string | null>(null)
const mutedIds = ref<Set<number | string>>(new Set())

// ----- date / status bar -----
const dateLine = computed(() => {
  const date = new Date()
  const pad = (n: number) => `${n}`.padStart(2, '0')
  const week = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][date.getDay()]
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${week}`
})

function resolveShiftLabel(time: string) {
  const hour = Number(time.split(':')[0] || NaN)
  if (!Number.isFinite(hour)) return '白天时段'
  if (hour >= 8 && hour < 14) return '白班 08:00-14:00'
  if (hour >= 14 && hour < 22) return '白班 14:00-22:00'
  return '夜班 22:00-08:00'
}

const shiftLabel = computed(() => resolveShiftLabel(currentTime.value))
const operatorName = computed(() => authStore.username || '运维')

const parkName = computed(() => {
  const scope = (authStore.locationScope || '').trim()
  if (scope) return scope
  return overview.value?.campus_entities?.[0]?.name || '园区'
})

// ----- alarms -----
function severityOf(s?: string): AlertSeverity {
  if (s === 'critical') return 'crit'
  if (s === 'warning') return 'warn'
  return 'info'
}

function alarmTimeAgo(timestamp: string) {
  const diffMin = Math.max(0, Math.round((Date.now() - new Date(timestamp).getTime()) / 60000))
  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin} 分钟前`
  const diffHr = Math.round(diffMin / 60)
  if (diffHr < 24) return `${diffHr} 小时前`
  return new Date(timestamp).toLocaleString('zh-CN', { hour12: false })
}

const topCritical = computed<Alarm | null>(() => {
  return alarmList.value.find((a) => !a.is_resolved && a.severity === 'critical') || null
})

const showBanner = computed(() => {
  const top = topCritical.value
  if (!top) return false
  if (bannerDismissedId.value === top.id) return false
  if (mutedIds.value.has(top.id)) return false
  return true
})

const pinnedAlarmId = computed(() => (showBanner.value ? topCritical.value?.id ?? null : null))

const recentAlerts = computed<AlertItem[]>(() => (
  alarmList.value.slice(0, 6).map((a) => ({
    id: a.id,
    sev: severityOf(a.severity),
    title: a.message,
    detail: a.handling_note || undefined,
    loc: a.source || undefined,
    time: alarmTimeAgo(a.timestamp),
    ack: a.is_resolved,
  }))
))

async function onBannerHandle() {
  const top = topCritical.value
  if (!top) return
  try {
    await resolveAlarm(top.id, '从首页确认处理')
    ElMessage.success('已确认处理')
    await fetchAlarms()
  } catch {
    ElMessage.error('处理失败，请重试')
  }
}

function onBannerMute() {
  const top = topCritical.value
  if (!top) return
  mutedIds.value.add(top.id)
  ElMessage.info('已暂时静音')
}

// ----- KPIs -----
function abbreviate(value: number) {
  if (value >= 10000) return value.toLocaleString(undefined, { maximumFractionDigits: 0 })
  if (value >= 1000) return value.toFixed(0)
  return value.toFixed(1)
}

function pctDelta(current: number, previous: number): { dir: 'up' | 'down'; pct: string } | null {
  if (!Number.isFinite(previous) || previous === 0) return null
  const delta = ((current - previous) / Math.abs(previous)) * 100
  if (!Number.isFinite(delta)) return null
  return { dir: delta >= 0 ? 'up' : 'down', pct: `${Math.abs(delta).toFixed(1)}%` }
}

const analysis = computed(() => overview.value?.analysis_summary)
const prevAnalysis = computed(() => previousOverview.value?.analysis_summary)
const alarmSeverityCounts = computed(() => {
  const m = overview.value?.alarm_summary?.by_severity || {}
  return {
    critical: Number(m.critical || 0),
    warning: Number(m.warning || 0),
    info: Number(m.info || 0),
  }
})

const kpiItems = computed<KpiItem[]>(() => {
  const a = analysis.value
  const prev = prevAnalysis.value
  const sev = alarmSeverityCounts.value
  const totalAlarms = sev.critical + sev.warning + sev.info

  const loadDelta = a && prev ? pctDelta(a.realtime_load, prev.realtime_load) : null
  const energyDelta = a && prev ? pctDelta(a.total_consumption, prev.total_consumption) : null
  const carbonDelta = a && prev ? pctDelta(a.estimated_carbon, prev.estimated_carbon) : null

  const items: KpiItem[] = [
    {
      label: '实时总负荷',
      value: a ? abbreviate(a.realtime_load) : '—',
      unit: 'kW',
      delta: loadDelta?.pct,
      deltaDir: loadDelta?.dir,
      sub: loadDelta ? 'vs 昨日同时段' : undefined,
      status: 'ok',
    },
    {
      label: '今日累计能耗',
      value: a ? abbreviate(a.total_consumption) : '—',
      unit: 'kWh',
      delta: energyDelta?.pct,
      deltaDir: energyDelta?.dir,
      sub: energyDelta ? 'vs 昨日' : undefined,
      status: 'ok',
    },
    {
      label: '光伏发电',
      value: pvCurrentPower.value != null ? abbreviate(pvCurrentPower.value) : '未配置',
      unit: pvCurrentPower.value != null ? 'kW' : '',
      sub: pvCurrentPower.value != null ? '当前出力' : '暂无光伏设备',
      status: 'ok',
    },
    {
      label: '储能 SOC',
      value: storageSOC.value != null ? storageSOC.value.toFixed(0) : '未配置',
      unit: storageSOC.value != null ? '%' : '',
      sub: storageSOC.value != null ? '平均荷电状态' : '暂无储能设备',
      status: storageSOC.value != null && storageSOC.value < 30 ? 'notice' : 'ok',
    },
    {
      label: '近 24h 告警',
      value: String(totalAlarms),
      unit: '条',
      delta: `${sev.critical} 严重 · ${sev.warning} 警告`,
      deltaDir: 'up',
      sub: `${sev.info} 提示`,
      status: sev.critical > 0 ? 'err' : (sev.warning > 0 ? 'warn' : 'ok'),
    },
    {
      label: '碳排放',
      value: a ? (a.estimated_carbon / 1000).toFixed(2) : '—',
      unit: 'tCO₂',
      delta: carbonDelta?.pct,
      deltaDir: carbonDelta?.dir,
      sub: carbonDelta ? '环比昨日' : undefined,
      status: 'ok',
    },
  ]
  return items
})

// ----- StackedTrend -----
const MEDIUM_META: Record<string, { name: string; color: string }> = {
  electricity: { name: '电', color: 'var(--m-elec)' },
  cooling: { name: '冷', color: 'var(--m-cool)' },
  heat: { name: '热', color: 'var(--m-heat)' },
  water: { name: '水', color: 'var(--m-water)' },
  gas: { name: '气', color: 'var(--m-gas)' },
}

const trendSeries = computed<TrendSeries[]>(() => {
  const order = ['electricity', 'cooling', 'heat', 'water', 'gas']
  return order
    .map((key) => {
      const points = perMediumTrend.value[key] || []
      const meta = MEDIUM_META[key]
      return {
        key,
        name: meta.name,
        color: meta.color,
        data: points.map((p) => Math.max(0, p.v)),
        unit: 'kW',
      } as TrendSeries
    })
    .filter((s) => s.data.length > 0)
})

// ----- DeviceMatrix -----
function deviceStatusFromHealth(deviceId: number, isActive: boolean): MatrixStatus {
  if (!isActive) return 'off'
  const health = ingestionByDevice.value[deviceId]
  if (!health) return 'on'
  if (health.status === 'degraded') return 'notice'
  if (health.status === 'offline') return 'off'
  return 'on'
}

const matrixGroups = computed<MatrixGroup[]>(() => {
  type GroupDef = { key: string; name: string; color: string; match: (d: Device) => boolean }
  type Device = typeof deviceList.value[number]
  const defs: GroupDef[] = [
    { key: 'elec', name: '电', color: 'var(--m-elec)', match: (d) => d.energy_type === 'electricity' && d.device_type !== 'storage' && d.device_type !== 'pv' },
    { key: 'pv-storage', name: '光储', color: 'var(--notice)', match: (d) => d.device_type === 'pv' || d.device_type === 'storage' || /光伏|储能|PV/i.test(d.name || '') },
    { key: 'cool-heat', name: '冷热', color: 'var(--m-cool)', match: (d) => d.energy_type === 'cooling' || d.energy_type === 'heat' },
    { key: 'water-gas', name: '水气', color: 'var(--m-water)', match: (d) => d.energy_type === 'water' || d.energy_type === 'gas' },
  ]
  return defs.map((g) => ({
    name: g.name,
    color: g.color,
    items: deviceList.value
      .filter(g.match)
      .slice(0, 6)
      .map((d) => {
        const status = deviceStatusFromHealth(d.id!, !!d.is_active)
        const health = ingestionByDevice.value[d.id!]
        const reason = status === 'notice'
          ? `采集状态降级 · 上次成功 ${health?.last_success_at ?? '—'}`
          : status === 'off'
            ? '设备已停机 / 离线 · 等待确认'
            : null
        return {
          n: d.name || `#${d.id}`,
          s: status,
          v: '—',
          u: d.unit || '',
          reason,
        }
      }),
  }))
})

const matrixLegend = computed(() => {
  let ok = 0, notice = 0, warn = 0, off = 0
  for (const d of deviceList.value) {
    const s = deviceStatusFromHealth(d.id!, !!d.is_active)
    if (s === 'on') ok += 1
    else if (s === 'notice') notice += 1
    else if (s === 'warn') warn += 1
    else off += 1
  }
  return { ok, notice, warn, off }
})

// ----- EnergyMixDonut -----
const ENERGY_CATEGORY_META: Record<string, { name: string; color: string }> = {
  electricity: { name: '电', color: 'var(--m-elec)' },
  cooling: { name: '冷', color: 'var(--m-cool)' },
  heat: { name: '热', color: 'var(--m-heat)' },
  gas: { name: '气', color: 'var(--m-gas)' },
  water: { name: '水', color: 'var(--m-water)' },
}

const energyMix = computed<MixItem[]>(() => {
  const categories = overview.value?.energy_category_summary || []
  if (categories.length === 0) return []
  const total = categories.reduce((sum, c) => sum + (c.total_consumption || 0), 0)
  return categories.map((c) => {
    const meta = ENERGY_CATEGORY_META[c.energy_category]
    return {
      name: meta?.name || c.label || c.energy_category,
      color: meta?.color || 'var(--accent)',
      kwh: c.total_consumption || 0,
      value: total > 0 ? (c.total_consumption / total) * 100 : (c.ratio || 0) * 100,
    }
  })
})

const totalKwhToday = computed(() => energyMix.value.reduce((a, b) => a + b.kwh, 0))

const energyDeltaPct = computed<number | undefined>(() => {
  const a = analysis.value
  const prev = prevAnalysis.value
  if (!a || !prev || !Number.isFinite(prev.total_consumption) || prev.total_consumption === 0) return undefined
  return ((a.total_consumption - prev.total_consumption) / prev.total_consumption) * 100
})

// ----- Ranking -----
const rankingItems = computed<RankItem[]>(() => {
  return rankings.value.slice(0, 6).map((r) => {
    const prev = prevRankingMap.value[r.location_id] || 0
    const delta = prev > 0 ? ((r.total_consumption - prev) / prev) * 100 : 0
    return {
      name: r.name,
      value: Math.round(r.total_consumption),
      deltaPct: Number.isFinite(delta) ? delta : 0,
    }
  })
})
</script>

<template>
  <div class="ems-cockpit-v2">
    <DashboardStatusBar
      :park="parkName"
      :operator="operatorName"
      :shift="shiftLabel"
      :sampling-online="samplingOnline"
      :sampling-total="samplingTotal"
      :time="currentTime"
      :date="dateLine"
    />

    <CriticalAlertBanner
      v-if="showBanner && topCritical"
      :title="topCritical.message"
      :location="topCritical.source"
      :started-at="alarmTimeAgo(topCritical.timestamp)"
      @dismiss="bannerDismissedId = topCritical!.id"
      @handle="onBannerHandle"
      @mute="onBannerMute"
    >
      {{ topCritical.message }}
    </CriticalAlertBanner>

    <KpiStrip :items="kpiItems" />

    <main class="main">
      <section class="col-main">
        <div class="card trend-card">
          <StackedTrend
            :series="trendSeries"
            :subtitle="`${currentDate} · ${trendSeries[0]?.data.length || 0} 点 · 1h`"
          />
        </div>
        <div class="row-pair">
          <DeviceMatrix :groups="matrixGroups" :legend="matrixLegend" />
          <EnergyMixDonut
            :items="energyMix"
            :total-kwh="totalKwhToday"
            :delta-pct="energyDeltaPct"
          />
        </div>
      </section>
      <aside class="col-side">
        <AlertTrack
          :alerts="recentAlerts"
          :pinned-id="pinnedAlarmId"
          :total-count="alarmList.length"
        />
        <Ranking :items="rankingItems" :is-sample="false" />
      </aside>
    </main>
  </div>
</template>

<style scoped>
.ems-cockpit-v2 {
  width: 100%;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  box-sizing: border-box;
  overflow-y: auto;
  overflow-x: hidden;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif;
}

.main {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 12px;
}
.col-main { display: flex; flex-direction: column; gap: 12px; min-width: 0; }
.col-side { display: flex; flex-direction: column; gap: 12px; min-width: 0; }
.row-pair { display: flex; gap: 12px; flex: 1; min-height: 0; }
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px;
  box-sizing: border-box;
}
.trend-card { flex: 0 0 auto; }
</style>
