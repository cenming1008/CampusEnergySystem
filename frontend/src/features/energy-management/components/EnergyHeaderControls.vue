<script setup lang="ts">
import { Refresh } from '@element-plus/icons-vue'
import type { Device } from '@/api/device'

defineProps<{
  deviceList: Device[]
  detailDeviceId?: number
  dateRange: [Date, Date]
  trendGranularity: 'hour' | 'day'
  loading: boolean
}>()

const emit = defineEmits<{
  (event: 'update:detailDeviceId', value?: number): void
  (event: 'update:dateRange', value: [Date, Date]): void
  (event: 'update:trendGranularity', value: 'hour' | 'day'): void
  (event: 'refresh'): void
}>()
</script>

<template>
  <div class="em-header__controls">
    <el-select
      :model-value="detailDeviceId"
      clearable
      filterable
      placeholder="选择设备查看明细"
      teleported
      popper-class="app-select-popper"
      style="width: 200px"
      @update:model-value="emit('update:detailDeviceId', $event)"
    >
      <el-option
        v-for="d in deviceList"
        :key="d.id"
        :label="d.name"
        :value="d.id"
      />
    </el-select>
    <el-select
      :model-value="trendGranularity"
      teleported
      popper-class="app-select-popper"
      style="width: 112px"
      @update:model-value="emit('update:trendGranularity', $event)"
    >
      <el-option label="天粒度" value="day" />
      <el-option label="小时粒度" value="hour" />
    </el-select>
    <el-date-picker
      :model-value="dateRange"
      type="daterange"
      range-separator="–"
      start-placeholder="开始"
      end-placeholder="结束"
      style="width: 240px"
      @update:model-value="emit('update:dateRange', $event)"
    />
    <el-button type="primary" :loading="loading" @click="emit('refresh')">
      <el-icon><Refresh /></el-icon>
      刷新
    </el-button>
  </div>
</template>
