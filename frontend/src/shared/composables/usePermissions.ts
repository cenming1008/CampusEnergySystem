import { computed } from 'vue'
import { useAuthStore } from '@/stores/useAuthStore'

export function usePermissions() {
  const authStore = useAuthStore()
  const currentRole = computed(() => (authStore.role || 'viewer').toLowerCase().trim())

  return {
    currentRole,
    isAdmin: computed(() => currentRole.value === 'admin'),
    hasScopedAccess: computed(() => Boolean(authStore.locationScope)),
    canManageDevices: computed(() => ['admin', 'maintainer'].includes(currentRole.value)),
    canControlDevices: computed(() => ['admin', 'operator'].includes(currentRole.value)),
    canManageLocations: computed(() => ['admin', 'maintainer'].includes(currentRole.value)),
    canManageGroups: computed(() => ['admin', 'maintainer'].includes(currentRole.value)),
    canManageMaintenance: computed(() => ['admin', 'maintainer'].includes(currentRole.value)),
    canOperateMaintenance: computed(() => ['admin', 'maintainer', 'operator'].includes(currentRole.value)),
    canManageInspection: computed(() => ['admin', 'maintainer'].includes(currentRole.value)),
    canOperateInspection: computed(() => ['admin', 'maintainer', 'operator'].includes(currentRole.value)),
    canManageForecast: computed(() => currentRole.value === 'admin'),
    canTrainModels: computed(() => currentRole.value === 'admin'),
  }
}
