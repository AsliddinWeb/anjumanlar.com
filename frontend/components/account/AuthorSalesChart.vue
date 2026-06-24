<script setup lang="ts">
import { formatPrice } from "~/composables/useLocaleText";

interface DayPoint { date: string; gross: number; earning: number; units: number }
interface TopBook { id: string; slug: string; title: Record<string, string>; earning: number; units: number }
interface AuthorOverview {
  currency: string;
  series: DayPoint[];
  totals: { gross: number; earning: number; units: number };
  top_books: TopBook[];
}

const { t } = useI18n();
const api = useApi();
const localePath = useLocalePath();
const { localised } = useLocaleText();

const days = ref(30);

const { data: rawOverview, pending } = await useAsyncData(
  "account:author-sales",
  () => api<AuthorOverview>("/finance/me", { query: { days: days.value } }),
  { server: false, watch: [days] },
);
const overview = computed(() => rawOverview.value as AuthorOverview | null);

const points = computed(() =>
  (overview.value?.series ?? []).map((s) => ({ date: s.date, value: s.earning })),
);

const hasData = computed(() =>
  (overview.value?.totals.units ?? 0) > 0 || (overview.value?.series ?? []).some((s) => s.earning > 0),
);
</script>

<template>
  <div class="rounded-md border border-border bg-bg-card p-5 space-y-4">
    <header class="flex items-center justify-between flex-wrap gap-3">
      <div>
        <h2 class="font-medium text-ink">{{ t("account.sales.title") }}</h2>
        <p class="text-xs text-ink-tertiary mt-0.5">{{ t("account.sales.subtitle") }}</p>
      </div>
      <select
        v-model.number="days"
        class="text-xs border border-border rounded px-2 py-1 bg-bg text-ink"
      >
        <option :value="7">{{ t("admin.finance.range_7d") }}</option>
        <option :value="30">{{ t("admin.finance.range_30d") }}</option>
        <option :value="90">{{ t("admin.finance.range_90d") }}</option>
      </select>
    </header>

    <div v-if="pending && !overview" class="space-y-2">
      <UiSkeleton height="180" block />
    </div>

    <template v-else-if="overview">
      <div class="grid grid-cols-3 gap-2">
        <div class="rounded border border-border bg-bg p-3">
          <div class="text-[10px] uppercase tracking-wide text-ink-tertiary">{{ t("account.sales.lifetime_units") }}</div>
          <div class="text-lg font-serif text-ink tabular-nums">{{ overview.totals.units }}</div>
        </div>
        <div class="rounded border border-border bg-bg p-3">
          <div class="text-[10px] uppercase tracking-wide text-ink-tertiary">{{ t("account.sales.lifetime_earning") }}</div>
          <div class="text-lg font-serif text-primary tabular-nums">{{ formatPrice(overview.totals.earning) }}</div>
        </div>
        <div class="rounded border border-border bg-bg p-3">
          <div class="text-[10px] uppercase tracking-wide text-ink-tertiary">{{ t("account.sales.lifetime_gross") }}</div>
          <div class="text-lg font-serif text-ink tabular-nums">{{ formatPrice(overview.totals.gross) }}</div>
        </div>
      </div>

      <div v-if="hasData">
        <AdminMiniChart :points="points" :format="(n) => formatPrice(n)" />
      </div>
      <UiEmptyState
        v-else
        icon="chart"
        :title="t('account.sales.empty_title')"
        :description="t('account.sales.empty_body')"
      />

      <div v-if="overview.top_books.length > 0">
        <h3 class="text-xs uppercase tracking-wide text-ink-tertiary mb-2">{{ t("account.sales.top_books") }}</h3>
        <ul class="space-y-1.5">
          <li v-for="(b, i) in overview.top_books" :key="b.id" class="flex items-center gap-2 text-sm">
            <span class="text-xs text-ink-tertiary w-4 tabular-nums">{{ i + 1 }}</span>
            <NuxtLink :to="localePath(`/books/${b.slug}`)" target="_blank" class="flex-1 truncate text-ink hover:text-primary">
              {{ localised(b.title, b.slug) }}
            </NuxtLink>
            <span class="text-xs text-ink-tertiary tabular-nums whitespace-nowrap">{{ b.units }} ×</span>
            <span class="text-sm text-primary tabular-nums whitespace-nowrap">{{ formatPrice(b.earning) }}</span>
          </li>
        </ul>
      </div>
    </template>
  </div>
</template>
