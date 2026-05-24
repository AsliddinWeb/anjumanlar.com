<script setup lang="ts">
import type { OrderList, OrderPublic } from "~/types/api";
import type { IconName } from "~/components/ui/Icon.vue";
import { formatPrice } from "~/composables/useLocaleText";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({ middleware: "auth" });

const { t, locale } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const { localised } = useLocaleText();
const api = useApi();
const toast = useToast();

useSiteSeo({ title: t("orders.title"), noindex: true });

const PAGE_SIZE = 10;
const currentPage = computed(() => Math.max(1, Number(route.query.page) || 1));
const statusFilter = computed(() => (route.query.status as string) || "");

const { data: ordersRaw, pending, refresh, error: ordersError } = await useAsyncData(
  "account:orders",
  () =>
    api<OrderList>("/orders/me", {
      query: { page: currentPage.value, page_size: PAGE_SIZE },
    }),
  { server: false, watch: [currentPage] },
);

const orders = computed(() => ordersRaw.value as OrderList | null);

const filtered = computed<OrderPublic[]>(() => {
  const items = orders.value?.items ?? [];
  if (!statusFilter.value) return items;
  return items.filter((o) => o.status === statusFilter.value);
});

const total = computed(() => orders.value?.total ?? 0);

function setQuery(updates: Record<string, string | number | undefined>) {
  const next: Record<string, string> = {};
  for (const [k, v] of Object.entries(route.query)) {
    if (typeof v === "string") next[k] = v;
  }
  for (const [k, v] of Object.entries(updates)) {
    if (v === undefined || v === null || v === "") delete next[k];
    else next[k] = String(v);
  }
  if (!("page" in updates)) delete next.page;
  router.push({ query: next });
}

function formatDate(iso: string) {
  return new Intl.DateTimeFormat(locale.value, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
}

const STATUS_META: Record<OrderPublic["status"], { tone: "success" | "warning" | "info" | "neutral" | "error"; icon: IconName }> = {
  pending: { tone: "warning", icon: "arrow-path" },
  paid: { tone: "success", icon: "check-circle-solid" },
  expired: { tone: "neutral", icon: "warning" },
  cancelled: { tone: "neutral", icon: "close" },
  failed: { tone: "error", icon: "warning-solid" },
  refunded: { tone: "info", icon: "arrow-left" },
};

function changePage(page: number) {
  setQuery({ page });
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}

const cancelTarget = ref<OrderPublic | null>(null);
const cancelling = ref(false);

async function confirmCancel() {
  if (!cancelTarget.value || cancelling.value) return;
  const order = cancelTarget.value;
  cancelling.value = true;
  try {
    await api(`/orders/${order.id}/cancel`, { method: "POST" });
    toast.success(t("orders.cancel_success", { number: order.order_number }));
    cancelTarget.value = null;
    await refresh();
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("orders.cancel_failed")));
  }
  finally {
    cancelling.value = false;
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
  catch (err) {
    payingOrderId.value = null;
    toast.error(apiErrorMessage(err, t("orders.pay_failed")));
  }
}

const statusOptions = computed(() => [
  { value: "", label: t("orders.filter_all") },
  { value: "pending", label: t("orders.statuses.pending") },
  { value: "paid", label: t("orders.statuses.paid") },
  { value: "cancelled", label: t("orders.statuses.cancelled") },
  { value: "failed", label: t("orders.statuses.failed") },
  { value: "refunded", label: t("orders.statuses.refunded") },
]);
</script>

<template>
  <AccountShell>
    <header class="space-y-2 mb-6">
      <div class="flex items-center gap-3">
        <span class="h-10 w-10 rounded-md bg-info/10 text-info inline-flex items-center justify-center shrink-0">
          <Icon name="clipboard-check" class="h-5 w-5" />
        </span>
        <div>
          <h1 class="font-serif text-2xl md:text-3xl text-ink leading-tight">
            {{ t("orders.title") }}
          </h1>
          <p class="text-sm text-ink-secondary">{{ t("orders.subtitle") }}</p>
        </div>
      </div>
    </header>

    <!-- Filter -->
    <div v-if="total > 0" class="flex flex-wrap items-center gap-2 mb-4">
      <div class="relative">
        <Icon
          name="settings"
          class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-tertiary pointer-events-none"
        />
        <select
          :value="statusFilter"
          class="appearance-none pl-9 pr-9 py-2 rounded-md border border-border bg-bg-card text-sm text-ink focus:outline-none focus:border-primary cursor-pointer"
          @change="setQuery({ status: ($event.target as HTMLSelectElement).value })"
        >
          <option v-for="s in statusOptions" :key="s.value" :value="s.value">
            {{ s.label }}
          </option>
        </select>
        <Icon
          name="chevron-down"
          class="absolute right-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-tertiary pointer-events-none"
        />
      </div>
      <div class="flex-1" />
      <span class="text-sm text-ink-secondary tabular-nums">
        {{ t("orders.results", { n: total }) }}
      </span>
    </div>

    <!-- Loading -->
    <div v-if="pending && !orders" class="space-y-3">
      <UiSkeleton v-for="i in 3" :key="i" height="7rem" block rounded="rounded-md" />
    </div>

    <!-- Error -->
    <div
      v-else-if="ordersError"
      class="rounded-md border border-error/30 bg-error/5 p-6 flex items-start gap-4"
    >
      <Icon name="warning-solid" class="h-6 w-6 text-error shrink-0" />
      <div>
        <h3 class="font-serif text-lg text-ink mb-1">{{ t("orders.error_title") }}</h3>
        <p class="text-sm text-ink-secondary">{{ t("orders.error_body") }}</p>
      </div>
    </div>

    <!-- Empty -->
    <UiEmptyState
      v-else-if="total === 0"
      icon="clipboard-check"
      :title="t('orders.empty_title')"
      :description="t('orders.empty_body')"
    >
      <UiButton :to="localePath('/books')">
        <Icon name="book" class="h-4 w-4" />
        {{ t("orders.empty_cta") }}
      </UiButton>
    </UiEmptyState>

    <UiEmptyState
      v-else-if="filtered.length === 0"
      icon="search"
      :title="t('orders.no_filter_match_title')"
      :description="t('orders.no_filter_match_body')"
    >
      <UiButton variant="ghost" @click="setQuery({ status: undefined })">
        <Icon name="close" class="h-4 w-4" />
        {{ t("orders.clear_filter") }}
      </UiButton>
    </UiEmptyState>

    <!-- Orders list -->
    <ul v-else class="space-y-3">
      <li
        v-for="order in filtered"
        :key="order.id"
        class="rounded-md border border-border bg-bg-card overflow-hidden"
      >
        <div class="p-4 space-y-3">
          <div class="flex items-start justify-between gap-3 flex-wrap">
            <div class="min-w-0">
              <div class="font-mono text-sm text-ink">{{ order.order_number }}</div>
              <div class="inline-flex items-center gap-1.5 text-xs text-ink-tertiary mt-1">
                <Icon name="sparkles" class="h-3.5 w-3.5" />
                {{ formatDate(order.created_at) }}
              </div>
            </div>
            <span
              class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-xs font-medium"
              :class="{
                'bg-success/10 text-success border-success/20': STATUS_META[order.status].tone === 'success',
                'bg-warning/10 text-warning border-warning/20': STATUS_META[order.status].tone === 'warning',
                'bg-error/10 text-error border-error/20': STATUS_META[order.status].tone === 'error',
                'bg-info/10 text-info border-info/20': STATUS_META[order.status].tone === 'info',
                'bg-bg-secondary text-ink-secondary border-border': STATUS_META[order.status].tone === 'neutral',
              }"
            >
              <Icon :name="STATUS_META[order.status].icon" class="h-3 w-3" />
              {{ t(`orders.statuses.${order.status}`) }}
            </span>
          </div>

          <ul class="space-y-1.5 pl-1">
            <li
              v-for="item in order.items"
              :key="item.id"
              class="flex items-center justify-between gap-3 text-sm"
            >
              <NuxtLink
                :to="localePath(`/books/${item.book.slug}`)"
                class="inline-flex items-center gap-2 text-ink-secondary hover:text-primary truncate min-w-0"
              >
                <Icon name="book" class="h-3.5 w-3.5 shrink-0 text-ink-tertiary" />
                <span class="truncate">{{ localised(item.book.title, item.book.slug) }}</span>
              </NuxtLink>
              <span class="text-ink-tertiary shrink-0 tabular-nums">{{ formatPrice(item.price) }}</span>
            </li>
          </ul>
        </div>

        <footer class="flex items-center justify-between gap-3 px-4 py-3 bg-bg-secondary/50 border-t border-border">
          <span class="text-sm">
            <span class="text-ink-secondary">{{ t("orders.total") }}:</span>
            <span class="font-serif text-lg text-primary tabular-nums ml-1">{{ formatPrice(order.total) }}</span>
          </span>
          <div class="flex gap-2">
            <UiButton
              v-if="order.status === 'pending'"
              size="sm"
              variant="ghost"
              :disabled="cancelling"
              @click="cancelTarget = order"
            >
              <Icon name="close" class="h-4 w-4" />
              {{ t("orders.cancel") }}
            </UiButton>
            <UiButton
              v-if="order.status === 'pending'"
              size="sm"
              :loading="payingOrderId === order.id"
              :disabled="!!payingOrderId"
              @click="payOrder(order)"
            >
              <Icon name="lock" class="h-4 w-4" />
              {{ t("orders.pay") }}
            </UiButton>
            <UiButton
              v-else-if="order.status === 'paid'"
              size="sm"
              variant="ghost"
              :to="localePath('/account/library')"
            >
              <Icon name="library" class="h-4 w-4" />
              {{ t("orders.view_in_library") }}
            </UiButton>
          </div>
        </footer>
      </li>
    </ul>

    <div v-if="total > PAGE_SIZE" class="mt-8">
      <UiPagination
        :page="currentPage"
        :page-size="PAGE_SIZE"
        :total="total"
        @change="changePage"
      />
    </div>

    <AdminConfirmDialog
      :open="!!cancelTarget"
      tone="danger"
      icon="close"
      :title="t('orders.cancel_modal_title')"
      :description="cancelTarget ? t('orders.cancel_modal_body', { number: cancelTarget.order_number }) : ''"
      :confirm-label="t('orders.cancel_modal_confirm')"
      :cancel-label="t('orders.cancel_modal_keep')"
      :loading="cancelling"
      @update:open="(v) => !v && (cancelTarget = null)"
      @confirm="confirmCancel"
    />
  </AccountShell>
</template>
