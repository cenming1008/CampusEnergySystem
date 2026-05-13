<template>
  <div
    class="monitor-view-shell"
    :class="{ 'monitor-view-shell--main-only': !$slots.side }"
  >
    <div
      v-if="$slots.header"
      class="monitor-view-shell__header"
    >
      <slot name="header" />
    </div>

    <div class="monitor-view-shell__grid">
      <section class="monitor-view-shell__main">
        <slot name="main" />
      </section>

      <aside
        v-if="$slots.side"
        class="monitor-view-shell__side"
      >
        <slot name="side" />
      </aside>
    </div>
  </div>
</template>

<style scoped>
.monitor-view-shell {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.monitor-view-shell__grid {
  display: grid;
  grid-template-columns: minmax(0, 1.95fr) 360px;
  gap: 16px;
}

.monitor-view-shell--main-only .monitor-view-shell__grid {
  grid-template-columns: minmax(0, 1fr);
}

.monitor-view-shell__main,
.monitor-view-shell__side {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

@media (min-width: 1920px) {
  .monitor-view-shell {
    gap: 20px;
  }

  .monitor-view-shell__grid {
    grid-template-columns: minmax(0, 1.95fr) 440px;
    gap: 20px;
  }
}

@media (min-width: 2400px) {
  .monitor-view-shell {
    gap: 24px;
  }

  .monitor-view-shell__grid {
    grid-template-columns: minmax(0, 1.95fr) 520px;
    gap: 24px;
  }
}

@media (max-width: 1360px) {
  .monitor-view-shell__grid {
    grid-template-columns: 1fr;
  }
}
</style>
