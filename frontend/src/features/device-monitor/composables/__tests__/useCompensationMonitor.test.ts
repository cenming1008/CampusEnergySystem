import { describe, expect, it } from 'vitest'
import {
  buildCompensationAlarmCountMetrics,
  buildCompensationEventTimeline,
  isTimestampFresh,
  REALTIME_FRESH_THRESHOLD_MS,
} from '../useCompensationMonitor'

describe('isTimestampFresh', () => {
  const now = Date.parse('2026-05-15T12:00:00Z')

  it('returns false when timestamp is missing', () => {
    expect(isTimestampFresh(undefined, REALTIME_FRESH_THRESHOLD_MS, now)).toBe(false)
    expect(isTimestampFresh(null, REALTIME_FRESH_THRESHOLD_MS, now)).toBe(false)
  })

  it('returns false when timestamp is unparseable', () => {
    expect(isTimestampFresh('not-a-date', REALTIME_FRESH_THRESHOLD_MS, now)).toBe(false)
  })

  it('returns true when timestamp is within threshold', () => {
    const recent = new Date(now - 30_000).toISOString()
    expect(isTimestampFresh(recent, REALTIME_FRESH_THRESHOLD_MS, now)).toBe(true)
  })

  it('returns false when timestamp is older than threshold', () => {
    const stale = new Date(now - 5 * 60_000).toISOString()
    expect(isTimestampFresh(stale, REALTIME_FRESH_THRESHOLD_MS, now)).toBe(false)
  })

  it('treats exact threshold as fresh', () => {
    const edge = new Date(now - REALTIME_FRESH_THRESHOLD_MS).toISOString()
    expect(isTimestampFresh(edge, REALTIME_FRESH_THRESHOLD_MS, now)).toBe(true)
  })
})

describe('buildCompensationAlarmCountMetrics', () => {
  it('shows the power factor bucket first and uses updated compensation alarm labels', () => {
    const metrics = buildCompensationAlarmCountMetrics({
      cap_power_factor_abnormal: 2,
      cap_undervoltage_a: 1,
      cap_overvoltage_b: 3,
      cap_undercompensation: 4,
      cap_overcompensation: 5,
      cap_overcurrent_b: 6,
    })

    expect(metrics.map((item) => item.label)).toEqual([
      '功率因数异常次数',
      '过压欠压告警次数',
      '谐波超限次数',
      '过补欠补偿次数',
      '温度告警次数',
      '电流异常次数',
      '通讯告警次数',
    ])
    expect(metrics[0]).toMatchObject({ key: 'alarm_power_factor', value: '2', unit: '次' })
    expect(metrics[1]).toMatchObject({ key: 'alarm_overvoltage', value: '4', unit: '次' })
    expect(metrics[3]).toMatchObject({ key: 'alarm_overcomp', value: '9', unit: '次' })
    expect(metrics[5]).toMatchObject({ key: 'alarm_current', value: '6', unit: '次' })
  })
})

describe('buildCompensationEventTimeline', () => {
  it('groups repeated alarm refreshes into one ongoing event with Chinese severity text', () => {
    const events = buildCompensationEventTimeline([
      {
        timestamp: '2026-05-18T11:52:00+08:00',
        event_type: 'alarm',
        status: 'active',
        title: 'B 相电压谐波超限：5.00%（门限 5.00%）',
        detail: '级别: warning',
      },
      {
        timestamp: '2026-05-18T11:51:00+08:00',
        event_type: 'alarm',
        status: 'active',
        title: 'B 相电压谐波超限：5.00%（门限 5.00%）',
        detail: '级别: warning',
      },
      {
        timestamp: '2026-05-18T11:50:00+08:00',
        event_type: 'alarm',
        status: 'active',
        title: 'B 相电压谐波超限：5.00%（门限 5.00%）',
        detail: '级别: warning',
      },
    ])

    expect(events).toHaveLength(1)
    expect(events[0]).toMatchObject({
      time: '11:52',
      title: 'B 相电压谐波超限',
      tag: '持续中',
      tone: 'warning',
    })
    expect(events[0].detail).toContain('级别：警告')
    expect(events[0].detail).toContain('首次 11:50')
    expect(events[0].detail).toContain('最近 11:52')
    expect(events[0].detail).toContain('持续 2 分钟')
    expect(events[0].detail).toContain('累计 3 次')
  })

  it('keeps the latest 20 running events in the timeline', () => {
    const events = buildCompensationEventTimeline(
      Array.from({ length: 25 }, (_, index) => ({
        timestamp: `2026-05-18T12:${String(index).padStart(2, '0')}:00+08:00`,
        event_type: 'control',
        status: 'success',
        title: `控制事件 ${index}`,
        detail: '已处理',
      })),
    )

    expect(events).toHaveLength(20)
    expect(events[0].title).toBe('控制事件 24')
    expect(events[19].title).toBe('控制事件 5')
  })

  it('labels successful control events as handled instead of success', () => {
    const events = buildCompensationEventTimeline([
      {
        timestamp: '2026-05-18T12:44:00+08:00',
        event_type: 'control',
        status: 'success',
        title: '参数写入 · 切除延时时间',
        detail: '已处理 | admin | 切除延时时间 -> 3 | 设备回执已处理',
      },
    ])

    expect(events).toHaveLength(1)
    expect(events[0]).toMatchObject({
      title: '参数写入 · 切除延时时间',
      tag: '已处理',
      tone: 'success',
    })
    expect(events[0].detail).toContain('已处理')
    expect(events[0].detail).not.toContain('成功')
  })

  it('labels manually handled alarm events as handled instead of recovered', () => {
    const events = buildCompensationEventTimeline([
      {
        timestamp: '2026-05-18T12:13:00+08:00',
        event_type: 'alarm_resolution',
        status: 'resolved',
        title: '告警已处理: C 相电压谐波超限：15.80%（门限 5.00%）',
        detail: 'admin',
      },
    ])

    expect(events).toHaveLength(1)
    expect(events[0]).toMatchObject({
      title: '告警已处理: C 相电压谐波超限：15.80%（门限 5.00%）',
      tag: '已处理',
      tone: 'success',
    })
  })
})
