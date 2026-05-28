<template>
  <section class="revenue-page">
    <PageHeader
      title="Прогноз доходов"
      eyebrow="Экономика сделок"
      description="Расчёт ожидаемого дохода по заявкам с учётом процентного дохода, стоимости фондирования и риска дефолта."
    >
      <template #actions>
        <el-tag effect="plain" type="info">{{ activeDeals.length }} сделок</el-tag>
      </template>
    </PageHeader>

    <el-scrollbar v-loading="isLoading" class="revenue-page__scroll">
      <div class="revenue-page__content">
        <section class="scenario-panel">
          <el-form label-position="top" class="scenario-form">
            <el-form-item label="Стоимость фондирования, годовых">
              <el-input-number v-model="fundingRatePercent" :min="0" :max="50" :step="0.5" />
            </el-form-item>
            <el-form-item label="LGD, потери при дефолте">
              <el-input-number v-model="lossGivenDefaultPercent" :min="0" :max="100" :step="1" />
            </el-form-item>
            <el-form-item label="Портфель">
              <el-switch
                v-model="approvedOnly"
                active-text="Только одобряемые"
                inactive-text="Все заявки"
                inline-prompt
              />
            </el-form-item>
          </el-form>
        </section>

        <section class="metric-grid">
          <article v-for="metric in metrics" :key="metric.label" class="metric-card">
            <span>{{ metric.label }}</span>
            <strong :class="metric.negative ? 'negative' : ''">{{ metric.value }}</strong>
            <small>{{ metric.caption }}</small>
          </article>
        </section>

        <section class="dashboard-grid dashboard-grid--top">
          <article class="chart-panel">
            <header>
              <h3>Экономика портфеля</h3>
              <span>проценты, расходы и риск</span>
            </header>
            <div class="chart-box">
              <Bar :data="portfolioChartData" :options="moneyBarOptions" />
            </div>
          </article>

          <article class="chart-panel">
            <header>
              <h3>Доходность сделок</h3>
              <span>по ожидаемой прибыли</span>
            </header>
            <div class="chart-box">
              <Doughnut :data="profitabilityChartData" :options="doughnutOptions" />
            </div>
          </article>
        </section>

        <section class="dashboard-grid">
          <article class="chart-panel">
            <header>
              <h3>Прибыль по целям кредита</h3>
              <span>топ категорий</span>
            </header>
            <div class="chart-box">
              <Bar :data="purposeProfitChartData" :options="horizontalMoneyOptions" />
            </div>
          </article>

          <article class="chart-panel">
            <header>
              <h3>Прибыль по типу занятости</h3>
              <span>сумма и маржа</span>
            </header>
            <div class="chart-box">
              <Bar :data="employmentProfitChartData" :options="mixedBarOptions" />
            </div>
          </article>
        </section>

        <section class="deal-table">
          <header>
            <div>
              <h3>Экономика каждой сделки</h3>
              <span>ожидаемая прибыль = проценты - фондирование - ожидаемые потери</span>
            </div>
            <div class="deal-table__tools">
              <el-segmented v-model="dealMode" :options="dealModeOptions" />
              <el-input
                v-model="search"
                :prefix-icon="Search"
                clearable
                placeholder="Поиск клиента"
              />
            </div>
          </header>

          <el-table :data="paginatedDeals" border height="520" @sort-change="handleSortChange">
            <el-table-column prop="borrower.name" label="Клиент" min-width="220" fixed sortable="custom" />
            <el-table-column prop="borrower.display.loanAmount" label="Сумма" width="140" />
            <el-table-column prop="grossInterest" label="Проценты" width="140" sortable="custom">
              <template #default="{ row }: { row: RevenueDeal }">
                {{ formatMoney(row.grossInterest) }}
              </template>
            </el-table-column>
            <el-table-column prop="fundingCost" label="Фондирование" width="150" sortable="custom">
              <template #default="{ row }: { row: RevenueDeal }">
                {{ formatMoney(row.fundingCost) }}
              </template>
            </el-table-column>
            <el-table-column prop="expectedLoss" label="Ожид. потери" width="150" sortable="custom">
              <template #default="{ row }: { row: RevenueDeal }">
                {{ formatMoney(row.expectedLoss) }}
              </template>
            </el-table-column>
            <el-table-column prop="expectedProfit" label="Прибыль" width="140" sortable="custom">
              <template #default="{ row }: { row: RevenueDeal }">
                <strong :class="row.expectedProfit < 0 ? 'negative' : 'positive'">
                  {{ formatMoney(row.expectedProfit) }}
                </strong>
              </template>
            </el-table-column>
            <el-table-column prop="margin" label="Маржа" width="110" sortable="custom">
              <template #default="{ row }: { row: RevenueDeal }">
                {{ formatPercent(row.margin) }}
              </template>
            </el-table-column>
            <el-table-column prop="probability" label="PD" width="100" sortable="custom">
              <template #default="{ row }: { row: RevenueDeal }">
                {{ formatPercent(row.probability) }}
              </template>
            </el-table-column>
            <el-table-column prop="decision" label="Решение" width="120">
              <template #default="{ row }: { row: RevenueDeal }">
                <el-tag :type="row.decision === 'отказать' ? 'danger' : 'success'" effect="light">
                  {{ row.decision }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>

          <footer class="deal-table__pagination">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[25, 50, 100]"
              :total="sortedDeals.length"
              background
              layout="sizes, prev, pager, next, total"
            />
          </footer>
        </section>
      </div>
    </el-scrollbar>
  </section>
</template>

<script setup lang="ts">
import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Tooltip,
} from 'chart.js';
import type { ChartData, ChartOptions } from 'chart.js';
import { Search } from '@element-plus/icons-vue';
import { computed, ref, watch } from 'vue';
import { Bar, Doughnut } from 'vue-chartjs';

import type { BorrowerCard } from '@/api/generated/creditpulse';
import PageHeader from '@/components/PageHeader.vue';
import { useBorrowers } from '@/composables/useBorrowers';

ChartJS.register(ArcElement, BarElement, CategoryScale, Legend, LinearScale, Tooltip);

interface RevenueDeal {
  borrower: BorrowerCard;
  probability: number;
  decision: 'одобрить' | 'отказать';
  grossInterest: number;
  fundingCost: number;
  expectedLoss: number;
  expectedProfit: number;
  margin: number;
}

interface SortChange {
  prop?: string;
  order?: 'ascending' | 'descending' | null;
}

interface ProfitGroup {
  label: string;
  count: number;
  amount: number;
  profit: number;
}

const { borrowers, isLoading } = useBorrowers();
const fundingRatePercent = ref(2);
const lossGivenDefaultPercent = ref(20);
const approvedOnly = ref(true);
const dealMode = ref<'all' | 'profitable' | 'loss'>('all');
const dealModeOptions = [
  { label: 'Все', value: 'all' },
  { label: 'В плюс', value: 'profitable' },
  { label: 'В минус', value: 'loss' },
];
const search = ref('');
const currentPage = ref(1);
const pageSize = ref(25);
const sortState = ref<SortChange>({ prop: 'expectedProfit', order: 'descending' });

const colors = {
  primary: '#409eff',
  success: '#67c23a',
  warning: '#e6a23c',
  danger: '#f56c6c',
  info: '#909399',
  cyan: '#14b8a6',
};

const employmentLabels: Record<string, string> = {
  full_time: 'Постоянная',
  part_time: 'Частичная',
  self_employed: 'Самозанятость',
  temporary: 'Временная',
  unemployed: 'Без работы',
};

const deals = computed<RevenueDeal[]>(() =>
  borrowers.value.map((borrower) => {
    const probability = estimateDefaultProbability(borrower);
    const grossInterest = estimateGrossInterest(borrower);
    const fundingCost =
      borrower.loanAmount * (fundingRatePercent.value / 100) * (borrower.loanTermMonths / 12);
    const expectedLoss = borrower.loanAmount * probability * (lossGivenDefaultPercent.value / 100);
    const expectedProfit = grossInterest - fundingCost - expectedLoss;
    return {
      borrower,
      probability,
      decision: probability >= 0.55 ? 'отказать' : 'одобрить',
      grossInterest,
      fundingCost,
      expectedLoss,
      expectedProfit,
      margin: borrower.loanAmount > 0 ? expectedProfit / borrower.loanAmount : 0,
    };
  }),
);

const activeDeals = computed(() =>
  approvedOnly.value ? deals.value.filter((deal) => deal.decision === 'одобрить') : deals.value,
);

const filteredDeals = computed(() => {
  const query = search.value.trim().toLowerCase();
  return activeDeals.value.filter((deal) => {
    const matchesMode =
      dealMode.value === 'profitable'
        ? deal.expectedProfit >= 0
        : dealMode.value === 'loss'
          ? deal.expectedProfit < 0
          : true;
    const matchesSearch = query
      ? `${deal.borrower.name} ${deal.borrower.id} ${deal.borrower.loanPurpose}`.toLowerCase().includes(query)
      : true;
    return matchesMode && matchesSearch;
  });
});

const sortedDeals = computed(() => {
  const { prop, order } = sortState.value;
  const items = [...filteredDeals.value];
  if (!prop || !order) return items;

  return items.sort((left, right) => {
    const result = compareValues(getSortValue(left, prop), getSortValue(right, prop));
    return order === 'ascending' ? result : -result;
  });
});

const paginatedDeals = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return sortedDeals.value.slice(start, start + pageSize.value);
});

const totals = computed(() =>
  activeDeals.value.reduce(
    (sum, deal) => ({
      amount: sum.amount + deal.borrower.loanAmount,
      interest: sum.interest + deal.grossInterest,
      funding: sum.funding + deal.fundingCost,
      loss: sum.loss + deal.expectedLoss,
      profit: sum.profit + deal.expectedProfit,
      profitable: sum.profitable + (deal.expectedProfit >= 0 ? 1 : 0),
    }),
    { amount: 0, interest: 0, funding: 0, loss: 0, profit: 0, profitable: 0 },
  ),
);

const metrics = computed(() => [
  {
    label: 'Ожидаемая прибыль',
    value: formatMoney(totals.value.profit),
    caption: `маржа ${formatPercent(totals.value.amount > 0 ? totals.value.profit / totals.value.amount : 0)}`,
    negative: totals.value.profit < 0,
  },
  {
    label: 'Процентный доход',
    value: formatMoney(totals.value.interest),
    caption: `до риска и фондирования`,
  },
  {
    label: 'Ожидаемые потери',
    value: formatMoney(totals.value.loss),
    caption: `LGD ${lossGivenDefaultPercent.value}%`,
    negative: true,
  },
  {
    label: 'Прибыльных сделок',
    value: formatPercent(totals.value.profitable / Math.max(1, activeDeals.value.length)),
    caption: `${totals.value.profitable} из ${activeDeals.value.length}`,
  },
]);

const portfolioChartData = computed<ChartData<'bar'>>(() => ({
  labels: ['Проценты', 'Фондирование', 'Ожид. потери', 'Итог'],
  datasets: [
    {
      label: '₽',
      data: [totals.value.interest, -totals.value.funding, -totals.value.loss, totals.value.profit],
      backgroundColor: [colors.success, colors.warning, colors.danger, totals.value.profit >= 0 ? colors.primary : colors.danger],
      borderRadius: 6,
    },
  ],
}));

const profitabilityChartData = computed<ChartData<'doughnut'>>(() => {
  const profitable = activeDeals.value.filter((deal) => deal.expectedProfit >= 0).length;
  return {
    labels: ['В плюс', 'В минус'],
    datasets: [
      {
        data: [profitable, activeDeals.value.length - profitable],
        backgroundColor: [colors.success, colors.danger],
        borderWidth: 0,
      },
    ],
  };
});

const purposeProfitChartData = computed<ChartData<'bar'>>(() => {
  const groups = groupDeals(activeDeals.value, (deal) => deal.borrower.loanPurpose)
    .sort((left, right) => right.profit - left.profit)
    .slice(0, 8);

  return {
    labels: groups.map((group) => group.label),
    datasets: [
      {
        label: 'Ожидаемая прибыль',
        data: groups.map((group) => Math.round(group.profit)),
        backgroundColor: groups.map((group) => (group.profit >= 0 ? colors.primary : colors.danger)),
        borderRadius: 6,
      },
    ],
  };
});

const employmentProfitChartData = computed<ChartData<'bar'>>(() => {
  const groups = groupDeals(activeDeals.value, (deal) => deal.borrower.employmentType);
  return {
    labels: groups.map((group) => employmentLabels[group.label] ?? group.label),
    datasets: [
      {
        label: 'Прибыль',
        data: groups.map((group) => Math.round(group.profit)),
        backgroundColor: colors.primary,
        borderRadius: 6,
        yAxisID: 'y',
      },
      {
        label: 'Маржа, %',
        data: groups.map((group) => Math.round((group.profit / Math.max(1, group.amount)) * 100)),
        backgroundColor: colors.cyan,
        borderRadius: 6,
        yAxisID: 'yPercent',
      },
    ],
  };
});

const moneyBarOptions: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (item) => formatMoney(Number(item.raw ?? 0)),
      },
    },
  },
  scales: {
    y: {
      grid: { color: 'rgba(144, 147, 153, 0.18)' },
      ticks: {
        callback: (value) => formatCompactMoney(Number(value)),
      },
    },
    x: { grid: { display: false } },
  },
};

const horizontalMoneyOptions: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: 'y',
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (item) => formatMoney(Number(item.raw ?? 0)),
      },
    },
  },
  scales: {
    x: {
      grid: { color: 'rgba(144, 147, 153, 0.18)' },
      ticks: {
        callback: (value) => formatCompactMoney(Number(value)),
      },
    },
    y: {
      grid: { display: false },
      ticks: {
        autoSkip: false,
      },
    },
  },
};

const mixedBarOptions: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
      labels: { boxWidth: 10, boxHeight: 10 },
    },
  },
  scales: {
    y: {
      grid: { color: 'rgba(144, 147, 153, 0.18)' },
      ticks: {
        callback: (value) => formatCompactMoney(Number(value)),
      },
    },
    yPercent: {
      position: 'right',
      grid: { drawOnChartArea: false },
      ticks: {
        callback: (value) => `${value}%`,
      },
    },
    x: { grid: { display: false } },
  },
};

const doughnutOptions: ChartOptions<'doughnut'> = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '64%',
  plugins: {
    legend: {
      position: 'bottom',
      labels: { boxWidth: 10, boxHeight: 10 },
    },
  },
};

watch([search, dealMode, approvedOnly, pageSize], () => {
  currentPage.value = 1;
});

watch(sortedDeals, () => {
  const maxPage = Math.max(1, Math.ceil(sortedDeals.value.length / pageSize.value));
  if (currentPage.value > maxPage) {
    currentPage.value = maxPage;
  }
});

function handleSortChange({ prop, order }: SortChange) {
  sortState.value = { prop, order };
  currentPage.value = 1;
}

function estimateGrossInterest(borrower: BorrowerCard) {
  const monthlyPayment = estimateMonthlyPayment(
    borrower.loanAmount,
    borrower.interestRate,
    borrower.loanTermMonths,
  );
  return Math.max(0, monthlyPayment * borrower.loanTermMonths - borrower.loanAmount);
}

function estimateMonthlyPayment(amount: number, annualRate: number, months: number) {
  if (months <= 0) return amount;
  const monthlyRate = annualRate / 100 / 12;
  if (monthlyRate <= 0) return amount / months;
  const multiplier = (1 + monthlyRate) ** months;
  return (amount * monthlyRate * multiplier) / (multiplier - 1);
}

function estimateDefaultProbability(borrower: BorrowerCard) {
  let risk = 0.28;
  const loanToIncome = borrower.income > 0 ? borrower.loanAmount / borrower.income : 0;

  if (borrower.income < 45000) risk += 0.16;
  else if (borrower.income > 110000) risk -= 0.1;
  if (loanToIncome > 14) risk += 0.13;
  else if (loanToIncome < 7) risk -= 0.06;
  if (borrower.debtLoad >= 0.5) risk += 0.18;
  else if (borrower.debtLoad <= 0.3) risk -= 0.08;
  if (borrower.employmentYears < 1) risk += 0.12;
  else if (borrower.employmentYears < 2) risk += 0.07;
  else if (borrower.employmentYears >= 5) risk -= 0.08;
  if (borrower.creditHistory === 'excellent') risk -= 0.12;
  else if (borrower.creditHistory === 'good') risk -= 0.07;
  else if (borrower.creditHistory === 'late_payments') risk += 0.12;
  else if (borrower.creditHistory === 'poor') risk += 0.18;
  if (borrower.pastDefaults) risk += 0.2;
  if (['temporary', 'unemployed'].includes(borrower.employmentType)) risk += 0.1;
  else if (borrower.employmentType === 'part_time') risk += 0.05;
  else if (borrower.employmentType === 'full_time') risk -= 0.04;
  if (borrower.housingType === 'own') risk -= 0.05;
  else if (borrower.housingType === 'parents') risk -= 0.02;
  else if (borrower.housingType === 'rent') risk += 0.04;
  if (borrower.interestRate >= 20) risk += 0.06;
  if (borrower.loanTermMonths >= 48) risk += 0.05;
  if (borrower.age < 25) risk += 0.04;

  return Math.min(0.99, Math.max(0.01, Number(risk.toFixed(2))));
}

function groupDeals(items: RevenueDeal[], getKey: (deal: RevenueDeal) => string) {
  const groups = new Map<string, ProfitGroup>();
  for (const deal of items) {
    const key = getKey(deal);
    const group = groups.get(key) ?? { label: key, count: 0, amount: 0, profit: 0 };
    group.count += 1;
    group.amount += deal.borrower.loanAmount;
    group.profit += deal.expectedProfit;
    groups.set(key, group);
  }
  return [...groups.values()];
}

function getSortValue(deal: RevenueDeal, prop: string) {
  if (prop === 'borrower.name') return deal.borrower.name;
  return deal[prop as keyof RevenueDeal];
}

function compareValues(left: unknown, right: unknown) {
  if (typeof left === 'number' && typeof right === 'number') return left - right;
  return String(left ?? '').localeCompare(String(right ?? ''), 'ru');
}

function formatMoney(value: number) {
  return `${new Intl.NumberFormat('ru-RU', {
    maximumFractionDigits: 0,
  }).format(Math.round(value))} ₽`;
}

function formatCompactMoney(value: number) {
  return `${new Intl.NumberFormat('ru-RU', {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value)} ₽`;
}

function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`;
}
</script>

<style scoped lang="scss">
.revenue-page {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  height: 100%;
  min-height: 0;
  overflow: hidden;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: var(--app-panel);
  padding: 20px;

  &__scroll {
    min-height: 0;
  }

  &__content {
    display: grid;
    gap: 16px;
    padding-right: 4px;
  }
}

.scenario-panel,
.metric-card,
.chart-panel,
.deal-table {
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: var(--el-fill-color-blank);
}

.scenario-panel {
  padding: 16px;
}

.scenario-form {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;

  :deep(.el-form-item) {
    margin-bottom: 0;
  }
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.metric-card {
  display: grid;
  gap: 6px;
  min-height: 118px;
  padding: 16px;

  span,
  small {
    color: var(--app-muted);
  }

  strong {
    font-size: 28px;
    line-height: 1.05;
  }
}

.positive {
  color: var(--el-color-success);
}

.negative {
  color: var(--el-color-danger);
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;

  &--top {
    grid-template-columns: minmax(0, 1.25fr) minmax(280px, 0.75fr);
  }
}

.chart-panel {
  display: grid;
  grid-template-rows: auto minmax(290px, 1fr);
  gap: 12px;
  min-width: 0;
  padding: 16px;

  header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
  }

  h3 {
    margin: 0;
    font-size: 16px;
  }

  span {
    color: var(--app-muted);
    font-size: 13px;
    text-align: right;
  }
}

.chart-box {
  position: relative;
  min-height: 290px;
}

.deal-table {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  gap: 12px;
  min-width: 0;
  padding: 16px;

  > header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;

    h3 {
      margin: 0;
      font-size: 16px;
    }

    span {
      display: block;
      margin-top: 4px;
      color: var(--app-muted);
      font-size: 13px;
    }
  }

  &__tools {
    display: grid;
    grid-template-columns: auto minmax(220px, 280px);
    gap: 10px;
    align-items: center;
  }

  &__pagination {
    display: flex;
    justify-content: flex-end;
    overflow-x: auto;
    border-top: 1px solid var(--app-border);
    padding-top: 12px;
  }
}

@media (max-width: 1180px) {
  .metric-grid,
  .dashboard-grid,
  .dashboard-grid--top,
  .scenario-form {
    grid-template-columns: 1fr;
  }

  .deal-table > header {
    flex-direction: column;
  }

  .deal-table__tools {
    width: 100%;
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .metric-grid {
    grid-template-columns: 1fr;
  }

  .chart-panel,
  .deal-table,
  .scenario-panel {
    padding: 12px;
  }
}
</style>
