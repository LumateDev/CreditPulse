<template>
  <main class="app-layout">
    <aside class="client-sidebar">
      <section class="brand-block">
        <div>
          <span class="kicker">ИСППР</span>
          <h1>CreditPulse</h1>
        </div>
        <el-tag effect="plain" type="info">LLM {{ healthProvider }}</el-tag>
      </section>

      <el-input
        v-model="search"
        :prefix-icon="Search"
        clearable
        placeholder="Поиск клиента"
        size="large"
      />

      <el-scrollbar class="client-scroll">
        <div class="client-list">
          <button
            v-for="borrower in filteredBorrowers"
            :key="borrower.id"
            class="client-card"
            :class="{ active: selectedBorrower?.id === borrower.id }"
            type="button"
            @click="selectBorrower(borrower.id)"
          >
            <span class="client-card__top">
              <strong>{{ borrower.name }}</strong>
              <el-tag
                :type="borrower.creditHistory === 'poor' ? 'danger' : 'success'"
                effect="light"
                round
              >
                {{ borrower.display.creditHistory }}
              </el-tag>
            </span>
            <span class="client-card__meta">
              {{ borrower.age }} лет · {{ borrower.display.employmentType }} ·
              {{ borrower.display.housingType }}
            </span>
            <span class="client-card__grid">
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

    <section class="workspace">
      <header class="workspace-header">
        <div>
          <span class="kicker">Клиентский чат</span>
          <h2>{{ selectedBorrower?.name ?? 'Загрузка...' }}</h2>
        </div>
        <div class="header-actions">
          <el-button :icon="RefreshRight" plain @click="resetCurrentChat">
            Новый чат
          </el-button>
          <el-button
            :loading="isLoading"
            type="primary"
            @click="sendQuestion(defaultQuestion)"
          >
            Получить рекомендацию
          </el-button>
        </div>
      </header>

      <section v-if="selectedBorrower" class="summary-strip">
        <el-statistic title="Доход" :value="selectedBorrower.display.income" />
        <el-statistic
          title="Сумма кредита"
          :value="selectedBorrower.display.loanAmount"
        />
        <el-statistic title="Срок" :value="selectedBorrower.display.loanTerm" />
        <el-statistic
          title="Кредитная нагрузка"
          :value="selectedBorrower.display.debtLoad"
        />
      </section>

      <el-scrollbar ref="chatScrollbar" class="chat-scroll">
        <div class="chat-feed">
          <el-empty
            v-if="currentMessages.length === 0"
            description="Для каждого клиента ведется отдельный чат. Задайте вопрос или получите рекомендацию."
          />

          <article
            v-for="message in currentMessages"
            :key="message.id"
            class="chat-message"
            :class="message.role"
          >
            <div class="chat-message__bubble">
              <strong v-if="message.role === 'user'">{{ selectedBorrower?.name }}</strong>
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
            </div>
          </article>

          <article v-if="isLoading" class="chat-message agent">
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
          :disabled="isLoading"
          placeholder="Например: можешь оценить срок возврата кредита?"
          resize="none"
          type="textarea"
          @keydown.enter.exact.prevent="sendDraft"
        />
        <el-button
          :disabled="!selectedBorrower"
          :loading="isLoading"
          :icon="Promotion"
          type="primary"
          @click="sendDraft"
        >
          Отправить
        </el-button>
      </footer>
    </section>
  </main>
</template>

<script setup lang="ts">
import {
  Loading,
  Promotion,
  RefreshRight,
  Search,
} from '@element-plus/icons-vue';
import type { ScrollbarInstance } from 'element-plus';
import { ElMessage } from 'element-plus';
import { computed, nextTick, onMounted, ref } from 'vue';

import { getCreditPulseAPI } from '@/api/generated/creditpulse';
import type {
  BorrowerCard,
  ScoringResult,
} from '@/api/generated/creditpulse';

interface ChatMessage {
  id: string;
  role: 'user' | 'agent';
  text: string;
  result?: ScoringResult;
}

const api = getCreditPulseAPI();
const borrowers = ref<BorrowerCard[]>([]);
const selectedBorrowerId = ref<string>('');
const healthProvider = ref('...');
const search = ref('');
const draft = ref('');
const isLoading = ref(false);
const chatScrollbar = ref<ScrollbarInstance>();
const chats = ref<Record<string, ChatMessage[]>>({});
const defaultQuestion = 'Оцени заявку и объясни рекомендацию.';

const selectedBorrower = computed(() =>
  borrowers.value.find((borrower) => borrower.id === selectedBorrowerId.value),
);

const filteredBorrowers = computed(() => {
  const query = search.value.trim().toLowerCase();
  if (!query) return borrowers.value;
  return borrowers.value.filter((borrower) =>
    `${borrower.name} ${borrower.loanPurpose}`.toLowerCase().includes(query),
  );
});

const currentMessages = computed(
  () => chats.value[selectedBorrowerId.value] ?? [],
);

function ensureChat(borrowerId: string) {
  if (!chats.value[borrowerId]) {
    chats.value[borrowerId] = [];
  }
}

function selectBorrower(borrowerId: string) {
  selectedBorrowerId.value = borrowerId;
  ensureChat(borrowerId);
  void scrollToBottom();
}

function resetCurrentChat() {
  if (!selectedBorrowerId.value) return;
  chats.value[selectedBorrowerId.value] = [];
}

function appendMessage(message: Omit<ChatMessage, 'id'>) {
  const borrowerId = selectedBorrowerId.value;
  ensureChat(borrowerId);
  chats.value[borrowerId].push({
    ...message,
    id: crypto.randomUUID(),
  });
}

async function scrollToBottom() {
  await nextTick();
  chatScrollbar.value?.setScrollTop(Number.MAX_SAFE_INTEGER);
}

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

async function sendQuestion(question: string) {
  const borrower = selectedBorrower.value;
  if (!borrower || isLoading.value) return;

  const normalizedQuestion = question.trim() || defaultQuestion;
  appendMessage({ role: 'user', text: normalizedQuestion });
  isLoading.value = true;
  await scrollToBottom();

  try {
    const response = await api.analyzeBorrower({
      borrowerId: borrower.id,
      question: normalizedQuestion,
    });

    appendMessage({
      role: 'agent',
      text: response.explanation,
      result: response.result,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Не удалось получить ответ от сервера.';
    ElMessage.error(message);
    appendMessage({
      role: 'agent',
      text: 'Не удалось получить ответ от сервера. Проверьте настройки backend и LLM-провайдера.',
    });
  } finally {
    isLoading.value = false;
    await scrollToBottom();
  }
}

function sendDraft() {
  const question = draft.value;
  draft.value = '';
  void sendQuestion(question);
}

onMounted(async () => {
  const [health, borrowerList] = await Promise.all([
    api.getHealth(),
    api.listBorrowers(),
  ]);

  healthProvider.value = health.llmProvider;
  borrowers.value = borrowerList;
  if (borrowerList[0]) {
    selectBorrower(borrowerList[0].id);
  }
});
</script>
