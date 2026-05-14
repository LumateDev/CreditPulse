<template>
  <div class="theme-toggle">
    <span>{{ isDark ? 'Темная тема' : 'Светлая тема' }}</span>
    <el-switch
      :model-value="isDark"
      @update:model-value="setTheme(Boolean($event))"
    />
  </div>
</template>

<script setup lang="ts">
import { useAppStore } from '@/stores/AppStore';

const { isDark, setTheme } = useAppStore();
</script>

<style scoped lang="scss">
.theme-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: var(--app-muted);
  font-size: 14px;
}
</style>
