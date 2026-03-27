import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { usePermissions } from '../usePermissions'
import { useAuthStore } from '@/stores/useAuthStore'

describe('usePermissions', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('defaults to viewer with no role', () => {
    const perms = usePermissions()
    expect(perms.currentRole.value).toBe('viewer')
    expect(perms.canManageDevices.value).toBe(false)
    expect(perms.canControlDevices.value).toBe(false)
    expect(perms.canTrainModels.value).toBe(false)
  })

  it('admin has full access', () => {
    const auth = useAuthStore()
    auth.role = 'admin'

    const perms = usePermissions()
    expect(perms.isAdmin.value).toBe(true)
    expect(perms.canManageDevices.value).toBe(true)
    expect(perms.canControlDevices.value).toBe(true)
    expect(perms.canManageForecast.value).toBe(true)
    expect(perms.canTrainModels.value).toBe(true)
    expect(perms.canManageLocations.value).toBe(true)
    expect(perms.canManageMaintenance.value).toBe(true)
  })

  it('operator can control devices but not manage', () => {
    const auth = useAuthStore()
    auth.role = 'operator'

    const perms = usePermissions()
    expect(perms.canControlDevices.value).toBe(true)
    expect(perms.canManageDevices.value).toBe(false)
    expect(perms.canManageForecast.value).toBe(false)
    expect(perms.canOperateMaintenance.value).toBe(true)
  })

  it('maintainer can manage but not control devices', () => {
    const auth = useAuthStore()
    auth.role = 'maintainer'

    const perms = usePermissions()
    expect(perms.canManageDevices.value).toBe(true)
    expect(perms.canControlDevices.value).toBe(false)
    expect(perms.canTrainModels.value).toBe(false)
  })

  it('normalizes role casing before evaluating permissions', () => {
    const auth = useAuthStore()
    auth.role = 'MAINTAINER'

    const perms = usePermissions()
    expect(perms.currentRole.value).toBe('maintainer')
    expect(perms.canManageDevices.value).toBe(true)
  })

  it('viewer has read-only access', () => {
    const auth = useAuthStore()
    auth.role = 'viewer'

    const perms = usePermissions()
    expect(perms.canManageDevices.value).toBe(false)
    expect(perms.canControlDevices.value).toBe(false)
    expect(perms.canManageMaintenance.value).toBe(false)
    expect(perms.canOperateMaintenance.value).toBe(false)
  })
})
