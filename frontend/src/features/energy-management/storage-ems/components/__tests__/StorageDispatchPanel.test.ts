import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import StorageDispatchPanel from '../StorageDispatchPanel.vue'
import type { StorageEnergyOverview } from '@/api/storageEnergy'

const overview = {
  storage_device_ids: [7],
  dispatch: {},
  provenance: {},
} as StorageEnergyOverview

function mountPanel(refreshing: boolean, generating: boolean) {
  return mount(StorageDispatchPanel, {
    props: {
      overview,
      refreshing,
      generating,
      generationResult: null,
      generationError: null,
      canGeneratePlan: true,
    },
  })
}

describe('StorageDispatchPanel', () => {
  it('disables refresh and generation while a plan is generating', () => {
    const wrapper = mountPanel(false, true)

    expect(wrapper.get('[data-testid="refresh-storage-overview"]').attributes('disabled')).toBeDefined()
    expect(wrapper.get('[data-testid="generate-storage-plan"]').attributes('disabled')).toBeDefined()
  })

  it('disables refresh and generation while the overview is refreshing', () => {
    const wrapper = mountPanel(true, false)

    expect(wrapper.get('[data-testid="refresh-storage-overview"]').attributes('disabled')).toBeDefined()
    expect(wrapper.get('[data-testid="generate-storage-plan"]').attributes('disabled')).toBeDefined()
  })
})
