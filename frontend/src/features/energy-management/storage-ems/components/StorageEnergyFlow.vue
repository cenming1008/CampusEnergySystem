<script setup lang="ts">
import type { StorageEnergyCurrent } from '@/api/storageEnergy'

defineProps<{
  current: StorageEnergyCurrent | null
}>()

function power(label: string, value: number | null | undefined): string {
  return `${label} ${value == null ? '--' : value.toFixed(1)} kW`
}
</script>

<template>
  <section
    class="storage-flow"
    aria-labelledby="storage-flow-title"
  >
    <div class="storage-section-heading">
      <div>
        <p class="storage-eyebrow">
          CURRENT FLOW
        </p>
        <h2 id="storage-flow-title">
          园区实时能流
        </h2>
      </div>
      <p>储能正值为充电，负值为放电</p>
    </div>
    <div class="storage-flow__line">
      <div class="storage-flow__node storage-flow__node--load">
        <span>园区</span>
        <strong>{{ power('负荷', current?.load_kw) }}</strong>
      </div>
      <span
        class="storage-flow__connector"
        aria-hidden="true"
      />
      <div class="storage-flow__node storage-flow__node--pv">
        <span>发电</span>
        <strong>{{ power('光伏', current?.pv_kw) }}</strong>
      </div>
      <span
        class="storage-flow__connector"
        aria-hidden="true"
      />
      <div class="storage-flow__node storage-flow__node--grid">
        <span>公共电网</span>
        <strong>{{ power('电网', current?.grid_kw) }}</strong>
      </div>
      <span
        class="storage-flow__connector"
        aria-hidden="true"
      />
      <div class="storage-flow__node storage-flow__node--storage">
        <span>电池系统</span>
        <strong>{{ power('储能', current?.storage_kw) }}</strong>
      </div>
    </div>
  </section>
</template>

<style scoped>
.storage-flow { padding: 18px 20px; border: 1px solid var(--em-border); border-radius: 14px; background: rgba(16, 22, 30, .72); }
.storage-section-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; margin-bottom: 16px; }
.storage-section-heading h2 { margin: 2px 0 0; font-size: 17px; color: var(--em-text); }
.storage-section-heading > p { margin: 0; color: var(--em-muted); font-size: 12px; }
.storage-eyebrow { margin: 0; font-size: 9px; letter-spacing: .12em; color: var(--em-subtle); }
.storage-flow__line { display: grid; grid-template-columns: 1fr 28px 1fr 28px 1fr 28px 1fr; align-items: center; }
.storage-flow__node { min-width: 0; padding-left: 12px; border-left: 2px solid var(--node-color, var(--em-cyan)); }
.storage-flow__node span { display: block; margin-bottom: 5px; color: var(--em-muted); font-size: 11px; }
.storage-flow__node strong { display: block; color: var(--em-text); font-size: 15px; white-space: nowrap; }
.storage-flow__node--load { --node-color: var(--em-amber); }
.storage-flow__node--pv { --node-color: var(--em-cyan); }
.storage-flow__node--grid { --node-color: var(--em-blue); }
.storage-flow__node--storage { --node-color: #a7f3d0; }
.storage-flow__connector { height: 1px; background: linear-gradient(90deg, var(--em-border), rgba(94, 234, 212, .55), var(--em-border)); }
@media (max-width: 820px) {
  .storage-flow__line { grid-template-columns: repeat(2, 1fr); gap: 16px; }
  .storage-flow__connector { display: none; }
  .storage-section-heading { align-items: flex-start; flex-direction: column; }
}
</style>
