import type { CompensationCapacitorBankTelemetry } from '@/api/compensation'

export type SlotState = boolean | null | 'unconfigured'

export interface CircuitGroup {
  label: string
  mask: number | null | undefined
  alarmFlag?: boolean | null
}

export interface FlagGroup {
  label: string
  title: string
  flags: Array<{ key: string; active: boolean | null | undefined }>
}

export interface ResolvedCountsInput {
  configuredSplitCircuitCount?: number | null
  configuredCommonCircuitCount?: number | null
  phaseACircuitTotalCount?: number | null
  phaseBCircuitTotalCount?: number | null
  phaseCCircuitTotalCount?: number | null
  common1CircuitTotalCount?: number | null
  common2CircuitTotalCount?: number | null
  common3CircuitTotalCount?: number | null
}

export function getCircuitGroups(t: CompensationCapacitorBankTelemetry): CircuitGroup[] {
  return [
    { label: 'A 相分补', mask: t.circuit_state_phase_a, alarmFlag: t.overvoltage_alarm_a },
    { label: 'B 相分补', mask: t.circuit_state_phase_b, alarmFlag: t.overvoltage_alarm_b },
    { label: 'C 相分补', mask: t.circuit_state_phase_c, alarmFlag: t.overvoltage_alarm_c },
    { label: '公补 1-8', mask: t.circuit_state_common_1 },
    { label: '公补 9-16', mask: t.circuit_state_common_2 },
    { label: '公补 17-24', mask: t.circuit_state_common_3 },
  ]
}

export function distributeBalanced(total: number | null | undefined, buckets: number, maxPerBucket: number): number[] {
  const normalized = Math.max(0, Math.min(Number(total || 0), buckets * maxPerBucket))
  const base = Math.floor(normalized / buckets)
  const remainder = normalized % buckets
  return Array.from({ length: buckets }, (_, index) => Math.min(maxPerBucket, base + (index < remainder ? 1 : 0)))
}

export function distributeSequential(total: number | null | undefined, bucketSizes: number[]): number[] {
  let remaining = Math.max(0, Number(total || 0))
  return bucketSizes.map((size) => {
    const allocated = Math.min(size, remaining)
    remaining -= allocated
    return allocated
  })
}

/**
 * Returns per-group configured counts (0–8), or null per entry when the count
 * is genuinely unknown (no profile data at all). null means "show as no-data",
 * while 0 means "explicitly zero circuits configured".
 */
export function resolvedConfiguredCounts(input: ResolvedCountsInput): (number | null)[] {
  const explicitCounts = [
    input.phaseACircuitTotalCount,
    input.phaseBCircuitTotalCount,
    input.phaseCCircuitTotalCount,
    input.common1CircuitTotalCount,
    input.common2CircuitTotalCount,
    input.common3CircuitTotalCount,
  ]
  if (explicitCounts.some((value) => value !== null && value !== undefined)) {
    return explicitCounts.map((value) => (value !== null && value !== undefined ? Math.max(0, Math.min(Number(value), 8)) : null))
  }
  const hasAggregateData =
    input.configuredSplitCircuitCount !== null && input.configuredSplitCircuitCount !== undefined
    || input.configuredCommonCircuitCount !== null && input.configuredCommonCircuitCount !== undefined
  if (!hasAggregateData) {
    return [null, null, null, null, null, null]
  }
  return [
    ...distributeBalanced(input.configuredSplitCircuitCount, 3, 8),
    ...distributeSequential(input.configuredCommonCircuitCount, [8, 8, 8]),
  ]
}

/** 将 8-bit mask 展开为 8 个槽位状态，bit0 = 第 1 路。configuredCount 为 null 表示路数未知，全部返回 null（无数据）。 */
export function toBits(mask: number | null | undefined, configuredCount: number | null): SlotState[] {
  if (configuredCount === null) {
    return Array.from({ length: 8 }, () => null)
  }
  return Array.from({ length: 8 }, (_, i) => {
    if (i >= configuredCount) return 'unconfigured'
    if (mask == null) return null
    return Boolean(mask & (1 << i))
  })
}

export function countOnSlots(mask: number | null | undefined, configuredCount: number | null): number {
  if (mask == null || !configuredCount) return 0
  let count = 0
  for (let i = 0; i < configuredCount; i++) {
    if (mask & (1 << i)) count++
  }
  return count
}

export function getFlagGroups(t: CompensationCapacitorBankTelemetry): FlagGroup[] {
  return [
    {
      label: '超前',
      title: '电容超前（容性过补偿）',
      flags: [
        { key: 'A', active: t.leading_a },
        { key: 'B', active: t.leading_b },
        { key: 'C', active: t.leading_c },
      ],
    },
    {
      label: '欠流',
      title: '回路欠电流',
      flags: [
        { key: 'A', active: t.undercurrent_a },
        { key: 'B', active: t.undercurrent_b },
        { key: 'C', active: t.undercurrent_c },
      ],
    },
    {
      label: 'V-THD',
      title: '电压谐波失真告警',
      flags: [
        { key: 'A', active: t.voltage_thd_alarm_a },
        { key: 'B', active: t.voltage_thd_alarm_b },
        { key: 'C', active: t.voltage_thd_alarm_c },
      ],
    },
    {
      label: 'I-THD',
      title: '电流谐波失真告警',
      flags: [
        { key: 'A', active: t.current_thd_alarm_a },
        { key: 'B', active: t.current_thd_alarm_b },
        { key: 'C', active: t.current_thd_alarm_c },
      ],
    },
    {
      label: '温度',
      title: '控制器温度超限',
      flags: [
        { key: '', active: t.temp_alarm },
      ],
    },
  ]
}

export function hasAnyActiveFlag(groups: FlagGroup[]): boolean {
  return groups.some(g => g.flags.some(f => f.active))
}
