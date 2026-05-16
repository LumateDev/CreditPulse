<template>
  <el-container class="app-shell" :class="{ 'app-shell--collapsed': isSidebarCollapsed }">
    <el-aside class="app-shell__aside" :width="sidebarWidth">
      <section class="app-shell__brand">
        <el-icon class="app-shell__brand-icon"><CreditCard /></el-icon>
        <span class="app-kicker">ИСППР</span>
        <strong>CreditPulse</strong>
      </section>

      <el-menu
        class="app-shell__menu"
        :collapse="isSidebarCollapsed"
        :default-active="activePath"
        router
      >
        <el-menu-item index="/">
          <el-icon><ChatDotRound /></el-icon>
          <template #title>Ассистент</template>
        </el-menu-item>
        <el-menu-item index="/clients">
          <el-icon><User /></el-icon>
          <template #title>Клиентская база</template>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <template #title>Настройки</template>
        </el-menu-item>
      </el-menu>

      <div class="app-shell__collapse-area">
        <el-tooltip
          :content="isSidebarCollapsed ? 'Развернуть меню' : 'Свернуть меню'"
          placement="right"
        >
          <el-button
            class="app-shell__collapse-toggle"
            :icon="isSidebarCollapsed ? ArrowRight : ArrowLeft"
            circle
            plain
            @click="toggleSidebar"
          />
        </el-tooltip>
      </div>
    </el-aside>

    <el-container class="app-shell__content">
      <el-header class="app-shell__header">
        <div>
          <span class="app-kicker">Раздел</span>
          <h1>{{ route.meta.title }}</h1>
        </div>
        <el-tag effect="plain" type="info">v{{ appVersion }}</el-tag>
      </el-header>

      <el-main class="app-shell__main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import {
  ArrowLeft,
  ArrowRight,
  ChatDotRound,
  CreditCard,
  Setting,
  User,
} from '@element-plus/icons-vue';
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';

import { getCreditPulseAPI } from '@/api/generated/creditpulse';
import { useAppStore } from '@/stores/AppStore';
import { APP_VERSION } from '@/version';

const route = useRoute();
const api = getCreditPulseAPI();
const appVersion = ref(APP_VERSION);
const { isSidebarCollapsed, sidebarWidth, toggleSidebar } = useAppStore();

const activePath = computed(() => route.path);

onMounted(async () => {
  const health = await api.getHealth();
  appVersion.value = health.version ?? appVersion.value;
});
</script>

<style scoped lang="scss">
.app-shell {
  width: 100%;
  height: 100%;
  overflow: hidden;

  &__aside {
    display: flex;
    flex-direction: column;
    overflow-x: hidden;
    border-right: 1px solid var(--app-border);
    background: var(--app-panel);
    transition: width 0.2s ease;
  }

  &__brand {
    display: grid;
    min-height: 112px;
    padding: 28px 24px 22px;
    transition: padding 0.2s ease;

    strong {
      display: block;
      overflow: hidden;
      font-size: 28px;
      line-height: 1;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }

  &__brand-icon {
    display: none;
    margin: 0 auto;
    color: var(--el-color-primary);
    font-size: 28px;
  }

  &__menu {
    flex: 1;
    min-height: 0;
    overflow-x: hidden;
    border-right: 0;

    &:not(.el-menu--collapse) {
      width: 100%;
    }

    :deep(.el-menu-item) {
      height: 54px;
      margin: 4px 12px;
      border-radius: 8px;
      font-size: 15px;
      font-weight: 600;
      line-height: 54px;
    }

    :deep(.el-icon) {
      width: 22px;
      font-size: 20px;
    }

    :deep(.el-tooltip__trigger) {
      justify-content: center;
    }
  }

  &__collapse-area {
    display: flex;
    flex: 0 0 64px;
    align-items: center;
    justify-content: flex-end;
    min-height: 64px;
    padding: 0 22px;
  }

  &__collapse-toggle {
    width: 30px;
    height: 30px;
    border-color: var(--app-border);
    color: var(--app-muted);
  }

  &__content {
    min-width: 0;
    min-height: 0;
  }

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: auto;
    border-bottom: 1px solid var(--app-border);
    background: var(--app-panel);
    padding: 18px 24px;

    h1 {
      margin: 0;
      font-size: 24px;
      line-height: 1.2;
    }
  }

  &__main {
    min-width: 0;
    min-height: 0;
    overflow: hidden;
    padding: 24px;
  }

  &--collapsed {
    .app-shell__brand {
      place-items: center;
      min-height: 112px;
      padding: 28px 10px 22px;

      .app-kicker,
      strong {
        display: none;
      }
    }

    .app-shell__brand-icon {
      display: inline-flex;
    }

    .app-shell__menu {
      width: 76px;

      :deep(.el-menu-item) {
        justify-content: center;
        width: 44px;
        margin: 4px auto;
        padding: 0;
      }
    }

    .app-shell__collapse-area {
      justify-content: center;
      padding-inline: 0;
    }
  }
}

@media (max-width: 760px) {
  .app-shell {
    &__main {
      padding: 16px;
    }
  }
}
</style>
