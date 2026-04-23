<script setup lang="ts">
import { reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { upsertCompensationSvgOperationsProfile, type CompensationSvgOperationsProfile } from '@/api/compensation'

const props = defineProps<{
  modelValue: boolean
  deviceId: number
  profile: CompensationSvgOperationsProfile | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'saved', profile: CompensationSvgOperationsProfile): void
}>()

const submitting = defineModel<boolean>('submitting', { default: false })

const form = reactive<Partial<CompensationSvgOperationsProfile>>({})

watch(() => props.modelValue, (open) => {
  if (!open) return
  const p: Partial<CompensationSvgOperationsProfile> = props.profile ?? {}
  Object.assign(form, {
    model_number: p.model_number ?? null,
    rated_voltage: p.rated_voltage ?? null,
    rated_frequency: p.rated_frequency ?? null,
    module_count: p.module_count ?? null,
    single_module_capacity: p.single_module_capacity ?? null,
    device_label_zh: p.device_label_zh ?? null,
    asset_number: p.asset_number ?? null,
    distribution_room: p.distribution_room ?? null,
    distribution_cabinet: p.distribution_cabinet ?? null,
    circuit: p.circuit ?? null,
    install_date: p.install_date ?? null,
    commission_date: p.commission_date ?? null,
    om_responsible: p.om_responsible ?? null,
    contact_phone: p.contact_phone ?? null,
    maintenance_cycle_days: p.maintenance_cycle_days ?? null,
  })
})

async function handleSubmit() {
  submitting.value = true
  try {
    const result = await upsertCompensationSvgOperationsProfile(props.deviceId, form)
    ElMessage.success('档案已保存')
    emit('saved', result)
    emit('update:modelValue', false)
  } catch {
    ElMessage.error('保存失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    title="编辑 SVG 运维档案"
    width="680px"
    :close-on-click-modal="false"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <el-form
      label-position="top"
      class="profile-form"
    >
      <div class="form-section-title">设备铭牌</div>
      <div class="form-row">
        <el-form-item label="型号">
          <el-input v-model="form.model_number" placeholder="例：SVG-200kVar" />
        </el-form-item>
        <el-form-item label="中文标识">
          <el-input v-model="form.device_label_zh" placeholder="例：2号配电室SVG" />
        </el-form-item>
      </div>
      <div class="form-row">
        <el-form-item label="额定电压 (V)">
          <el-input-number v-model="form.rated_voltage" :min="0" :max="35000" :step="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="额定频率 (Hz)">
          <el-input-number v-model="form.rated_frequency" :min="40" :max="70" :step="1" style="width:100%" />
        </el-form-item>
      </div>
      <div class="form-row">
        <el-form-item label="模块数量">
          <el-input-number v-model="form.module_count" :min="0" :max="100" :step="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="单模块容量 (kVar)">
          <el-input-number v-model="form.single_module_capacity" :min="0" :max="2000" :step="0.1" :precision="1" style="width:100%" />
        </el-form-item>
      </div>

      <div class="form-section-title">安装位置</div>
      <div class="form-row">
        <el-form-item label="配电室">
          <el-input v-model="form.distribution_room" placeholder="例：2楼高压配电室" />
        </el-form-item>
        <el-form-item label="配电柜">
          <el-input v-model="form.distribution_cabinet" placeholder="例：2P-SVG柜" />
        </el-form-item>
      </div>
      <div class="form-row">
        <el-form-item label="回路">
          <el-input v-model="form.circuit" placeholder="例：2P-05" />
        </el-form-item>
        <el-form-item label="资产编号">
          <el-input v-model="form.asset_number" placeholder="例：FA-2023-0012" />
        </el-form-item>
      </div>

      <div class="form-section-title">运维信息</div>
      <div class="form-row">
        <el-form-item label="安装日期">
          <el-date-picker
            v-model="form.install_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择安装日期"
            style="width:100%"
          />
        </el-form-item>
        <el-form-item label="投运日期">
          <el-date-picker
            v-model="form.commission_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择投运日期"
            style="width:100%"
          />
        </el-form-item>
      </div>
      <div class="form-row">
        <el-form-item label="运维负责人">
          <el-input v-model="form.om_responsible" placeholder="例：张工" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="form.contact_phone" placeholder="例：138-0000-0000" />
        </el-form-item>
      </div>
      <div class="form-row">
        <el-form-item label="维护周期 (天)">
          <el-input-number v-model="form.maintenance_cycle_days" :min="1" :max="3650" :step="1" style="width:100%" />
        </el-form-item>
        <div class="form-placeholder" />
      </div>
    </el-form>

    <template #footer>
      <div class="dialog-actions">
        <el-button @click="emit('update:modelValue', false)">取消</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          保存档案
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
.profile-form {
  padding: 0 2px;
}

.form-section-title {
  font-size: 12px;
  font-weight: 600;
  color: #8ea0bc;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin: 16px 0 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(53, 72, 97, 0.4);
}

.form-section-title:first-child {
  margin-top: 0;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.form-placeholder {
  flex: 1;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
