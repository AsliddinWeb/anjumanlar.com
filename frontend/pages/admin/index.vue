<script setup lang="ts">
import { formatPrice } from "~/composables/useLocaleText";
import type { IconName } from "~/components/ui/Icon.vue";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin"],
});

interface StatsSnapshot {
  users: { total: number; last_7d: number; authors: number; admins: number };
  books: { approved: number; pending: number };
  reviews: { pending: number };
  orders: { paid_total: number; paid_this_month: number };
  revenue: { gross: number; platform_fee: number; currency: string };
  withdrawals: { open: number; open_amount: number };
  generated_at: string;
}

const { t } = useI18n();
const localePath = useLocalePath();
const { user } = useAuth();
const api = useApi();

useHead({ title: t("admin.title") });

const { data: statsRaw } = await useAsyncData(
  "admin:stats",
  () => api<StatsSnapshot>("/admin/stats"),
);

const stats = computed(() => statsRaw.value as StatsSnapshot | null);

// Action items — surface anything that needs admin attention.
const actionItems = computed(() => {
  const s = stats.value;
  if (!s) return [];
  const items: { to: string; icon: IconName; title: string; count: number }[] = [];
  if (s.books.pending > 0)
    items.push({
      to: "/admin/books",
      icon: "book",
      title: t("admin.kpi.books_pending"),
      count: s.books.pending,
    });
  if (s.reviews.pending > 0)
    items.push({
      to: "/admin/reviews",
      icon: "chat",
      title: t("admin.kpi.reviews_pending"),
      count: s.reviews.pending,
    });
  if (s.withdrawals.open > 0)
    items.push({
      to: "/admin/withdrawals",
      icon: "money",
      title: t("admin.kpi.withdrawals_open"),
      count: s.withdrawals.open,
    });
  return items;
});
</script>

<template>
  <section class="space-y-8">
    <header class="space-y-1">
      <h1 class="font-serif text-3xl text-ink">
        {{ t("admin.welcome", { name: user?.full_name ?? "" }) }}
      </h1>
      <p class="text-sm text-ink-secondary">{{ t("admin.welcome_subtitle") }}</p>
    </header>

    <!-- Action items -->
    <section v-if="stats" class="space-y-3">
      <h2 class="font-medium text-ink">{{ t("admin.kpi.needs_attention") }}</h2>
      <div v-if="actionItems.length > 0" class="grid sm:grid-cols-3 gap-3">
        <NuxtLink
          v-for="item in actionItems"
          :key="item.to"
          :to="localePath(item.to)"
          class="rounded border border-warning/40 bg-warning/5 p-4 hover:border-warning hover:bg-warning/10 transition-colors"
        >
          <div class="flex items-center gap-3">
            <Icon :name="item.icon" class="h-7 w-7 text-warning" />
            <div>
              <div class="text-xs text-ink-tertiary">{{ item.title }}</div>
              <div class="font-serif text-2xl text-warning">{{ item.count }}</div>
            </div>
          </div>
        </NuxtLink>
      </div>
      <p v-else class="flex items-center gap-1 text-sm text-success">
        <Icon name="check-circle-solid" class="h-4 w-4" />
        {{ t("admin.kpi.all_clear") }}
      </p>
    </section>

    <!-- KPI grid -->
    <section v-if="stats" class="space-y-3">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div class="rounded border border-border bg-bg-card p-4">
          <div class="text-xs text-ink-tertiary">{{ t("admin.kpi.users_total") }}</div>
          <div class="font-serif text-2xl text-ink mt-1">{{ stats.users.total }}</div>
          <div class="text-xs text-ink-tertiary mt-1">
            {{ t("admin.kpi.users_last_7d", { n: stats.users.last_7d }) }}
          </div>
        </div>
        <div class="rounded border border-border bg-bg-card p-4">
          <div class="text-xs text-ink-tertiary">{{ t("admin.kpi.authors") }}</div>
          <div class="font-serif text-2xl text-ink mt-1">{{ stats.users.authors }}</div>
        </div>
        <div class="rounded border border-border bg-bg-card p-4">
          <div class="text-xs text-ink-tertiary">{{ t("admin.kpi.books_approved") }}</div>
          <div class="font-serif text-2xl text-ink mt-1">{{ stats.books.approved }}</div>
        </div>
        <div class="rounded border border-border bg-bg-card p-4">
          <div class="text-xs text-ink-tertiary">{{ t("admin.kpi.orders_paid") }}</div>
          <div class="font-serif text-2xl text-ink mt-1">{{ stats.orders.paid_total }}</div>
          <div class="text-xs text-ink-tertiary mt-1">
            {{ t("admin.kpi.orders_this_month", { n: stats.orders.paid_this_month }) }}
          </div>
        </div>
        <div class="rounded border border-border bg-bg-card p-4 col-span-2">
          <div class="text-xs text-ink-tertiary">{{ t("admin.kpi.revenue_gross") }}</div>
          <div class="font-serif text-2xl text-success mt-1">
            {{ formatPrice(stats.revenue.gross) }}
          </div>
          <div class="text-xs text-ink-tertiary mt-1">
            {{ t("admin.kpi.revenue_platform") }}: {{ formatPrice(stats.revenue.platform_fee) }}
          </div>
        </div>
        <div class="rounded border border-border bg-bg-card p-4 col-span-2">
          <div class="text-xs text-ink-tertiary">{{ t("admin.kpi.withdrawals_amount") }}</div>
          <div class="font-serif text-2xl text-warning mt-1">
            {{ formatPrice(stats.withdrawals.open_amount) }}
          </div>
          <div class="text-xs text-ink-tertiary mt-1">
            {{ stats.withdrawals.open }} {{ t("admin.kpi.withdrawals_open").toLowerCase() }}
          </div>
        </div>
      </div>
    </section>
  </section>
</template>
