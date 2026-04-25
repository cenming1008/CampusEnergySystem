<script setup lang="ts">
import { Plus } from '@element-plus/icons-vue'
import type { CarbonEmission, CarbonFactor, EnergyData, EnergyTypeInfo } from '@/api/energy'

defineOptions({ name: 'EnergyDataEntryTab' })

interface CarbonCalculationResult {
  energy_type: string
  consumption: number
  consumption_unit: string
  carbon_factor: number
  carbon_emission: number
  emission_unit: string
}

defineProps<{
  visibleEnergyTypes: EnergyTypeInfo[]
  carbonFactors: Record<string, CarbonFactor>
  carbonCalculator: {
    energy_type: string
    consumption: number
    result: CarbonCalculationResult | null
  }
  detailDeviceId?: number
  detailLoading: boolean
  detailDeviceName: string
  energyDetails: EnergyData[]
  carbonDetails: CarbonEmission[]
}>()

const emit = defineEmits<{
  (event: 'open-entry'): void
  (event: 'calculate-carbon'): void
}>()
</script>

<template>
  <div class="energy-data-entry-tab">
    <div class="entry-actions-bar">
      <el-button type="primary" @click="emit('open-entry')">
        <el-icon><Plus /></el-icon>
        手工补录能源数据
      </el-button>
    </div>

    <div class="glass-card em-card">
      <div class="card-head">
        <p class="eyebrow">Carbon Calculator</p>
        <h3 class="card-title">碳排放试算</h3>
      </div>
      <div class="trial-form">
        <el-form label-width="90px">
          <el-form-item label="能源类型">
            <el-select
              v-model="carbonCalculator.energy_type"
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
          <el-form-item label="消耗量">
            <el-input-number
              v-model="carbonCalculator.consumption"
              :min="0"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="emit('calculate-carbon')">
              计算碳排放
            </el-button>
          </el-form-item>
        </el-form>
        <div v-if="carbonCalculator.result" class="result-box">
          <h4>计算结果</h4>
          <div class="result-item">
            <span>能源类型</span>
            <strong>{{ carbonCalculator.result.energy_type }}</strong>
          </div>
          <div class="result-item">
            <span>消耗量</span>
            <strong>{{ carbonCalculator.result.consumption }} {{ carbonCalculator.result.consumption_unit }}</strong>
          </div>
          <div class="result-item">
            <span>碳排放因子</span>
            <strong>{{ carbonCalculator.result.carbon_factor }} {{ carbonCalculator.result.emission_unit }}/{{ carbonCalculator.result.consumption_unit }}</strong>
          </div>
          <div class="result-item result-item--highlight">
            <span>碳排放量</span>
            <strong>{{ carbonCalculator.result.carbon_emission }} {{ carbonCalculator.result.emission_unit }}</strong>
          </div>
        </div>
      </div>
    </div>

    <div class="detail-layout">
      <div class="glass-card detail-panel">
        <div class="detail-panel__head">
          <h3>能源明细</h3>
          <el-tag size="small" effect="dark" type="info">{{ detailDeviceName }}</el-tag>
        </div>
        <el-alert
          v-if="!detailDeviceId"
          title="未选择设备时仅展示系统级统计，能源原始明细需选择具体设备。"
          type="warning"
          :closable="false"
          show-icon
        />
        <el-table
          v-else
          v-loading="detailLoading"
          :data="energyDetails"
          max-height="320"
          size="small"
        >
          <el-table-column prop="timestamp" label="时间" min-width="180" />
          <el-table-column prop="consumption" label="累计消耗" width="120" />
          <el-table-column prop="flow_rate" label="瞬时流量/功率" width="140" />
          <el-table-column prop="voltage" label="电压" width="100" />
          <el-table-column prop="current" label="电流" width="100" />
        </el-table>
      </div>

      <div class="glass-card detail-panel">
        <div class="detail-panel__head">
          <h3>碳排放明细</h3>
          <el-tag size="small" type="danger" effect="dark">{{ carbonDetails.length }} 条</el-tag>
        </div>
        <el-table
          v-loading="detailLoading"
          :data="carbonDetails"
          max-height="320"
          size="small"
        >
          <el-table-column prop="timestamp" label="时间" min-width="180" />
          <el-table-column prop="energy_consumption" label="能耗" width="120" />
          <el-table-column prop="carbon_factor" label="因子" width="100" />
          <el-table-column prop="carbon_emission" label="碳排放" width="120" />
        </el-table>
      </div>
    </div>
  </div>
</template>
