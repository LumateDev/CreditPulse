<template>
  <section class="assistant-page">
    <AssistantBorrowerList
      v-model:search="search"
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :borrowers="paginatedBorrowers"
      :selected-id="selectedBorrowerId"
      :total="filteredBorrowers.length"
      :loading="borrowersLoading"
      :disabled="isAnswerLoading"
      @select="selectBorrower"
    />

    <AssistantChat
      v-if="selectedBorrower"
      :borrower="selectedBorrower"
      :messages="currentMessages"
      :loading="isCurrentChatLoading"
      @ask="sendQuestion"
      @reset="resetCurrentChat"
    />
  </section>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus';
import { computed, ref, watch } from 'vue';

import { getCreditPulseAPI } from '@/api/generated/creditpulse';
import type {
  AiAssessment,
  ChatMessage as ApiChatMessage,
  PredictionComparison,
  ScoringResult,
} from '@/api/generated/creditpulse';
import { useBorrowers } from '@/composables/useBorrowers';
import AssistantBorrowerList from '@/pages/assistant/components/AssistantBorrowerList.vue';
import AssistantChat from '@/pages/assistant/components/AssistantChat.vue';

interface ChatMessage {
  id: string;
  role: 'user' | 'agent';
  text: string;
  result?: ScoringResult;
  mlResult?: ScoringResult;
  aiAssessment?: AiAssessment;
  comparison?: PredictionComparison;
}

const api = getCreditPulseAPI();
const { borrowers, isLoading: borrowersLoading } = useBorrowers();
const selectedBorrowerId = ref('');
const search = ref('');
const currentPage = ref(1);
const pageSize = ref(25);
const pendingBorrowerId = ref<string | null>(null);
const chatLoadingBorrowerId = ref<string | null>(null);
const chats = ref<Record<string, ChatMessage[]>>({});
const loadedChats = ref<Record<string, boolean>>({});

const isAnswerLoading = computed(() => pendingBorrowerId.value !== null);

const filteredBorrowers = computed(() => {
  const query = search.value.trim().toLowerCase();
  if (!query) return borrowers.value;
  return borrowers.value.filter((borrower) =>
    `${borrower.name} ${borrower.loanPurpose}`.toLowerCase().includes(query),
  );
});

const paginatedBorrowers = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return filteredBorrowers.value.slice(start, start + pageSize.value);
});

const selectedBorrower = computed(() => {
  const selected = borrowers.value.find((borrower) => borrower.id === selectedBorrowerId.value);
  if (selected) return selected;
  return borrowers.value[0];
});

const isCurrentChatLoading = computed(() => {
  const borrowerId = selectedBorrower.value?.id;
  return pendingBorrowerId.value === borrowerId || chatLoadingBorrowerId.value === borrowerId;
});

const currentMessages = computed(() => {
  const borrowerId = selectedBorrower.value?.id ?? '';
  return chats.value[borrowerId] ?? [];
});

function ensureChat(borrowerId: string) {
  if (!chats.value[borrowerId]) {
    chats.value[borrowerId] = [];
  }
}

function mapApiMessage(message: ApiChatMessage): ChatMessage {
  return {
    id: message.id,
    role: message.role,
    text: message.text,
    result: message.result ?? undefined,
    mlResult: message.mlResult ?? undefined,
    aiAssessment: message.aiAssessment ?? undefined,
    comparison: message.comparison ?? undefined,
  };
}

async function loadChatMessages(borrowerId: string) {
  ensureChat(borrowerId);
  if (loadedChats.value[borrowerId]) return;

  chatLoadingBorrowerId.value = borrowerId;
  try {
    const messages = await api.listChatMessages(borrowerId);
    chats.value[borrowerId] = messages.map(mapApiMessage);
    loadedChats.value[borrowerId] = true;
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Не удалось загрузить историю чата.';
    ElMessage.error(message);
  } finally {
    chatLoadingBorrowerId.value = null;
  }
}

function selectBorrower(borrowerId: string) {
  if (isAnswerLoading.value) {
    ElMessage.info('Дождитесь ответа агента перед переключением клиента.');
    return;
  }

  selectedBorrowerId.value = borrowerId;
  ensureChat(borrowerId);
  void loadChatMessages(borrowerId);
}

async function resetCurrentChat() {
  const borrower = selectedBorrower.value;
  if (!borrower || isAnswerLoading.value) return;
  try {
    await api.clearChatMessages(borrower.id);
    chats.value[borrower.id] = [];
    loadedChats.value[borrower.id] = true;
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Не удалось очистить историю чата.';
    ElMessage.error(message);
  }
}

function appendMessage(borrowerId: string, message: Omit<ChatMessage, 'id'>) {
  ensureChat(borrowerId);
  chats.value[borrowerId].push({
    ...message,
    id: crypto.randomUUID(),
  });
}

async function sendQuestion(question: string) {
  const borrower = selectedBorrower.value;
  if (!borrower || isAnswerLoading.value) return;

  const normalizedQuestion = question.trim() || 'Оцени заявку и объясни рекомендацию.';
  appendMessage(borrower.id, { role: 'user', text: normalizedQuestion });
  pendingBorrowerId.value = borrower.id;

  try {
    const response = await api.analyzeBorrower({
      borrowerId: borrower.id,
      question: normalizedQuestion,
    });

    appendMessage(borrower.id, {
      role: 'agent',
      text: response.explanation,
      result: response.result,
      mlResult: response.mlResult,
      aiAssessment: response.aiAssessment,
      comparison: response.comparison,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Не удалось получить ответ от сервера.';
    ElMessage.error(message);
    appendMessage(borrower.id, {
      role: 'agent',
      text: 'Не удалось получить ответ от сервера. Проверьте настройки backend и LLM-провайдера.',
    });
  } finally {
    pendingBorrowerId.value = null;
  }
}

watch(search, () => {
  currentPage.value = 1;
});

watch([filteredBorrowers, pageSize], () => {
  const maxPage = Math.max(1, Math.ceil(filteredBorrowers.value.length / pageSize.value));
  if (currentPage.value > maxPage) {
    currentPage.value = maxPage;
  }
});

watch(
  () => selectedBorrower.value?.id,
  (borrowerId) => {
    if (!borrowerId) return;
    if (!selectedBorrowerId.value) {
      selectedBorrowerId.value = borrowerId;
    }
    void loadChatMessages(borrowerId);
  },
  { immediate: true },
);
</script>

<style scoped lang="scss">
.assistant-page {
  display: grid;
  grid-template-columns: 390px minmax(0, 1fr);
  gap: 20px;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

@media (max-width: 1100px) {
  .assistant-page {
    grid-template-columns: 1fr;
  }
}
</style>
