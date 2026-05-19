# 补偿控制器运行监视模块重设计 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把电容补偿控制器「运行监视」工作台标签页重做成设计稿的 at-a-glance 监控视角 —— 新增 PF 趋势 / P-Q 象限 / 设备健康度三大可视化、电容器组拓扑、三相状态矩阵，并把右侧栏换成未处理告警 + 控制参数摘要。

**Architecture:** 新建 `components/compensation/runtime/` 子目录，放一组聚焦组件，由容器 `CompensationRuntimeBoard.vue` 组合。`CompensationMonitorView.vue` 的 `runtime` 分支换用容器组件；其它三个标签页和非工作台分支保持不变。新增的派生数据（健康度模型、P-Q 点/轨迹）在 `viewMapping.ts` 与 `useCompensationMonitor.ts` 计算，不改动网络请求。所有可视化基于真实遥测，数据缺失时优雅降级（不使用 mock）。

**Tech Stack:** Vue 3 `<script setup>` + TypeScript、Vitest + `@vue/test-utils`、内联 SVG 图表（无新依赖）、Element Plus（仅 `el-select` 等已有用法）。

设计稿来源（实施时可参考，路径在本机临时目录）：`/tmp/design_extract/screen/project/` 下 `panels.jsx`、`charts.jsx`、`app.jsx`、`styles.css`。本计划已内联所有需要的代码，无需依赖该目录。

参考规格：`docs/superpowers/specs/2026-05-19-compensation-runtime-monitor-redesign-design.md`

---

## File Structure

新建（全部在 `frontend/src/features/device-monitor/components/compensation/runtime/`）：

- `CompensationRuntimeBoard.vue` — 运行监视主区容器，组合 Hero 行 / 拓扑行 / 底部行，并持有回路抽屉选中态。
- `CompensationPfTrendCard.vue` — 功率因数大数 + 目标带 sparkline + P/Q/S 统计。
- `CompensationPqQuadrantCard.vue` — P-Q 四象限运行图。
- `CompensationHealthCard.vue` — 设备健康度评分 + 6 维条形图。
- `CompensationBankTopology.vue` — 电容器组拓扑（6 条母线 + 回路色块）。
- `CompensationPhaseMatrix.vue` — 三相状态矩阵表。
- `CompensationCircuitDrawer.vue` — 单回路详情右滑抽屉。
- `CompensationAlarmRail.vue` — 侧栏未处理告警列表。
- `CompensationParamSummary.vue` — 侧栏控制参数摘要。
- `__tests__/` — 上述组件的单元测试。

修改：

- `components/compensation/types.ts` — 新增健康度与 P-Q 相关类型。
- `components/compensation/viewMapping.ts` — 新增 `buildCompensationHealthModel`。
- `composables/useCompensationMonitor.ts` — 新增 `compensationHealthModel` / `compensationPqPoint` / `compensationPqHistory` computed 并导出。
- `views/CompensationMonitorView.vue` — `runtime` 分支换 `CompensationRuntimeBoard`；`#side` 槽对 runtime 标签条件化渲染新侧栏。
- `views/__tests__/CompensationMonitorView.test.ts`（若存在则更新 runtime 分支断言；不存在则跳过）。
- `components/compensation/__tests__/viewMapping.test.ts` — 新增健康度用例。
- `composables/__tests__/useCompensationMonitor.test.ts` — 新增 P-Q / 健康度用例。

---

## Task 1: 新增类型定义

**Files:**
- Modify: `frontend/src/features/device-monitor/components/compensation/types.ts`（文件末尾追加）

- [ ] **Step 1: 在 types.ts 末尾追加类型**

在 `frontend/src/features/device-monitor/components/compensation/types.ts` 文件末尾追加：

```typescript

/* ───── 运行监视重设计：健康度 / P-Q / 拓扑 ───── */

export type CompensationHealthDimensionKey =
  | 'comm'
  | 'voltageHarmonic'
  | 'currentHarmonic'
  | 'switching'
  | 'temperature'
  | 'voltageStability'

export interface CompensationHealthDimension {
  key: CompensationHealthDimensionKey
  label: string
  /** 0–100；null 表示该维数据缺失，视图显示「待采集」且不计入总分。 */
  value: number | null
}

export interface CompensationHealthModel {
  /** 0–100；null 表示所有维度均缺数据。 */
  score: number | null
  rating: string
  ratingTone: CompensationTone
  breakdown: CompensationHealthDimension[]
}

export interface CompensationPqPoint {
  /** 有功功率 kW；null 表示缺测。 */
  p: number | null
  /** 无功功率 kVar；null 表示缺测。 */
  q: number | null
}

export type CompensationCircuitSlotState = 'on' | 'off' | 'unconfigured'

export interface CompensationCircuitPick {
  groupLabel: string
  phase: 'A' | 'B' | 'C' | 'COMMON'
  /** 公补组号（1–3），分相为 null。 */
  commonGroup: 1 | 2 | 3 | null
  /** 该回路在所属相/组内的 1-based 序号。 */
  index: number
  state: CompensationCircuitSlotState
  phaseAlarm: boolean
}
```

- [ ] **Step 2: 类型检查通过**

Run: `cd frontend && npx vue-tsc --noEmit -p tsconfig.app.json 2>&1 | head -20`
Expected: 无新增错误（输出为空或与改动前一致）。

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/device-monitor/components/compensation/types.ts
git commit -m "feat(compensation): add runtime monitor redesign types"
```

---

## Task 2: 健康度模型构建函数

**Files:**
- Modify: `frontend/src/features/device-monitor/components/compensation/viewMapping.ts`（文件末尾追加）
- Test: `frontend/src/features/device-monitor/components/compensation/__tests__/viewMapping.test.ts`（追加 describe 块）

- [ ] **Step 1: 写失败测试**

在 `viewMapping.test.ts` 文件末尾追加（顶部 import 处确保引入 `buildCompensationHealthModel`，若 import 是聚合 `from '../viewMapping'` 则把名字加入）：

```typescript
import { buildCompensationHealthModel } from '../viewMapping'

describe('buildCompensationHealthModel', () => {
  it('健康设备：所有维度有数据，给出高分与良好评级', () => {
    const model = buildCompensationHealthModel({
      ingestionStatus: 'online',
      isRealtimeFresh: true,
      voltageThd: [1.2, 1.4, 1.1],
      currentThd: [2.0, 1.8, 2.2],
      temperature: 38,
      voltage: 221,
      switchingFlags: [false, false, false, false, false, false],
    })
    expect(model.score).not.toBeNull()
    expect(model.score as number).toBeGreaterThan(80)
    expect(model.breakdown).toHaveLength(6)
    expect(model.breakdown.every((d) => d.value !== null)).toBe(true)
    expect(model.rating).toBe('优秀')
  })

  it('缺测维度记为 null 且不计入总分', () => {
    const model = buildCompensationHealthModel({
      ingestionStatus: 'online',
      isRealtimeFresh: true,
      voltageThd: [null, null, null],
      currentThd: [2.0, null, null],
      temperature: null,
      voltage: 221,
      switchingFlags: [null, null, null, null, null, null],
    })
    const vh = model.breakdown.find((d) => d.key === 'voltageHarmonic')
    const temp = model.breakdown.find((d) => d.key === 'temperature')
    const sw = model.breakdown.find((d) => d.key === 'switching')
    expect(vh?.value).toBeNull()
    expect(temp?.value).toBeNull()
    expect(sw?.value).toBeNull()
    expect(model.score).not.toBeNull()
  })

  it('全部维度缺数据时 score 为 null', () => {
    const model = buildCompensationHealthModel({
      ingestionStatus: 'unknown',
      isRealtimeFresh: false,
      voltageThd: [null, null, null],
      currentThd: [null, null, null],
      temperature: null,
      voltage: null,
      switchingFlags: [null, null, null, null, null, null],
    })
    expect(model.score).toBeNull()
    expect(model.rating).toBe('暂无评级')
  })

  it('严重谐波超限时该维得分很低', () => {
    const model = buildCompensationHealthModel({
      ingestionStatus: 'online',
      isRealtimeFresh: true,
      voltageThd: [27, 27, 27],
      currentThd: [2, 2, 2],
      temperature: 38,
      voltage: 221,
      switchingFlags: [false, false, false, false, false, false],
    })
    const vh = model.breakdown.find((d) => d.key === 'voltageHarmonic')
    expect(vh?.value).toBeLessThan(20)
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd frontend && npx vitest run src/features/device-monitor/components/compensation/__tests__/viewMapping.test.ts -t buildCompensationHealthModel`
Expected: FAIL，报 `buildCompensationHealthModel is not a function` 或导入错误。

- [ ] **Step 3: 实现 buildCompensationHealthModel**

在 `viewMapping.ts` 文件末尾追加。先确保文件顶部 import 含 `CompensationHealthModel`、`CompensationHealthDimension`、`CompensationTone`（这些来自 `./types`，若已聚合导入则把名字加入现有 import 列表）：

```typescript

/* ───── 设备健康度模型 ───── */

export interface CompensationHealthModelInput {
  ingestionStatus?: string | null
  isRealtimeFresh: boolean
  voltageThd: Array<number | null | undefined>
  currentThd: Array<number | null | undefined>
  temperature: number | null | undefined
  voltage: number | null | undefined
  /** [overvoltage_a,b,c, undercurrent_a,b,c]，true=异常。 */
  switchingFlags: Array<boolean | null | undefined>
}

const HEALTH_VOLTAGE_THD_THRESHOLD = 5
const HEALTH_CURRENT_THD_THRESHOLD = 5
const HEALTH_TEMP_THRESHOLD = 55
const HEALTH_NOMINAL_VOLTAGE = 220

function clampHealthScore(value: number): number {
  return Math.max(0, Math.min(100, Math.round(value)))
}

/** 低于门限得高分，超门限急剧下降。 */
function scoreByThreshold(value: number, threshold: number): number {
  const ratio = value / threshold
  if (ratio <= 1) return clampHealthScore(100 - ratio * 20)
  return clampHealthScore(80 - (ratio - 1) * 40)
}

function maxDefinedNumber(values: Array<number | null | undefined>): number | null {
  const nums = values.filter((v): v is number => typeof v === 'number' && Number.isFinite(v))
  return nums.length ? Math.max(...nums) : null
}

function commHealthScore(ingestionStatus: string | null | undefined, isRealtimeFresh: boolean): number | null {
  if (ingestionStatus === 'online') return isRealtimeFresh ? 100 : 70
  if (ingestionStatus === 'degraded') return 55
  if (ingestionStatus === 'offline') return 15
  return null
}

function voltageStabilityScore(voltage: number | null | undefined): number | null {
  if (typeof voltage !== 'number' || !Number.isFinite(voltage)) return null
  const deviationPct = (Math.abs(voltage - HEALTH_NOMINAL_VOLTAGE) / HEALTH_NOMINAL_VOLTAGE) * 100
  return clampHealthScore(100 - deviationPct * 4)
}

function switchingHealthScore(flags: Array<boolean | null | undefined>): number | null {
  if (flags.every((f) => f === null || f === undefined)) return null
  const activeCount = flags.filter((f) => f === true).length
  return clampHealthScore(100 - activeCount * 18)
}

function healthRating(score: number | null): { rating: string; ratingTone: CompensationTone } {
  if (score === null) return { rating: '暂无评级', ratingTone: 'neutral' }
  if (score >= 85) return { rating: '优秀', ratingTone: 'success' }
  if (score >= 70) return { rating: '良好', ratingTone: 'success' }
  if (score >= 50) return { rating: '关注', ratingTone: 'warning' }
  return { rating: '异常', ratingTone: 'danger' }
}

export function buildCompensationHealthModel(input: CompensationHealthModelInput): CompensationHealthModel {
  const vthd = maxDefinedNumber(input.voltageThd)
  const cthd = maxDefinedNumber(input.currentThd)

  const breakdown: CompensationHealthDimension[] = [
    {
      key: 'comm',
      label: '通讯链路',
      value: commHealthScore(input.ingestionStatus, input.isRealtimeFresh),
    },
    {
      key: 'voltageHarmonic',
      label: '电压谐波',
      value: vthd === null ? null : scoreByThreshold(vthd, HEALTH_VOLTAGE_THD_THRESHOLD),
    },
    {
      key: 'currentHarmonic',
      label: '电流谐波',
      value: cthd === null ? null : scoreByThreshold(cthd, HEALTH_CURRENT_THD_THRESHOLD),
    },
    {
      key: 'switching',
      label: '投切动作',
      value: switchingHealthScore(input.switchingFlags),
    },
    {
      key: 'temperature',
      label: '温度',
      value:
        typeof input.temperature === 'number' && Number.isFinite(input.temperature)
          ? scoreByThreshold(input.temperature, HEALTH_TEMP_THRESHOLD)
          : null,
    },
    {
      key: 'voltageStability',
      label: '电压稳定',
      value: voltageStabilityScore(input.voltage),
    },
  ]

  const definedScores = breakdown
    .map((d) => d.value)
    .filter((v): v is number => v !== null)
  const score = definedScores.length
    ? clampHealthScore(definedScores.reduce((sum, v) => sum + v, 0) / definedScores.length)
    : null
  const { rating, ratingTone } = healthRating(score)

  return { score, rating, ratingTone, breakdown }
}
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd frontend && npx vitest run src/features/device-monitor/components/compensation/__tests__/viewMapping.test.ts -t buildCompensationHealthModel`
Expected: PASS（4 个用例全过）。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/device-monitor/components/compensation/viewMapping.ts frontend/src/features/device-monitor/components/compensation/__tests__/viewMapping.test.ts
git commit -m "feat(compensation): add device health model builder"
```

---

## Task 3: composable 接入健康度与 P-Q 数据

**Files:**
- Modify: `frontend/src/features/device-monitor/composables/useCompensationMonitor.ts`
- Test: `frontend/src/features/device-monitor/composables/__tests__/useCompensationMonitor.test.ts`（追加 describe 块）

- [ ] **Step 1: 写失败测试**

先打开 `useCompensationMonitor.test.ts` 顶部，确认其如何构造 `useCompensationMonitor` 输入（既有用例已有模式，复用同样的 ref 构造方式）。在文件末尾追加：

```typescript
describe('useCompensationMonitor P-Q 与健康度', () => {
  it('compensationPqPoint 取 realtime 的有功/无功', () => {
    const overview = ref({
      archive: { device_type: 'compensation', device_subtype: 'capacitor_bank_controller' },
      realtime: { flow_rate: 168, reactive_power: 38 },
    }) as unknown as Ref<MonitorOverview | null>
    const monitor = useCompensationMonitor({
      deviceId: computed(() => 1),
      overview,
      trend: ref(null),
      statusHistory: ref([]),
      timeRange: ref(null),
      compensationTrendTab: ref('effect'),
      canControlDevices: computed(() => true),
    })
    expect(monitor.compensationPqPoint.value).toEqual({ p: 168, q: 38 })
  })

  it('compensationPqHistory 仅取同时有有功与无功的趋势点', () => {
    const overview = ref({
      archive: { device_type: 'compensation', device_subtype: 'capacitor_bank_controller' },
      realtime: {},
    }) as unknown as Ref<MonitorOverview | null>
    const trend = ref({
      points: [
        { timestamp: 't1', flow_rate: 100, reactive_power: 60 },
        { timestamp: 't2', flow_rate: 110, reactive_power: null },
        { timestamp: 't3', flow_rate: 120, reactive_power: 40 },
      ],
    }) as unknown as Ref<DeviceTrendResponse | null>
    const monitor = useCompensationMonitor({
      deviceId: computed(() => 1),
      overview,
      trend,
      statusHistory: ref([]),
      timeRange: ref(null),
      compensationTrendTab: ref('effect'),
      canControlDevices: computed(() => true),
    })
    expect(monitor.compensationPqHistory.value).toEqual([[100, 60], [120, 40]])
  })

  it('compensationHealthModel 暴露 6 维', () => {
    const overview = ref({
      archive: { device_type: 'compensation', device_subtype: 'capacitor_bank_controller' },
      realtime: { voltage: 221 },
      runtime_status: { is_online: true, ingestion_status: 'online' },
    }) as unknown as Ref<MonitorOverview | null>
    const monitor = useCompensationMonitor({
      deviceId: computed(() => 1),
      overview,
      trend: ref(null),
      statusHistory: ref([]),
      timeRange: ref(null),
      compensationTrendTab: ref('effect'),
      canControlDevices: computed(() => true),
    })
    expect(monitor.compensationHealthModel.value.breakdown).toHaveLength(6)
  })
})
```

如测试文件顶部尚未 import `computed` / `ref` / `Ref` / `MonitorOverview` / `DeviceTrendResponse`，按既有用例补齐 import（多为 `import { computed, ref } from 'vue'`、`import type { Ref } from 'vue'`、`import type { MonitorOverview, DeviceTrendResponse } from '@/api/deviceMonitor'`）。

- [ ] **Step 2: 运行测试确认失败**

Run: `cd frontend && npx vitest run src/features/device-monitor/composables/__tests__/useCompensationMonitor.test.ts -t "P-Q 与健康度"`
Expected: FAIL，`compensationPqPoint`/`compensationPqHistory`/`compensationHealthModel` 为 undefined。

- [ ] **Step 3: 在 composable 中实现 computed**

在 `useCompensationMonitor.ts` 顶部 import 区，把 `buildCompensationHealthModel` 加入从 `viewMapping` 的聚合 import，并把 `CompensationHealthModel`、`CompensationPqPoint` 加入从 `./types` 的 import。

在 `useCompensationMonitor` 函数体内、`return { ... }` 之前（紧接 `capacitorBankControlSummaryView` 定义之后）追加：

```typescript
  const compensationPqPoint = computed<CompensationPqPoint>(() => ({
    p:
      typeof realtime.value?.flow_rate === 'number' && Number.isFinite(realtime.value.flow_rate)
        ? realtime.value.flow_rate
        : null,
    q:
      typeof realtime.value?.reactive_power === 'number' && Number.isFinite(realtime.value.reactive_power)
        ? realtime.value.reactive_power
        : null,
  }))

  const compensationPqHistory = computed<Array<[number, number]>>(() => {
    const points = input.trend.value?.points || []
    const pairs: Array<[number, number]> = []
    for (const point of points) {
      const p = point.flow_rate
      const q = point.reactive_power
      if (
        typeof p === 'number' && Number.isFinite(p)
        && typeof q === 'number' && Number.isFinite(q)
      ) {
        pairs.push([p, q])
      }
    }
    return pairs
  })

  const compensationHealthModel = computed<CompensationHealthModel>(() => {
    const cap = compensationCapacitorBankTelemetry.value
    return buildCompensationHealthModel({
      ingestionStatus: runtimeStatus.value?.ingestion_status,
      isRealtimeFresh: isRealtimeFresh.value,
      voltageThd: [cap?.voltage_thd_a, cap?.voltage_thd_b, cap?.voltage_thd_c],
      currentThd: [cap?.current_harmonic_a, cap?.current_harmonic_b, cap?.current_harmonic_c],
      temperature: cap?.temperature ?? realtime.value?.temperature ?? null,
      voltage: realtime.value?.voltage ?? null,
      switchingFlags: [
        cap?.overvoltage_alarm_a, cap?.overvoltage_alarm_b, cap?.overvoltage_alarm_c,
        cap?.undercurrent_a, cap?.undercurrent_b, cap?.undercurrent_c,
      ],
    })
  })
```

在该函数的 `return reactive-less object`（即 `return { ... }`）中，把以下三项加入导出列表（追加到 `capacitorBankControlSummaryView,` 之后）：

```typescript
    compensationPqPoint,
    compensationPqHistory,
    compensationHealthModel,
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd frontend && npx vitest run src/features/device-monitor/composables/__tests__/useCompensationMonitor.test.ts -t "P-Q 与健康度"`
Expected: PASS（3 个用例）。

- [ ] **Step 5: 类型检查**

Run: `cd frontend && npx vue-tsc --noEmit -p tsconfig.app.json 2>&1 | head -20`
Expected: 无新增错误。`compensationPqPoint` 等通过 `useDeviceMonitorPage` 的 `...compensation` 展开自动进入 `DeviceMonitorPageModel`，无需改 `useDeviceMonitorPage.ts`。

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/device-monitor/composables/useCompensationMonitor.ts frontend/src/features/device-monitor/composables/__tests__/useCompensationMonitor.test.ts
git commit -m "feat(compensation): expose health model and P-Q data from monitor composable"
```

---

## Task 4: CompensationPfTrendCard 组件

功率因数趋势卡：大数字 + 较上一区间 Δ + 目标带 sparkline + 时间范围切换 + P/Q/S 统计。

**Files:**
- Create: `frontend/src/features/device-monitor/components/compensation/runtime/CompensationPfTrendCard.vue`
- Test: `frontend/src/features/device-monitor/components/compensation/runtime/__tests__/CompensationPfTrendCard.test.ts`

- [ ] **Step 1: 写失败测试**

创建 `runtime/__tests__/CompensationPfTrendCard.test.ts`：

```typescript
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import CompensationPfTrendCard from '../CompensationPfTrendCard.vue'

function mountCard(props: Record<string, unknown> = {}) {
  return mount(CompensationPfTrendCard, {
    props: {
      pf: 0.975,
      p: 168,
      q: 38,
      pfTrend: { values: [0.96, 0.97, 0.975], timestamps: [], target: 0.95 },
      timeRangeKey: '1h',
      ...props,
    },
  })
}

describe('CompensationPfTrendCard', () => {
  it('渲染 PF 大数字与视在功率', () => {
    const wrapper = mountCard()
    expect(wrapper.text()).toContain('0.975')
    expect(wrapper.text()).toContain('功率因数')
    // S = round(sqrt(168^2 + 38^2)) = 172
    expect(wrapper.text()).toContain('172')
  })

  it('趋势点 >= 2 时渲染 sparkline 折线', () => {
    const wrapper = mountCard()
    expect(wrapper.find('[data-test="pf-spark-line"]').exists()).toBe(true)
  })

  it('趋势点不足时隐藏 sparkline', () => {
    const wrapper = mountCard({ pfTrend: { values: [0.97], timestamps: [], target: 0.95 } })
    expect(wrapper.find('[data-test="pf-spark-line"]').exists()).toBe(false)
  })

  it('点击时间范围标签触发 range-change', async () => {
    const wrapper = mountCard()
    await wrapper.findAll('[data-test="pf-range-tab"]')[2].trigger('click')
    expect(wrapper.emitted('range-change')?.[0]).toEqual(['24h'])
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd frontend && npx vitest run src/features/device-monitor/components/compensation/runtime/__tests__/CompensationPfTrendCard.test.ts`
Expected: FAIL，找不到组件文件。

- [ ] **Step 3: 创建组件**

创建 `runtime/CompensationPfTrendCard.vue`：

```vue
<script setup lang="ts">
import { computed } from 'vue'
import type { PropType } from 'vue'
import type { CompensationPowerFactorTrend } from '../types'

const props = defineProps({
  pf: { type: Number as PropType<number | null>, default: null },
  p: { type: Number as PropType<number | null>, default: null },
  q: { type: Number as PropType<number | null>, default: null },
  pfTrend: {
    type: Object as PropType<CompensationPowerFactorTrend>,
    default: () => ({ values: [], timestamps: [], target: null }),
  },
  timeRangeKey: { type: String as PropType<'10m' | '1h' | '24h'>, default: '1h' },
})

const emit = defineEmits<{ (e: 'range-change', value: '10m' | '1h' | '24h'): void }>()

const ranges: Array<{ key: '10m' | '1h' | '24h'; label: string }> = [
  { key: '10m', label: '10 分钟' },
  { key: '1h', label: '1 小时' },
  { key: '24h', label: '24 小时' },
]

const W = 400
const H = 80
const MIN = 0.85
const MAX = 1.0
const PAD = { l: 2, r: 24, t: 6, b: 10 }

const hasSpark = computed(() => props.pfTrend.values.length >= 2)

const geometry = computed(() => {
  const data = props.pfTrend.values
  if (data.length < 2) return null
  const w = W - PAD.l - PAD.r
  const h = H - PAD.t - PAD.b
  const points = data.map((d, i) => {
    const x = PAD.l + (i / (data.length - 1)) * w
    const y = PAD.t + h - ((Math.min(MAX, Math.max(MIN, d)) - MIN) / (MAX - MIN)) * h
    return [x, y] as const
  })
  const line = points.map((pt, i) => `${i === 0 ? 'M' : 'L'} ${pt[0].toFixed(2)} ${pt[1].toFixed(2)}`).join(' ')
  const last = points[points.length - 1]
  const area = `${line} L ${last[0].toFixed(2)} ${PAD.t + h} L ${points[0][0].toFixed(2)} ${PAD.t + h} Z`
  const yTop = PAD.t + h - ((1.0 - MIN) / (MAX - MIN)) * h
  const yBot = PAD.t + h - ((0.95 - MIN) / (MAX - MIN)) * h
  return { line, area, last, bandY: yTop, bandH: yBot - yTop, bandBot: yBot, w }
})

const delta = computed(() => {
  const values = props.pfTrend.values
  if (values.length < 2) return null
  return values[values.length - 1] - values[0]
})

const apparentPower = computed(() => {
  if (props.p === null || props.q === null) return null
  return Math.round(Math.sqrt(props.p * props.p + props.q * props.q))
})

function fmt(value: number | null, digits = 0): string {
  return value === null ? '--' : value.toFixed(digits)
}
</script>

<template>
  <section class="pf-card">
    <header class="rt-card-head">
      <span class="rt-card-title"><span class="rt-accent" />功率因数 <span class="rt-sub">实时 · 滞后为正</span></span>
      <div class="pf-tabs">
        <button
          v-for="r in ranges"
          :key="r.key"
          type="button"
          class="pf-tab"
          :class="{ 'is-active': timeRangeKey === r.key }"
          data-test="pf-range-tab"
          @click="emit('range-change', r.key)"
        >{{ r.label }}</button>
      </div>
    </header>

    <div class="pf-body">
      <div class="pf-readout">
        <strong class="pf-big">{{ fmt(pf, 3) }}</strong>
        <span class="pf-unit">PF</span>
        <span
          v-if="delta !== null"
          class="pf-delta"
          :class="delta >= 0 ? 'is-up' : 'is-down'"
        >{{ delta >= 0 ? '▲' : '▼' }} {{ Math.abs(delta).toFixed(3) }}</span>
      </div>

      <div class="pf-spark">
        <svg
          v-if="hasSpark && geometry"
          :viewBox="`0 0 ${W} ${H}`"
          preserveAspectRatio="none"
          class="pf-spark-svg"
        >
          <defs>
            <linearGradient id="pfAreaGrad" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stop-color="#34d399" stop-opacity="0.35" />
              <stop offset="100%" stop-color="#34d399" stop-opacity="0" />
            </linearGradient>
          </defs>
          <rect :x="PAD.l" :y="geometry.bandY" :width="geometry.w" :height="geometry.bandH" fill="#34d399" fill-opacity="0.06" />
          <line :x1="PAD.l" :x2="PAD.l + geometry.w" :y1="geometry.bandBot" :y2="geometry.bandBot" stroke="#34d399" stroke-opacity="0.25" stroke-dasharray="2 3" />
          <path :d="geometry.area" fill="url(#pfAreaGrad)" />
          <path data-test="pf-spark-line" :d="geometry.line" fill="none" stroke="#34d399" stroke-width="1.4" stroke-linejoin="round" stroke-linecap="round" />
          <circle :cx="geometry.last[0]" :cy="geometry.last[1]" r="3" fill="#34d399" />
        </svg>
        <div v-else class="pf-spark-empty">趋势数据不足</div>
      </div>

      <div class="pf-stats">
        <div class="pf-stat"><span class="pf-stat-lbl">有功 P</span><span class="pf-stat-val cyan">{{ fmt(p) }} <i>kW</i></span></div>
        <div class="pf-stat"><span class="pf-stat-lbl">无功 Q</span><span class="pf-stat-val" :class="q !== null && q > 50 ? 'amber' : 'cyan'">{{ q !== null && q > 0 ? '+' : '' }}{{ fmt(q) }} <i>kVar</i></span></div>
        <div class="pf-stat"><span class="pf-stat-lbl">视在 S</span><span class="pf-stat-val">{{ fmt(apparentPower) }} <i>kVA</i></span></div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.pf-card {
  display: flex;
  flex-direction: column;
  background: #121d2e;
  border: 1px solid #1f2c41;
  border-radius: 10px;
  min-height: 0;
}
.rt-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 14px;
  border-bottom: 1px solid #1f2c41;
}
.rt-card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #e5edf7;
}
.rt-accent {
  width: 3px;
  height: 12px;
  border-radius: 2px;
  background: #22d3ee;
}
.rt-sub {
  color: #5e6c83;
  font-weight: 400;
}
.pf-tabs {
  display: flex;
  gap: 2px;
  padding: 3px;
  background: #0b1623;
  border: 1px solid #1f2c41;
  border-radius: 8px;
}
.pf-tab {
  padding: 4px 9px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #9aa7bd;
  font: inherit;
  font-size: 11px;
  cursor: pointer;
}
.pf-tab.is-active {
  background: #182538;
  color: #67e8f9;
  box-shadow: inset 0 0 0 1px rgba(34, 211, 238, 0.25);
}
.pf-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 14px;
  flex: 1;
  min-height: 0;
}
.pf-readout {
  display: flex;
  align-items: flex-end;
  gap: 10px;
}
.pf-big {
  font-size: 44px;
  line-height: 0.95;
  font-weight: 300;
  color: #34d399;
  font-variant-numeric: tabular-nums;
}
.pf-unit {
  color: #9aa7bd;
  padding-bottom: 5px;
}
.pf-delta {
  margin-left: auto;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}
.pf-delta.is-up { color: #34d399; }
.pf-delta.is-down { color: #f59e0b; }
.pf-spark {
  flex: 1;
  min-height: 60px;
}
.pf-spark-svg {
  width: 100%;
  height: 100%;
  display: block;
}
.pf-spark-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #5e6c83;
  font-size: 11px;
}
.pf-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  padding-top: 6px;
  border-top: 1px solid #1f2c41;
}
.pf-stat-lbl {
  display: block;
  font-size: 10px;
  color: #5e6c83;
}
.pf-stat-val {
  font-size: 14px;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  color: #e5edf7;
}
.pf-stat-val i {
  font-size: 11px;
  font-style: normal;
  color: #5e6c83;
}
.pf-stat-val.cyan { color: #67e8f9; }
.pf-stat-val.amber { color: #f59e0b; }
</style>
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd frontend && npx vitest run src/features/device-monitor/components/compensation/runtime/__tests__/CompensationPfTrendCard.test.ts`
Expected: PASS（4 个用例）。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/device-monitor/components/compensation/runtime/CompensationPfTrendCard.vue frontend/src/features/device-monitor/components/compensation/runtime/__tests__/CompensationPfTrendCard.test.ts
git commit -m "feat(compensation): add PF trend card for runtime monitor"
```

---

## Task 5: CompensationPqQuadrantCard 组件

P-Q 四象限运行图：坐标轴 + PF 等值线 + 目标区 + 当前运行点 + 可选轨迹。

**Files:**
- Create: `frontend/src/features/device-monitor/components/compensation/runtime/CompensationPqQuadrantCard.vue`
- Test: `frontend/src/features/device-monitor/components/compensation/runtime/__tests__/CompensationPqQuadrantCard.test.ts`

- [ ] **Step 1: 写失败测试**

创建 `runtime/__tests__/CompensationPqQuadrantCard.test.ts`：

```typescript
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import CompensationPqQuadrantCard from '../CompensationPqQuadrantCard.vue'

describe('CompensationPqQuadrantCard', () => {
  it('有 P/Q 时渲染当前运行点', () => {
    const wrapper = mount(CompensationPqQuadrantCard, {
      props: { point: { p: 168, q: 38 }, history: [] },
    })
    expect(wrapper.find('[data-test="pq-current-point"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('P 168')
  })

  it('P 或 Q 缺失时显示空状态', () => {
    const wrapper = mount(CompensationPqQuadrantCard, {
      props: { point: { p: null, q: 38 }, history: [] },
    })
    expect(wrapper.find('[data-test="pq-current-point"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('等待实时遥测')
  })

  it('有轨迹时渲染轨迹路径，无轨迹时不渲染', () => {
    const withHistory = mount(CompensationPqQuadrantCard, {
      props: { point: { p: 168, q: 38 }, history: [[100, 60], [120, 50]] },
    })
    expect(withHistory.find('[data-test="pq-history-path"]').exists()).toBe(true)
    const noHistory = mount(CompensationPqQuadrantCard, {
      props: { point: { p: 168, q: 38 }, history: [] },
    })
    expect(noHistory.find('[data-test="pq-history-path"]').exists()).toBe(false)
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd frontend && npx vitest run src/features/device-monitor/components/compensation/runtime/__tests__/CompensationPqQuadrantCard.test.ts`
Expected: FAIL，找不到组件文件。

- [ ] **Step 3: 创建组件**

创建 `runtime/CompensationPqQuadrantCard.vue`：

```vue
<script setup lang="ts">
import { computed } from 'vue'
import type { PropType } from 'vue'
import type { CompensationPqPoint } from '../types'

const props = defineProps({
  point: { type: Object as PropType<CompensationPqPoint>, default: () => ({ p: null, q: null }) },
  history: { type: Array as PropType<Array<[number, number]>>, default: () => [] },
})

const W = 380
const H = 240
const CX = W / 2
const CY = H / 2
const SCALE = Math.min(W * 0.42, H * 0.42)
const P_MAX = 400
const Q_MAX = 200

function toXY(p: number, q: number): [number, number] {
  return [CX + (p / P_MAX) * SCALE, CY - (q / Q_MAX) * SCALE]
}

const hasPoint = computed(() => props.point.p !== null && props.point.q !== null)

const current = computed(() => {
  if (!hasPoint.value) return null
  return toXY(props.point.p as number, props.point.q as number)
})

const historyPath = computed(() => {
  if (props.history.length < 2) return ''
  return props.history
    .map((pt, i) => {
      const [x, y] = toXY(pt[0], pt[1])
      return `${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`
    })
    .join(' ')
})

const pfLines = [
  { pf: 0.9, color: '#f59e0b' },
  { pf: 0.95, color: '#34d399' },
]

const pfLineGeometry = computed(() =>
  pfLines.map((l) => {
    const ang = Math.acos(l.pf)
    const x1 = CX + Math.cos(ang) * SCALE
    const yLag = CY - Math.sin(ang) * SCALE
    const yLead = CY + Math.sin(ang) * SCALE
    return { ...l, x1, yLag, yLead }
  }),
)
</script>

<template>
  <section class="pq-card">
    <header class="rt-card-head">
      <span class="rt-card-title"><span class="rt-accent" />P-Q 运行象限 <span class="rt-sub">补偿轨迹</span></span>
      <div class="pq-legend">
        <span><i class="sw" style="background:#34d399;opacity:.5" />目标区</span>
        <span><i class="sw" style="background:#22d3ee" />当前点</span>
      </div>
    </header>

    <div class="pq-body">
      <svg :viewBox="`0 0 ${W} ${H}`" preserveAspectRatio="xMidYMid meet" class="pq-svg">
        <defs>
          <radialGradient id="pqGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#22d3ee" stop-opacity="0.8" />
            <stop offset="100%" stop-color="#22d3ee" stop-opacity="0" />
          </radialGradient>
          <radialGradient id="pqTarget" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#34d399" stop-opacity="0.18" />
            <stop offset="100%" stop-color="#34d399" stop-opacity="0" />
          </radialGradient>
        </defs>

        <rect x="0" y="0" :width="W" :height="CY" fill="#0e1828" fill-opacity="0.4" />
        <circle v-for="r in [0.33, 0.66, 1]" :key="r" :cx="CX" :cy="CY" :r="SCALE * r" fill="none" stroke="#1f2c41" stroke-dasharray="2 3" />

        <path
          :d="`M ${CX} ${CY} L ${CX + SCALE * 0.95} ${CY - SCALE * 0.31} A ${SCALE} ${SCALE} 0 0 0 ${CX + SCALE * 0.95} ${CY + SCALE * 0.31} Z`"
          fill="url(#pqTarget)"
        />

        <g v-for="l in pfLineGeometry" :key="l.pf" :stroke="l.color" stroke-opacity="0.35" stroke-dasharray="3 4">
          <line :x1="CX" :y1="CY" :x2="l.x1" :y2="l.yLag" />
          <line :x1="CX" :y1="CY" :x2="l.x1" :y2="l.yLead" />
          <text :x="l.x1 + 3" :y="l.yLag - 2" :fill="l.color" fill-opacity="0.7" font-size="9">PF {{ l.pf }}</text>
        </g>

        <line x1="14" :y1="CY" :x2="W - 14" :y2="CY" stroke="#2a3a55" />
        <line :x1="CX" y1="14" :x2="CX" :y2="H - 14" stroke="#2a3a55" />
        <text :x="W - 6" :y="CY - 5" fill="#9aa7bd" font-size="9" text-anchor="end">+P kW</text>
        <text :x="CX + 6" y="20" fill="#9aa7bd" font-size="9">+Q 感性</text>
        <text :x="CX + 6" :y="H - 6" fill="#9aa7bd" font-size="9">-Q 容性</text>

        <path
          v-if="historyPath"
          data-test="pq-history-path"
          :d="historyPath"
          fill="none"
          stroke="#22d3ee"
          stroke-opacity="0.35"
          stroke-width="1.2"
          stroke-dasharray="2 2"
        />

        <g v-if="current" data-test="pq-current-point">
          <circle :cx="current[0]" :cy="current[1]" r="16" fill="url(#pqGlow)" />
          <circle :cx="current[0]" :cy="current[1]" r="5" fill="#22d3ee" stroke="#07101c" stroke-width="2" />
          <g :transform="`translate(${current[0] + 10}, ${current[1] - 10})`">
            <rect x="0" y="0" width="86" height="28" rx="5" fill="#0b1623" stroke="#22d3ee" stroke-opacity="0.5" />
            <text x="6" y="11" fill="#9aa7bd" font-size="8">当前运行点</text>
            <text x="6" y="22" fill="#67e8f9" font-size="10" font-weight="600">
              P {{ point.p }} · Q {{ (point.q as number) > 0 ? '+' : '' }}{{ point.q }}
            </text>
          </g>
        </g>
        <circle :cx="CX" :cy="CY" r="2" fill="#5e6c83" />
      </svg>

      <div v-if="!hasPoint" class="pq-empty">等待实时遥测（有功 / 无功功率）</div>
    </div>
  </section>
</template>

<style scoped>
.pq-card {
  display: flex;
  flex-direction: column;
  background: #121d2e;
  border: 1px solid #1f2c41;
  border-radius: 10px;
  min-height: 0;
}
.rt-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 14px;
  border-bottom: 1px solid #1f2c41;
}
.rt-card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #e5edf7;
}
.rt-accent {
  width: 3px;
  height: 12px;
  border-radius: 2px;
  background: #22d3ee;
}
.rt-sub {
  color: #5e6c83;
  font-weight: 400;
}
.pq-legend {
  display: flex;
  gap: 10px;
  font-size: 11px;
  color: #5e6c83;
}
.pq-legend span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.pq-legend .sw {
  width: 8px;
  height: 8px;
  border-radius: 2px;
}
.pq-body {
  position: relative;
  flex: 1;
  min-height: 0;
  padding: 8px 12px 10px;
}
.pq-svg {
  width: 100%;
  height: 100%;
  display: block;
}
.pq-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(11, 22, 35, 0.82);
  color: #9aa7bd;
  font-size: 12px;
}
</style>
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd frontend && npx vitest run src/features/device-monitor/components/compensation/runtime/__tests__/CompensationPqQuadrantCard.test.ts`
Expected: PASS（3 个用例）。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/device-monitor/components/compensation/runtime/CompensationPqQuadrantCard.vue frontend/src/features/device-monitor/components/compensation/runtime/__tests__/CompensationPqQuadrantCard.test.ts
git commit -m "feat(compensation): add P-Q quadrant card for runtime monitor"
```

---

## Task 6: CompensationHealthCard 组件

设备健康度评分卡：总分 + 评级 + 6 维条形图。

**Files:**
- Create: `frontend/src/features/device-monitor/components/compensation/runtime/CompensationHealthCard.vue`
- Test: `frontend/src/features/device-monitor/components/compensation/runtime/__tests__/CompensationHealthCard.test.ts`

- [ ] **Step 1: 写失败测试**

创建 `runtime/__tests__/CompensationHealthCard.test.ts`：

```typescript
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import CompensationHealthCard from '../CompensationHealthCard.vue'
import type { CompensationHealthModel } from '../../types'

function model(overrides: Partial<CompensationHealthModel> = {}): CompensationHealthModel {
  return {
    score: 78,
    rating: '良好',
    ratingTone: 'success',
    breakdown: [
      { key: 'comm', label: '通讯链路', value: 65 },
      { key: 'voltageHarmonic', label: '电压谐波', value: 42 },
      { key: 'currentHarmonic', label: '电流谐波', value: 88 },
      { key: 'switching', label: '投切动作', value: 96 },
      { key: 'temperature', label: '温度', value: 100 },
      { key: 'voltageStability', label: '电压稳定', value: null },
    ],
    ...overrides,
  }
}

describe('CompensationHealthCard', () => {
  it('渲染总分与 6 维', () => {
    const wrapper = mount(CompensationHealthCard, { props: { model: model() } })
    expect(wrapper.text()).toContain('78')
    expect(wrapper.text()).toContain('良好')
    expect(wrapper.findAll('[data-test="health-bar"]')).toHaveLength(6)
  })

  it('缺测维度显示「待采集」', () => {
    const wrapper = mount(CompensationHealthCard, { props: { model: model() } })
    expect(wrapper.text()).toContain('待采集')
  })

  it('score 为 null 时显示空状态', () => {
    const wrapper = mount(CompensationHealthCard, {
      props: { model: model({ score: null, rating: '暂无评级', ratingTone: 'neutral' }) },
    })
    expect(wrapper.text()).toContain('暂无健康度数据')
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd frontend && npx vitest run src/features/device-monitor/components/compensation/runtime/__tests__/CompensationHealthCard.test.ts`
Expected: FAIL，找不到组件文件。

- [ ] **Step 3: 创建组件**

创建 `runtime/CompensationHealthCard.vue`：

```vue
<script setup lang="ts">
import type { PropType } from 'vue'
import type { CompensationHealthModel } from '../types'

defineProps({
  model: {
    type: Object as PropType<CompensationHealthModel>,
    required: true,
  },
})

function barColor(value: number): string {
  if (value >= 90) return '#34d399'
  if (value >= 70) return '#22d3ee'
  if (value >= 50) return '#f59e0b'
  return '#ef4444'
}
</script>

<template>
  <section class="health-card">
    <header class="rt-card-head">
      <span class="rt-card-title"><span class="rt-accent" />设备健康度</span>
      <span class="health-tag">实时计算</span>
    </header>

    <div v-if="model.score === null" class="health-empty">暂无健康度数据</div>

    <div v-else class="health-body">
      <div class="health-score">
        <strong class="health-score-val">{{ model.score }}</strong>
        <span class="health-score-max">/100</span>
      </div>
      <div class="health-rating">
        状态评级 · <span :class="`tone-${model.ratingTone}`">{{ model.rating }}</span>
      </div>
      <div class="health-bars">
        <div
          v-for="dim in model.breakdown"
          :key="dim.key"
          class="health-bar"
          data-test="health-bar"
        >
          <span class="health-bar-lbl">{{ dim.label }}</span>
          <div class="health-bar-track">
            <div
              v-if="dim.value !== null"
              class="health-bar-fill"
              :style="{ width: `${dim.value}%`, background: barColor(dim.value) }"
            />
          </div>
          <span
            class="health-bar-val"
            :style="{ color: dim.value !== null ? barColor(dim.value) : '#5e6c83' }"
          >{{ dim.value === null ? '待采集' : dim.value }}</span>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.health-card {
  display: flex;
  flex-direction: column;
  background: #121d2e;
  border: 1px solid #1f2c41;
  border-radius: 10px;
  min-height: 0;
}
.rt-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 14px;
  border-bottom: 1px solid #1f2c41;
}
.rt-card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #e5edf7;
}
.rt-accent {
  width: 3px;
  height: 12px;
  border-radius: 2px;
  background: #22d3ee;
}
.health-tag {
  padding: 1px 8px;
  border-radius: 999px;
  font-size: 10px;
  color: #67e8f9;
  border: 1px solid rgba(34, 211, 238, 0.4);
  background: rgba(34, 211, 238, 0.08);
}
.health-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9aa7bd;
  font-size: 12px;
}
.health-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 14px;
  flex: 1;
  min-height: 0;
}
.health-score {
  display: flex;
  align-items: baseline;
  gap: 6px;
}
.health-score-val {
  font-size: 40px;
  font-weight: 300;
  line-height: 0.95;
  color: #67e8f9;
  font-variant-numeric: tabular-nums;
}
.health-score-max {
  color: #5e6c83;
}
.health-rating {
  font-size: 11px;
  color: #5e6c83;
}
.tone-success { color: #34d399; }
.tone-warning { color: #f59e0b; }
.tone-danger { color: #ef4444; }
.tone-info,
.tone-neutral { color: #67e8f9; }
.health-bars {
  display: flex;
  flex-direction: column;
  gap: 5px;
  flex: 1;
  justify-content: center;
}
.health-bar {
  display: grid;
  grid-template-columns: 64px 1fr 40px;
  gap: 8px;
  align-items: center;
}
.health-bar-lbl {
  font-size: 10px;
  color: #9aa7bd;
}
.health-bar-track {
  height: 5px;
  background: #0b1623;
  border: 1px solid #1f2c41;
  border-radius: 3px;
  overflow: hidden;
}
.health-bar-fill {
  height: 100%;
  border-radius: 2px;
}
.health-bar-val {
  font-size: 10px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}
</style>
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd frontend && npx vitest run src/features/device-monitor/components/compensation/runtime/__tests__/CompensationHealthCard.test.ts`
Expected: PASS（3 个用例）。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/device-monitor/components/compensation/runtime/CompensationHealthCard.vue frontend/src/features/device-monitor/components/compensation/runtime/__tests__/CompensationHealthCard.test.ts
git commit -m "feat(compensation): add device health card for runtime monitor"
```

---

## Task 7: CompensationBankTopology 组件

电容器组拓扑：6 条母线（A/B/C 分补 + 公补 1-8/9-16/17-24），每回路一个色块；点击 emit `pick`。

**Files:**
- Create: `frontend/src/features/device-monitor/components/compensation/runtime/CompensationBankTopology.vue`
- Test: `frontend/src/features/device-monitor/components/compensation/runtime/__tests__/CompensationBankTopology.test.ts`

- [ ] **Step 1: 写失败测试**

创建 `runtime/__tests__/CompensationBankTopology.test.ts`：

```typescript
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import CompensationBankTopology from '../CompensationBankTopology.vue'
import type { CompensationCapacitorBankTelemetry } from '@/api/compensation'

function telemetry(overrides: Partial<CompensationCapacitorBankTelemetry> = {}): CompensationCapacitorBankTelemetry {
  return {
    device_id: 1,
    timestamp: '2026-05-19T10:00:00+08:00',
    // A 相：第 1 路投入（bit0），其余切除
    circuit_state_phase_a: 0b00000001,
    circuit_state_phase_b: 0b00000110,
    circuit_state_phase_c: 0b00000010,
    circuit_state_common_1: 0,
    circuit_state_common_2: 0,
    circuit_state_common_3: 0,
    overvoltage_alarm_a: false,
    overvoltage_alarm_b: false,
    overvoltage_alarm_c: false,
    ...overrides,
  } as CompensationCapacitorBankTelemetry
}

const profile = {
  splitCircuitCount: 24,
  commonCircuitCount: 24,
  phaseACircuitTotalCount: 8,
  phaseBCircuitTotalCount: 8,
  phaseCCircuitTotalCount: 8,
  common1CircuitTotalCount: 8,
  common2CircuitTotalCount: 8,
  common3CircuitTotalCount: 8,
}

describe('CompensationBankTopology', () => {
  it('渲染 6 条母线', () => {
    const wrapper = mount(CompensationBankTopology, {
      props: { telemetry: telemetry(), circuitProfile: profile },
    })
    expect(wrapper.findAll('[data-test="topo-bus"]')).toHaveLength(6)
  })

  it('mask 解码为投入/切除回路', () => {
    const wrapper = mount(CompensationBankTopology, {
      props: { telemetry: telemetry(), circuitProfile: profile },
    })
    // A 相 8 路中 1 路投入
    const aBus = wrapper.findAll('[data-test="topo-bus"]')[0]
    expect(aBus.findAll('.topo-cap.is-on')).toHaveLength(1)
    expect(aBus.findAll('.topo-cap.is-off')).toHaveLength(7)
  })

  it('点击回路 emit pick', async () => {
    const wrapper = mount(CompensationBankTopology, {
      props: { telemetry: telemetry(), circuitProfile: profile },
    })
    await wrapper.findAll('.topo-cap')[0].trigger('click')
    const pick = wrapper.emitted('pick')?.[0]?.[0] as Record<string, unknown>
    expect(pick.phase).toBe('A')
    expect(pick.index).toBe(1)
    expect(pick.state).toBe('on')
  })

  it('相级告警时该相标签带告警角标', () => {
    const wrapper = mount(CompensationBankTopology, {
      props: {
        telemetry: telemetry({ overvoltage_alarm_b: true }),
        circuitProfile: profile,
      },
    })
    const bBus = wrapper.findAll('[data-test="topo-bus"]')[1]
    expect(bBus.find('.topo-phase-alarm').exists()).toBe(true)
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd frontend && npx vitest run src/features/device-monitor/components/compensation/runtime/__tests__/CompensationBankTopology.test.ts`
Expected: FAIL，找不到组件文件。

- [ ] **Step 3: 创建组件**

创建 `runtime/CompensationBankTopology.vue`。该组件复用既有 `circuitStateUtils` 的 `getCircuitGroups` / `resolvedConfiguredCounts` / `toBits` / `countOnSlots`：

```vue
<script setup lang="ts">
import { computed } from 'vue'
import type { PropType } from 'vue'
import type { CompensationCapacitorBankTelemetry } from '@/api/compensation'
import {
  getCircuitGroups,
  resolvedConfiguredCounts,
  toBits,
} from '../circuitStateUtils'
import type { CompensationCircuitPick, CompensationCircuitSlotState } from '../types'

interface CircuitProfileView {
  splitCircuitCount?: number
  commonCircuitCount?: number
  phaseACircuitTotalCount?: number
  phaseBCircuitTotalCount?: number
  phaseCCircuitTotalCount?: number
  common1CircuitTotalCount?: number
  common2CircuitTotalCount?: number
  common3CircuitTotalCount?: number
}

const props = defineProps({
  telemetry: {
    type: Object as PropType<CompensationCapacitorBankTelemetry | null>,
    default: null,
  },
  circuitProfile: {
    type: Object as PropType<CircuitProfileView | null>,
    default: null,
  },
})

const emit = defineEmits<{ (e: 'pick', circuit: CompensationCircuitPick): void }>()

const BUS_META: Array<{
  phase: 'A' | 'B' | 'C' | 'COMMON'
  commonGroup: 1 | 2 | 3 | null
  phaseClass: string
  chip: string
  divider: boolean
}> = [
  { phase: 'A', commonGroup: null, phaseClass: 'a', chip: 'A', divider: false },
  { phase: 'B', commonGroup: null, phaseClass: 'b', chip: 'B', divider: false },
  { phase: 'C', commonGroup: null, phaseClass: 'c', chip: 'C', divider: false },
  { phase: 'COMMON', commonGroup: 1, phaseClass: 'n', chip: 'N', divider: true },
  { phase: 'COMMON', commonGroup: 2, phaseClass: 'n', chip: 'N', divider: false },
  { phase: 'COMMON', commonGroup: 3, phaseClass: 'n', chip: 'N', divider: false },
]

const buses = computed(() => {
  const t = props.telemetry
  const groups = t
    ? getCircuitGroups(t)
    : Array.from({ length: 6 }, () => ({ label: '', mask: null as number | null, alarmFlag: null }))
  const counts = resolvedConfiguredCounts({
    configuredSplitCircuitCount: props.circuitProfile?.splitCircuitCount ?? null,
    configuredCommonCircuitCount: props.circuitProfile?.commonCircuitCount ?? null,
    phaseACircuitTotalCount: props.circuitProfile?.phaseACircuitTotalCount ?? null,
    phaseBCircuitTotalCount: props.circuitProfile?.phaseBCircuitTotalCount ?? null,
    phaseCCircuitTotalCount: props.circuitProfile?.phaseCCircuitTotalCount ?? null,
    common1CircuitTotalCount: props.circuitProfile?.common1CircuitTotalCount ?? null,
    common2CircuitTotalCount: props.circuitProfile?.common2CircuitTotalCount ?? null,
    common3CircuitTotalCount: props.circuitProfile?.common3CircuitTotalCount ?? null,
  })

  return BUS_META.map((meta, i) => {
    const group = groups[i]
    const slots = toBits(group.mask, counts[i])
    const phaseAlarm = Boolean(group.alarmFlag)
    return {
      ...meta,
      label: group.label || meta.chip,
      phaseAlarm,
      caps: slots.map((slot, slotIdx) => {
        const state: CompensationCircuitSlotState =
          slot === true ? 'on' : slot === false ? 'off' : 'unconfigured'
        return { slotIdx, index: slotIdx + 1, state }
      }),
    }
  })
})

const summary = computed(() => {
  let running = 0
  let total = 0
  for (const bus of buses.value) {
    for (const cap of bus.caps) {
      if (cap.state === 'unconfigured') continue
      total += 1
      if (cap.state === 'on') running += 1
    }
  }
  const rate = total > 0 ? Math.round((running / total) * 1000) / 10 : 0
  return { running, total, rate }
})

function handlePick(
  bus: (typeof buses.value)[number],
  cap: { index: number; state: CompensationCircuitSlotState },
) {
  if (cap.state === 'unconfigured') return
  emit('pick', {
    groupLabel: bus.label,
    phase: bus.phase,
    commonGroup: bus.commonGroup,
    index: cap.index,
    state: cap.state,
    phaseAlarm: bus.phaseAlarm,
  })
}
</script>

<template>
  <section class="topo-card">
    <header class="rt-card-head">
      <span class="rt-card-title">
        <span class="rt-accent" />电容器组拓扑
        <span class="rt-sub">分补 + 公补 · {{ summary.running }} 路投运</span>
      </span>
      <div class="topo-legend">
        <span><i class="sw on" />投入</span>
        <span><i class="sw off" />切除</span>
        <span><i class="sw empty" />未配置</span>
      </div>
    </header>

    <div class="topo-body">
      <div class="topo">
        <template v-for="bus in buses" :key="`${bus.phase}-${bus.commonGroup}`">
          <div v-if="bus.divider" class="topo-divider" />
          <div class="topo-bus" data-test="topo-bus">
            <div class="topo-phase">
              <span class="topo-chip" :class="bus.phaseClass">{{ bus.chip }}</span>
              <span class="topo-phase-label">
                {{ bus.label }}
                <span v-if="bus.phaseAlarm" class="topo-phase-alarm" title="该相存在告警">!</span>
              </span>
            </div>
            <div class="topo-rail">
              <button
                v-for="cap in bus.caps"
                :key="cap.slotIdx"
                type="button"
                class="topo-cap"
                :class="{
                  'is-on': cap.state === 'on',
                  'is-off': cap.state === 'off',
                  'is-empty': cap.state === 'unconfigured',
                }"
                :disabled="cap.state === 'unconfigured'"
                @click="handlePick(bus, cap)"
              >
                <span class="topo-cap-idx">#{{ cap.index }}</span>
              </button>
            </div>
          </div>
        </template>
      </div>
      <div class="topo-summary">
        <span><b>{{ summary.running }} / {{ summary.total }}</b> 路投运</span>
        <span>投运率 <b>{{ summary.rate }}%</b></span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.topo-card {
  display: flex;
  flex-direction: column;
  background: #121d2e;
  border: 1px solid #1f2c41;
  border-radius: 10px;
  min-height: 0;
}
.rt-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 14px;
  border-bottom: 1px solid #1f2c41;
}
.rt-card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #e5edf7;
}
.rt-accent {
  width: 3px;
  height: 12px;
  border-radius: 2px;
  background: #22d3ee;
}
.rt-sub {
  color: #5e6c83;
  font-weight: 400;
}
.topo-legend {
  display: flex;
  gap: 12px;
  font-size: 10px;
  color: #5e6c83;
}
.topo-legend span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.topo-legend .sw {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  border: 1px solid #1f2c41;
}
.topo-legend .sw.on { background: #34d399; border-color: rgba(52, 211, 153, 0.5); }
.topo-legend .sw.off { background: #0b1623; }
.topo-legend .sw.empty { border-style: dashed; }
.topo-body {
  display: flex;
  flex-direction: column;
  padding: 8px 14px;
  flex: 1;
  min-height: 0;
}
.topo {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}
.topo-bus {
  display: flex;
  align-items: center;
  gap: 10px;
}
.topo-phase {
  width: 96px;
  display: flex;
  align-items: center;
  gap: 7px;
  flex-shrink: 0;
}
.topo-chip {
  width: 22px;
  height: 22px;
  border-radius: 5px;
  display: grid;
  place-items: center;
  font-weight: 700;
  font-size: 11px;
  color: #07101c;
}
.topo-chip.a { background: #facc15; }
.topo-chip.b { background: #34d399; }
.topo-chip.c { background: #f87171; }
.topo-chip.n { background: #a78bfa; }
.topo-phase-label {
  font-size: 11px;
  color: #e5edf7;
}
.topo-phase-alarm {
  display: inline-grid;
  place-items: center;
  width: 14px;
  height: 14px;
  margin-left: 2px;
  border-radius: 50%;
  background: #ef4444;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
}
.topo-rail {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 6px;
  position: relative;
}
.topo-rail::before {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  height: 2px;
  background: linear-gradient(90deg, rgba(34, 211, 238, 0.5), rgba(34, 211, 238, 0.1));
}
.topo-cap {
  position: relative;
  height: 36px;
  border-radius: 6px;
  background: #0b1623;
  border: 1px solid #1f2c41;
  color: #9aa7bd;
  cursor: pointer;
  display: grid;
  place-items: center;
}
.topo-cap-idx {
  font-size: 10px;
  font-variant-numeric: tabular-nums;
}
.topo-cap:hover:not(:disabled) {
  border-color: #22d3ee;
}
.topo-cap.is-on {
  background: linear-gradient(180deg, rgba(52, 211, 153, 0.18), rgba(52, 211, 153, 0.05));
  border-color: rgba(52, 211, 153, 0.5);
  color: #34d399;
}
.topo-cap.is-empty {
  border-style: dashed;
  opacity: 0.45;
  cursor: not-allowed;
}
.topo-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, #1f2c41, transparent);
  margin: 3px 0;
}
.topo-summary {
  display: flex;
  gap: 16px;
  padding-top: 8px;
  font-size: 11px;
  color: #9aa7bd;
}
.topo-summary b {
  color: #e5edf7;
  font-variant-numeric: tabular-nums;
}
</style>
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd frontend && npx vitest run src/features/device-monitor/components/compensation/runtime/__tests__/CompensationBankTopology.test.ts`
Expected: PASS（4 个用例）。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/device-monitor/components/compensation/runtime/CompensationBankTopology.vue frontend/src/features/device-monitor/components/compensation/runtime/__tests__/CompensationBankTopology.test.ts
git commit -m "feat(compensation): add capacitor bank topology for runtime monitor"
```

---

## Task 8: CompensationCircuitDrawer 组件

单回路详情右滑抽屉：当前状态 + 相关事件 + 投/切操作。

**Files:**
- Create: `frontend/src/features/device-monitor/components/compensation/runtime/CompensationCircuitDrawer.vue`
- Test: `frontend/src/features/device-monitor/components/compensation/runtime/__tests__/CompensationCircuitDrawer.test.ts`

- [ ] **Step 1: 写失败测试**

创建 `runtime/__tests__/CompensationCircuitDrawer.test.ts`：

```typescript
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import CompensationCircuitDrawer from '../CompensationCircuitDrawer.vue'
import type { CompensationCircuitPick } from '../../types'

const circuit: CompensationCircuitPick = {
  groupLabel: 'A 相分补',
  phase: 'A',
  commonGroup: null,
  index: 1,
  state: 'on',
  phaseAlarm: false,
}

describe('CompensationCircuitDrawer', () => {
  it('渲染回路标题与当前状态', () => {
    const wrapper = mount(CompensationCircuitDrawer, {
      props: { circuit, canControl: true, events: [] },
    })
    expect(wrapper.text()).toContain('A 相分补')
    expect(wrapper.text()).toContain('第 1 路')
    expect(wrapper.text()).toContain('投入运行')
  })

  it('无相关事件时显示空状态', () => {
    const wrapper = mount(CompensationCircuitDrawer, {
      props: { circuit, canControl: true, events: [] },
    })
    expect(wrapper.text()).toContain('暂无该回路的投切记录')
  })

  it('canControl 为 false 时操作按钮禁用', () => {
    const wrapper = mount(CompensationCircuitDrawer, {
      props: { circuit, canControl: false, events: [] },
    })
    const buttons = wrapper.findAll('[data-test="circuit-action"]')
    expect(buttons.every((b) => b.attributes('disabled') !== undefined)).toBe(true)
  })

  it('点击「立即切除」emit switch 含相位与动作', async () => {
    const wrapper = mount(CompensationCircuitDrawer, {
      props: { circuit, canControl: true, events: [] },
    })
    await wrapper.find('[data-test="circuit-action-off"]').trigger('click')
    expect(wrapper.emitted('switch')?.[0]?.[0]).toEqual({
      phase: 'A',
      commonGroup: null,
      action: 'off',
    })
  })

  it('点击遮罩 emit close', async () => {
    const wrapper = mount(CompensationCircuitDrawer, {
      props: { circuit, canControl: true, events: [] },
    })
    await wrapper.find('[data-test="drawer-mask"]').trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd frontend && npx vitest run src/features/device-monitor/components/compensation/runtime/__tests__/CompensationCircuitDrawer.test.ts`
Expected: FAIL，找不到组件文件。

- [ ] **Step 3: 创建组件**

创建 `runtime/CompensationCircuitDrawer.vue`。`events` 是与该回路相关的 `CompensationEventItem` 列表（由父组件过滤）：

```vue
<script setup lang="ts">
import { computed } from 'vue'
import type { PropType } from 'vue'
import type { CompensationCircuitPick } from '../types'
import type { CompensationEventItem } from '../types'

const props = defineProps({
  circuit: {
    type: Object as PropType<CompensationCircuitPick>,
    required: true,
  },
  canControl: { type: Boolean, default: false },
  events: {
    type: Array as PropType<CompensationEventItem[]>,
    default: () => [],
  },
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'switch', payload: { phase: 'A' | 'B' | 'C' | 'COMMON'; commonGroup: 1 | 2 | 3 | null; action: 'on' | 'off' }): void
}>()

const stateText = computed(() => {
  if (props.circuit.state === 'on') return '投入运行'
  if (props.circuit.state === 'off') return '已切除'
  return '未配置'
})

const stateClass = computed(() => `state-${props.circuit.state}`)

const switchScopeHint = computed(() =>
  props.circuit.phase === 'COMMON'
    ? '投切指令作用于整个公补组'
    : '投切指令作用于整相回路',
)

function doSwitch(action: 'on' | 'off') {
  if (!props.canControl) return
  emit('switch', {
    phase: props.circuit.phase,
    commonGroup: props.circuit.commonGroup,
    action,
  })
}
</script>

<template>
  <div class="drawer-mask" data-test="drawer-mask" @click="emit('close')">
    <aside class="drawer" @click.stop>
      <header class="drawer-head">
        <div>
          <div class="drawer-title">{{ circuit.groupLabel }} · 第 {{ circuit.index }} 路</div>
          <div class="drawer-sub">
            状态：<span :class="stateClass">{{ stateText }}</span>
          </div>
        </div>
        <button type="button" class="drawer-close" @click="emit('close')">✕</button>
      </header>

      <section class="drawer-section">
        <h3>当前参数</h3>
        <div class="drawer-grid">
          <div><span class="k">所属相</span><span class="v">{{ circuit.phase === 'COMMON' ? '公补' : `${circuit.phase} 相` }}</span></div>
          <div><span class="k">回路序号</span><span class="v">第 {{ circuit.index }} 路</span></div>
          <div><span class="k">投切状态</span><span class="v" :class="stateClass">{{ stateText }}</span></div>
          <div><span class="k">相级告警</span><span class="v">{{ circuit.phaseAlarm ? '存在' : '无' }}</span></div>
        </div>
      </section>

      <section class="drawer-section">
        <h3>投切动作历史</h3>
        <div v-if="events.length === 0" class="drawer-empty">暂无该回路的投切记录</div>
        <ul v-else class="drawer-events">
          <li v-for="(ev, i) in events" :key="i">
            <span class="ev-time">{{ ev.time }}</span>
            <span class="ev-title">{{ ev.title }}</span>
          </li>
        </ul>
      </section>

      <section class="drawer-section">
        <h3>操作</h3>
        <p class="drawer-scope-hint">{{ switchScopeHint }}</p>
        <div class="drawer-actions">
          <button
            type="button"
            class="drawer-btn primary"
            data-test="circuit-action circuit-action-on"
            :disabled="!canControl"
            @click="doSwitch('on')"
          >立即投入</button>
          <button
            type="button"
            class="drawer-btn"
            data-test="circuit-action circuit-action-off"
            :disabled="!canControl"
            @click="doSwitch('off')"
          >立即切除</button>
        </div>
        <p v-if="!canControl" class="drawer-deny">当前无远程控制权限或设备不可投切</p>
      </section>
    </aside>
  </div>
</template>

<style scoped>
.drawer-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 2000;
  display: flex;
  justify-content: flex-end;
}
.drawer {
  width: 380px;
  max-width: 92vw;
  height: 100%;
  background: #0b1623;
  border-left: 1px solid #1f2c41;
  overflow-y: auto;
}
.drawer-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 16px 18px;
  border-bottom: 1px solid #1f2c41;
}
.drawer-title {
  font-size: 15px;
  font-weight: 600;
  color: #e5edf7;
}
.drawer-sub {
  font-size: 11px;
  color: #5e6c83;
  margin-top: 2px;
}
.drawer-close {
  width: 26px;
  height: 26px;
  border-radius: 6px;
  background: #121d2e;
  border: 1px solid #1f2c41;
  color: #9aa7bd;
  cursor: pointer;
}
.drawer-section {
  padding: 16px 18px;
  border-bottom: 1px solid #1f2c41;
}
.drawer-section h3 {
  margin: 0 0 10px;
  font-size: 12px;
  color: #9aa7bd;
  font-weight: 600;
}
.drawer-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px 14px;
}
.drawer-grid .k {
  display: block;
  font-size: 11px;
  color: #5e6c83;
}
.drawer-grid .v {
  font-size: 13px;
  color: #e5edf7;
}
.state-on { color: #34d399; }
.state-off { color: #9aa7bd; }
.state-unconfigured { color: #5e6c83; }
.drawer-empty {
  font-size: 12px;
  color: #5e6c83;
}
.drawer-events {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.drawer-events li {
  display: flex;
  gap: 10px;
  font-size: 12px;
}
.ev-time {
  color: #5e6c83;
  font-variant-numeric: tabular-nums;
}
.ev-title {
  color: #e5edf7;
}
.drawer-scope-hint {
  margin: 0 0 8px;
  font-size: 11px;
  color: #f59e0b;
}
.drawer-actions {
  display: flex;
  gap: 10px;
}
.drawer-btn {
  flex: 1;
  height: 34px;
  border-radius: 7px;
  background: #182538;
  border: 1px solid #2a3a55;
  color: #e5edf7;
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}
.drawer-btn.primary {
  background: linear-gradient(180deg, #0891b2, #155e75);
  border-color: #0891b2;
  color: #ecfeff;
}
.drawer-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.drawer-deny {
  margin: 8px 0 0;
  font-size: 11px;
  color: #5e6c83;
}
</style>
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd frontend && npx vitest run src/features/device-monitor/components/compensation/runtime/__tests__/CompensationCircuitDrawer.test.ts`
Expected: PASS（5 个用例）。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/device-monitor/components/compensation/runtime/CompensationCircuitDrawer.vue frontend/src/features/device-monitor/components/compensation/runtime/__tests__/CompensationCircuitDrawer.test.ts
git commit -m "feat(compensation): add circuit detail drawer for runtime monitor"
```

---

## Task 9: CompensationPhaseMatrix 组件

三相状态矩阵表：指标行 × A/B/C/系统列。

**Files:**
- Create: `frontend/src/features/device-monitor/components/compensation/runtime/CompensationPhaseMatrix.vue`
- Test: `frontend/src/features/device-monitor/components/compensation/runtime/__tests__/CompensationPhaseMatrix.test.ts`

- [ ] **Step 1: 写失败测试**

创建 `runtime/__tests__/CompensationPhaseMatrix.test.ts`：

```typescript
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import CompensationPhaseMatrix from '../CompensationPhaseMatrix.vue'
import type { CompensationCapacitorBankTelemetry } from '@/api/compensation'

function telemetry(overrides: Partial<CompensationCapacitorBankTelemetry> = {}): CompensationCapacitorBankTelemetry {
  return {
    device_id: 1,
    timestamp: '2026-05-19T10:00:00+08:00',
    current_a: 12, current_b: 12, current_c: 12,
    voltage_thd_a: 1.2, voltage_thd_b: 1.4, voltage_thd_c: 1.1,
    current_harmonic_a: 2, current_harmonic_b: 2, current_harmonic_c: 2,
    ...overrides,
  } as CompensationCapacitorBankTelemetry
}

describe('CompensationPhaseMatrix', () => {
  it('渲染指标行与 A/B/C/系统 列', () => {
    const wrapper = mount(CompensationPhaseMatrix, { props: { telemetry: telemetry() } })
    expect(wrapper.text()).toContain('V-THD 谐波')
    expect(wrapper.text()).toContain('A 相')
    expect(wrapper.text()).toContain('系统')
  })

  it('V-THD 超限单元格标记为超限态', () => {
    const wrapper = mount(CompensationPhaseMatrix, {
      props: { telemetry: telemetry({ voltage_thd_a: 27 }) },
    })
    expect(wrapper.find('.matrix-cell.is-crit').exists()).toBe(true)
  })

  it('遥测缺失时单元格显示占位符', () => {
    const wrapper = mount(CompensationPhaseMatrix, { props: { telemetry: null } })
    expect(wrapper.text()).toContain('--')
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd frontend && npx vitest run src/features/device-monitor/components/compensation/runtime/__tests__/CompensationPhaseMatrix.test.ts`
Expected: FAIL，找不到组件文件。

- [ ] **Step 3: 创建组件**

创建 `runtime/CompensationPhaseMatrix.vue`：

```vue
<script setup lang="ts">
import { computed } from 'vue'
import type { PropType } from 'vue'
import type { CompensationCapacitorBankTelemetry } from '@/api/compensation'

type CellSeverity = 'ok' | 'warn' | 'crit' | 'na'

interface MatrixCell {
  text: string
  severity: CellSeverity
}

interface MatrixRow {
  label: string
  cells: MatrixCell[]
  system: MatrixCell
}

const props = defineProps({
  telemetry: {
    type: Object as PropType<CompensationCapacitorBankTelemetry | null>,
    default: null,
  },
})

const VOLTAGE_THD_THRESHOLD = 5
const CURRENT_THD_THRESHOLD = 5
const TEMP_THRESHOLD = 55

function num(value: number | null | undefined): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

function valueCell(value: number | null, unit: string, threshold: number | null, digits = 1): MatrixCell {
  if (value === null) return { text: '--', severity: 'na' }
  let severity: CellSeverity = 'ok'
  if (threshold !== null) {
    if (value > threshold) severity = 'crit'
    else if (value > threshold * 0.8) severity = 'warn'
  }
  return { text: `${value.toFixed(digits)}${unit}`, severity }
}

function systemCell(cells: MatrixCell[]): MatrixCell {
  if (cells.every((c) => c.severity === 'na')) return { text: '--', severity: 'na' }
  if (cells.some((c) => c.severity === 'crit')) return { text: '超限', severity: 'crit' }
  if (cells.some((c) => c.severity === 'warn')) return { text: '异常', severity: 'warn' }
  return { text: '正常', severity: 'ok' }
}

const rows = computed<MatrixRow[]>(() => {
  const t = props.telemetry
  const definitions: Array<{ label: string; unit: string; threshold: number | null; values: Array<number | null> }> = [
    {
      label: '电流幅值',
      unit: ' A',
      threshold: null,
      values: [num(t?.current_a), num(t?.current_b), num(t?.current_c)],
    },
    {
      label: 'V-THD 谐波',
      unit: '%',
      threshold: VOLTAGE_THD_THRESHOLD,
      values: [num(t?.voltage_thd_a), num(t?.voltage_thd_b), num(t?.voltage_thd_c)],
    },
    {
      label: 'I-THD 谐波',
      unit: '%',
      threshold: CURRENT_THD_THRESHOLD,
      values: [num(t?.current_harmonic_a), num(t?.current_harmonic_b), num(t?.current_harmonic_c)],
    },
  ]
  const result = definitions.map((def) => {
    const cells = def.values.map((v) => valueCell(v, def.unit, def.threshold))
    return { label: def.label, cells, system: systemCell(cells) }
  })

  // 柜内温度：单值，铺到系统列
  const temp = num(t?.temperature)
  const tempCell = valueCell(temp, ' °C', TEMP_THRESHOLD, 0)
  result.push({
    label: '柜内温度',
    cells: [
      { text: '—', severity: 'na' },
      { text: '—', severity: 'na' },
      { text: '—', severity: 'na' },
    ],
    system: tempCell,
  })
  return result
})

const alarmCount = computed(() =>
  rows.value.reduce((sum, row) => {
    const cellCount = row.cells.filter((c) => c.severity === 'crit' || c.severity === 'warn').length
    const sysCount = row.system.severity === 'crit' || row.system.severity === 'warn' ? 1 : 0
    return sum + cellCount + sysCount
  }, 0),
)
</script>

<template>
  <section class="matrix-card">
    <header class="rt-card-head">
      <span class="rt-card-title"><span class="rt-accent" />三相状态总览</span>
      <span class="matrix-meta">{{ alarmCount }} 项关注</span>
    </header>
    <div class="matrix-body">
      <table class="matrix">
        <thead>
          <tr>
            <th class="matrix-row-head">指标</th>
            <th>A 相</th>
            <th>B 相</th>
            <th>C 相</th>
            <th>系统</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.label">
            <td class="matrix-row-head">{{ row.label }}</td>
            <td v-for="(cell, i) in row.cells" :key="i">
              <span class="matrix-cell" :class="`is-${cell.severity}`">{{ cell.text }}</span>
            </td>
            <td>
              <span class="matrix-cell" :class="`is-${row.system.severity}`">{{ row.system.text }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped>
.matrix-card {
  display: flex;
  flex-direction: column;
  background: #121d2e;
  border: 1px solid #1f2c41;
  border-radius: 10px;
  min-height: 0;
}
.rt-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 14px;
  border-bottom: 1px solid #1f2c41;
}
.rt-card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #e5edf7;
}
.rt-accent {
  width: 3px;
  height: 12px;
  border-radius: 2px;
  background: #22d3ee;
}
.matrix-meta {
  font-size: 11px;
  color: #5e6c83;
}
.matrix-body {
  padding: 6px 14px 10px;
  flex: 1;
  min-height: 0;
}
.matrix {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}
.matrix th,
.matrix td {
  text-align: center;
  padding: 5px 4px;
  font-size: 11px;
  color: #9aa7bd;
  border-bottom: 1px solid #1f2c41;
}
.matrix th {
  color: #5e6c83;
  font-size: 10px;
  font-weight: 400;
}
.matrix tr:last-child td {
  border-bottom: none;
}
.matrix-row-head {
  text-align: left !important;
  color: #9aa7bd;
}
.matrix-cell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
  height: 20px;
  padding: 0 6px;
  border-radius: 5px;
  font-size: 10px;
  border: 1px solid #1f2c41;
  background: #0b1623;
  color: #5e6c83;
}
.matrix-cell.is-ok {
  color: #6ee7b7;
  border-color: rgba(52, 211, 153, 0.25);
  background: rgba(52, 211, 153, 0.06);
}
.matrix-cell.is-warn {
  color: #fcd34d;
  border-color: rgba(245, 158, 11, 0.4);
  background: rgba(245, 158, 11, 0.1);
}
.matrix-cell.is-crit {
  color: #fda4af;
  border-color: rgba(239, 68, 68, 0.4);
  background: rgba(239, 68, 68, 0.12);
}
.matrix-cell.is-na {
  opacity: 0.5;
}
</style>
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd frontend && npx vitest run src/features/device-monitor/components/compensation/runtime/__tests__/CompensationPhaseMatrix.test.ts`
Expected: PASS（3 个用例）。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/device-monitor/components/compensation/runtime/CompensationPhaseMatrix.vue frontend/src/features/device-monitor/components/compensation/runtime/__tests__/CompensationPhaseMatrix.test.ts
git commit -m "feat(compensation): add three-phase status matrix for runtime monitor"
```

---

## Task 10: CompensationAlarmRail 与 CompensationParamSummary 侧栏组件

**Files:**
- Create: `frontend/src/features/device-monitor/components/compensation/runtime/CompensationAlarmRail.vue`
- Create: `frontend/src/features/device-monitor/components/compensation/runtime/CompensationParamSummary.vue`
- Test: `frontend/src/features/device-monitor/components/compensation/runtime/__tests__/CompensationAlarmRail.test.ts`
- Test: `frontend/src/features/device-monitor/components/compensation/runtime/__tests__/CompensationParamSummary.test.ts`

- [ ] **Step 1: 写失败测试（告警栏）**

创建 `runtime/__tests__/CompensationAlarmRail.test.ts`：

```typescript
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import CompensationAlarmRail from '../CompensationAlarmRail.vue'
import type { DeviceAlarmRecord } from '@/api/deviceMonitor'

function makeAlarm(id: number, isResolved = false): DeviceAlarmRecord {
  return {
    id,
    device_id: 1,
    message: `告警 ${id}`,
    severity: id === 1 ? 'critical' : 'warning',
    timestamp: `2026-05-19T12:${String(id).padStart(2, '0')}:00+08:00`,
    is_resolved: isResolved,
  }
}

describe('CompensationAlarmRail', () => {
  it('只渲染未处理告警并显示数量', () => {
    const wrapper = mount(CompensationAlarmRail, {
      props: { rows: [makeAlarm(1), makeAlarm(2), makeAlarm(3, true)], actionId: null },
    })
    expect(wrapper.text()).toContain('未处理告警')
    expect(wrapper.text()).toContain('2 待处理')
    expect(wrapper.findAll('[data-test="alarm-rail-item"]')).toHaveLength(2)
  })

  it('点击处理按钮 emit resolve', async () => {
    const wrapper = mount(CompensationAlarmRail, {
      props: { rows: [makeAlarm(1)], actionId: null },
    })
    await wrapper.find('[data-test="alarm-resolve"]').trigger('click')
    expect(wrapper.emitted('resolve')?.[0]?.[0]).toEqual(expect.objectContaining({ id: 1 }))
  })

  it('无未处理告警时显示空状态', () => {
    const wrapper = mount(CompensationAlarmRail, {
      props: { rows: [makeAlarm(1, true)], actionId: null },
    })
    expect(wrapper.text()).toContain('暂无未处理告警')
  })
})
```

- [ ] **Step 2: 写失败测试（参数摘要）**

创建 `runtime/__tests__/CompensationParamSummary.test.ts`：

```typescript
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import CompensationParamSummary from '../CompensationParamSummary.vue'

describe('CompensationParamSummary', () => {
  it('渲染参数键值对', () => {
    const wrapper = mount(CompensationParamSummary, {
      props: {
        items: [
          { label: '目标 PF', value: '0.98（滞后）' },
          { label: '投切延时', value: '30 s' },
        ],
      },
    })
    expect(wrapper.text()).toContain('控制参数')
    expect(wrapper.text()).toContain('目标 PF')
    expect(wrapper.text()).toContain('0.98（滞后）')
  })

  it('点击「修改」emit edit', async () => {
    const wrapper = mount(CompensationParamSummary, {
      props: { items: [] },
    })
    await wrapper.find('[data-test="param-edit"]').trigger('click')
    expect(wrapper.emitted('edit')).toBeTruthy()
  })

  it('无参数时显示空状态', () => {
    const wrapper = mount(CompensationParamSummary, { props: { items: [] } })
    expect(wrapper.text()).toContain('暂无控制参数')
  })
})
```

- [ ] **Step 3: 运行测试确认失败**

Run: `cd frontend && npx vitest run src/features/device-monitor/components/compensation/runtime/__tests__/CompensationAlarmRail.test.ts src/features/device-monitor/components/compensation/runtime/__tests__/CompensationParamSummary.test.ts`
Expected: FAIL，找不到组件文件。

- [ ] **Step 4: 创建 CompensationAlarmRail.vue**

`DeviceAlarmRecord` 含 `id / device_id / message / severity / timestamp / is_resolved`。`severity` 为 `'critical' | 'warning' | 'info'` 等字符串。

```vue
<script setup lang="ts">
import { computed } from 'vue'
import type { PropType } from 'vue'
import type { DeviceAlarmRecord } from '@/api/deviceMonitor'

const props = defineProps({
  rows: { type: Array as PropType<DeviceAlarmRecord[]>, default: () => [] },
  actionId: { type: Number as PropType<number | null>, default: null },
})

const emit = defineEmits<{ (e: 'resolve', row: DeviceAlarmRecord): void }>()

const unresolved = computed(() => props.rows.filter((r) => !r.is_resolved))

function sevClass(severity: string): string {
  if (severity === 'critical') return 'crit'
  if (severity === 'warning') return 'warn'
  return 'info'
}

function sevLabel(severity: string): string {
  if (severity === 'critical') return '严重'
  if (severity === 'warning') return '警告'
  return '提示'
}

function timeText(timestamp: string): string {
  const date = new Date(timestamp)
  if (Number.isNaN(date.getTime())) return '--:--'
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}
</script>

<template>
  <section class="rail-card">
    <header class="rt-card-head">
      <span class="rt-card-title"><span class="rt-accent" />未处理告警</span>
      <span class="rail-count">{{ unresolved.length }} 待处理</span>
    </header>
    <div class="rail-body">
      <div v-if="unresolved.length === 0" class="rail-empty">暂无未处理告警</div>
      <div
        v-for="alarm in unresolved"
        :key="alarm.id"
        class="rail-item"
        data-test="alarm-rail-item"
      >
        <span class="rail-sev" :class="sevClass(alarm.severity)" />
        <div class="rail-content">
          <div class="rail-row">
            <span class="rail-title">{{ alarm.message }}</span>
            <span class="rail-time">{{ timeText(alarm.timestamp) }}</span>
          </div>
          <div class="rail-foot">
            <span class="rail-tag" :class="sevClass(alarm.severity)">{{ sevLabel(alarm.severity) }}</span>
            <button
              type="button"
              class="rail-resolve"
              data-test="alarm-resolve"
              :disabled="actionId === alarm.id"
              @click="emit('resolve', alarm)"
            >{{ actionId === alarm.id ? '处理中…' : '处理' }}</button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.rail-card {
  display: flex;
  flex-direction: column;
  background: #121d2e;
  border: 1px solid #1f2c41;
  border-radius: 10px;
  min-height: 0;
  flex: 1;
}
.rt-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 14px;
  border-bottom: 1px solid #1f2c41;
}
.rt-card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #e5edf7;
}
.rt-accent {
  width: 3px;
  height: 12px;
  border-radius: 2px;
  background: #22d3ee;
}
.rail-count {
  font-size: 10px;
  padding: 1px 7px;
  border-radius: 999px;
  background: rgba(245, 158, 11, 0.16);
  color: #f59e0b;
}
.rail-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}
.rail-empty {
  padding: 18px 14px;
  text-align: center;
  font-size: 12px;
  color: #5e6c83;
}
.rail-item {
  display: flex;
  gap: 9px;
  padding: 9px 14px;
  border-bottom: 1px solid #1f2c41;
}
.rail-sev {
  width: 3px;
  border-radius: 2px;
  flex-shrink: 0;
}
.rail-sev.crit { background: #ef4444; }
.rail-sev.warn { background: #f59e0b; }
.rail-sev.info { background: #22d3ee; }
.rail-content {
  flex: 1;
  min-width: 0;
}
.rail-row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}
.rail-title {
  font-size: 11px;
  color: #e5edf7;
  font-weight: 500;
}
.rail-time {
  font-size: 10px;
  color: #5e6c83;
  font-variant-numeric: tabular-nums;
}
.rail-foot {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}
.rail-tag {
  font-size: 9px;
  padding: 1px 5px;
  border-radius: 3px;
}
.rail-tag.crit { background: rgba(239, 68, 68, 0.15); color: #fda4af; }
.rail-tag.warn { background: rgba(245, 158, 11, 0.15); color: #f59e0b; }
.rail-tag.info { background: rgba(34, 211, 238, 0.15); color: #67e8f9; }
.rail-resolve {
  margin-left: auto;
  padding: 2px 9px;
  border-radius: 5px;
  background: #182538;
  border: 1px solid #2a3a55;
  color: #9aa7bd;
  font: inherit;
  font-size: 10px;
  cursor: pointer;
}
.rail-resolve:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
```

- [ ] **Step 5: 创建 CompensationParamSummary.vue**

```vue
<script setup lang="ts">
import type { PropType } from 'vue'

interface ParamItem {
  label: string
  value: string
}

defineProps({
  items: { type: Array as PropType<ParamItem[]>, default: () => [] },
})

const emit = defineEmits<{ (e: 'edit'): void }>()
</script>

<template>
  <section class="param-card">
    <header class="rt-card-head">
      <span class="rt-card-title"><span class="rt-accent" />控制参数</span>
      <button type="button" class="param-edit" data-test="param-edit" @click="emit('edit')">
        修改 →
      </button>
    </header>
    <div class="param-body">
      <div v-if="items.length === 0" class="param-empty">暂无控制参数</div>
      <div v-for="item in items" :key="item.label" class="param-row">
        <span class="param-k">{{ item.label }}</span>
        <span class="param-v">{{ item.value }}</span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.param-card {
  display: flex;
  flex-direction: column;
  background: #121d2e;
  border: 1px solid #1f2c41;
  border-radius: 10px;
}
.rt-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 14px;
  border-bottom: 1px solid #1f2c41;
}
.rt-card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #e5edf7;
}
.rt-accent {
  width: 3px;
  height: 12px;
  border-radius: 2px;
  background: #22d3ee;
}
.param-edit {
  background: transparent;
  border: none;
  color: #67e8f9;
  font: inherit;
  font-size: 11px;
  cursor: pointer;
}
.param-body {
  padding: 9px 14px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.param-empty {
  font-size: 12px;
  color: #5e6c83;
  text-align: center;
  padding: 8px 0;
}
.param-row {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
}
.param-k {
  color: #5e6c83;
}
.param-v {
  color: #e5edf7;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}
</style>
```

- [ ] **Step 6: 运行测试确认通过**

Run: `cd frontend && npx vitest run src/features/device-monitor/components/compensation/runtime/__tests__/CompensationAlarmRail.test.ts src/features/device-monitor/components/compensation/runtime/__tests__/CompensationParamSummary.test.ts`
Expected: PASS（6 个用例）。

- [ ] **Step 7: Commit**

```bash
git add frontend/src/features/device-monitor/components/compensation/runtime/CompensationAlarmRail.vue frontend/src/features/device-monitor/components/compensation/runtime/CompensationParamSummary.vue frontend/src/features/device-monitor/components/compensation/runtime/__tests__/CompensationAlarmRail.test.ts frontend/src/features/device-monitor/components/compensation/runtime/__tests__/CompensationParamSummary.test.ts
git commit -m "feat(compensation): add alarm rail and param summary side panels"
```

---

## Task 11: CompensationRuntimeBoard 容器组件

组合 Hero 行 / 拓扑行 / 底部行，并持有回路抽屉选中态；远程控制复用现有 `ControlConsoleRemotePanel`。

**Files:**
- Create: `frontend/src/features/device-monitor/components/compensation/runtime/CompensationRuntimeBoard.vue`
- Test: `frontend/src/features/device-monitor/components/compensation/runtime/__tests__/CompensationRuntimeBoard.test.ts`

- [ ] **Step 1: 写失败测试**

创建 `runtime/__tests__/CompensationRuntimeBoard.test.ts`。容器以 `page` 对象为唯一 prop，测试用最小桩对象 + 子组件全 stub：

```typescript
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import CompensationRuntimeBoard from '../CompensationRuntimeBoard.vue'

function makePage(overrides: Record<string, unknown> = {}) {
  return {
    realtime: { power_factor: 0.975, flow_rate: 168, reactive_power: 38 },
    compensationPowerFactorTrend: { values: [0.96, 0.97], timestamps: [], target: 0.95 },
    compensationPqPoint: { p: 168, q: 38 },
    compensationPqHistory: [],
    compensationHealthModel: { score: 78, rating: '良好', ratingTone: 'success', breakdown: [] },
    compensationCapacitorBankTelemetry: null,
    compensationCircuitProfile: {},
    compensationEvents: [],
    alarms: [],
    alarmActionId: null,
    capacitorBankControlSummaryView: { summaryItems: [], capacityExpansionItems: [], hasSummaryData: false },
    controlConsoleActionCards: [],
    controlConsoleToggleSubmitting: false,
    controlConsoleCurrentControlModeLabel: '自动',
    controlConsoleCanRunManualSwitch: true,
    controlConsoleManualSwitchDisabledReason: '',
    controlConsoleManualPhaseOptions: [],
    controlConsoleManualSwitchActionOptions: [],
    controlConsoleManualCommonGroupOptions: [],
    controlConsoleManualSwitchForm: { phase: 'A', switch_action: 'none', group: 1 },
    controlConsoleLoadError: '',
    canControlDevices: true,
    isPendingArchiveDevice: false,
    timeRange: null,
    handleResolveAlarm: () => {},
    handleControlConsoleManualSwitchCommand: () => {},
    handleControlConsoleActionCard: () => {},
    handleRangeChange: () => {},
    ...overrides,
  }
}

function mountBoard(page: Record<string, unknown>) {
  return mount(CompensationRuntimeBoard, {
    props: { page },
    global: {
      stubs: {
        CompensationPfTrendCard: true,
        CompensationPqQuadrantCard: true,
        CompensationHealthCard: true,
        CompensationBankTopology: true,
        CompensationPhaseMatrix: true,
        CompensationCircuitDrawer: true,
        ControlConsoleRemotePanel: true,
        MonitorInlineAlert: true,
      },
    },
  })
}

describe('CompensationRuntimeBoard', () => {
  it('渲染 hero / topology / bottom 三段', () => {
    const wrapper = mountBoard(makePage())
    expect(wrapper.find('.rt-hero').exists()).toBe(true)
    expect(wrapper.find('.rt-topology').exists()).toBe(true)
    expect(wrapper.find('.rt-bottom').exists()).toBe(true)
  })

  it('未选中回路时不渲染抽屉', () => {
    const wrapper = mountBoard(makePage())
    expect(wrapper.findComponent({ name: 'CompensationCircuitDrawer' }).exists()).toBe(false)
  })

  it('拓扑 emit pick 后渲染抽屉', async () => {
    const wrapper = mountBoard(makePage())
    await wrapper.findComponent({ name: 'CompensationBankTopology' }).vm.$emit('pick', {
      groupLabel: 'A 相分补',
      phase: 'A',
      commonGroup: null,
      index: 1,
      state: 'on',
      phaseAlarm: false,
    })
    expect(wrapper.findComponent({ name: 'CompensationCircuitDrawer' }).exists()).toBe(true)
  })

  it('控制台加载错误时显示告警而非远程控制面板', () => {
    const wrapper = mountBoard(makePage({ controlConsoleLoadError: '控制台不可用' }))
    expect(wrapper.findComponent({ name: 'ControlConsoleRemotePanel' }).exists()).toBe(false)
    expect(wrapper.findComponent({ name: 'MonitorInlineAlert' }).exists()).toBe(true)
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd frontend && npx vitest run src/features/device-monitor/components/compensation/runtime/__tests__/CompensationRuntimeBoard.test.ts`
Expected: FAIL，找不到组件文件。

- [ ] **Step 3: 创建容器组件**

创建 `runtime/CompensationRuntimeBoard.vue`。注意 `timeRange` 是 `[Date, Date] | null`，由其跨度推出 `10m/1h/24h` 的近似标签键；时间范围切换调用 `page.handleRangeChange` 前先把 `page.timeRange` 改成对应跨度的 `[start, now]`。

```vue
<script setup lang="ts">
import { computed, ref } from 'vue'
import type { PropType } from 'vue'
import ControlConsoleRemotePanel from '@/features/device-control/components/ControlConsoleRemotePanel.vue'
import MonitorInlineAlert from '@/shared/components/MonitorInlineAlert.vue'
import type { DeviceMonitorPageModel } from '@/features/device-monitor/composables/useDeviceMonitorPage'
import type { CompensationCircuitPick } from '../types'
import CompensationPfTrendCard from './CompensationPfTrendCard.vue'
import CompensationPqQuadrantCard from './CompensationPqQuadrantCard.vue'
import CompensationHealthCard from './CompensationHealthCard.vue'
import CompensationBankTopology from './CompensationBankTopology.vue'
import CompensationPhaseMatrix from './CompensationPhaseMatrix.vue'
import CompensationCircuitDrawer from './CompensationCircuitDrawer.vue'

const props = defineProps({
  page: {
    type: Object as PropType<DeviceMonitorPageModel>,
    required: true,
  },
})

const pickedCircuit = ref<CompensationCircuitPick | null>(null)

const RANGE_MS: Record<'10m' | '1h' | '24h', number> = {
  '10m': 10 * 60 * 1000,
  '1h': 60 * 60 * 1000,
  '24h': 24 * 60 * 60 * 1000,
}

const timeRangeKey = computed<'10m' | '1h' | '24h'>(() => {
  const range = props.page.timeRange
  if (!range) return '1h'
  const span = range[1].getTime() - range[0].getTime()
  if (span <= RANGE_MS['10m'] * 1.5) return '10m'
  if (span >= RANGE_MS['24h'] * 0.75) return '24h'
  return '1h'
})

function handleRangeChange(key: '10m' | '1h' | '24h') {
  const now = new Date()
  props.page.timeRange = [new Date(now.getTime() - RANGE_MS[key]), now]
  void props.page.handleRangeChange()
}

const circuitEvents = computed(() => {
  if (!pickedCircuit.value) return []
  const phaseToken = pickedCircuit.value.phase === 'COMMON' ? '公补' : `${pickedCircuit.value.phase} 相`
  return props.page.compensationEvents.filter(
    (ev) => !ev.isMock && (ev.title.includes(phaseToken) || ev.detail.includes(phaseToken)),
  )
})

function handleCircuitSwitch(payload: {
  phase: 'A' | 'B' | 'C' | 'COMMON'
  commonGroup: 1 | 2 | 3 | null
  action: 'on' | 'off'
}) {
  if (!props.page.controlConsoleCanRunManualSwitch) return
  props.page.controlConsoleManualSwitchForm.phase = payload.phase
  props.page.controlConsoleManualSwitchForm.switch_action = payload.action
  if (payload.phase === 'COMMON' && payload.commonGroup) {
    props.page.controlConsoleManualSwitchForm.group = payload.commonGroup
  }
  void props.page.handleControlConsoleManualSwitchCommand()
  pickedCircuit.value = null
}
</script>

<template>
  <div class="runtime-board">
    <div class="rt-hero">
      <CompensationPfTrendCard
        :pf="page.realtime?.power_factor ?? null"
        :p="page.compensationPqPoint.p"
        :q="page.compensationPqPoint.q"
        :pf-trend="page.compensationPowerFactorTrend"
        :time-range-key="timeRangeKey"
        @range-change="handleRangeChange"
      />
      <CompensationPqQuadrantCard
        :point="page.compensationPqPoint"
        :history="page.compensationPqHistory"
      />
      <CompensationHealthCard :model="page.compensationHealthModel" />
    </div>

    <div class="rt-topology">
      <CompensationBankTopology
        :telemetry="page.compensationCapacitorBankTelemetry"
        :circuit-profile="page.compensationCircuitProfile"
        @pick="pickedCircuit = $event"
      />
    </div>

    <div class="rt-bottom">
      <CompensationPhaseMatrix :telemetry="page.compensationCapacitorBankTelemetry" />

      <MonitorInlineAlert
        v-if="page.controlConsoleLoadError"
        title="远程控制暂不可用"
        :message="page.controlConsoleLoadError"
        tone="danger"
      />
      <ControlConsoleRemotePanel
        v-else
        :action-cards="page.controlConsoleActionCards"
        :toggle-submitting="page.controlConsoleToggleSubmitting"
        :current-control-mode-label="page.controlConsoleCurrentControlModeLabel"
        :can-run-manual-switch="page.controlConsoleCanRunManualSwitch"
        :manual-switch-disabled-reason="page.controlConsoleManualSwitchDisabledReason"
        :manual-phase-options="page.controlConsoleManualPhaseOptions"
        :manual-switch-action-options="page.controlConsoleManualSwitchActionOptions"
        :manual-common-group-options="page.controlConsoleManualCommonGroupOptions"
        :manual-phase="page.controlConsoleManualSwitchForm.phase"
        :manual-switch-action="page.controlConsoleManualSwitchForm.switch_action"
        :manual-common-group="page.controlConsoleManualSwitchForm.group"
        @action-card="page.handleControlConsoleActionCard"
        @update:manual-phase="page.controlConsoleManualSwitchForm.phase = $event"
        @update:manual-switch-action="page.controlConsoleManualSwitchForm.switch_action = $event"
        @update:manual-common-group="page.controlConsoleManualSwitchForm.group = $event"
        @manual-switch="page.handleControlConsoleManualSwitchCommand"
      />
    </div>

    <CompensationCircuitDrawer
      v-if="pickedCircuit"
      :circuit="pickedCircuit"
      :can-control="page.controlConsoleCanRunManualSwitch && !page.isPendingArchiveDevice"
      :events="circuitEvents"
      @close="pickedCircuit = null"
      @switch="handleCircuitSwitch"
    />
  </div>
</template>

<style scoped>
.runtime-board {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}
.rt-hero {
  display: grid;
  grid-template-columns: 1fr 1.2fr 1fr;
  gap: 12px;
}
.rt-hero > * {
  min-height: 244px;
}
.rt-bottom {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 12px;
  align-items: start;
}
@media (max-width: 1280px) {
  .rt-hero {
    grid-template-columns: 1fr;
  }
  .rt-bottom {
    grid-template-columns: 1fr;
  }
}
</style>
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd frontend && npx vitest run src/features/device-monitor/components/compensation/runtime/__tests__/CompensationRuntimeBoard.test.ts`
Expected: PASS（4 个用例）。

- [ ] **Step 5: 类型检查**

Run: `cd frontend && npx vue-tsc --noEmit -p tsconfig.app.json 2>&1 | head -20`
Expected: 无新增错误。

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/device-monitor/components/compensation/runtime/CompensationRuntimeBoard.vue frontend/src/features/device-monitor/components/compensation/runtime/__tests__/CompensationRuntimeBoard.test.ts
git commit -m "feat(compensation): add runtime monitor board container"
```

---

## Task 12: 接入 CompensationMonitorView

把 `runtime` 分支换成 `CompensationRuntimeBoard`；`#side` 槽对 runtime 标签条件化渲染新侧栏。

**Files:**
- Modify: `frontend/src/features/device-monitor/views/CompensationMonitorView.vue`

- [ ] **Step 1: 替换 runtime 分支**

打开 `CompensationMonitorView.vue`。在 `<script setup>` 顶部 import 区，新增：

```typescript
import CompensationRuntimeBoard from '@/features/device-monitor/components/compensation/runtime/CompensationRuntimeBoard.vue'
import CompensationAlarmRail from '@/features/device-monitor/components/compensation/runtime/CompensationAlarmRail.vue'
import CompensationParamSummary from '@/features/device-monitor/components/compensation/runtime/CompensationParamSummary.vue'
```

在 `<script setup>` 内新增一个把控制摘要映射成参数键值对的 computed（放在 `shouldShowSideTraceability` 函数之后）：

```typescript
const runtimeParamItems = computed(() =>
  props.page.capacitorBankControlSummaryView.summaryItems.map((item) => ({
    label: item.label,
    value: item.value,
  })),
)

function isRuntimeTab() {
  return (
    props.page.compensationSubtype === 'capacitor_bank_controller'
    && props.page.compensationWorkbenchTab === 'runtime'
  )
}
```

确认 `<script setup>` 顶部已 import `computed`（若未 import，加 `import { computed } from 'vue'`）。

将模板中 `<template v-if="page.compensationWorkbenchTab === 'runtime'">` 内的全部内容（当前 99-148 行：`CompensationRealtimeOverview` + `CompensationDetailPanel` + `MonitorInlineAlert`/`ControlConsoleRemotePanel`）整体替换为：

```html
          <template v-if="page.compensationWorkbenchTab === 'runtime'">
            <CompensationRuntimeBoard :page="page" />
          </template>
```

- [ ] **Step 2: 条件化 #side 槽**

在 `#side` 模板（当前约 277-303 行）最外层包一个 runtime / 非 runtime 分支。把现有 `#side` 内容整体改为：

```html
    <template #side>
      <template v-if="isRuntimeTab()">
        <CompensationAlarmRail
          :rows="page.alarms"
          :action-id="page.alarmActionId"
          @resolve="page.handleResolveAlarm"
        />
        <CompensationParamSummary
          :items="runtimeParamItems"
          @edit="openParameterWorkbench"
        />
      </template>
      <template v-else>
        <CompensationEventTimeline
          v-if="shouldShowSideTraceability()"
          :events="page.compensationEvents"
        />
        <CompensationAlarmSummaryPanel
          :rows="page.alarms"
          :action-id="page.alarmActionId"
          @resolve="page.handleResolveAlarm"
        />
        <CompensationControlSummaryPanel
          v-if="page.compensationSubtype === 'capacitor_bank_controller'"
          :summary-items="page.capacitorBankControlSummaryView.summaryItems"
          :capacity-expansion-items="page.capacitorBankControlSummaryView.capacityExpansionItems"
          :has-summary-data="page.capacitorBankControlSummaryView.hasSummaryData"
          @open-console="openParameterWorkbench"
        />
        <CompensationDeviceProfile
          :items="page.compensationProfileItems"
          :editable="page.isSvgDevice && page.canControlDevices"
          @edit="page.svgProfileEditVisible = true"
        />
        <CompensationDiagnosticsCollapsible
          v-if="page.templateDiagnostics && shouldShowSideTraceability()"
          :diagnostics="page.templateDiagnostics"
        />
      </template>
    </template>
```

- [ ] **Step 3: 清理未使用的 import**

`runtime` 分支替换后，检查 `CompensationRealtimeOverview`、`CompensationDetailPanel`、`ControlConsoleRemotePanel`、`MonitorInlineAlert` 是否仍被本文件其它分支使用：
- `CompensationRealtimeOverview` / `CompensationDetailPanel`：仍被非工作台 `v-else` 分支（约 235-257 行）使用 → 保留 import。
- `ControlConsoleRemotePanel`：runtime 分支移除后本文件不再直接引用（已移入 `CompensationRuntimeBoard`）→ 删除其 import 行。
- `MonitorInlineAlert`：仍被 `parameter-settings` 分支使用 → 保留 import。

只删除确认无引用的 import 行。用 grep 复核：

Run: `cd frontend && grep -n "ControlConsoleRemotePanel\|CompensationRealtimeOverview\|CompensationDetailPanel\|MonitorInlineAlert" src/features/device-monitor/views/CompensationMonitorView.vue`
Expected: `ControlConsoleRemotePanel` 仅剩 0 处（import 已删）；其余仍有模板引用。

- [ ] **Step 4: 类型检查与全量测试**

Run: `cd frontend && npx vue-tsc --noEmit -p tsconfig.app.json 2>&1 | head -20`
Expected: 无新增错误。

Run: `cd frontend && npx vitest run src/features/device-monitor`
Expected: 全部 PASS。若 `views/__tests__/CompensationMonitorView.test.ts` 存在且断言了 runtime 分支旧组件（`CompensationRealtimeOverview` 等出现在 runtime 标签），更新这些断言为 `CompensationRuntimeBoard` 存在；非 runtime 标签断言不变。若该测试文件不存在则跳过。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/device-monitor/views/CompensationMonitorView.vue
git commit -m "feat(compensation): wire runtime board and redesigned side rail into monitor view"
```

---

## Task 13: 浏览器验证

**Files:** 无（手动 / 工具验证）

- [ ] **Step 1: 启动开发服务器并打开补偿设备监控页**

启动前端 dev server，导航到一个 `capacitor_bank_controller` 设备的监控页（路由形如 `/device-monitor/:id`，确保 URL `?tab=runtime` 或默认 runtime 标签）。

- [ ] **Step 2: 核对运行监视标签页**

确认：Hero 行三栏（PF 趋势 / P-Q 象限 / 健康度）等高并排；拓扑行 6 条母线渲染；底部行三相矩阵 + 远程控制并排；右侧栏为「未处理告警」+「控制参数」。检查控制台无报错。

- [ ] **Step 3: 核对交互**

点击拓扑任一已配置回路 → 右侧抽屉滑出；点击遮罩关闭。切换 PF 卡时间范围标签 → 趋势重新加载。切到「曲线分析 / 参数设置 / 事件记录」标签 → 侧栏恢复为原事件时间线 / 告警汇总等，主区为原内容。

- [ ] **Step 4: 核对降级**

若设备无实时遥测：P-Q 卡显示「等待实时遥测」；健康度缺测维显示「待采集」；矩阵单元格显示 `--`；拓扑回路显示未配置态。均不应出现示例 / mock 数值。

- [ ] **Step 5: 全量测试与构建**

Run: `cd frontend && npx vitest run && npx vue-tsc --noEmit -p tsconfig.app.json`
Expected: 测试全 PASS，类型检查无错误。

- [ ] **Step 6: Commit（如验证中有修复）**

若验证发现并修复了问题：

```bash
git add -A
git commit -m "fix(compensation): address runtime monitor verification findings"
```

若无修复则跳过本步。

---

## Self-Review

**Spec coverage:**
- 布局（Hero / 拓扑 / 底部 + runtime 侧栏）→ Task 11、12 ✓
- PF 趋势卡 → Task 4 ✓
- P-Q 象限卡 → Task 5 ✓
- 健康度卡 + 6 维派生 → Task 2、3、6 ✓
- 电容器组拓扑 → Task 7 ✓
- 三相矩阵 → Task 9 ✓
- 回路抽屉 → Task 8 ✓
- 告警栏 + 参数摘要 → Task 10 ✓
- 数据层（健康度模型、P-Q 点/轨迹）→ Task 2、3 ✓
- 降级（健康度待采集 / P-Q 空状态 / 拓扑 3 态 + 相级告警 / 矩阵 --）→ Task 6、5、7、9 各有测试用例 ✓
- 接入 CompensationMonitorView 且其它标签页不动 → Task 12 ✓
- 测试覆盖 → 各 Task 均含 ✓

**Placeholder scan:** 无 TBD / TODO；所有步骤含完整代码或精确命令。

**Type consistency:** `CompensationHealthModel` / `CompensationHealthDimension` / `CompensationPqPoint` / `CompensationCircuitPick` / `CompensationCircuitSlotState` 在 Task 1 定义，Task 2/3/6/7/8/11 一致引用。`buildCompensationHealthModel` 签名（`CompensationHealthModelInput`）在 Task 2 定义、Task 3 按字段调用一致。`ControlConsoleRemotePanel` props/emits 与现有 `CompensationMonitorView.vue` 用法逐项一致（Task 11）。手动投切表单字段 `phase` / `switch_action` / `group` 与 `controlConsoleManualSwitchForm` 一致。

**注意事项（实施时确认）:**
- `DeviceAlarmRecord` 的 `severity` 取值若与 `'critical' | 'warning'` 不同（例如带 `info` 等），`CompensationAlarmRail` 的 `sevClass` 已有 `else → info` 兜底，无需改。
- `capacitorBankControlSummaryView.summaryItems` 的元素须有 `label` 与 `value` 字段；若实际字段名不同，Task 12 的 `runtimeParamItems` 映射需按真实字段调整（实施时打开 `viewMapping.ts` 的 `buildCapacitorBankControlSummaryView` 与 `CapacitorBankControlSummaryView` 类型核对）。
