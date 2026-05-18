<script setup lang="ts">
withDefaults(defineProps<{
  title?: string
  sectionLabel?: string
  tone?: 'readonly' | 'writable'
  description?: string
  metaText?: string
  tags?: Array<{ text: string; tone: 'success' | 'warning' | 'info' }>
  locked?: boolean
}>(), {
  title: '',
  sectionLabel: '',
  tone: 'readonly',
  description: '',
  metaText: '',
  tags: () => [],
  locked: false,
})
</script>

<template>
  <section
    class="control-console-parameter-section"
    :class="[
      `control-console-parameter-section--${tone}`,
      { 'control-console-parameter-section--locked': locked },
    ]"
  >
    <div class="control-console-parameter-section__head">
      <div class="control-console-parameter-section__head-main">
        <span
          v-if="sectionLabel"
          class="control-console-parameter-section__label"
        >
          {{ sectionLabel }}
        </span>
        <h4 v-if="title">{{ title }}</h4>
      </div>
      <div
        v-if="tags.length || metaText"
        class="control-console-parameter-section__head-right"
      >
        <el-tag
          v-for="tag in tags"
          :key="tag.text"
          :type="tag.tone"
          effect="dark"
          size="small"
        >
          {{ tag.text }}
        </el-tag>
        <small v-if="metaText">{{ metaText }}</small>
      </div>
    </div>
    <p
      v-if="description"
      class="control-console-parameter-section__desc"
    >
      {{ description }}
    </p>
    <slot name="alert" />
    <slot />
  </section>
</template>

<style scoped>
.control-console-parameter-section {
  margin-top: 16px;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid transparent;
}

.control-console-parameter-section__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.control-console-parameter-section__head-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.control-console-parameter-section__head-main h4 {
  margin: 0;
  font-size: 14px;
  color: #eef4fd;
}

.control-console-parameter-section__head-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.control-console-parameter-section__head-right small {
  color: #7a90ab;
  font-size: 11px;
}

.control-console-parameter-section__label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
}

.control-console-parameter-section__desc {
  margin: 0 0 12px;
  color: #8ca0ba;
  font-size: 12px;
  line-height: 1.7;
}

.control-console-parameter-section--readonly,
.control-console-parameter-section--writable {
  background:
    linear-gradient(180deg, rgba(45, 212, 191, 0.035), rgba(12, 24, 39, 0.56)),
    rgba(20, 38, 58, 0.22);
  border-color: rgba(71, 100, 135, 0.36);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.025);
}

.control-console-parameter-section--readonly .control-console-parameter-section__label,
.control-console-parameter-section--writable .control-console-parameter-section__label {
  color: #7fafd4;
}

.control-console-parameter-section--locked {
  opacity: 0.75;
  border-style: dashed;
}
</style>
