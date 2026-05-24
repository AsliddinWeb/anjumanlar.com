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

const { t, locale } = useI18n();
const localePath = useLocalePath();
const { user } = useAuth();
const api = useApi();

useHead({ title: t("admin.title") });

const { data: statsRaw, pending } = await useAsyncData(
  "admin:stats",
  () => api<StatsSnapshot>("/admin/stats"),
);

const stats = computed(() => statsRaw.value as StatsSnapshot | null);

const actionItems = computed(() => {
  const s = stats.value;
  if (!s) return [];
  const items: { to: string; icon: IconName; title: string; count: number; description: string }[] = [];
  if (s.books.pending > 0)
    items.push({
      to: "/admin/books",
      icon: "book",
      title: t("admin.kpi.books_pending"),
      count: s.books.pending,
      description: t("admin.kpi.books_pending_desc"),
    });
  if (s.reviews.pending > 0)
    items.push({
      to: "/admin/reviews",
      icon: "chat",
      title: t("admin.kpi.reviews_pending"),
      count: s.reviews.pending,
      description: t("admin.kpi.reviews_pending_desc"),
    });
  if (s.withdrawals.open > 0)
    items.push({
      to: "/admin/withdrawals",
      icon: "money",
      title: t("admin.kpi.withdrawals_open"),
      count: s.withdrawals.open,
      description: t("admin.kpi.withdrawals_open_desc"),
    });
  return items;
});

const greeting = computed(() => {
  const h = new Date().getHours();
  if (h < 12) return t("admin.greeting_morning");
  if (h < 18) return t("admin.greeting_afternoon");
  return t("admin.greeting_evening");
});

const generatedAt = computed(() => {
  if (!stats.value) return "";
  return new Intl.DateTimeFormat(locale.value, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(stats.value.generated_at));
});
</script>

<template>
  <section class="space-y-8">
    <header class="space-y-2">
      <p class="text-sm text-ink-tertiary">{{ greeting }}</p>
      <h1 class="font-serif text-3xl md:text-4xl text-ink leading-tight">
        <ClientOnly>
          <template #fallback>{{ t("admin.welcome_short") }}</template>
          {{ t("admin.welcome", { name: user?.full_name ?? "" }) }}
        </ClientOnly>
      </h1>
      <p class="text-sm text-ink-secondary">
        {{ t("admin.welcome_subtitle") }}
      </p>
    </header>

    <div v-if="pending && !stats" class="grid grid-cols-2 md:grid-cols-4 gap-3">
      <UiSkeleton v-for="i in 8" :key="i" height="6rem" block />
    </div>

    <template v-else-if="stats">
      <section v-if="actionItems.length > 0" class="space-y-3">
        <div class="flex items-center justify-between">
          <h2 class="text-sm uppercase tracking-wider text-ink-tertiary">
            {{ t("admin.kpi.needs_attention") }}
          </h2>
          <AdminStatusPill
            tone="warning"
            icon="warning"
            :label="t('admin.kpi.action_items_count', { n: actionItems.length })"
            pulse
          />
        </div>
        <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <NuxtLink
            v-for="item in actionItems"
            :key="item.to"
            :to="localePath(item.to)"
            class="group rounded-md border border-warning/40 bg-warning/5 p-4 hover:border-warning hover:bg-warning/10 transition-colors"
          >
            <div class="flex items-start gap-3">
              <div class="h-10 w-10 rounded bg-warning/15 text-warning flex items-center justify-center shrink-0">
                <Icon :name="item.icon" class="h-5 w-5" />
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-baseline gap-2">
                  <div class="font-serif text-2xl text-warning">{{ item.count }}</div>
                  <div class="text-sm font-medium text-ink truncate">{{ item.title }}</div>
                </div>
                <div class="text-xs text-ink-tertiary mt-0.5">{{ item.description }}</div>
              </div>
              <Icon name="arrow-right" class="h-4 w-4 text-ink-tertiary mt-1 group-hover:translate-x-0.5 group-hover:text-warning transition-all" />
            </div>
          </NuxtLink>
        </div>
      </section>

      <section v-else class="rounded-md border border-success/30 bg-success/5 p-4 flex items-center gap-3">
        <Icon name="check-circle-solid" class="h-6 w-6 text-success shrink-0" />
        <div>
          <p class="font-medium text-ink">{{ t("admin.kpi.all_clear") }}</p>
          <p class="text-xs text-ink-tertiary">{{ t("admin.kpi.all_clear_desc") }}</p>
        </div>
      </section>

      <section class="space-y-3">
        <div class="flex items-center justify-between">
          <h2 class="text-sm uppercase tracking-wider text-ink-tertiary">
            {{ t("admin.kpi.overview") }}
          </h2>
          <span class="text-xs text-ink-tertiary inline-flex items-center gap-1">
            <Icon name="arrow-path" class="h-3 w-3" />
            {{ generatedAt }}
          </span>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <AdminKpiCard
            :label="t('admin.kpi.users_total')"
            :value="stats.users.total"
            :hint="t('admin.kpi.users_last_7d', { n: stats.users.last_7d })"
            icon="users"
            tone="info"
            :to="localePath('/admin/users')"
          />
          <AdminKpiCard
            :label="t('admin.kpi.authors')"
            :value="stats.users.authors"
            icon="pencil"
            :to="localePath('/admin/users') + '?role=author'"
          />
          <AdminKpiCard
            :label="t('admin.kpi.books_approved')"
            :value="stats.books.approved"
            icon="book"
            tone="success"
          />
          <AdminKpiCard
            :label="t('admin.kpi.orders_paid')"
            :value="stats.orders.paid_total"
            :hint="t('admin.kpi.orders_this_month', { n: stats.orders.paid_this_month })"
            icon="clipboard-check"
          />
        </div>
      </section>

      <section class="space-y-3">
        <h2 class="text-sm uppercase tracking-wider text-ink-tertiary">
          {{ t("admin.kpi.financials") }}
        </h2>
        <div class="grid md:grid-cols-2 gap-3">
          <AdminKpiCard
            :label="t('admin.kpi.revenue_gross')"
            :value="formatPrice(stats.revenue.gross)"
            :hint="t('admin.kpi.revenue_platform') + ': ' + formatPrice(stats.revenue.platform_fee)"
            icon="currency"
            tone="success"
          />
          <AdminKpiCard
            :label="t('admin.kpi.withdrawals_amount')"
            :value="formatPrice(stats.withdrawals.open_amount)"
            :hint="t('admin.kpi.withdrawals_open_count', { n: stats.withdrawals.open })"
            icon="money"
            tone="warning"
            :to="localePath('/admin/withdrawals')"
          />
        </div>
      </section>
    </template>
  </section>
</template>
