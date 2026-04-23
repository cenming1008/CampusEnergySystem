<script setup lang="ts">
import { computed } from 'vue'
import type { CompensationCapacitorBankControlProfile } from '@/api/compensation'
import {
  formatCapacitorBankControlValue,
  type CapacitorBankControlParameterMeta,
} from '@/features/device-control/capacitorBankControlProfile'
import MonitorInlineAlert from '@/shared/components/MonitorInlineAlert.vue'

const props = defineProps<{
  modelValue: boolean
  selectedWriteMeta: CapacitorBankControlParameterMeta | null
  controlProfile: CompensationCapacitorBankControlProfile | null
  targetValue: string | number | boolean | null
  reason: string
  writeSubmitting: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'update:targetValue', value: string | number | boolean | null): void
  (e: 'update:reason', value: string): void
  (e: 'submit'): void
}>()

const numericPrecision = computed(() => {
  const step = props.selectedWriteMeta?.step
  if (!step || step >= 1) return 0
  return Math.round(-Math.log10(step))
})
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    width="560px"
    :close-on-click-modal="false"
    title="参数写入"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <template v-if="selectedWriteMeta">
      <div class="dialog-intro">
        <strong>{{ selectedWriteMeta.label }}</strong>
        <span>{{ selectedWriteMeta.description }}</span>
      </div>
      <div class="dialog-current">
        <span>当前快照值</span>
        <strong>{{ formatCapacitorBankControlValue(controlProfile, selectedWriteMeta) }}</strong>
      </div>
      <el-form label-position="top">
        <el-form-item label="目标值">
          <el-switch
            v-if="selectedWriteMeta.inputKind === 'boolean'"
            :model-value="targetValue"
            inline-prompt
            active-text="开启"
            inactive-text="关闭"
            @update:model-value="emit('update:targetValue', $event)"
          />
          <el-select
            v-else-if="selectedWriteMeta.inputKind === 'select'"
            :model-value="targetValue"
            style="width: 100%"
            @update:model-value="emit('update:targetValue', $event)"
          >
            <el-option
              v-for="item in selectedWriteMeta.options || []"
              :key="String(item.value)"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
          <el-input
            v-else-if="selectedWriteMeta.inputKind === 'text'"
            :model-value="targetValue"
            placeholder="请输入参数值"
            @update:model-value="emit('update:targetValue', $event)"
          />
          <template v-else>
            <el-input-number
              :model-value="targetValue"
              :min="selectedWriteMeta.min"
              :max="selectedWriteMeta.max"
              :step="selectedWriteMeta.step || 1"
              :precision="numericPrecision"
              style="width: 100%"
              @update:model-value="emit('update:targetValue', $event)"
            />
            <div
              v-if="selectedWriteMeta.min !== undefined || selectedWriteMeta.max !== undefined"
              class="range-hint"
            >
              范围：{{ selectedWriteMeta.min ?? '—' }} ~ {{ selectedWriteMeta.max ?? '—' }}{{ selectedWriteMeta.unit ? ' ' + selectedWriteMeta.unit : '' }}
            </div>
          </template>
        </el-form-item>
        <el-form-item label="写入说明（选填）">
          <el-input
            :model-value="reason"
            type="textarea"
            :rows="3"
            maxlength="120"
            show-word-limit
            placeholder="例如：联调验证 / 现场调优 / 告警阈值收敛"
            @update:model-value="emit('update:reason', $event)"
          />
        </el-form-item>
      </el-form>
      <MonitorInlineAlert
        title="风险提示"
        message="接口当前仅表示 accepted 入队；提交后请结合设备回读、控制日志与现场反馈确认实际执行结果。"
        subtle
      />
    </template>
    <template #footer>
      <div class="dialog-actions">
        <el-button @click="emit('update:modelValue', false)">取消</el-button>
        <el-button
          type="warning"
          :loading="writeSubmitting"
          @click="emit('submit')"
        >
          确认写入
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
.dialog-intro,
.dialog-current {
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid rgba(48, 70, 95, 0.65);
  background: rgba(19, 34, 53, 0.74);
}

.dialog-current {
  margin-top: 10px;
  margin-bottom: 14px;
}

.dialog-intro strong,
.dialog-current strong {
  display: block;
  color: #eef5ff;
}

.dialog-intro span,
.dialog-current span {
  display: block;
  margin-top: 6px;
  color: #8ca0ba;
  font-size: 12px;
  line-height: 1.6;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
}

.range-hint {
  margin-top: 5px;
  font-size: 11px;
  color: #6b84a3;
}
</style>
