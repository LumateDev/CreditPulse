<template>
  <section class="scenarios-page">
    <PageHeader
      title="Сценарии"
      eyebrow="Что если"
      description="Сравнение стратегий одобрения по прибыли, риску и объёму выдач."
    >
      <template #actions>
        <el-tag effect="plain" type="info">{{ scenarios.length }} сценариев</el-tag>
      </template>
    </PageHeader>

    <el-scrollbar v-loading="isLoading" class="scenarios-page__scroll">
      <div class="scenarios-page__content">
        <section class="scenario-editor">
          <header>
            <div>
              <h3>Настройка сценария</h3>
              <span>Сценарий сохраняется в браузере и сразу попадает в сравнение.</span>
            </div>
            <el-button plain :icon="RefreshRight" @click="resetDraft">Сбросить</el-button>
          </header>

          <el-form label-position="top" class="scenario-form">
            <el-form-item label="Название">
              <el-input v-model="draft.name" maxlength="32" />
            </el-form-item>
            <el-form-item label="Стоимость фондирования">
              <el-input-number v-model="draft.fundingRatePercent" :min="0" :max="50" :step="0.5" />
            </el-form-item>
            <el-form-item label="LGD">
              <el-input-number v-model="draft.lgdPercent" :min="0" :max="100" :step="1" />
            </el-form-item>
            <el-form-item label="Максимальный PD для одобрения">
              <el-input-number v-model="draft.maxPdPercent" :min="1" :max="99" :step="1" />
            </el-form-item>
            <el-form-item label="Действие">
              <el-button type="primary" :icon="Plus" @click="saveDraft">Сохранить сценарий</el-button>
            </el-form-item>
          </el-form>
        </section>

        <section class="metric-grid">
          <article v-for="summary in scenarioSummaries" :key="summary.scenario.id" class="scenario-card">
            <span>{{ summary.scenario.name }}</span>
            <strong :class="summary.profit < 0 ? 'negative' : ''">{{ formatMoney(summary.profit) }}</strong>
            <small>
              Одобрение {{ formatPercent(summary.approvalRate) }} · маржа {{ formatPercent(summary.margin) }}
            </small>
            <el-button link type="primary" @click="openReport(summary.scenario.id)">Открыть отчёт</el-button>
          </article>
        </section>

        <section class="dashboard-grid">
          <article class="chart-panel">
            <header>
              <h3>Ожидаемая прибыль</h3>
              <span>по сценариям</span>
            </header>
            <div class="chart-box">
              <Bar :data="profitChartData" :options="moneyBarOptions" />
            </div>
          </article>

          <article class="chart-panel">
            <header>
              <h3>Одобрение и маржа</h3>
              <span>доля заявок и доходность</span>
            </header>
            <div class="chart-box">
              <Bar :data="rateChartData" :options="percentBarOptions" />
            </div>
          </article>
        </section>

        <section class="comparison-table">
          <header>
            <div>
              <h3>Сравнение сценариев</h3>
              <span>расчёт выполнен по всей клиентской базе</span>
            </div>
          </header>

          <el-table :data="scenarioSummaries" border height="420">
            <el-table-column prop="scenario.name" label="Сценарий" min-width="190" fixed />
            <el-table-column prop="approvedCount" label="Одобрено" width="120" sortable />
            <el-table-column prop="approvalRate" label="Доля" width="100" sortable>
              <template #default="{ row }: { row: ScenarioSummary }">
                {{ formatPercent(row.approvalRate) }}
              </template>
            </el-table-column>
            <el-table-column prop="amount" label="Выдачи" width="150" sortable>
              <template #default="{ row }: { row: ScenarioSummary }">
                {{ formatMoney(row.amount) }}
              </template>
            </el-table-column>
            <el-table-column prop="interest" label="Проценты" width="150" sortable>
              <template #default="{ row }: { row: ScenarioSummary }">
                {{ formatMoney(row.interest) }}
              </template>
            </el-table-column>
            <el-table-column prop="loss" label="Ожид. потери" width="150" sortable>
              <template #default="{ row }: { row: ScenarioSummary }">
                {{ formatMoney(row.loss) }}
              </template>
            </el-table-column>
            <el-table-column prop="profit" label="Прибыль" width="150" sortable>
              <template #default="{ row }: { row: ScenarioSummary }">
                <strong :class="row.profit < 0 ? 'negative' : 'positive'">
                  {{ formatMoney(row.profit) }}
                </strong>
              </template>
            </el-table-column>
            <el-table-column prop="margin" label="Маржа" width="110" sortable>
              <template #default="{ row }: { row: ScenarioSummary }">
                {{ formatPercent(row.margin) }}
              </template>
            </el-table-column>
            <el-table-column label="Действия" width="180" fixed="right">
              <template #default="{ row }: { row: ScenarioSummary }">
                <el-button link type="primary" @click="openReport(row.scenario.id)">Отчёт</el-button>
                <el-button
                  v-if="row.scenario.custom"
                  link
                  type="danger"
                  @click="deleteScenario(row.scenario.id)"
                >
                  Удалить
                </el-button>
                <el-tag v-else effect="plain" type="info">preset</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </section>
      </div>
    </el-scrollbar>

    <el-drawer
      v-model="reportVisible"
      :title="selectedReport?.scenario.name ?? 'Отчёт по сценарию'"
      size="76%"
    >
      <section v-if="selectedReport" class="scenario-report">
        <header class="scenario-report__header">
          <div>
            <span class="app-kicker">Отчёт</span>
            <h3>{{ selectedReport.scenario.name }}</h3>
            <p>
              PD до {{ selectedReport.scenario.maxPdPercent }}%, фондирование
              {{ selectedReport.scenario.fundingRatePercent }}%, LGD {{ selectedReport.scenario.lgdPercent }}%.
            </p>
          </div>
          <el-tag :type="selectedReport.profit >= 0 ? 'success' : 'danger'" effect="light">
            {{ selectedReport.profit >= 0 ? 'прибыльный' : 'убыточный' }}
          </el-tag>
        </header>

        <section class="report-metrics">
          <article>
            <span>Ожидаемая прибыль</span>
            <strong :class="selectedReport.profit < 0 ? 'negative' : 'positive'">
              {{ formatMoney(selectedReport.profit) }}
            </strong>
          </article>
          <article>
            <span>Одобрено</span>
            <strong>{{ selectedReport.approvedCount }}</strong>
          </article>
          <article>
            <span>Доля одобрения</span>
            <strong>{{ formatPercent(selectedReport.approvalRate) }}</strong>
          </article>
          <article>
            <span>Маржа</span>
            <strong>{{ formatPercent(selectedReport.margin) }}</strong>
          </article>
        </section>

        <section class="report-grid">
          <article class="chart-panel">
            <header>
              <h3>Разложение прибыли</h3>
              <span>проценты, фондирование, риск</span>
            </header>
            <div class="chart-box">
              <Bar :data="reportBreakdownChartData" :options="moneyBarOptions" />
            </div>
          </article>

          <article class="comparison-table">
            <header>
              <div>
                <h3>Сегменты по целям</h3>
                <span>где сценарий зарабатывает больше всего</span>
              </div>
            </header>
            <el-table :data="reportPurposeRows" border height="300">
              <el-table-column prop="label" label="Цель" min-width="170" />
              <el-table-column prop="count" label="Сделки" width="100" />
              <el-table-column prop="profit" label="Прибыль" width="150">
                <template #default="{ row }: { row: ReportSegment }">
                  <strong :class="row.profit < 0 ? 'negative' : 'positive'">
                    {{ formatMoney(row.profit) }}
                  </strong>
                </template>
              </el-table-column>
              <el-table-column prop="margin" label="Маржа" width="100">
                <template #default="{ row }: { row: ReportSegment }">
                  {{ formatPercent(row.margin) }}
                </template>
              </el-table-column>
            </el-table>
          </article>
        </section>
      </section>
    </el-drawer>
  </section>
</template>

<script setup lang="ts">
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Tooltip,
} from 'chart.js';
import type { ChartData, ChartOptions } from 'chart.js';
import { Plus, RefreshRight } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus/es/components/message/index';
import { computed, reactive, ref, watch } from 'vue';
import { Bar } from 'vue-chartjs';

import type { BorrowerCard } from '@/api/generated/creditpulse';
import PageHeader from '@/components/PageHeader.vue';
import { useBorrowers } from '@/composables/useBorrowers';

ChartJS.register(BarElement, CategoryScale, Legend, LinearScale, Tooltip);

interface ScenarioConfig {
  id: string;
  name: string;
  fundingRatePercent: number;
  lgdPercent: number;
  maxPdPercent: number;
  custom?: boolean;
}

interface ScenarioSummary {
  scenario: ScenarioConfig;
  approvedCount: number;
  approvalRate: number;
  amount: number;
  interest: number;
  funding: number;
  loss: number;
  profit: number;
  margin: number;
}

interface ScenarioDeal {
  borrower: BorrowerCard;
  probability: number;
  profit: number;
}

interface ReportSegment {
  label: string;
  count: number;
  amount: number;
  profit: number;
  margin: number;
}

const STORAGE_KEY = 'creditpulse.revenueScenarios';

const presetScenarios: ScenarioConfig[] = [
  {
    id: 'base',
    name: 'Базовый',
    fundingRatePercent: 2,
    lgdPercent: 20,
    maxPdPercent: 45,
  },
  {
    id: 'conservative',
    name: 'Консервативный',
    fundingRatePercent: 2,
    lgdPercent: 20,
    maxPdPercent: 30,
  },
  {
    id: 'balanced',
    name: 'Оптимальный',
    fundingRatePercent: 2,
    lgdPercent: 20,
    maxPdPercent: 35,
  },
  {
    id: 'growth',
    name: 'Агрессивный рост',
    fundingRatePercent: 3,
    lgdPercent: 25,
    maxPdPercent: 55,
  },
];

const { borrowers, isLoading } = useBorrowers();
const customScenarios = ref<ScenarioConfig[]>(loadCustomScenarios());
const reportVisible = ref(false);
const selectedReportId = ref('');
const draft = reactive<ScenarioConfig>({
  id: '',
  name: 'Новый сценарий',
  fundingRatePercent: 2,
  lgdPercent: 20,
  maxPdPercent: 35,
  custom: true,
});

const colors = {
  primary: '#409eff',
  success: '#67c23a',
  warning: '#e6a23c',
  danger: '#f56c6c',
  cyan: '#14b8a6',
};

const scenarios = computed(() => [...presetScenarios, ...customScenarios.value]);

const scenarioSummaries = computed(() =>
  scenarios.value.map((scenario) => calculateScenarioSummary(scenario, borrowers.value)),
);

const selectedReport = computed(() =>
  scenarioSummaries.value.find((summary) => summary.scenario.id === selectedReportId.value),
);

const selectedReportDeals = computed(() => {
  if (!selectedReport.value) return [];
  return calculateScenarioDeals(selectedReport.value.scenario, borrowers.value);
});

const reportBreakdownChartData = computed<ChartData<'bar'>>(() => {
  const summary = selectedReport.value;
  return {
    labels: ['Проценты', 'Фондирование', 'Ожид. потери', 'Итог'],
    datasets: [
      {
        label: '₽',
        data: summary
          ? [summary.interest, -summary.funding, -summary.loss, summary.profit]
          : [0, 0, 0, 0],
        backgroundColor: [
          colors.success,
          colors.warning,
          colors.danger,
          summary && summary.profit >= 0 ? colors.primary : colors.danger,
        ],
        borderRadius: 6,
      },
    ],
  };
});

const reportPurposeRows = computed(() =>
  groupReportSegments(selectedReportDeals.value, (deal) => deal.borrower.loanPurpose)
    .sort((left, right) => right.profit - left.profit)
    .slice(0, 8),
);

const profitChartData = computed<ChartData<'bar'>>(() => ({
  labels: scenarioSummaries.value.map((summary) => summary.scenario.name),
  datasets: [
    {
      label: 'Ожидаемая прибыль',
      data: scenarioSummaries.value.map((summary) => Math.round(summary.profit)),
      backgroundColor: scenarioSummaries.value.map((summary) =>
        summary.profit >= 0 ? colors.primary : colors.danger,
      ),
      borderRadius: 6,
    },
    {
      label: 'Ожидаемые потери',
      data: scenarioSummaries.value.map((summary) => Math.round(-summary.loss)),
      backgroundColor: colors.warning,
      borderRadius: 6,
    },
  ],
}));

const rateChartData = computed<ChartData<'bar'>>(() => ({
  labels: scenarioSummaries.value.map((summary) => summary.scenario.name),
  datasets: [
    {
      label: 'Одобрение, %',
      data: scenarioSummaries.value.map((summary) => Math.round(summary.approvalRate * 100)),
      backgroundColor: colors.success,
      borderRadius: 6,
    },
    {
      label: 'Маржа, %',
      data: scenarioSummaries.value.map((summary) => Math.round(summary.margin * 100)),
      backgroundColor: colors.cyan,
      borderRadius: 6,
    },
  ],
}));

const moneyBarOptions: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
      labels: { boxWidth: 10, boxHeight: 10 },
    },
    tooltip: {
      callbacks: {
        label: (item) => `${item.dataset.label}: ${formatMoney(Number(item.raw ?? 0))}`,
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

const percentBarOptions: ChartOptions<'bar'> = {
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
        callback: (value) => `${value}%`,
      },
    },
    x: { grid: { display: false } },
  },
};

watch(
  customScenarios,
  (items) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  },
  { deep: true },
);

function saveDraft() {
  const name = draft.name.trim();
  if (!name) {
    ElMessage.error('Укажите название сценария.');
    return;
  }

  customScenarios.value = [
    ...customScenarios.value,
    {
      id: crypto.randomUUID(),
      name,
      fundingRatePercent: draft.fundingRatePercent,
      lgdPercent: draft.lgdPercent,
      maxPdPercent: draft.maxPdPercent,
      custom: true,
    },
  ];
  ElMessage.success('Сценарий сохранён.');
}

function resetDraft() {
  Object.assign(draft, {
    id: '',
    name: 'Новый сценарий',
    fundingRatePercent: 2,
    lgdPercent: 20,
    maxPdPercent: 35,
    custom: true,
  });
}

function openReport(scenarioId: string) {
  selectedReportId.value = scenarioId;
  reportVisible.value = true;
}

function deleteScenario(scenarioId: string) {
  customScenarios.value = customScenarios.value.filter((scenario) => scenario.id !== scenarioId);
  if (selectedReportId.value === scenarioId) {
    reportVisible.value = false;
    selectedReportId.value = '';
  }
}

function calculateScenarioSummary(scenario: ScenarioConfig, items: BorrowerCard[]): ScenarioSummary {
  const maxPd = scenario.maxPdPercent / 100;
  const approvedDeals = items
    .map((borrower) => ({
      borrower,
      probability: estimateDefaultProbability(borrower),
    }))
    .filter((deal) => deal.probability <= maxPd);

  const totals = approvedDeals.reduce(
    (sum, deal) => {
      const grossInterest = estimateGrossInterest(deal.borrower);
      const funding =
        deal.borrower.loanAmount *
        (scenario.fundingRatePercent / 100) *
        (deal.borrower.loanTermMonths / 12);
      const loss = deal.borrower.loanAmount * deal.probability * (scenario.lgdPercent / 100);
      return {
        amount: sum.amount + deal.borrower.loanAmount,
        interest: sum.interest + grossInterest,
        funding: sum.funding + funding,
        loss: sum.loss + loss,
        profit: sum.profit + grossInterest - funding - loss,
      };
    },
    { amount: 0, interest: 0, funding: 0, loss: 0, profit: 0 },
  );

  return {
    scenario,
    approvedCount: approvedDeals.length,
    approvalRate: approvedDeals.length / Math.max(1, items.length),
    amount: totals.amount,
    interest: totals.interest,
    funding: totals.funding,
    loss: totals.loss,
    profit: totals.profit,
    margin: totals.amount > 0 ? totals.profit / totals.amount : 0,
  };
}

function calculateScenarioDeals(scenario: ScenarioConfig, items: BorrowerCard[]): ScenarioDeal[] {
  const maxPd = scenario.maxPdPercent / 100;
  return items
    .map((borrower) => {
      const probability = estimateDefaultProbability(borrower);
      const grossInterest = estimateGrossInterest(borrower);
      const funding =
        borrower.loanAmount * (scenario.fundingRatePercent / 100) * (borrower.loanTermMonths / 12);
      const loss = borrower.loanAmount * probability * (scenario.lgdPercent / 100);
      return {
        borrower,
        probability,
        profit: grossInterest - funding - loss,
      };
    })
    .filter((deal) => deal.probability <= maxPd);
}

function groupReportSegments(items: ScenarioDeal[], getKey: (deal: ScenarioDeal) => string) {
  const groups = new Map<string, ReportSegment>();
  for (const deal of items) {
    const key = getKey(deal);
    const group = groups.get(key) ?? { label: key, count: 0, amount: 0, profit: 0, margin: 0 };
    group.count += 1;
    group.amount += deal.borrower.loanAmount;
    group.profit += deal.profit;
    group.margin = group.amount > 0 ? group.profit / group.amount : 0;
    groups.set(key, group);
  }
  return [...groups.values()];
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

function loadCustomScenarios() {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '[]');
    return Array.isArray(parsed) ? parsed.filter(isScenarioConfig) : [];
  } catch {
    return [];
  }
}

function isScenarioConfig(value: unknown): value is ScenarioConfig {
  if (!value || typeof value !== 'object') return false;
  const scenario = value as Record<string, unknown>;
  return (
    typeof scenario.id === 'string' &&
    typeof scenario.name === 'string' &&
    typeof scenario.fundingRatePercent === 'number' &&
    typeof scenario.lgdPercent === 'number' &&
    typeof scenario.maxPdPercent === 'number'
  );
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
.scenarios-page {
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

.scenario-editor,
.scenario-card,
.chart-panel,
.comparison-table {
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: var(--el-fill-color-blank);
}

.scenario-editor {
  display: grid;
  gap: 14px;
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
    display: block;
    margin-top: 4px;
    color: var(--app-muted);
    font-size: 13px;
  }
}

.scenario-form {
  display: grid;
  grid-template-columns: minmax(180px, 1fr) repeat(3, minmax(150px, 180px)) auto;
  gap: 12px;
  align-items: end;

  :deep(.el-form-item) {
    margin-bottom: 0;
  }
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.scenario-card {
  display: grid;
  gap: 6px;
  min-height: 112px;
  padding: 16px;

  span,
  small {
    color: var(--app-muted);
  }

  strong {
    font-size: 28px;
    line-height: 1.05;
  }

  :deep(.el-button) {
    justify-self: start;
    padding: 0;
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
}

.chart-panel {
  display: grid;
  grid-template-rows: auto minmax(300px, 1fr);
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
  min-height: 300px;
}

.comparison-table {
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

.scenario-report {
  display: grid;
  gap: 16px;

  &__header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    border-bottom: 1px solid var(--app-border);
    padding-bottom: 16px;

    h3 {
      margin: 0;
      font-size: 24px;
    }

    p {
      margin: 6px 0 0;
      color: var(--app-muted);
    }
  }
}

.report-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;

  article {
    display: grid;
    gap: 6px;
    border: 1px solid var(--app-border);
    border-radius: 8px;
    padding: 14px;
  }

  span {
    color: var(--app-muted);
    font-size: 13px;
  }

  strong {
    font-size: 24px;
  }
}

.report-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(360px, 0.95fr);
  gap: 16px;
}

@media (max-width: 1180px) {
  .dashboard-grid,
  .metric-grid,
  .report-grid,
  .report-metrics,
  .scenario-form {
    grid-template-columns: 1fr;
  }

  .scenario-editor header {
    flex-direction: column;
  }
}

@media (max-width: 760px) {
  .scenario-editor,
  .chart-panel,
  .comparison-table {
    padding: 12px;
  }
}
</style>
