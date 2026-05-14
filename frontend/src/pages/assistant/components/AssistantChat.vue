<template>
  <section class="assistant-chat">
    <header class="assistant-chat__header">
      <div>
        <span class="app-kicker">Клиентский чат</span>
        <h2>{{ borrower.name }}</h2>
      </div>
      <div class="assistant-chat__actions">
        <el-button :icon="RefreshRight" plain @click="emit('reset')">
          Новый чат
        </el-button>
        <el-button
          :loading="loading"
          type="primary"
          @click="emit('ask', defaultQuestion)"
        >
          Получить рекомендацию
        </el-button>
      </div>
    </header>

    <section class="summary-strip">
      <el-statistic title="Доход" :value="borrower.display.income" />
      <el-statistic title="Сумма кредита" :value="borrower.display.loanAmount" />
      <el-statistic title="Срок" :value="borrower.display.loanTerm" />
      <el-statistic title="Кредитная нагрузка" :value="borrower.display.debtLoad" />
    </section>

    <el-scrollbar ref="chatScrollbar" class="chat-scroll">
      <div class="chat-feed">
        <el-empty
          v-if="messages.length === 0"
          description="Задайте вопрос или получите рекомендацию."
        />

        <article
          v-for="message in messages"
          :key="message.id"
          class="chat-message"
          :class="message.role"
        >
          <div class="chat-message__bubble">
            <strong v-if="message.role === 'user'">{{ borrower.name }}</strong>
            <p>{{ message.text }}</p>
            <div v-if="message.result" class="result-panel">
              <el-tag
                :type="message.result.borrowerClass === 'good' ? 'success' : 'danger'"
                effect="light"
              >
                Риск {{ percent(message.result.defaultProbability) }}
              </el-tag>
              <el-tag
                :type="message.result.borrowerClass === 'good' ? 'success' : 'danger'"
                effect="plain"
              >
                {{ message.result.recommendation }}
              </el-tag>
              <el-tag effect="plain">
                Платеж {{ money(message.result.loanMetrics.monthlyPayment) }}
              </el-tag>
              <el-tag effect="plain">
                Платеж/доход {{ percent(message.result.loanMetrics.paymentToIncome) }}
              </el-tag>
            </div>

            <div
              v-if="message.mlResult && message.aiAssessment && message.comparison"
              class="comparison-grid"
            >
              <section class="comparison-card">
                <span>Classic ML</span>
                <strong>{{ percent(message.mlResult.defaultProbability) }}</strong>
                <el-tag
                  :type="message.mlResult.borrowerClass === 'good' ? 'success' : 'danger'"
                  effect="light"
                >
                  {{ message.mlResult.recommendation }}
                </el-tag>
              </section>
              <section class="comparison-card">
                <span>LLM</span>
                <strong>{{ percent(message.aiAssessment.defaultProbability) }}</strong>
                <el-tag
                  :type="message.aiAssessment.borrowerClass === 'good' ? 'success' : 'danger'"
                  effect="light"
                >
                  {{ message.aiAssessment.recommendation }}
                </el-tag>
              </section>
              <section class="comparison-card comparison-card--wide">
                <span>{{ message.comparison.agreement ? 'Решения совпали' : 'Есть расхождение' }}</span>
                <strong>{{ percent(message.comparison.probabilityGap) }}</strong>
                <p>{{ message.comparison.summary }}</p>
              </section>
            </div>
          </div>
        </article>

        <article v-if="loading" class="chat-message agent">
          <div class="chat-message__bubble loading-bubble">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>Агент анализирует заявку и формирует ответ</span>
          </div>
        </article>
      </div>
    </el-scrollbar>

    <footer class="chat-composer">
      <el-input
        v-model="draft"
        :autosize="{ minRows: 2, maxRows: 5 }"
        :disabled="loading"
        placeholder="Например: можешь оценить срок возврата кредита?"
        resize="none"
        type="textarea"
        @keydown.enter.exact.prevent="sendDraft"
      />
      <el-button
        :loading="loading"
        :icon="Promotion"
        type="primary"
        @click="sendDraft"
      >
        Отправить
      </el-button>
    </footer>
  </section>
</template>

<script setup lang="ts">
import {
  Loading,
  Promotion,
  RefreshRight,
} from '@element-plus/icons-vue';
import type { ScrollbarInstance } from 'element-plus';
import { nextTick, ref, watch } from 'vue';

import type {
  AiAssessment,
  BorrowerCard,
  PredictionComparison,
  ScoringResult,
} from '@/api/generated/creditpulse';

interface ChatMessage {
  id: string;
  role: 'user' | 'agent';
  text: string;
  result?: ScoringResult;
  mlResult?: ScoringResult;
  aiAssessment?: AiAssessment;
  comparison?: PredictionComparison;
}

const props = defineProps<{
  borrower: BorrowerCard;
  messages: ChatMessage[];
  loading: boolean;
}>();

const emit = defineEmits<{
  ask: [question: string];
  reset: [];
}>();

const defaultQuestion = 'Оцени заявку и объясни рекомендацию.';
const draft = ref('');
const chatScrollbar = ref<ScrollbarInstance>();

function percent(value: number) {
  return `${Math.round(value * 100)}%`;
}

function money(value: number) {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0,
  }).format(value);
}

function sendDraft() {
  const question = draft.value;
  draft.value = '';
  emit('ask', question);
}

watch(
  () => props.messages.length,
  async () => {
    await nextTick();
    chatScrollbar.value?.setScrollTop(Number.MAX_SAFE_INTEGER);
  },
);
</script>

<style scoped lang="scss">
.assistant-chat {
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr) auto;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: var(--app-panel);
  padding: 20px;

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    border-bottom: 1px solid var(--app-border);
    padding-bottom: 18px;

    h2 {
      margin: 0;
      font-size: 26px;
    }
  }

  &__actions {
    display: flex;
    align-items: center;
    gap: 10px;
  }
}

.summary-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  padding: 18px 0;

  :deep(.el-statistic) {
    border: 1px solid var(--app-border);
    border-radius: 8px;
    background: var(--el-fill-color-blank);
    padding: 14px;
  }
}

.chat-scroll {
  min-height: 0;
}

.chat-feed {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 100%;
  padding: 8px 0 20px;
}

.chat-message {
  display: flex;

  &.user {
    justify-content: flex-end;

    .chat-message__bubble {
      border-color: var(--el-color-primary-light-5);
      background: var(--el-color-primary-light-9);
    }
  }

  &.agent {
    justify-content: flex-start;
  }

  &__bubble {
    max-width: 780px;
    border: 1px solid var(--app-border);
    border-radius: 8px;
    background: var(--app-panel);
    padding: 14px 16px;
    line-height: 1.5;
    box-shadow: var(--el-box-shadow-light);

    strong {
      display: block;
      margin-bottom: 5px;
      font-size: 13px;
    }

    p {
      margin: 0;
    }
  }
}

.result-panel {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.comparison-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 12px;
}

.comparison-card {
  display: grid;
  align-content: start;
  gap: 8px;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: var(--el-fill-color-blank);
  padding: 12px;

  span {
    color: var(--app-muted);
    font-size: 12px;
    font-weight: 600;
  }

  strong {
    font-size: 24px;
    line-height: 1;
  }

  p {
    margin: 0;
    color: var(--app-muted);
    font-size: 13px;
  }

  &--wide {
    grid-column: 1 / -1;
  }
}

.loading-bubble {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--app-muted);
}

.chat-composer {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 140px;
  gap: 12px;
  border-top: 1px solid var(--app-border);
  padding-top: 18px;

  :deep(.el-button) {
    min-height: 54px;
  }
}

@media (max-width: 760px) {
  .assistant-chat__header,
  .assistant-chat__actions {
    align-items: flex-start;
    flex-direction: column;
  }

  .summary-strip,
  .chat-composer,
  .comparison-grid {
    grid-template-columns: 1fr;
  }
}
</style>
