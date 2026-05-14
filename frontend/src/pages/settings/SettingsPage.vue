<template>
  <section class="settings-page">
    <el-scrollbar>
      <div class="settings-page__grid">
        <el-card shadow="never">
          <PageHeader
            title="Настройки"
            eyebrow="Параметры приложения"
            description="Пока здесь собрана техническая информация и переключатель темы."
          />

          <div class="settings-list">
            <div class="settings-list__row">
              <span>Тема интерфейса</span>
              <ThemeToggle />
            </div>
            <div class="settings-list__row">
              <span>Версия приложения</span>
              <strong>{{ appVersion }}</strong>
            </div>
            <div class="settings-list__row">
              <span>LLM-провайдер</span>
              <strong>{{ llmProvider }}</strong>
            </div>
            <div class="settings-list__row">
              <span>UI kit</span>
              <strong>Element Plus</strong>
            </div>
          </div>
        </el-card>

        <el-card shadow="never">
          <PageHeader
            title="Интеграции"
            eyebrow="Backend"
            description="API-клиент генерируется через Orval по OpenAPI-схеме FastAPI."
          />
          <el-descriptions border :column="1">
            <el-descriptions-item label="OpenAPI">
              /openapi.json
            </el-descriptions-item>
            <el-descriptions-item label="Healthcheck">
              /api/health
            </el-descriptions-item>
            <el-descriptions-item label="LLM">
              mock / yandex
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </div>
    </el-scrollbar>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';

import { getCreditPulseAPI } from '@/api/generated/creditpulse';
import PageHeader from '@/components/PageHeader.vue';
import ThemeToggle from '@/components/ThemeToggle.vue';

const api = getCreditPulseAPI();
const appVersion = ref('0.4.0');
const llmProvider = ref('...');

onMounted(async () => {
  const health = await api.getHealth();
  appVersion.value = health.version ?? appVersion.value;
  llmProvider.value = health.llmProvider ?? llmProvider.value;
});
</script>

<style scoped lang="scss">
.settings-page {
  height: 100%;
  min-height: 0;
  overflow: hidden;

  &__grid {
    display: grid;
    grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr);
    gap: 20px;
    padding-right: 2px;
  }

  :deep(.el-card) {
    border-radius: 8px;
  }
}

.settings-list {
  display: grid;
  gap: 12px;

  &__row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    border: 1px solid var(--app-border);
    border-radius: 8px;
    padding: 14px 16px;
  }
}

@media (max-width: 1100px) {
  .settings-page__grid {
    grid-template-columns: 1fr;
  }
}
</style>
