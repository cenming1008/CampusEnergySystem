<script setup lang="ts">
import type { PropType } from 'vue'
import type { CompensationEventItem } from './types'

defineProps({
  events: {
    type: Array as PropType<CompensationEventItem[]>,
    default: () => [],
  },
})

function tagType(tone?: CompensationEventItem['tone']) {
  if (tone === 'success') return 'success'
  if (tone === 'warning') return 'warning'
  if (tone === 'danger') return 'danger'
  if (tone === 'info') return 'primary'
  return 'info'
}
</script>

<template>
  <section class="side-panel">
    <div class="side-panel__head">
      <h3>运行事件</h3>
      <span v-if="events.length" class="event-count">共 {{ events.length }} 条</span>
    </div>

    <div
      v-if="events.length"
      class="timeline-wrap"
    >
      <el-timeline>
        <el-timeline-item
          v-for="item in events"
          :key="`${item.time}-${item.title}`"
          :timestamp="item.time"
          :type="tagType(item.tone)"
          hollow
        >
          <div class="timeline-card">
            <div class="timeline-card__head">
              <strong>{{ item.title }}</strong>
              <el-tag
                v-if="item.tag"
                size="small"
                effect="plain"
                :type="tagType(item.tone)"
              >
                {{ item.tag }}
              </el-tag>
              <el-tag
                v-if="item.isMock"
                size="small"
                effect="plain"
                type="warning"
              >
                估算/占位
              </el-tag>
            </div>
            <p>{{ item.detail }}</p>
          </div>
        </el-timeline-item>
      </el-timeline>
    </div>

    <div
      v-else
      class="empty-hint"
    >
      当前暂无运行事件，设备最近运行较平稳。
    </div>
  </section>
</template>

<style scoped>
.side-panel {
  padding: 16px;
  background: linear-gradient(180deg, rgba(18, 32, 50, 0.96), rgba(13, 22, 35, 0.98));
  border: 1px solid rgba(53, 72, 97, 0.88);
  border-radius: 16px;
}

.side-panel__head {
  margin-bottom: 12px;
}

.side-panel__head h3 {
  margin: 0;
  font-size: 15px;
  color: #f5f7fb;
}

.event-count {
  font-size: 12px;
  color: #5d7699;
}

.side-panel__head em {
  font-style: normal;
  color: #5d7699;
}

.timeline-wrap {
  max-height: 420px;
  overflow-y: auto;
  padding-right: 6px;
  scrollbar-width: thin;
  scrollbar-color: rgba(53, 72, 97, 0.5) transparent;
}

.timeline-card {
  padding: 10px 12px;
  background: rgba(16, 27, 42, 0.9);
  border: 1px solid rgba(48, 67, 91, 0.78);
  border-radius: 12px;
}

.timeline-card__head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
  margin-bottom: 6px;
}

.timeline-card strong {
  color: #f3f6fb;
  font-size: 13px;
}

.timeline-card p {
  margin: 0;
  color: #8ea0bc;
  font-size: 12px;
  line-height: 1.6;
}

.empty-hint {
  padding: 14px 0 4px;
  color: #8ea0bc;
  font-size: 12px;
}
</style>
