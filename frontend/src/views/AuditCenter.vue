<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { getAuditSummary, searchAuditEvents, type AuditEvent } from '@/api/audit'

const loading = ref(false)
const events = ref<AuditEvent[]>([])
const total = ref(0)
const summary = ref<{ total: number; outcomes: Record<string, number>; top_actions: Array<{ action: string; count: number }> } | null>(null)

const filters = reactive({
  action: '',
  actor: '',
  outcome: '',
  failed_only: false,
  denied_only: false,
  limit: 20,
  offset: 0,
})

const loadSummary = async () => {
  const response = await getAuditSummary(24)
  summary.value = response
}

const loadEvents = async () => {
  loading.value = true
  try {
    const response = await searchAuditEvents(filters)
    events.value = response.items
    total.value = response.total
  } finally {
    loading.value = false
  }
}

const handlePageChange = async (page: number) => {
  filters.offset = (page - 1) * filters.limit
  await loadEvents()
}

onMounted(async () => {
  await Promise.all([loadSummary(), loadEvents()])
})
</script>

<template>
  <div class="page">
    <div class="hero">
      <div>
        <h2>审计日志</h2>
        <p>查看高风险操作、失败事件和权限拒绝，前端已对齐后端审计查询能力。</p>
      </div>
      <div
        v-if="summary"
        class="stats"
      >
        <el-tag effect="dark">
          24h 总数 {{ summary.total }}
        </el-tag>
        <el-tag
          type="danger"
          effect="dark"
        >
          失败 {{ summary.outcomes.failed || 0 }}
        </el-tag>
        <el-tag
          type="warning"
          effect="dark"
        >
          拒绝 {{ summary.outcomes.denied || 0 }}
        </el-tag>
      </div>
    </div>

    <el-card shadow="never">
      <div class="filters">
        <el-input
          v-model="filters.action"
          placeholder="操作标识"
          clearable
        />
        <el-input
          v-model="filters.actor"
          placeholder="执行人"
          clearable
        />
        <el-select
          v-model="filters.outcome"
          placeholder="结果"
          clearable
        >
          <el-option
            label="成功"
            value="success"
          />
          <el-option
            label="失败"
            value="failed"
          />
          <el-option
            label="拒绝"
            value="denied"
          />
        </el-select>
        <el-checkbox v-model="filters.failed_only">
          仅失败/拒绝
        </el-checkbox>
        <el-checkbox v-model="filters.denied_only">
          仅拒绝
        </el-checkbox>
        <el-button
          type="primary"
          @click="loadEvents"
        >
          查询
        </el-button>
      </div>

      <el-table
        v-loading="loading"
        :data="events"
        class="table"
      >
        <el-table-column
          prop="created_at"
          label="时间"
          min-width="180"
        />
        <el-table-column
          prop="action"
          label="操作"
          min-width="160"
        />
        <el-table-column
          prop="actor"
          label="执行人"
          width="120"
        />
        <el-table-column
          prop="target"
          label="目标"
          min-width="180"
        />
        <el-table-column
          prop="outcome"
          label="结果"
          width="100"
        />
        <el-table-column
          label="细节"
          min-width="260"
        >
          <template #default="{ row }">
            <pre class="details">{{ JSON.stringify(row.details, null, 2) }}</pre>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          layout="prev, pager, next, total"
          :total="total"
          :page-size="filters.limit"
          :current-page="Math.floor(filters.offset / filters.limit) + 1"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.page {
  display: grid;
  gap: 16px;
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: start;
}

.hero h2, .hero p {
  margin: 0;
}

.hero p {
  color: #94a3b8;
  margin-top: 6px;
}

.stats {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.filters {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
  align-items: center;
}

.details {
  margin: 0;
  white-space: pre-wrap;
  font-size: 12px;
  color: #94a3b8;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
