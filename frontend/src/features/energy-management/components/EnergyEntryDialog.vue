<script setup lang="ts">
import type { Device } from '@/api/device'
import type { EnergyTypeInfo } from '@/api/energy'

export interface EnergyEntryForm {
  device_id?: number
  energy_type: string
  consumption: number
  flow_rate: number
  timestamp: string
}

defineProps<{
  visible: boolean
  form: EnergyEntryForm
  deviceList: Device[]
  visibleEnergyTypes: EnergyTypeInfo[]
}>()

const emit = defineEmits<{
  (event: 'update:visible', value: boolean): void
  (event: 'submit'): void
}>()
</script>

<template>
  <el-dialog
    :model-value="visible"
    title="手工补录能源数据"
    width="520px"
    class="em-entry-dialog"
    @update:model-value="emit('update:visible', $event)"
  >
    <el-form label-position="top">
      <el-form-item label="设备">
        <el-select
          v-model="form.device_id"
          filterable
          placeholder="选择设备"
          style="width: 100%"
          teleported
          popper-class="app-select-popper"
        >
          <el-option
            v-for="d in deviceList"
            :key="d.id"
            :label="d.name"
            :value="d.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="能源类型">
        <el-select
          v-model="form.energy_type"
          style="width: 100%"
          teleported
          popper-class="app-select-popper"
        >
          <el-option
            v-for="type in visibleEnergyTypes"
            :key="type.value"
            :label="type.label"
            :value="type.value"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="累计消耗">
        <el-input-number v-model="form.consumption" :min="0" style="width: 100%" />
      </el-form-item>
      <el-form-item label="瞬时流量/功率">
        <el-input-number v-model="form.flow_rate" :min="0" style="width: 100%" />
      </el-form-item>
      <el-form-item label="时间戳">
        <el-date-picker
          v-model="form.timestamp"
          type="datetime"
          value-format="YYYY-MM-DDTHH:mm:ss"
          placeholder="选择时间"
          style="width: 100%"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="emit('update:visible', false)">取消</el-button>
      <el-button type="primary" @click="emit('submit')">提交补录</el-button>
    </template>
  </el-dialog>
</template>
