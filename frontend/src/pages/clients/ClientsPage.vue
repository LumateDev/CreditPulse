<template>
  <section class="clients-page">
    <PageHeader
      title="Клиентская база"
      eyebrow="Справочник"
      description="Здесь можно подготовить карточки клиентов для будущего сохранения на backend."
    >
      <template #actions>
        <el-button type="primary" :icon="Plus" @click="openCreateDialog">
          Добавить клиента
        </el-button>
      </template>
    </PageHeader>

    <el-table
      v-loading="isLoading"
      :data="borrowers"
      border
      height="100%"
    >
      <el-table-column prop="name" label="ФИО" min-width="190" fixed />
      <el-table-column prop="age" label="Возраст" width="100" />
      <el-table-column label="Доход" min-width="130">
        <template #default="{ row }: { row: BorrowerCard }">
          {{ row.display.income }}
        </template>
      </el-table-column>
      <el-table-column label="Кредит" min-width="140">
        <template #default="{ row }: { row: BorrowerCard }">
          {{ row.display.loanAmount }}
        </template>
      </el-table-column>
      <el-table-column label="Срок" width="110">
        <template #default="{ row }: { row: BorrowerCard }">
          {{ row.display.loanTerm }}
        </template>
      </el-table-column>
      <el-table-column label="История" width="130">
        <template #default="{ row }: { row: BorrowerCard }">
          <el-tag :type="row.creditHistory === 'poor' ? 'danger' : 'success'" effect="light">
            {{ row.display.creditHistory }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="Действия" width="180" fixed="right">
        <template #default="{ row }: { row: BorrowerCard }">
          <el-button link type="primary" @click="openEditDialog(row)">
            Редактировать
          </el-button>
          <el-popconfirm
            title="Удалить клиента из локального списка?"
            confirm-button-text="Удалить"
            cancel-button-text="Отмена"
            @confirm="removeBorrower(row.id)"
          >
            <template #reference>
              <el-button link type="danger">Удалить</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? 'Редактирование клиента' : 'Новый клиент'"
      width="720"
    >
      <el-form :model="form" label-position="top" class="client-form">
        <el-form-item label="ФИО">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="Возраст">
          <el-input-number v-model="form.age" :min="18" :max="80" />
        </el-form-item>
        <el-form-item label="Доход">
          <el-input-number v-model="form.income" :min="0" :step="5000" />
        </el-form-item>
        <el-form-item label="Сумма кредита">
          <el-input-number v-model="form.loanAmount" :min="0" :step="10000" />
        </el-form-item>
        <el-form-item label="Срок, мес.">
          <el-input-number v-model="form.loanTermMonths" :min="1" :max="120" />
        </el-form-item>
        <el-form-item label="Кредитная история">
          <el-select v-model="form.creditHistory">
            <el-option label="Отличная" value="excellent" />
            <el-option label="Хорошая" value="good" />
            <el-option label="Просрочки" value="late_payments" />
            <el-option label="Слабая" value="poor" />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">Отмена</el-button>
        <el-button type="primary" @click="saveBorrower">Сохранить</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { Plus } from '@element-plus/icons-vue';
import { reactive, ref } from 'vue';

import type { BorrowerCard } from '@/api/generated/creditpulse';
import PageHeader from '@/components/PageHeader.vue';
import { useBorrowers } from '@/composables/useBorrowers';

type ClientForm = Pick<
  BorrowerCard,
  'name' | 'age' | 'income' | 'loanAmount' | 'loanTermMonths' | 'creditHistory'
>;

const { borrowers, isLoading } = useBorrowers();
const dialogVisible = ref(false);
const editingId = ref<string | null>(null);
const form = reactive<ClientForm>({
  name: '',
  age: 30,
  income: 80000,
  loanAmount: 500000,
  loanTermMonths: 24,
  creditHistory: 'good',
});

function openCreateDialog() {
  editingId.value = null;
  Object.assign(form, {
    name: '',
    age: 30,
    income: 80000,
    loanAmount: 500000,
    loanTermMonths: 24,
    creditHistory: 'good',
  });
  dialogVisible.value = true;
}

function openEditDialog(row: BorrowerCard) {
  editingId.value = row.id;
  Object.assign(form, {
    name: row.name,
    age: row.age,
    income: row.income,
    loanAmount: row.loanAmount,
    loanTermMonths: row.loanTermMonths,
    creditHistory: row.creditHistory,
  });
  dialogVisible.value = true;
}

function toDisplayMoney(value: number) {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0,
  }).format(value);
}

function buildLocalBorrower(id: string): BorrowerCard {
  return {
    id,
    name: form.name || 'Новый клиент',
    age: form.age,
    income: form.income,
    employmentYears: 1,
    employmentType: 'full_time',
    housingType: 'rent',
    loanAmount: form.loanAmount,
    loanTermMonths: form.loanTermMonths,
    interestRate: 15,
    loanPurpose: 'потребительский кредит',
    creditHistory: form.creditHistory,
    pastDefaults: false,
    debtLoad: 0.3,
    display: {
      employmentType: 'постоянная',
      housingType: 'аренда',
      creditHistory: form.creditHistory,
      income: toDisplayMoney(form.income),
      loanAmount: toDisplayMoney(form.loanAmount),
      loanTerm: `${form.loanTermMonths} мес.`,
      debtLoad: '30%',
    },
  };
}

function saveBorrower() {
  if (editingId.value) {
    const index = borrowers.value.findIndex((borrower) => borrower.id === editingId.value);
    if (index >= 0) {
      borrowers.value[index] = buildLocalBorrower(editingId.value);
    }
  } else {
    borrowers.value.unshift(buildLocalBorrower(`local-${crypto.randomUUID()}`));
  }
  dialogVisible.value = false;
}

function removeBorrower(borrowerId: string) {
  borrowers.value = borrowers.value.filter((borrower) => borrower.id !== borrowerId);
}
</script>

<style scoped lang="scss">
.clients-page {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  height: 100%;
  min-height: 0;
  overflow: hidden;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: var(--app-panel);
  padding: 20px;
}

.client-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 4px 16px;
}

@media (max-width: 760px) {
  .client-form {
    grid-template-columns: 1fr;
  }
}
</style>
