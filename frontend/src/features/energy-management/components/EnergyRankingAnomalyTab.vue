<script setup lang="ts">
import type {
  AnalysisAnomaly,
  AnalysisAnomalyItem,
  AnalysisDeviceRankingItem,
  AnalysisInsightItem,
  AnalysisLocationRankingItem,
} from '@/api/energy'
import {
  formatMetricValue,
  formatTimestamp,
  getAnomalyKindLabel,
  getSeverityType,
  severityLabels,
} from '../formatters'

defineOptions({ name: 'EnergyRankingAnomalyTab' })

defineProps<{
  rankingTopN: number
  areaRanking: AnalysisLocationRankingItem[]
  buildingRanking: AnalysisLocationRankingItem[]
  deviceRanking: AnalysisDeviceRankingItem[]
  analysisAnomaly: AnalysisAnomaly | null
  anomalyItems: AnalysisAnomalyItem[]
  insightItems: AnalysisInsightItem[]
}>()

const emit = defineEmits<{
  (event: 'update:rankingTopN', value: number): void
}>()
</script>

<template>
  <div class="energy-ranking-anomaly-tab">
    <div class="glass-card em-card">
      <div class="card-head">
        <p class="eyebrow">Ranking</p>
        <h3 class="card-title">区域 / 楼栋 / 设备排行</h3>
      </div>
      <div class="ranking-grid">
        <div class="ranking-toolbar">
          <span>排行数量</span>
          <el-select
            :model-value="rankingTopN"
            size="small"
            teleported
            popper-class="app-select-popper"
            style="width: 96px"
            @update:model-value="emit('update:rankingTopN', $event)"
          >
            <el-option :value="3" label="Top 3" />
            <el-option :value="5" label="Top 5" />
            <el-option :value="10" label="Top 10" />
            <el-option :value="20" label="Top 20" />
          </el-select>
        </div>
        <div class="ranking-block">
          <div class="ranking-title">区域排行</div>
          <div v-if="areaRanking.length" class="rank-list">
            <div
              v-for="(item, index) in areaRanking"
              :key="`area-${item.location_id}`"
              class="rank-item"
            >
              <span class="rank-index">{{ index + 1 }}</span>
              <div class="rank-main">
                <strong>{{ item.name }}</strong>
                <span>{{ formatMetricValue(item.total_consumption, 1) }} 周期能耗</span>
              </div>
              <span class="rank-side">{{ formatMetricValue(item.avg_load, 1) }}</span>
            </div>
          </div>
          <el-empty v-else description="暂无区域排行" />
        </div>

        <div class="ranking-block">
          <div class="ranking-title">楼栋排行</div>
          <div v-if="buildingRanking.length" class="rank-list">
            <div
              v-for="(item, index) in buildingRanking"
              :key="`building-${item.location_id}`"
              class="rank-item"
            >
              <span class="rank-index">{{ index + 1 }}</span>
              <div class="rank-main">
                <strong>{{ item.name }}</strong>
                <span>{{ formatMetricValue(item.total_consumption, 1) }} 周期能耗</span>
              </div>
              <span class="rank-side">{{ formatMetricValue(item.avg_load, 1) }}</span>
            </div>
          </div>
          <el-empty v-else description="暂无楼栋排行" />
        </div>

        <div class="ranking-block">
          <div class="ranking-title">设备排行</div>
          <div v-if="deviceRanking.length" class="rank-list">
            <div
              v-for="(item, index) in deviceRanking"
              :key="`device-${item.device_id}`"
              class="rank-item"
            >
              <span class="rank-index">{{ index + 1 }}</span>
              <div class="rank-main">
                <strong>{{ item.name }}</strong>
                <span>{{ item.location || '未分配位置' }}</span>
              </div>
              <span class="rank-side">{{ formatMetricValue(item.total_consumption, 1) }}</span>
            </div>
          </div>
          <el-empty v-else description="暂无设备排行" />
        </div>
      </div>
    </div>

    <div class="glass-card em-card">
      <div class="card-head">
        <p class="eyebrow">Anomaly</p>
        <div class="card-title-row">
          <h3 class="card-title">异常信号</h3>
          <el-tag
            :type="analysisAnomaly?.boundary === 'operational_signal_first_batch' ? 'warning' : 'info'"
            effect="plain"
          >
            {{ analysisAnomaly?.boundary === 'operational_signal_first_batch' ? '第一批运营信号' : (analysisAnomaly?.boundary || '未覆盖') }}
          </el-tag>
        </div>
      </div>

      <div v-if="analysisAnomaly" class="anomaly-summary">
        <div class="anomaly-pill">
          <span>总数</span>
          <strong>{{ analysisAnomaly.summary.total_count }}</strong>
        </div>
        <div class="anomaly-pill">
          <span>断档</span>
          <strong>{{ analysisAnomaly.summary.data_gap_count }}</strong>
        </div>
        <div class="anomaly-pill">
          <span>失败</span>
          <strong>{{ analysisAnomaly.summary.ingestion_failure_count }}</strong>
        </div>
        <div class="anomaly-pill">
          <span>告警</span>
          <strong>{{ analysisAnomaly.summary.active_alarm_count }}</strong>
        </div>
      </div>

      <div v-if="anomalyItems.length" class="alert-list">
        <div
          v-for="item in anomalyItems"
          :key="`${item.kind}-${item.device_id}-${item.detected_at}`"
          class="alert-item"
        >
          <div class="alert-main">
            <div class="alert-title-row">
              <strong>{{ item.device_name }}</strong>
              <el-tag
                :type="getSeverityType(item.severity)"
                effect="plain"
                size="small"
              >
                {{ severityLabels[item.severity] || item.severity }}
              </el-tag>
            </div>
            <span>{{ getAnomalyKindLabel(item.kind) }} · {{ item.location || '未分配位置' }}</span>
            <p>{{ item.message }}</p>
          </div>
          <span class="alert-time">{{ formatTimestamp(item.detected_at, 'hour') }}</span>
        </div>
      </div>
      <el-empty v-else description="当前统计窗口无运营异常信号" />
    </div>

    <div v-if="insightItems.length" class="glass-card em-card">
      <div class="card-head">
        <p class="eyebrow">Insights</p>
        <h3 class="card-title">运营洞察</h3>
      </div>
      <div class="insight-list">
        <div
          v-for="item in insightItems"
          :key="item.title"
          class="insight-item"
        >
          <div class="insight-top">
            <strong>{{ item.title }}</strong>
            <el-tag
              :type="getSeverityType(item.severity)"
              effect="plain"
              size="small"
            >
              {{ severityLabels[item.severity] || item.severity }}
            </el-tag>
          </div>
          <p>{{ item.detail }}</p>
          <span>{{ item.dimension }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
