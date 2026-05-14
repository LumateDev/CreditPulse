import { ElMessage } from 'element-plus';
import { onMounted, ref } from 'vue';

import { getCreditPulseAPI } from '@/api/generated/creditpulse';
import type { BorrowerCard } from '@/api/generated/creditpulse';

const api = getCreditPulseAPI();

export function useBorrowers() {
  const borrowers = ref<BorrowerCard[]>([]);
  const isLoading = ref(false);

  async function loadBorrowers() {
    isLoading.value = true;
    try {
      borrowers.value = await api.listBorrowers();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Не удалось загрузить клиентов.';
      ElMessage.error(message);
    } finally {
      isLoading.value = false;
    }
  }

  onMounted(() => {
    void loadBorrowers();
  });

  return {
    borrowers,
    isLoading,
    loadBorrowers,
  };
}
