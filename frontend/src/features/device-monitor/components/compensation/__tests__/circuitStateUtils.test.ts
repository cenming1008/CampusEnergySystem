import { describe, expect, it } from 'vitest'
import {
  countOnSlots,
  distributeBalanced,
  distributeSequential,
  getFlagGroups,
  getCircuitGroups,
  hasAnyActiveFlag,
  resolvedConfiguredCounts,
  toBits,
} from '../circuitStateUtils'
import type { CompensationCapacitorBankTelemetry } from '@/api/compensation'

function makeTelemetry(overrides: Partial<CompensationCapacitorBankTelemetry> = {}): CompensationCapacitorBankTelemetry {
  return {
    circuit_state_phase_a: null,
    circuit_state_phase_b: null,
    circuit_state_phase_c: null,
    circuit_state_common_1: null,
    circuit_state_common_2: null,
    circuit_state_common_3: null,
    overvoltage_alarm_a: null,
    overvoltage_alarm_b: null,
    overvoltage_alarm_c: null,
    leading_a: null,
    leading_b: null,
    leading_c: null,
    undercurrent_a: null,
    undercurrent_b: null,
    undercurrent_c: null,
    voltage_thd_alarm_a: null,
    voltage_thd_alarm_b: null,
    voltage_thd_alarm_c: null,
    current_thd_alarm_a: null,
    current_thd_alarm_b: null,
    current_thd_alarm_c: null,
    temp_alarm: null,
    ...overrides,
  } as CompensationCapacitorBankTelemetry
}

describe('distributeBalanced', () => {
  it('returns zeros when total is 0', () => {
    expect(distributeBalanced(0, 3, 8)).toEqual([0, 0, 0])
  })

  it('distributes evenly when divisible', () => {
    expect(distributeBalanced(12, 3, 8)).toEqual([4, 4, 4])
  })

  it('distributes remainder front-loaded', () => {
    expect(distributeBalanced(7, 3, 8)).toEqual([3, 2, 2])
  })

  it('clamps to maxPerBucket', () => {
    expect(distributeBalanced(30, 3, 8)).toEqual([8, 8, 8])
  })

  it('handles null/undefined as 0', () => {
    expect(distributeBalanced(null, 3, 8)).toEqual([0, 0, 0])
    expect(distributeBalanced(undefined, 3, 8)).toEqual([0, 0, 0])
  })
})

describe('distributeSequential', () => {
  it('returns zeros when total is 0', () => {
    expect(distributeSequential(0, [8, 8, 8])).toEqual([0, 0, 0])
  })

  it('fills buckets sequentially', () => {
    expect(distributeSequential(12, [8, 8, 8])).toEqual([8, 4, 0])
  })

  it('handles total within first bucket', () => {
    expect(distributeSequential(5, [8, 8, 8])).toEqual([5, 0, 0])
  })

  it('clamps when total exceeds all buckets', () => {
    expect(distributeSequential(30, [8, 8, 8])).toEqual([8, 8, 8])
  })

  it('handles null/undefined as 0', () => {
    expect(distributeSequential(null, [8, 8, 8])).toEqual([0, 0, 0])
  })
})

describe('resolvedConfiguredCounts', () => {
  it('uses explicit per-group counts when provided', () => {
    const result = resolvedConfiguredCounts({
      phaseACircuitTotalCount: 6,
      phaseBCircuitTotalCount: 4,
      phaseCCircuitTotalCount: 8,
      common1CircuitTotalCount: 3,
      common2CircuitTotalCount: 0,
      common3CircuitTotalCount: 2,
    })
    expect(result).toEqual([6, 4, 8, 3, 0, 2])
  })

  it('clamps explicit counts to [0, 8] and preserves unknown groups as null', () => {
    const result = resolvedConfiguredCounts({
      phaseACircuitTotalCount: 10,
      phaseBCircuitTotalCount: -1,
      phaseCCircuitTotalCount: 0,
      common1CircuitTotalCount: null,
      common2CircuitTotalCount: null,
      common3CircuitTotalCount: null,
    })
    expect(result).toEqual([8, 0, 0, null, null, null])
  })

  it('falls back to distribution when only split+common totals provided', () => {
    const result = resolvedConfiguredCounts({
      configuredSplitCircuitCount: 6,
      configuredCommonCircuitCount: 16,
    })
    expect(result).toEqual([2, 2, 2, 8, 8, 0])
  })

  it('returns all nulls when device has not reported circuit counts yet', () => {
    const result = resolvedConfiguredCounts({})
    expect(result).toEqual([null, null, null, null, null, null])
  })

  it('uses explicit counts even if only one is provided and keeps others unknown', () => {
    const result = resolvedConfiguredCounts({
      phaseACircuitTotalCount: 4,
    })
    expect(result).toEqual([4, null, null, null, null, null])
  })
})

describe('toBits', () => {
  it('returns all true when mask=0xFF and count=8', () => {
    expect(toBits(0xFF, 8)).toEqual([true, true, true, true, true, true, true, true])
  })

  it('marks unconfigured slots beyond configuredCount', () => {
    const result = toBits(0xFF, 3)
    expect(result.slice(0, 3)).toEqual([true, true, true])
    expect(result.slice(3)).toEqual(['unconfigured', 'unconfigured', 'unconfigured', 'unconfigured', 'unconfigured'])
  })

  it('returns null for configured slots when mask is null', () => {
    const result = toBits(null, 3)
    expect(result.slice(0, 3)).toEqual([null, null, null])
    expect(result.slice(3)).toEqual(['unconfigured', 'unconfigured', 'unconfigured', 'unconfigured', 'unconfigured'])
  })

  it('decodes individual bits correctly', () => {
    // 0x03 = 0b00000011: bits 0 and 1 set
    expect(toBits(0x03, 8)).toEqual([true, true, false, false, false, false, false, false])
  })

  it('returns all unconfigured when count=0', () => {
    expect(toBits(0xFF, 0)).toEqual(Array(8).fill('unconfigured'))
  })
})

describe('countOnSlots', () => {
  it('returns 0 when mask is null', () => {
    expect(countOnSlots(null, 4)).toBe(0)
  })

  it('returns 0 when configuredCount is 0', () => {
    expect(countOnSlots(0xFF, 0)).toBe(0)
  })

  it('counts only within configuredCount', () => {
    expect(countOnSlots(0xFF, 4)).toBe(4)
  })

  it('counts set bits correctly', () => {
    expect(countOnSlots(0x05, 8)).toBe(2) // bits 0 and 2
  })
})

describe('getFlagGroups', () => {
  it('returns 5 groups', () => {
    const groups = getFlagGroups(makeTelemetry())
    expect(groups).toHaveLength(5)
  })

  it('maps leading flags to 超前 group', () => {
    const t = makeTelemetry({ leading_a: true, leading_b: false, leading_c: null })
    const groups = getFlagGroups(t)
    const leading = groups.find(g => g.label === '超前')!
    expect(leading.flags[0].active).toBe(true)
    expect(leading.flags[1].active).toBe(false)
    expect(leading.flags[2].active).toBe(null)
  })

  it('maps temp_alarm to 温度 group', () => {
    const t = makeTelemetry({ temp_alarm: true })
    const groups = getFlagGroups(t)
    const temp = groups.find(g => g.label === '温度')!
    expect(temp.flags[0].active).toBe(true)
  })
})

describe('hasAnyActiveFlag', () => {
  it('returns false when all flags are null or false', () => {
    const groups = getFlagGroups(makeTelemetry())
    expect(hasAnyActiveFlag(groups)).toBe(false)
  })

  it('returns true when any flag is truthy', () => {
    const t = makeTelemetry({ leading_a: true })
    const groups = getFlagGroups(t)
    expect(hasAnyActiveFlag(groups)).toBe(true)
  })
})

describe('getCircuitGroups', () => {
  it('returns 6 groups in correct order', () => {
    const t = makeTelemetry()
    const groups = getCircuitGroups(t)
    expect(groups).toHaveLength(6)
    expect(groups[0].label).toBe('A 相分补')
    expect(groups[1].label).toBe('B 相分补')
    expect(groups[2].label).toBe('C 相分补')
    expect(groups[3].label).toBe('公补 1-8')
    expect(groups[4].label).toBe('公补 9-16')
    expect(groups[5].label).toBe('公补 17-24')
  })

  it('maps overvoltage alarm flags to phase groups', () => {
    const t = makeTelemetry({ overvoltage_alarm_a: true, overvoltage_alarm_b: false })
    const groups = getCircuitGroups(t)
    expect(groups[0].alarmFlag).toBe(true)
    expect(groups[1].alarmFlag).toBe(false)
    expect(groups[3].alarmFlag).toBeUndefined()
  })

  it('maps circuit state masks correctly', () => {
    const t = makeTelemetry({ circuit_state_phase_a: 0x0F })
    const groups = getCircuitGroups(t)
    expect(groups[0].mask).toBe(0x0F)
  })
})
