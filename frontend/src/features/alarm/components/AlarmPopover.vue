<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAlarmPolling } from '@/features/alarm/composables/useAlarmPolling'

const router = useRouter()
const { alarmCount, alarmList, clearAlarms } = useAlarmPolling()

const formatTime = (timestamp: string) => {
  if (!timestamp) return ''

  try {
    const date = new Date(timestamp)
    const now = new Date()
    const days = Math.floor((now.getTime() - date.getTime()) / 86400000)

    if (date.toDateString() === now.toDateString()) {
      return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    }

    if (days === 1) {
      return `昨天 ${date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`
    }

    if (days < 7) {
      return `${days}天前`
    }

    return date.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (_error) {
    return timestamp
  }
}
</script>

<template>
  <el-popover
    placement="bottom"
    title="未处理报警"
    :width="300"
    trigger="click"
    popper-class="alarm-popper"
  >
    <template #reference>
      <div class="tool-item alarm-wrapper">
        <el-badge
          :value="alarmCount"
          :hidden="alarmCount === 0"
          class="item"
        >
          <el-button
            circle
            :class="{ 'has-alarm': alarmCount > 0 }"
          >
            <el-icon><Bell /></el-icon>
          </el-button>
        </el-badge>
      </div>
    </template>

    <div class="alarm-list">
      <div
        v-if="alarmList.length === 0"
        class="empty-alarm"
      >
        系统运行正常
      </div>
      <div
        v-for="alarm in alarmList"
        v-else
        :key="alarm.id"
        class="alarm-item"
      >
        <el-icon color="#ef4444">
          <Warning />
        </el-icon>
        <div class="alarm-content">
          <div class="msg">
            {{ alarm.message }}
          </div>
          <div class="time">
            {{ formatTime(alarm.timestamp) }}
          </div>
        </div>
      </div>
      <div
        v-if="alarmList.length > 0"
        class="alarm-footer"
      >
        <el-button
          type="primary"
          link
          size="small"
          @click="clearAlarms"
        >
          全部清除
        </el-button>
        <el-button
          type="primary"
          link
          size="small"
          @click="router.push('/alarms')"
        >
          查看全部
        </el-button>
      </div>
    </div>
  </el-popover>
</template>

<style scoped>
.alarm-list {
  max-height: 300px;
  overflow-y: auto;
}

.alarm-item {
  display: flex;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid #eee;
}

.alarm-content .msg {
  font-size: 13px;
  color: #333;
}

.alarm-content .time {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.alarm-footer {
  text-align: center;
  margin-top: 10px;
}

.empty-alarm {
  text-align: center;
  color: #999;
  padding: 20px;
}
</style>
