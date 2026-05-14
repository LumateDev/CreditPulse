<template>
  <aside class="assistant-borrowers">
    <PageHeader
      title="Клиенты"
      eyebrow="Выбор карточки"
      description="Каждый клиент ведет отдельную историю диалога."
    />

    <el-input
      :disabled="disabled"
      :model-value="search"
      :prefix-icon="Search"
      clearable
      placeholder="Поиск клиента"
      size="large"
      @update:model-value="emit('update:search', String($event))"
    />

    <el-scrollbar v-loading="loading" class="assistant-borrowers__scroll">
      <div class="borrower-list">
        <button
          v-for="borrower in borrowers"
          :key="borrower.id"
          class="borrower-card"
          :class="{ active: selectedId === borrower.id }"
          :disabled="disabled"
          type="button"
          @click="emit('select', borrower.id)"
        >
          <span class="borrower-card__top">
            <strong>{{ borrower.name }}</strong>
            <el-tag
              :type="borrower.creditHistory === 'poor' ? 'danger' : 'success'"
              effect="light"
              round
            >
              {{ borrower.display.creditHistory }}
            </el-tag>
          </span>
          <span class="borrower-card__meta">
            {{ borrower.age }} лет · {{ borrower.display.employmentType }} ·
            {{ borrower.display.housingType }}
          </span>
          <span class="borrower-card__grid">
            <span>
              <small>Доход</small>
              {{ borrower.display.income }}
            </span>
            <span>
              <small>Кредит</small>
              {{ borrower.display.loanAmount }}
            </span>
            <span>
              <small>Срок</small>
              {{ borrower.display.loanTerm }}
            </span>
            <span>
              <small>Нагрузка</small>
              {{ borrower.display.debtLoad }}
            </span>
          </span>
        </button>
      </div>
    </el-scrollbar>
  </aside>
</template>

<script setup lang="ts">
import { Search } from '@element-plus/icons-vue';

import type { BorrowerCard } from '@/api/generated/creditpulse';
import PageHeader from '@/components/PageHeader.vue';

defineProps<{
  borrowers: BorrowerCard[];
  selectedId: string;
  search: string;
  loading: boolean;
  disabled: boolean;
}>();

const emit = defineEmits<{
  select: [borrowerId: string];
  'update:search': [value: string];
}>();
</script>

<style scoped lang="scss">
.assistant-borrowers {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: var(--app-panel);
  padding: 20px;

  &__scroll {
    flex: 1;
    min-height: 0;
  }
}

.borrower-list {
  display: grid;
  gap: 12px;
  padding-right: 2px;
}

.borrower-card {
  display: grid;
  gap: 10px;
  width: 100%;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: var(--el-fill-color-blank);
  padding: 16px;
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease,
    opacity 0.18s ease;

  &:hover,
  &.active {
    border-color: var(--el-color-primary);
    background: var(--el-color-primary-light-9);
    box-shadow: var(--el-box-shadow-light);
  }

  &:disabled {
    cursor: not-allowed;
    opacity: 0.72;
  }

  &__top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;

    strong {
      font-size: 16px;
    }
  }

  &__meta {
    color: var(--app-muted);
    font-size: 13px;
  }

  &__grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
    font-size: 14px;

    span {
      min-width: 0;
      overflow-wrap: anywhere;
    }

    small {
      display: block;
      margin-bottom: 3px;
      color: var(--app-muted);
      font-size: 12px;
    }
  }
}

@media (max-width: 1100px) {
  .assistant-borrowers__scroll {
    max-height: 460px;
  }
}
</style>
