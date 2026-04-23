import { beforeEach, describe, expect, it, vi } from 'vitest'

const { warningMock } = vi.hoisted(() => ({
  warningMock: vi.fn(),
}))

vi.mock('element-plus', async () => {
  const actual = await vi.importActual<typeof import('element-plus')>('element-plus')
  return {
    ...actual,
    ElMessage: {
      warning: warningMock,
    },
  }
})

import {
  extractControlConsoleErrorMessage,
  formatWriteTargetValue,
  normalizeWriteTargetValue,
  notifyInvalidWriteTarget,
  roleLabel,
} from '../controlConsoleUtils'
import { getCapacitorBankEditableParameterMeta } from '../capacitorBankControlProfile'

describe('control console utils', () => {
  beforeEach(() => {
    warningMock.mockReset()
  })

  it('normalizes text and invalid numeric targets', () => {
    const textMeta = getCapacitorBankEditableParameterMeta('common_capacity_code')
    const numberMeta = getCapacitorBankEditableParameterMeta('switch_on_delay_seconds')

    expect(textMeta).toBeTruthy()
    expect(numberMeta).toBeTruthy()
    expect(normalizeWriteTargetValue(textMeta!, '  AA-BB  ')).toEqual({
      value: 'AA-BB',
      message: '',
    })
    expect(normalizeWriteTargetValue(numberMeta!, null)).toEqual({
      value: null,
      message: '请填写有效的 投入延时',
    })
  })

  it('formats write target values and notifies invalid writes', () => {
    const booleanMeta = getCapacitorBankEditableParameterMeta('current_polarity_identification_enabled')
    expect(booleanMeta).toBeTruthy()

    expect(formatWriteTargetValue(booleanMeta!, true)).toBe('开启')
    expect(notifyInvalidWriteTarget(booleanMeta!, null)).toBeNull()
    expect(warningMock).toHaveBeenCalledWith('请确认 电流极性识别 的开关状态')
  })

  it('extracts backend error messages and resolves role labels', () => {
    expect(extractControlConsoleErrorMessage({
      response: {
        data: {
          detail: '设备拒绝执行',
        },
      },
    }, 'fallback')).toBe('设备拒绝执行')
    expect(roleLabel('admin')).toBe('管理员')
    expect(roleLabel('visitor')).toBe('访客')
  })
})
