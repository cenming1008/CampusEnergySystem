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

function tagClass(tag?: string) {
  if (tag === '持续中') return 'event-pill--active'
  if (tag === '已处理') return 'event-pill--handled'
  if (tag === '已恢复') return 'event-pill--recovered'
  return 'event-pill--default'
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
              <span
                v-if="item.tag"
                class="event-pill"
                :class="tagClass(item.tag)"
              >
                {{ item.tag }}
              </span>
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
  font-size: var(--font-caption);
  color: var(--text-label);
}

.side-panel__head em {
  font-style: normal;
  color: var(--text-label);
}

.timeline-wrap {
  max-height: clamp(360px, 50vh, 720px);
  overflow-y: auto;
  padding-right: 8px;
  scrollbar-width: auto;
  scrollbar-color: rgba(74, 96, 128, 0.6) transparent;
}

.timeline-wrap::-webkit-scrollbar {
  width: 8px;
}

.timeline-wrap::-webkit-scrollbar-thumb {
  background: rgba(74, 96, 128, 0.6);
  border-radius: 4px;
}

.timeline-wrap::-webkit-scrollbar-track {
  background: transparent;
}

.timeline-card {
  padding: 11px 12px;
  background: rgba(16, 27, 42, 0.9);
  border: 1px solid rgba(48, 67, 91, 0.78);
  border-radius: 12px;
}

.timeline-card__head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: flex-start;
  margin-bottom: 6px;
}

.timeline-card strong {
  color: #f3f6fb;
  font-size: 13px;
  line-height: 1.45;
  min-width: 0;
}

.timeline-card p {
  margin: 0;
  color: #b4c4dc;
  font-size: var(--font-caption);
  line-height: 1.6;
}

.event-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  min-width: 52px;
  height: 24px;
  padding: 0 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
  border: 1px solid transparent;
  white-space: nowrap;
}

.event-pill--active {
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.1);
  border-color: rgba(245, 158, 11, 0.42);
}

.event-pill--handled {
  color: #22c55e;
  background: rgba(34, 197, 94, 0.1);
  border-color: rgba(34, 197, 94, 0.42);
}

.event-pill--recovered {
  color: #38bdf8;
  background: rgba(56, 189, 248, 0.1);
  border-color: rgba(56, 189, 248, 0.38);
}

.event-pill--default {
  color: #cbd5e1;
  background: rgba(148, 163, 184, 0.1);
  border-color: rgba(148, 163, 184, 0.28);
}

.empty-hint {
  padding: 14px 0 4px;
  color: var(--text-label);
  font-size: var(--font-caption);
}
</style>
