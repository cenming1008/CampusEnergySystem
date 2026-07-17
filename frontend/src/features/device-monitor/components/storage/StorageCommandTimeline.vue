<script setup lang="ts">
import type { StorageCommandTimelineItem } from './types'

defineProps<{
  items: StorageCommandTimelineItem[]
}>()

function resultClass(result: string) {
  if (result === 'success') return 'is-success'
  if (result === 'accepted' || result === 'running') return 'is-pending'
  if (['failed', 'timeout', 'rejected'].includes(result)) return 'is-danger'
  return ''
}
</script>

<template>
  <section class="command-timeline">
    <div class="command-timeline__head">
      <h3>控制命令</h3>
      <span>{{ items.length }} 条</span>
    </div>
    <div
      v-if="items.length"
      class="command-timeline__list"
    >
      <article
        v-for="item in items"
        :key="`${item.commandId}-${item.result}`"
      >
        <i :class="resultClass(item.result)" />
        <div>
          <div class="command-timeline__title">
            <strong>{{ item.actionLabel }}</strong>
            <span :class="resultClass(item.result)">{{ item.resultLabel }}</span>
          </div>
          <p v-if="item.detail">
            {{ item.detail }}
          </p>
          <small>{{ item.createdAt }} · #{{ item.commandId }}</small>
        </div>
      </article>
    </div>
    <p
      v-else
      class="command-timeline__empty"
    >
      暂无储能控制命令
    </p>
  </section>
</template>

<style scoped>
.command-timeline { padding: 16px; border: 1px solid rgba(53, 72, 97, 0.88); border-radius: 16px; background: linear-gradient(180deg, rgba(18, 32, 50, 0.96), rgba(13, 22, 35, 0.98)); }
.command-timeline__head, .command-timeline__title { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.command-timeline__head h3 { margin: 0; color: #f5f7fb; font-size: 15px; }
.command-timeline__head > span { color: #64748b; font-size: 11px; }
.command-timeline__list { display: flex; flex-direction: column; margin-top: 12px; }
.command-timeline article { display: grid; grid-template-columns: 9px minmax(0, 1fr); gap: 9px; padding: 10px 0; border-bottom: 1px solid rgba(41, 57, 77, 0.72); }
.command-timeline article:last-child { border-bottom: 0; }
.command-timeline article > i { width: 8px; height: 8px; margin-top: 5px; border-radius: 999px; background: #64748b; }
.command-timeline article > i.is-success { background: #4ade80; }
.command-timeline article > i.is-pending { background: #60a5fa; }
.command-timeline article > i.is-danger { background: #fb7185; }
.command-timeline__title strong { color: #e5edf7; font-size: 12px; }
.command-timeline__title span { color: #94a3b8; font-size: 11px; }
.command-timeline__title span.is-success { color: #4ade80; }
.command-timeline__title span.is-pending { color: #60a5fa; }
.command-timeline__title span.is-danger { color: #fb7185; }
.command-timeline p { margin: 5px 0; color: #cbd5e1; font-size: 11px; line-height: 1.5; }
.command-timeline small { color: #64748b; font-size: 10px; }
.command-timeline__empty { margin: 18px 0 4px; color: #64748b; text-align: center; font-size: 12px; }
</style>
