<script setup lang="ts">
import { formatPrice } from "~/composables/useLocaleText";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin"],
});

interface DayPoint {
  date: string;
  gross: number;
  orders: number;
}
interface KpiBucket { gross: number; fee: number; orders: number }
interface TopBookRow { id: string; slug: string; title: Record<string, string>; revenue: number; units: number }
interface TopAuthorRow { id: string; slug: string; display_name: string; earning: number; units: number }
interface FinanceOverview {
  currency: string;
  generated_at: string;
  kpi: {
    today: KpiBucket;
    week: KpiBucket;
    month: KpiBucket;
    prev_month: KpiBucket;
    all_time: KpiBucket;
  };
  series: DayPoint[];
  top_books: TopBookRow[];
  top_authors: TopAuthorRow[];
  status_breakdown: Record<string, number>;
}

const { t } = useI18n();
const localePath = useLocalePath();
const api = useApi();
const { localised } = useLocaleText();

useHead({ title: t("admin.finance.title") });

const days = ref(30);

const { data: rawOverview, refresh, pending } = await useAsyncData(
  "admin:finance:overview",
  () => api<FinanceOverview>("/admin/finance/overview", { query: { days: days.value } }),
  { server: false, watch: [days] },
);
const overview = computed(() => rawOverview.value as FinanceOverview | null);

const seriesPoints = computed(() =>
  (overview.value?.series ?? []).map((s) => ({ date: s.date, value: s.gross })),
);

const monthDelta = computed(() => {
  if (!overview.value) return null;
  const cur = overview.value.kpi.month.gross;
  const prev = overview.value.kpi.prev_month.gross;
  if (prev <= 0) return cur > 0 ? 100 : 0;
  return Math.round(((cur - prev) / prev) * 100);
});

function exportCsv() {
  if (!overview.value) return;
  const rows = [["date", "gross_uzs", "orders"]];
  for (const p of overview.value.series) rows.push([p.date, String(p.gross), String(p.orders)]);
  const csv = rows.map((r) => r.join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `monografiya-finance-${overview.value.generated_at.slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
</script>

<template>
  <section class="space-y-5">
    <AdminPageHeader
      :title="t('admin.finance.title')"
      :description="t('admin.finance.subtitle')"
      icon="money"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('admin.finance.title') },
      ]"
    >
      <template #actions>
        <select
          v-model.number="days"
          class="text-xs border border-border rounded px-2 py-1 bg-bg text-ink"
        >
          <option :value="7">{{ t("admin.finance.range_7d") }}</option>
          <option :value="30">{{ t("admin.finance.range_30d") }}</option>
          <option :value="90">{{ t("admin.finance.range_90d") }}</option>
          <option :value="180">{{ t("admin.finance.range_180d") }}</option>
        </select>
        <UiButton variant="ghost" size="sm" :disabled="!overview" @click="exportCsv">
          <Icon name="document" class="h-3.5 w-3.5" />
          {{ t("admin.finance.export_csv") }}
        </UiButton>
      </template>
    </AdminPageHeader>

    <!-- KPI cards -->
    <div v-if="overview" class="grid grid-cols-2 lg:grid-cols-5 gap-3">
      <div class="rounded-md border border-border bg-bg-card p-4">
        <div class="text-[10px] uppercase tracking-wide text-ink-tertiary">{{ t("admin.finance.kpi.today") }}</div>
        <div class="text-xl font-serif text-ink mt-1 tabular-nums">{{ formatPrice(overview.kpi.today.gross) }}</div>
        <div class="text-xs text-ink-tertiary mt-0.5">{{ t("admin.finance.kpi.orders_count", { n: overview.kpi.today.orders }) }}</div>
      </div>
      <div class="rounded-md border border-border bg-bg-card p-4">
        <div class="text-[10px] uppercase tracking-wide text-ink-tertiary">{{ t("admin.finance.kpi.week") }}</div>
        <div class="text-xl font-serif text-ink mt-1 tabular-nums">{{ formatPrice(overview.kpi.week.gross) }}</div>
        <div class="text-xs text-ink-tertiary mt-0.5">{{ t("admin.finance.kpi.orders_count", { n: overview.kpi.week.orders }) }}</div>
      </div>
      <div class="rounded-md border border-primary/30 bg-primary/5 p-4">
        <div class="text-[10px] uppercase tracking-wide text-primary">{{ t("admin.finance.kpi.month") }}</div>
        <div class="text-xl font-serif text-primary mt-1 tabular-nums">{{ formatPrice(overview.kpi.month.gross) }}</div>
        <div class="text-xs text-ink-secondary mt-0.5 inline-flex items-center gap-1">
          <span>{{ t("admin.finance.kpi.orders_count", { n: overview.kpi.month.orders }) }}</span>
          <span v-if="monthDelta !== null" :class="monthDelta >= 0 ? 'text-success' : 'text-error'">
            ({{ monthDelta >= 0 ? "+" : "" }}{{ monthDelta }}%)
          </span>
        </div>
      </div>
      <div class="rounded-md border border-border bg-bg-card p-4">
        <div class="text-[10px] uppercase tracking-wide text-ink-tertiary">{{ t("admin.finance.kpi.platform_fee") }}</div>
        <div class="text-xl font-serif text-ink mt-1 tabular-nums">{{ formatPrice(overview.kpi.month.fee) }}</div>
        <div class="text-xs text-ink-tertiary mt-0.5">{{ t("admin.finance.kpi.this_month") }}</div>
      </div>
      <div class="rounded-md border border-border bg-bg-card p-4">
        <div class="text-[10px] uppercase tracking-wide text-ink-tertiary">{{ t("admin.finance.kpi.all_time") }}</div>
        <div class="text-xl font-serif text-ink mt-1 tabular-nums">{{ formatPrice(overview.kpi.all_time.gross) }}</div>
        <div class="text-xs text-ink-tertiary mt-0.5">{{ t("admin.finance.kpi.orders_count", { n: overview.kpi.all_time.orders }) }}</div>
      </div>
    </div>

    <div v-else-if="pending" class="grid grid-cols-2 lg:grid-cols-5 gap-3">
      <UiSkeleton v-for="i in 5" :key="i" height="5rem" block />
    </div>

    <!-- Revenue series chart -->
    <div v-if="overview" class="rounded-md border border-border bg-bg-card p-5">
      <div class="flex items-center justify-between mb-3">
        <h2 class="font-medium text-ink">{{ t("admin.finance.chart_title") }}</h2>
        <span class="text-xs text-ink-tertiary">{{ t("admin.finance.last_n_days", { n: days }) }}</span>
      </div>
      <AdminMiniChart :points="seriesPoints" :format="(n) => formatPrice(n)" />
    </div>

    <!-- Top books + authors -->
    <div v-if="overview" class="grid lg:grid-cols-2 gap-3">
      <div class="rounded-md border border-border bg-bg-card overflow-hidden">
        <header class="px-4 py-3 border-b border-border flex items-center justify-between">
          <h3 class="font-medium text-ink">{{ t("admin.finance.top_books") }}</h3>
          <Icon name="book" class="h-4 w-4 text-ink-tertiary" />
        </header>
        <UiEmptyState
          v-if="overview.top_books.length === 0"
          icon="book"
          :title="t('admin.finance.empty_top_books')"
          :description="t('admin.finance.empty_top_body')"
        />
        <ul v-else class="divide-y divide-border">
          <li v-for="(b, i) in overview.top_books" :key="b.id" class="px-4 py-2.5 flex items-center gap-3">
            <span class="text-xs text-ink-tertiary w-5 tabular-nums">{{ i + 1 }}</span>
            <NuxtLink :to="localePath(`/admin/books/${b.id}/edit`)" class="flex-1 text-sm text-ink hover:text-primary truncate">
              {{ localised(b.title, b.slug) }}
            </NuxtLink>
            <span class="text-xs text-ink-tertiary tabular-nums whitespace-nowrap">{{ b.units }} ×</span>
            <span class="text-sm text-primary tabular-nums whitespace-nowrap">{{ formatPrice(b.revenue) }}</span>
          </li>
        </ul>
      </div>

      <div class="rounded-md border border-border bg-bg-card overflow-hidden">
        <header class="px-4 py-3 border-b border-border flex items-center justify-between">
          <h3 class="font-medium text-ink">{{ t("admin.finance.top_authors") }}</h3>
          <Icon name="user-circle" class="h-4 w-4 text-ink-tertiary" />
        </header>
        <UiEmptyState
          v-if="overview.top_authors.length === 0"
          icon="users"
          :title="t('admin.finance.empty_top_authors')"
          :description="t('admin.finance.empty_top_body')"
        />
        <ul v-else class="divide-y divide-border">
          <li v-for="(a, i) in overview.top_authors" :key="a.id" class="px-4 py-2.5 flex items-center gap-3">
            <span class="text-xs text-ink-tertiary w-5 tabular-nums">{{ i + 1 }}</span>
            <NuxtLink :to="localePath(`/authors/${a.slug}`)" target="_blank" class="flex-1 text-sm text-ink hover:text-primary truncate">
              {{ a.display_name }}
            </NuxtLink>
            <span class="text-xs text-ink-tertiary tabular-nums whitespace-nowrap">{{ a.units }} ×</span>
            <span class="text-sm text-primary tabular-nums whitespace-nowrap">{{ formatPrice(a.earning) }}</span>
          </li>
        </ul>
      </div>
    </div>

    <!-- Status breakdown -->
    <div v-if="overview" class="rounded-md border border-border bg-bg-card p-5">
      <h3 class="font-medium text-ink mb-3">{{ t("admin.finance.status_breakdown") }}</h3>
      <div class="flex flex-wrap gap-3">
        <div
          v-for="(count, status) in overview.status_breakdown"
          :key="status"
          class="inline-flex items-center gap-2 px-3 py-1.5 rounded-md border border-border"
        >
          <span class="text-xs uppercase tracking-wide text-ink-tertiary">{{ t(`orders.statuses.${status}`) }}</span>
          <span class="text-sm font-medium text-ink tabular-nums">{{ count }}</span>
        </div>
      </div>
    </div>
  </section>
</template>
