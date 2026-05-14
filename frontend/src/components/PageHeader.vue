<template>
  <header class="page-header">
    <div>
      <span v-if="eyebrow" class="app-kicker">{{ eyebrow }}</span>
      <h2>{{ title }}</h2>
      <p v-if="description">{{ description }}</p>
    </div>
    <slot name="actions" />
  </header>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  eyebrow?: string;
  description?: string;
}>();
</script>

<style scoped lang="scss">
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;

  h2 {
    margin: 0;
    font-size: 24px;
  }

  p {
    margin: 6px 0 0;
    color: var(--app-muted);
  }
}

@media (max-width: 760px) {
  .page-header {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
