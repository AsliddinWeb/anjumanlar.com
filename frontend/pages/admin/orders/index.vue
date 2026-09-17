<script setup lang="ts">
import type { OrderAdminList, OrderAdminPublic, OrderStatus } from "~/types/api";
import type { Column } from "~/components/admin/AdminDataTable.vue";
import { formatPrice } from "~/composables/useLocaleText";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin", "admin-scope"],
  adminScope: "orders",
});

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const api = useApi();
const { formatDate } = useFormatDate();

useHead({ title: t("admin.orders.title") });

const PAGE_SIZE = 20;

const sort = computed(() => (route.query.sort as string) || "-created_at");

const queryParams = computed(() => ({
  page: Math.max(1, Number(route.query.page) || 1),
  page_size: PAGE_SIZE,
  search: ((route.query.q as string) || "").trim() || undefined,
  status: ((route.query.status as string) || undefined) as OrderStatus | undefined,
  sort: sort.value,
}));

const { data: ordersRaw, pending } = await useAsyncData(
  "admin:orders",
  () => api<OrderAdminList>("/admin/orders", { query: queryParams.value }),
  { server: false, watch: [queryParams] },
);

const orders = computed(() => ordersRaw.value as OrderAdminList | null);

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

function changePage(page: number) {
  setQuery({ page });
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}

function resetFilters() {
  router.replace({ query: {} });
}

const filtersDirty = computed(() => Boolean(route.query.q || route.query.status));

const STATUS_TONE: Record<OrderStatus, "success" | "warning" | "neutral" | "error" | "info"> = {
  pending: "warning",
  paid: "success",
  expired: "neutral",
  cancelled: "neutral",
  failed: "error",
  refunded: "info",
};

const columns: Column<OrderAdminPublic>[] = [
  { key: "order", label: t("admin.orders.table.order"), sortKey: "created_at" },
  { key: "buyer", label: t("admin.orders.table.buyer") },
  { key: "items", label: t("admin.orders.table.items"), align: "center", width: "w-20" },
  { key: "status", label: t("admin.orders.table.status"), align: "center", width: "w-32" },
  { key: "total", label: t("admin.orders.table.total"), align: "right", width: "w-32", sortKey: "total" },
  { key: "payment_method", label: t("admin.orders.table.payment_method"), width: "w-32", mobileHidden: true },
];
</script>

<template>
  <section>
    <AdminPageHeader
      :title="t('admin.orders.title')"
      :description="t('admin.orders.subtitle')"
      icon="cart"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('admin.orders.title') },
      ]"
    >
      <template #actions>
        <AdminStatusPill
          v-if="orders"
          tone="info"
          icon="cart"
          :label="t('admin.orders.results', { n: orders.total })"
        />
      </template>
    </AdminPageHeader>

    <AdminFilterBar
      :search="(route.query.q as string) || ''"
      :search-placeholder="t('admin.orders.search_placeholder')"
      :dirty="filtersDirty"
      @update:search="(v) => setQuery({ q: v })"
      @reset="resetFilters"
    >
      <UiSelect
        :model-value="(route.query.status as string) || ''"
        size="sm"
        :options="[
          { value: '', label: t('admin.orders.filter_status_any') },
          { value: 'pending', label: t('orders.statuses.pending') },
          { value: 'paid', label: t('orders.statuses.paid') },
          { value: 'expired', label: t('orders.statuses.expired') },
          { value: 'cancelled', label: t('orders.statuses.cancelled') },
          { value: 'failed', label: t('orders.statuses.failed') },
          { value: 'refunded', label: t('orders.statuses.refunded') },
        ]"
        @update:model-value="(v) => setQuery({ status: v })"
      />
    </AdminFilterBar>

    <AdminDataTable
      :columns="columns"
      :rows="orders?.items ?? []"
      :row-key="(r) => r.id"
      :loading="pending"
      :empty="{
        icon: 'cart',
        title: filtersDirty ? t('admin.filters.no_results') : t('admin.orders.empty_title'),
        description: filtersDirty ? t('admin.filters.no_results_desc') : t('admin.orders.empty_body'),
      }"
      :sort="sort"
      @update:sort="(v) => setQuery({ sort: v })"
    >
      <template #cell-order="{ row }">
        <NuxtLink
          :to="localePath(`/admin/orders/${row.id}`)"
          class="font-mono text-sm text-ink hover:text-primary block"
        >
          {{ row.order_number }}
        </NuxtLink>
        <div class="text-xs text-ink-tertiary">{{ formatDate(row.created_at) }}</div>
      </template>
      <template #cell-buyer="{ row }">
        <div class="min-w-0">
          <div class="text-ink truncate">{{ row.user.full_name }}</div>
          <div class="text-xs text-ink-tertiary truncate">{{ row.user.email }}</div>
        </div>
      </template>
      <template #cell-items="{ row }">
        <span class="text-xs text-ink-tertiary tabular-nums">{{ row.items.length }}</span>
      </template>
      <template #cell-status="{ row }">
        <AdminStatusPill :tone="STATUS_TONE[row.status]" :label="t(`orders.statuses.${row.status}`)" />
      </template>
      <template #cell-total="{ row }">
        <span class="font-serif text-primary tabular-nums">{{ formatPrice(row.total) }}</span>
      </template>
      <template #cell-payment_method="{ row }">
        <span class="text-xs text-ink-tertiary uppercase">{{ row.payment_method || "—" }}</span>
      </template>
      <template #actions="{ row }">
        <UiButton variant="ghost" size="sm" :to="localePath(`/admin/orders/${row.id}`)">
          <Icon name="eye" class="h-3.5 w-3.5" />
          {{ t("admin.orders.view") }}
        </UiButton>
      </template>
    </AdminDataTable>

    <div v-if="orders && orders.total > PAGE_SIZE" class="pt-4">
      <UiPagination
        :page="queryParams.page"
        :page-size="PAGE_SIZE"
        :total="orders.total"
        @change="changePage"
      />
    </div>
  </section>
</template>
