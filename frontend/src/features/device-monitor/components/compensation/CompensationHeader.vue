<script setup lang="ts">
import { ArrowLeft, Refresh, SwitchButton } from '@element-plus/icons-vue'
import type { PropType } from 'vue'
import type { CompensationHeaderModel } from './types'

defineProps({
  model: {
    type: Object as PropType<CompensationHeaderModel>,
    required: true,
  },
  toggleActionLabel: {
    type: String,
    required: true,
  },
  toggleButtonType: {
    type: String,
    required: true,
  },
  toggleSubmitting: {
    type: Boolean,
    default: false,
  },
  canControlDevices: {
    type: Boolean,
    default: false,
  },
})

defineEmits<{
  back: []
  refresh: []
  toggle: []
}>()

function tagType(tone: CompensationHeaderModel['tags'][number]['tone']) {
  if (tone === 'success') return 'success'
  if (tone === 'warning') return 'warning'
  if (tone === 'danger') return 'danger'
  if (tone === 'info') return 'primary'
  return 'info'
}
</script>

<template>
  <div class="comp-header">
    <div class="comp-header__left">
      <el-button
        :icon="ArrowLeft"
        text
        @click="$emit('back')"
      >
        返回设备台账
      </el-button>
      <div class="comp-header__title">
        <h2>{{ model.title }}</h2>
        <p>设备编号：{{ model.serial }} · 安装位置：{{ model.location }}</p>
      </div>
    </div>

    <div class="comp-header__right">
      <div class="comp-header__tags">
        <el-tag
          v-for="tag in model.tags"
          :key="tag.label"
          effect="dark"
          :type="tagType(tag.tone)"
          class="comp-header__tag"
        >
          {{ tag.label }}
        </el-tag>
        <el-tag
          effect="plain"
          :type="tagType(model.deviceStatusTone)"
          class="comp-header__tag comp-header__tag--outline"
        >
          {{ model.deviceStatus }}
        </el-tag>
      </div>

      <div class="comp-header__actions">
        <el-button
          :type="toggleButtonType"
          plain
          :icon="SwitchButton"
          :loading="toggleSubmitting"
          :disabled="!canControlDevices"
          @click="$emit('toggle')"
        >
          {{ toggleActionLabel }}
        </el-button>
        <el-button
          :icon="Refresh"
          @click="$emit('refresh')"
        >
          刷新
        </el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.comp-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  padding: 20px 22px;
  background:
    linear-gradient(135deg, rgba(14, 25, 40, 0.98), rgba(18, 32, 50, 0.96)),
    radial-gradient(circle at top right, rgba(0, 172, 193, 0.16), transparent 42%);
  border: 1px solid rgba(58, 76, 102, 0.88);
  border-radius: 16px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.comp-header__left {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.comp-header__title h2 {
  margin: 0;
  font-size: 24px;
  color: #f5f7fb;
  letter-spacing: 0.02em;
}

.comp-header__title p {
  margin: 6px 0 0;
  font-size: 12px;
  color: #8ea0bc;
}

.comp-header__right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12px;
}

.comp-header__tags,
.comp-header__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.comp-header__tag {
  border: none;
  letter-spacing: 0.04em;
}

.comp-header__tag--outline {
  background: rgba(20, 31, 47, 0.76);
}

@media (max-width: 1320px) {
  .comp-header {
    flex-direction: column;
  }

  .comp-header__right {
    width: 100%;
    align-items: flex-start;
  }

  .comp-header__tags,
  .comp-header__actions {
    justify-content: flex-start;
  }
}
</style>
