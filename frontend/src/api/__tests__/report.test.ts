import { describe, expect, it } from 'vitest'

import { buildReportDownloadName } from '../report'

describe('report api helpers', () => {
  it('includes device id in device history download names', () => {
    expect(buildReportDownloadName({
      report_type: 'device_history',
      device_id: 8,
      end_time: '2026-05-14T18:30:00',
    })).toBe('device_history_8_20260514.csv')
  })
})
