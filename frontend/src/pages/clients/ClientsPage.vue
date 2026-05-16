<template>
  <section class="clients-page">
    <PageHeader
      title="Клиентская база"
      eyebrow="Справочник"
      description="Клиенты, заявки и сохраненная история работы с ними."
    >
      <template #actions>
        <el-button type="primary" :icon="Plus" @click="openCreateDialog">
          Добавить клиента
        </el-button>
      </template>
    </PageHeader>

    <section class="clients-toolbar">
      <el-input
        v-model="search"
        :prefix-icon="Search"
        clearable
        placeholder="Поиск по ФИО, цели или ID"
      />
      <el-select v-model="creditHistoryFilter" placeholder="Кредитная история" clearable>
        <el-option label="Отличная" value="excellent" />
        <el-option label="Хорошая" value="good" />
        <el-option label="Просрочки" value="late_payments" />
        <el-option label="Слабая" value="poor" />
      </el-select>
      <el-select v-model="defaultsFilter" placeholder="Дефолты" clearable>
        <el-option label="Без дефолтов" value="without_defaults" />
        <el-option label="Есть дефолты" value="with_defaults" />
      </el-select>
      <el-select v-model="debtLoadFilter" placeholder="Нагрузка" clearable>
        <el-option label="До 30%" value="low" />
        <el-option label="30-50%" value="medium" />
        <el-option label="Более 50%" value="high" />
      </el-select>
      <el-button :icon="RefreshRight" plain @click="resetFilters">
        Сбросить
      </el-button>
      <el-tag effect="plain">
        {{ sortedBorrowers.length }} из {{ borrowers.length }}
      </el-tag>
    </section>

    <section class="clients-table">
      <el-table
        v-loading="isLoading"
        :data="paginatedBorrowers"
        border
        height="100%"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="name" label="ФИО" min-width="210" fixed sortable="custom" />
        <el-table-column prop="age" label="Возраст" width="110" sortable="custom" />
        <el-table-column prop="income" label="Доход" min-width="140" sortable="custom">
          <template #default="{ row }: { row: BorrowerCard }">
            {{ row.display.income }}
          </template>
        </el-table-column>
        <el-table-column prop="loanAmount" label="Кредит" min-width="150" sortable="custom">
          <template #default="{ row }: { row: BorrowerCard }">
            {{ row.display.loanAmount }}
          </template>
        </el-table-column>
        <el-table-column prop="loanTermMonths" label="Срок" width="120" sortable="custom">
          <template #default="{ row }: { row: BorrowerCard }">
            {{ row.display.loanTerm }}
          </template>
        </el-table-column>
        <el-table-column prop="debtLoad" label="Нагрузка" width="130" sortable="custom">
          <template #default="{ row }: { row: BorrowerCard }">
            {{ row.display.debtLoad }}
          </template>
        </el-table-column>
        <el-table-column prop="creditHistory" label="История" width="140" sortable="custom">
          <template #default="{ row }: { row: BorrowerCard }">
            <el-tag :type="row.creditHistory === 'poor' ? 'danger' : 'success'" effect="light">
              {{ row.display.creditHistory }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="pastDefaults" label="Дефолты" width="120" sortable="custom">
          <template #default="{ row }: { row: BorrowerCard }">
            <el-tag :type="row.pastDefaults ? 'danger' : 'info'" effect="plain">
              {{ row.pastDefaults ? 'Есть' : 'Нет' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Действия" width="180" fixed="right">
          <template #default="{ row }: { row: BorrowerCard }">
            <el-button link type="primary" @click="openEditDialog(row)">
              Редактировать
            </el-button>
            <el-popconfirm
              title="Удалить клиента и его историю чата?"
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

      <footer class="clients-pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[25, 50, 100]"
          :total="sortedBorrowers.length"
          background
          layout="sizes, prev, pager, next, total"
        />
      </footer>
    </section>

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
import { Plus, RefreshRight, Search } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue';

import { getCreditPulseAPI } from '@/api/generated/creditpulse';
import type { BorrowerCard, BorrowerCreate } from '@/api/generated/creditpulse';
import PageHeader from '@/components/PageHeader.vue';
import { useBorrowers } from '@/composables/useBorrowers';

type ClientForm = Pick<
  BorrowerCard,
  'name' | 'age' | 'income' | 'loanAmount' | 'loanTermMonths' | 'creditHistory'
>;

type SortOrder = 'ascending' | 'descending' | null;

interface SortChange {
  prop?: string;
  order?: SortOrder;
}

const api = getCreditPulseAPI();
const { borrowers, isLoading, loadBorrowers } = useBorrowers();
const dialogVisible = ref(false);
const editingId = ref<string | null>(null);
const search = ref('');
const debouncedSearch = ref('');
const creditHistoryFilter = ref('');
const defaultsFilter = ref('');
const debtLoadFilter = ref('');
const currentPage = ref(1);
const pageSize = ref(25);
const sortState = ref<SortChange>({});
const form = reactive<ClientForm>({
  name: '',
  age: 30,
  income: 80000,
  loanAmount: 500000,
  loanTermMonths: 24,
  creditHistory: 'good',
});

let searchTimer: number | undefined;

const filteredBorrowers = computed(() => {
  const query = debouncedSearch.value.trim().toLowerCase();

  return borrowers.value.filter((borrower) => {
    const matchesSearch = query
      ? `${borrower.id} ${borrower.name} ${borrower.loanPurpose}`.toLowerCase().includes(query)
      : true;
    const matchesHistory = creditHistoryFilter.value
      ? borrower.creditHistory === creditHistoryFilter.value
      : true;
    const matchesDefaults = defaultsFilter.value === 'with_defaults'
      ? borrower.pastDefaults
      : defaultsFilter.value === 'without_defaults'
        ? !borrower.pastDefaults
        : true;
    const matchesDebtLoad = debtLoadFilter.value
      ? getDebtLoadGroup(borrower.debtLoad) === debtLoadFilter.value
      : true;

    return matchesSearch && matchesHistory && matchesDefaults && matchesDebtLoad;
  });
});

const sortedBorrowers = computed(() => {
  const { prop, order } = sortState.value;
  if (!prop || !order) return filteredBorrowers.value;

  return [...filteredBorrowers.value].sort((left, right) => {
    const leftValue = getSortValue(left, prop);
    const rightValue = getSortValue(right, prop);
    const result = compareValues(leftValue, rightValue);
    return order === 'ascending' ? result : -result;
  });
});

const paginatedBorrowers = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return sortedBorrowers.value.slice(start, start + pageSize.value);
});

watch(search, (value) => {
  if (searchTimer) {
    window.clearTimeout(searchTimer);
  }
  searchTimer = window.setTimeout(() => {
    debouncedSearch.value = value;
  }, 180);
});

watch(
  [debouncedSearch, creditHistoryFilter, defaultsFilter, debtLoadFilter, pageSize],
  () => {
    currentPage.value = 1;
  },
);

watch(sortedBorrowers, (items) => {
  const maxPage = Math.max(1, Math.ceil(items.length / pageSize.value));
  if (currentPage.value > maxPage) {
    currentPage.value = maxPage;
  }
});

onBeforeUnmount(() => {
  if (searchTimer) {
    window.clearTimeout(searchTimer);
  }
});

function handleSortChange({ prop, order }: SortChange) {
  sortState.value = { prop, order };
  currentPage.value = 1;
}

function getSortValue(borrower: BorrowerCard, prop: string) {
  return borrower[prop as keyof BorrowerCard];
}

function compareValues(left: unknown, right: unknown) {
  if (typeof left === 'number' && typeof right === 'number') {
    return left - right;
  }
  if (typeof left === 'boolean' && typeof right === 'boolean') {
    return Number(left) - Number(right);
  }
  return String(left ?? '').localeCompare(String(right ?? ''), 'ru');
}

function getDebtLoadGroup(value: number) {
  if (value < 0.3) return 'low';
  if (value <= 0.5) return 'medium';
  return 'high';
}

function resetFilters() {
  search.value = '';
  debouncedSearch.value = '';
  creditHistoryFilter.value = '';
  defaultsFilter.value = '';
  debtLoadFilter.value = '';
}

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

function buildBorrowerPayload(id?: string): BorrowerCreate {
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
  };
}

async function saveBorrower() {
  try {
    if (editingId.value) {
      await api.updateBorrower(editingId.value, buildBorrowerPayload(editingId.value));
      ElMessage.success('Клиент обновлен.');
    } else {
      await api.createBorrower(buildBorrowerPayload());
      ElMessage.success('Клиент добавлен.');
    }
    await loadBorrowers();
    dialogVisible.value = false;
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Не удалось сохранить клиента.';
    ElMessage.error(message);
  }
}

async function removeBorrower(borrowerId: string) {
  try {
    await api.deleteBorrower(borrowerId);
    borrowers.value = borrowers.value.filter((borrower) => borrower.id !== borrowerId);
    ElMessage.success('Клиент удален.');
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Не удалось удалить клиента.';
    ElMessage.error(message);
  }
}
</script>

<style scoped lang="scss">
.clients-page {
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr);
  gap: 14px;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: var(--app-panel);
  padding: 20px;
}

.clients-toolbar {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) 190px 160px 160px auto auto;
  align-items: center;
  gap: 10px;

  :deep(.el-tag) {
    justify-self: end;
  }
}

.clients-table {
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto;
  min-height: 0;
}

.clients-pagination {
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid var(--app-border);
  padding-top: 12px;
}

.client-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 4px 16px;
}

@media (max-width: 1100px) {
  .clients-toolbar {
    grid-template-columns: repeat(2, minmax(0, 1fr));

    :deep(.el-tag) {
      justify-self: start;
    }
  }
}

@media (max-width: 760px) {
  .clients-toolbar,
  .client-form {
    grid-template-columns: 1fr;
  }

  .clients-pagination {
    justify-content: flex-start;
    overflow-x: auto;
  }
}
</style>
