<script setup lang="ts">
import type { OrderList, OrderPublic } from "~/types/api";
import { formatPrice } from "~/composables/useLocaleText";

definePageMeta({ middleware: "auth" });

const { t, locale } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const { localised } = useLocaleText();
const api = useApi();

const PAGE_SIZE = 20;
const currentPage = computed(() => Math.max(1, Number(route.query.page) || 1));

const { data: ordersRaw, pending, refresh } = await useAsyncData(
  "account:orders",
  () =>
    api<OrderList>("/orders/me", {
      query: { page: currentPage.value, page_size: PAGE_SIZE },
    }),
  { watch: [currentPage] },
);

const orders = computed(() => ordersRaw.value as OrderList | null);

useHead({ title: t("orders.title") });

const breadcrumbs = computed(() => [
  { label: t("nav.home"), to: localePath("/") },
  { label: t("account.title"), to: localePath("/account") },
  { label: t("orders.title") },
]);

function formatDate(iso: string) {
  return new Intl.DateTimeFormat(locale.value, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
}

function statusTone(status: OrderPublic["status"]) {
  return (
    {
      pending: "warning",
      paid: "success",
      expired: "neutral",
      cancelled: "neutral",
      failed: "warning",
      refunded: "info",
    } as const
  )[status];
}

function changePage(page: number) {
  router.push({ query: { ...route.query, page } });
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}

const cancelling = ref<Set<string>>(new Set());

async function cancelOrder(order: OrderPublic) {
  if (!confirm(t("orders.cancel_confirm"))) return;
  if (cancelling.value.has(order.id)) return;
  cancelling.value.add(order.id);
  try {
    await api(`/orders/${order.id}/cancel`, { method: "POST" });
    await refresh();
  }
  catch {
    // Show via the global error toast (Phase 4.8 polish) — silent for now.
  }
  finally {
    cancelling.value.delete(order.id);
  }
}

const payingOrderId = ref<string | null>(null);

async function payOrder(order: OrderPublic) {
  if (payingOrderId.value) return;
  payingOrderId.value = order.id;
  try {
    const resp = await api<{ url: string }>(`/payments/payme/checkout/${order.id}`, {
      method: "POST",
    });
    window.location.href = resp.url;
  }
  catch {
    payingOrderId.value = null;
  }
}
</script>

<template>
  <section class="max-w-4xl mx-auto px-4 py-8 space-y-6">
    <UiBreadcrumbs :items="breadcrumbs" />

    <header class="space-y-1">
      <h1 class="font-serif text-3xl text-ink">{{ t("orders.title") }}</h1>
      <p class="text-sm text-ink-secondary">{{ t("orders.subtitle") }}</p>
    </header>

    <div v-if="pending && !orders" class="space-y-3">
      <UiSkeleton v-for="i in 3" :key="i" :height="'5rem'" :block="true" />
    </div>

    <UiEmptyState
      v-else-if="(orders?.items.length ?? 0) === 0"
      icon="📋"
      :title="t('orders.empty_title')"
      :description="t('orders.empty_body')"
    >
      <UiButton :to="localePath('/books')">{{ t("home.hero.cta_browse") }}</UiButton>
    </UiEmptyState>

    <ul v-else class="space-y-3">
      <li
        v-for="order in orders!.items"
        :key="order.id"
        class="rounded border border-border bg-bg-card p-4 space-y-3"
      >
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <div class="font-medium text-ink">{{ order.order_number }}</div>
            <div class="text-xs text-ink-tertiary">{{ formatDate(order.created_at) }}</div>
          </div>
          <UiBadge :tone="statusTone(order.status)" size="sm">
            {{ t(`orders.statuses.${order.status}`) }}
          </UiBadge>
        </div>

        <ul class="text-sm space-y-1">
          <li
            v-for="item in order.items"
            :key="item.id"
            class="flex justify-between gap-3"
          >
            <span class="truncate text-ink-secondary">
              {{ localised(item.book.title, item.book.slug) }}
            </span>
            <span class="text-ink-tertiary shrink-0">{{ formatPrice(item.price) }}</span>
          </li>
        </ul>

        <div class="flex items-center justify-between gap-3 pt-2 border-t border-border">
          <span class="text-sm font-medium text-ink">
            {{ t("orders.total") }}:
            <span class="text-primary">{{ formatPrice(order.total) }}</span>
          </span>
          <div class="flex gap-2">
            <UiButton
              v-if="order.status === 'pending'"
              size="sm"
              :loading="payingOrderId === order.id"
              :disabled="!!payingOrderId"
              @click="payOrder(order)"
            >
              {{ t("orders.pay") }}
            </UiButton>
            <UiButton
              v-if="order.status === 'pending'"
              size="sm"
              variant="ghost"
              :disabled="cancelling.has(order.id)"
              @click="cancelOrder(order)"
            >
              {{ t("orders.cancel") }}
            </UiButton>
          </div>
        </div>
      </li>
    </ul>

    <div class="pt-4">
      <UiPagination
        :page="currentPage"
        :page-size="PAGE_SIZE"
        :total="orders?.total ?? 0"
        @change="changePage"
      />
    </div>
  </section>
</template>
