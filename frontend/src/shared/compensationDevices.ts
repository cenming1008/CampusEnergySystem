const COMPENSATION_CATEGORY = 'compensation'
const COMPENSATION_SUBTYPE_ALIASES: Record<string, string> = {
  reactive_power_compensator: 'capacitor_bank_controller',
  compensation: 'capacitor_bank_controller',
}

export const COMPENSATION_DEVICE_SUBTYPES = new Set([
  'svg',
  'capacitor_bank_controller',
])

function normalizeAlias(value?: string | null) {
  const normalized = value?.trim()
  if (!normalized) return ''
  return COMPENSATION_SUBTYPE_ALIASES[normalized] || normalized
}

export function resolveCompensationSubtype(
  deviceType?: string | null,
  deviceSubtype?: string | null,
) {
  const normalizedSubtype = normalizeAlias(deviceSubtype)
  if (COMPENSATION_DEVICE_SUBTYPES.has(normalizedSubtype)) {
    return normalizedSubtype
  }

  const normalizedType = normalizeAlias(deviceType)
  if (COMPENSATION_DEVICE_SUBTYPES.has(normalizedType)) {
    return normalizedType
  }

  return undefined
}

export function isCompensationDeviceIdentity(device: {
  device_type?: string | null
  device_subtype?: string | null
  device_category?: string | null
}) {
  return (
    device.device_category === COMPENSATION_CATEGORY ||
    resolveCompensationSubtype(device.device_type, device.device_subtype) !== undefined
  )
}

export function normalizeCompensationDevice<T extends {
  device_type: string
  device_subtype?: string
  device_category?: string
}>(device: T): T {
  const subtype = resolveCompensationSubtype(device.device_type, device.device_subtype)
  if (!subtype) {
    return device
  }

  return {
    ...device,
    device_subtype: subtype,
    device_category:
      device.device_category && device.device_category !== 'load'
        ? device.device_category
        : COMPENSATION_CATEGORY,
  }
}

