<template>
  <section class="analytics-page">
    <PageHeader
      title="Аналитика портфеля"
      eyebrow="Прогнозы"
      description="Сводка по клиентской базе, рискам дефолта и структуре заявок."
    >
      <template #actions>
        <el-tag effect="plain" type="info">{{ borrowers.length }} заявок</el-tag>
      </template>
    </PageHeader>

    <el-scrollbar v-loading="isLoading" class="analytics-page__scroll">
      <div class="analytics-page__content">
        <section class="metric-grid">
          <article v-for="metric in metrics" :key="metric.label" class="metric-card">
            <span>{{ metric.label }}</span>
            <strong>{{ metric.value }}</strong>
            <small>{{ metric.caption }}</small>
          </article>
        </section>

        <section class="summary-strip">
          <article v-for="item in summaryItems" :key="item.title" class="summary-item">
            <strong>{{ item.title }}</strong>
            <span>{{ item.text }}</span>
          </article>
        </section>

        <section class="dashboard-grid dashboard-grid--top">
          <article class="chart-panel">
            <header>
              <h3>Прогноз решений</h3>
              <span>{{ approvedCount }} / {{ declinedCount }}</span>
            </header>
            <div class="chart-box">
              <Doughnut :data="decisionChartData" :options="doughnutOptions" />
            </div>
          </article>

          <article class="chart-panel chart-panel--wide">
            <header>
              <h3>Распределение риска</h3>
              <span>по вероятности дефолта</span>
            </header>
            <div class="chart-box">
              <Bar :data="riskBucketChartData" :options="barOptions" />
            </div>
            <ul class="risk-legend">
              <li v-for="bucket in riskBucketLegend" :key="bucket.label">
                <i :style="{ background: bucket.color }" />
                <span>{{ bucket.label }}</span>
                <strong>{{ bucket.count }}</strong>
                <small>{{ bucket.share }}</small>
              </li>
            </ul>
          </article>
        </section>

        <section class="dashboard-grid dashboard-grid--single">
          <article class="chart-panel chart-panel--wide">
            <header>
              <div>
                <h3>{{ topBorrowersTitle }}</h3>
                <span>{{ topBorrowersSubtitle }}</span>
              </div>
              <el-segmented v-model="topBorrowerMode" :options="topBorrowerModeOptions" />
            </header>
            <div class="chart-box chart-box--large">
              <Bar :data="topBorrowersChartData" :options="topBorrowersChartOptions" />
            </div>
          </article>
        </section>

        <section class="dashboard-grid">
          <article class="chart-panel">
            <header>
              <h3>Средний риск по целям</h3>
              <span>топ-7 категорий</span>
            </header>
            <div class="chart-box">
              <Bar :data="purposeRiskChartData" :options="horizontalBarOptions" />
            </div>
          </article>

          <article class="chart-panel">
            <header>
              <h3>Тип занятости</h3>
              <span>объём и риск</span>
            </header>
            <div class="chart-box">
              <Bar :data="employmentChartData" :options="barOptions" />
            </div>
          </article>

          <article class="chart-panel">
            <header>
              <h3>Возрастные группы</h3>
              <span>средняя вероятность</span>
            </header>
            <div class="chart-box">
              <Line :data="ageRiskChartData" :options="lineOptions" />
            </div>
          </article>

          <article class="chart-panel">
            <header>
              <h3>Жилье</h3>
              <span>структура базы</span>
            </header>
            <div class="chart-box">
              <Doughnut :data="housingChartData" :options="doughnutOptions" />
            </div>
          </article>
        </section>

        <section class="risk-table">
          <header>
            <div>
              <h3>{{ topBorrowersTitle }}</h3>
              <span>{{ topBorrowersSubtitle }}</span>
            </div>
            <el-segmented v-model="topBorrowerMode" :options="topBorrowerModeOptions" />
          </header>

          <el-table :data="selectedTopBorrowers" border height="430">
            <el-table-column prop="borrower.name" label="Клиент" min-width="220" fixed />
            <el-table-column prop="borrower.display.loanAmount" label="Кредит" width="140" />
            <el-table-column prop="borrower.display.income" label="Доход" width="140" />
            <el-table-column prop="borrower.display.debtLoad" label="Нагрузка" width="120" />
            <el-table-column prop="borrower.display.creditHistory" label="История" width="140">
              <template #default="{ row }: { row: ScoredBorrower }">
                <el-tag :type="row.borrower.creditHistory === 'poor' ? 'danger' : 'info'" effect="plain">
                  {{ row.borrower.display.creditHistory }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="probability" label="PD" width="110">
              <template #default="{ row }: { row: ScoredBorrower }">
                <strong>{{ formatPercent(row.probability) }}</strong>
              </template>
            </el-table-column>
            <el-table-column prop="decision" label="Решение" width="120">
              <template #default="{ row }: { row: ScoredBorrower }">
                <el-tag :type="row.decision === 'отказать' ? 'danger' : 'success'" effect="light">
                  {{ row.decision }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
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
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js';
import type { ChartData, ChartOptions } from 'chart.js';
import { computed, ref } from 'vue';
import { Bar, Doughnut, Line } from 'vue-chartjs';

import type { BorrowerCard } from '@/api/generated/creditpulse';
import PageHeader from '@/components/PageHeader.vue';
import { useBorrowers } from '@/composables/useBorrowers';

ChartJS.register(
  ArcElement,
  BarElement,
  CategoryScale,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
);

interface ScoredBorrower {
  borrower: BorrowerCard;
  probability: number;
  decision: 'одобрить' | 'отказать';
  paymentToIncome: number;
}

interface GroupStats {
  label: string;
  count: number;
  riskSum: number;
}

const { borrowers, isLoading } = useBorrowers();
const topBorrowerMode = ref<'worst' | 'best'>('worst');

const chartColors = {
  primary: '#409eff',
  success: '#67c23a',
  warning: '#e6a23c',
  danger: '#f56c6c',
  info: '#909399',
  purple: '#8b5cf6',
  cyan: '#14b8a6',
};

const riskBuckets = [
  { label: '0-20%', min: 0, max: 0.2, color: chartColors.success },
  { label: '20-35%', min: 0.2, max: 0.35, color: chartColors.primary },
  { label: '35-55%', min: 0.35, max: 0.55, color: chartColors.warning },
  { label: '55-75%', min: 0.55, max: 0.75, color: chartColors.danger },
  { label: '75-100%', min: 0.75, max: 1.01, color: chartColors.purple },
];

const topBorrowerModeOptions = [
  { label: 'Худшие', value: 'worst' },
  { label: 'Лучшие', value: 'best' },
];

const employmentLabels: Record<string, string> = {
  full_time: 'Постоянная',
  part_time: 'Частичная',
  self_employed: 'Самозанятость',
  temporary: 'Временная',
  unemployed: 'Без работы',
};

const housingLabels: Record<string, string> = {
  own: 'Собственное',
  parents: 'У родителей',
  rent: 'Аренда',
  mortgage: 'Ипотека',
};

const scoredBorrowers = computed<ScoredBorrower[]>(() =>
  borrowers.value.map((borrower) => {
    const probability = estimateDefaultProbability(borrower);
    return {
      borrower,
      probability,
      decision: probability >= 0.55 ? 'отказать' : 'одобрить',
      paymentToIncome: estimatePaymentToIncome(borrower),
    };
  }),
);

const approvedCount = computed(() => scoredBorrowers.value.filter((item) => item.decision === 'одобрить').length);
const declinedCount = computed(() => scoredBorrowers.value.length - approvedCount.value);
const highRiskCount = computed(() => scoredBorrowers.value.filter((item) => item.probability >= 0.55).length);
const mediumRiskCount = computed(
  () => scoredBorrowers.value.filter((item) => item.probability >= 0.35 && item.probability < 0.55).length,
);
const averageRisk = computed(() => average(scoredBorrowers.value.map((item) => item.probability)));
const averagePaymentToIncome = computed(() =>
  average(scoredBorrowers.value.map((item) => item.paymentToIncome)),
);
const totalLoanAmount = computed(() =>
  borrowers.value.reduce((sum, borrower) => sum + borrower.loanAmount, 0),
);

const metrics = computed(() => [
  {
    label: 'Средний риск',
    value: formatPercent(averageRisk.value),
    caption: `${mediumRiskCount.value} заявок в средней зоне`,
  },
  {
    label: 'К одобрению',
    value: formatPercent(approvedCount.value / Math.max(1, scoredBorrowers.value.length)),
    caption: `${approvedCount.value} заявок`,
  },
  {
    label: 'Высокий риск',
    value: formatPercent(highRiskCount.value / Math.max(1, scoredBorrowers.value.length)),
    caption: `${highRiskCount.value} заявок`,
  },
  {
    label: 'Портфель',
    value: formatMoney(totalLoanAmount.value),
    caption: `платёж / доход ${formatPercent(averagePaymentToIncome.value)}`,
  },
]);

const summaryItems = computed(() => {
  const riskiestPurpose = groupByRisk(scoredBorrowers.value, (item) => item.borrower.loanPurpose)[0];
  const safestEmployment = groupByRisk(scoredBorrowers.value, (item) => item.borrower.employmentType)
    .filter((item) => item.count >= 20)
    .at(-1);
  const largestHousing = groupByCount(borrowers.value, (borrower) => borrower.housingType)[0];

  return [
    {
      title: 'Самая рискованная цель',
      text: riskiestPurpose
        ? `${riskiestPurpose.label}: ${formatPercent(riskiestPurpose.riskSum / riskiestPurpose.count)}`
        : 'Нет данных',
    },
    {
      title: 'Самая спокойная занятость',
      text: safestEmployment
        ? `${employmentLabels[safestEmployment.label] ?? safestEmployment.label}: ${formatPercent(
            safestEmployment.riskSum / safestEmployment.count,
          )}`
        : 'Нет данных',
    },
    {
      title: 'Основной тип жилья',
      text: largestHousing
        ? `${housingLabels[largestHousing.label] ?? largestHousing.label}: ${largestHousing.count}`
        : 'Нет данных',
    },
  ];
});

const selectedTopBorrowers = computed(() =>
  [...scoredBorrowers.value]
    .sort((left, right) =>
      topBorrowerMode.value === 'worst'
        ? right.probability - left.probability
        : left.probability - right.probability,
    )
    .slice(0, 12),
);

const topBorrowersTitle = computed(() =>
  topBorrowerMode.value === 'worst'
    ? 'Топ-12 заявок с максимальным риском'
    : 'Топ-12 заявок с минимальным риском',
);

const topBorrowersSubtitle = computed(() =>
  topBorrowerMode.value === 'worst'
    ? 'клиенты с наибольшей прогнозной вероятностью дефолта'
    : 'клиенты с наименьшей прогнозной вероятностью дефолта',
);

const decisionChartData = computed<ChartData<'doughnut'>>(() => ({
  labels: ['Одобрить', 'Отказать'],
  datasets: [
    {
      data: [approvedCount.value, declinedCount.value],
      backgroundColor: [chartColors.success, chartColors.danger],
      borderWidth: 0,
    },
  ],
}));

const riskBucketChartData = computed<ChartData<'bar'>>(() => {
  return {
    labels: riskBuckets.map((bucket) => bucket.label),
    datasets: [
      {
        label: 'Заявки',
        data: riskBuckets.map(
          (bucket) =>
            scoredBorrowers.value.filter(
              (item) => item.probability >= bucket.min && item.probability < bucket.max,
            ).length,
        ),
        backgroundColor: riskBuckets.map((bucket) => bucket.color),
        borderRadius: 6,
      },
    ],
  };
});

const riskBucketLegend = computed(() =>
  riskBuckets.map((bucket) => {
    const count = scoredBorrowers.value.filter(
      (item) => item.probability >= bucket.min && item.probability < bucket.max,
    ).length;
    return {
      ...bucket,
      count,
      share: formatPercent(count / Math.max(1, scoredBorrowers.value.length)),
    };
  }),
);

const topBorrowersChartData = computed<ChartData<'bar'>>(() => ({
  labels: selectedTopBorrowers.value.map((item) => shortName(item.borrower.name)),
  datasets: [
    {
      label: 'PD, %',
      data: selectedTopBorrowers.value.map((item) => Math.round(item.probability * 100)),
      backgroundColor: topBorrowerMode.value === 'worst' ? chartColors.danger : chartColors.success,
      borderRadius: 6,
    },
  ],
}));

const purposeRiskChartData = computed<ChartData<'bar'>>(() => {
  const groups = groupByRisk(scoredBorrowers.value, (item) => item.borrower.loanPurpose).slice(0, 7);
  return {
    labels: groups.map((group) => group.label),
    datasets: [
      {
        label: 'Средний PD',
        data: groups.map((group) => Math.round((group.riskSum / group.count) * 100)),
        backgroundColor: chartColors.warning,
        borderRadius: 6,
      },
    ],
  };
});

const employmentChartData = computed<ChartData<'bar'>>(() => {
  const groups = groupByRisk(scoredBorrowers.value, (item) => item.borrower.employmentType);
  return {
    labels: groups.map((group) => employmentLabels[group.label] ?? group.label),
    datasets: [
      {
        label: 'Заявки',
        data: groups.map((group) => group.count),
        backgroundColor: chartColors.primary,
        borderRadius: 6,
        yAxisID: 'y',
      },
      {
        label: 'Средний PD, %',
        data: groups.map((group) => Math.round((group.riskSum / group.count) * 100)),
        backgroundColor: chartColors.danger,
        borderRadius: 6,
        yAxisID: 'yRisk',
      },
    ],
  };
});

const ageRiskChartData = computed<ChartData<'line'>>(() => {
  const groups = [
    { label: '20-24', min: 20, max: 24 },
    { label: '25-34', min: 25, max: 34 },
    { label: '35-44', min: 35, max: 44 },
    { label: '45-54', min: 45, max: 54 },
    { label: '55-64', min: 55, max: 64 },
    { label: '65+', min: 65, max: 120 },
  ];

  return {
    labels: groups.map((group) => group.label),
    datasets: [
      {
        label: 'Средний PD, %',
        data: groups.map((group) => {
          const items = scoredBorrowers.value.filter(
            (item) => item.borrower.age >= group.min && item.borrower.age <= group.max,
          );
          return Math.round(average(items.map((item) => item.probability)) * 100);
        }),
        borderColor: chartColors.cyan,
        backgroundColor: 'rgba(20, 184, 166, 0.16)',
        fill: true,
        tension: 0.35,
      },
    ],
  };
});

const housingChartData = computed<ChartData<'doughnut'>>(() => {
  const groups = groupByCount(borrowers.value, (borrower) => borrower.housingType);
  return {
    labels: groups.map((group) => housingLabels[group.label] ?? group.label),
    datasets: [
      {
        data: groups.map((group) => group.count),
        backgroundColor: [chartColors.primary, chartColors.success, chartColors.warning, chartColors.info],
        borderWidth: 0,
      },
    ],
  };
});

const barOptions: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        boxWidth: 10,
        boxHeight: 10,
      },
    },
    tooltip: {
      intersect: false,
      mode: 'index',
    },
  },
  scales: {
    y: {
      beginAtZero: true,
      grid: { color: 'rgba(144, 147, 153, 0.18)' },
    },
    yRisk: {
      beginAtZero: true,
      max: 100,
      position: 'right',
      grid: { drawOnChartArea: false },
      ticks: {
        callback: (value) => `${value}%`,
      },
    },
    x: {
      grid: { display: false },
    },
  },
};

const horizontalBarOptions: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: 'y',
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        boxWidth: 10,
        boxHeight: 10,
      },
    },
    tooltip: {
      intersect: false,
      mode: 'index',
    },
  },
  scales: {
    x: {
      beginAtZero: true,
      max: 100,
      grid: { color: 'rgba(144, 147, 153, 0.18)' },
      ticks: {
        callback: (value) => `${value}%`,
      },
    },
    y: {
      grid: { display: false },
    },
  },
};

const topBorrowersChartOptions: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: 'y',
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      intersect: false,
      mode: 'index',
    },
  },
  scales: {
    x: {
      beginAtZero: true,
      max: 100,
      grid: { color: 'rgba(144, 147, 153, 0.18)' },
      ticks: {
        callback: (value) => `${value}%`,
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

const lineOptions: ChartOptions<'line'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        boxWidth: 10,
        boxHeight: 10,
      },
    },
    tooltip: {
      intersect: false,
      mode: 'index',
    },
  },
  scales: {
    y: {
      beginAtZero: true,
      max: 100,
      grid: { color: 'rgba(144, 147, 153, 0.18)' },
      ticks: {
        callback: (value) => `${value}%`,
      },
    },
    x: {
      grid: { display: false },
    },
  },
};

const doughnutOptions: ChartOptions<'doughnut'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        boxWidth: 10,
        boxHeight: 10,
      },
    },
    tooltip: {
      intersect: false,
    },
  },
  cutout: '64%',
};

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

  return clamp(Number(risk.toFixed(2)), 0.01, 0.99);
}

function estimatePaymentToIncome(borrower: BorrowerCard) {
  const monthlyRate = borrower.interestRate / 100 / 12;
  let payment = borrower.loanAmount / Math.max(1, borrower.loanTermMonths);
  if (monthlyRate > 0) {
    const multiplier = (1 + monthlyRate) ** borrower.loanTermMonths;
    payment = (borrower.loanAmount * monthlyRate * multiplier) / (multiplier - 1);
  }
  return borrower.income > 0 ? payment / borrower.income : 1;
}

function groupByRisk(items: ScoredBorrower[], getKey: (item: ScoredBorrower) => string) {
  const groups = new Map<string, GroupStats>();
  for (const item of items) {
    const key = getKey(item);
    const group = groups.get(key) ?? { label: key, count: 0, riskSum: 0 };
    group.count += 1;
    group.riskSum += item.probability;
    groups.set(key, group);
  }
  return [...groups.values()].sort((left, right) => right.riskSum / right.count - left.riskSum / left.count);
}

function groupByCount(items: BorrowerCard[], getKey: (item: BorrowerCard) => string) {
  const groups = new Map<string, { label: string; count: number }>();
  for (const item of items) {
    const key = getKey(item);
    const group = groups.get(key) ?? { label: key, count: 0 };
    group.count += 1;
    groups.set(key, group);
  }
  return [...groups.values()].sort((left, right) => right.count - left.count);
}

function average(values: number[]) {
  if (values.length === 0) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`;
}

function formatMoney(value: number) {
  return `${new Intl.NumberFormat('ru-RU', {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value)} ₽`;
}

function shortName(name: string) {
  const parts = name.split(' ').filter(Boolean);
  if (parts.length <= 2) return name;
  return `${parts[0]} ${parts[1][0]}. ${parts[2][0]}.`;
}
</script>

<style scoped lang="scss">
.analytics-page {
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

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.metric-card,
.summary-item,
.chart-panel,
.risk-table {
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: var(--el-fill-color-blank);
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
    font-size: 30px;
    line-height: 1;
  }
}

.summary-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.summary-item {
  display: grid;
  gap: 6px;
  padding: 14px 16px;

  span {
    color: var(--app-muted);
    overflow-wrap: anywhere;
  }
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;

  &--top {
    grid-template-columns: minmax(280px, 0.8fr) minmax(0, 1.2fr);
  }

  &--single {
    grid-template-columns: minmax(0, 1fr);
  }
}

.chart-panel {
  display: grid;
  grid-template-rows: auto minmax(260px, 1fr);
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

  &--wide {
    min-width: 0;
  }
}

.chart-box {
  position: relative;
  min-height: 260px;

  &--large {
    min-height: 360px;
  }
}

.risk-legend {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;

  li {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 4px 8px;
    align-items: center;
    min-width: 0;
    border: 1px solid var(--app-border);
    border-radius: 8px;
    padding: 8px;
  }

  i {
    width: 10px;
    height: 10px;
    border-radius: 50%;
  }

  span,
  strong,
  small {
    min-width: 0;
  }

  span {
    color: var(--app-muted);
    font-size: 12px;
  }

  strong {
    grid-column: 2;
    font-size: 15px;
  }

  small {
    grid-column: 2;
    color: var(--app-muted);
    font-size: 12px;
  }
}

.risk-table {
  display: grid;
  gap: 12px;
  min-width: 0;
  padding: 16px;

  > header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;

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
}

@media (max-width: 1180px) {
  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .dashboard-grid,
  .dashboard-grid--top,
  .dashboard-grid--single,
  .summary-strip {
    grid-template-columns: 1fr;
  }

  .risk-legend {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .metric-grid {
    grid-template-columns: 1fr;
  }

  .chart-panel,
  .risk-table {
    padding: 12px;
  }

  .risk-table > header {
    flex-direction: column;
  }

  .risk-legend {
    grid-template-columns: 1fr;
  }
}
</style>
