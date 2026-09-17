<script setup lang="ts">
import type { OrderAdminDetail, OrderStatus } from "~/types/api";
import { formatPrice } from "~/composables/useLocaleText";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin", "admin-scope"],
  adminScope: "orders",
});

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const api = useApi();
const { formatDate } = useFormatDate();
const { localised } = useLocaleText();

const orderId = computed(() => route.params.id as string);

const { data: orderRaw } = await useAsyncData(
  `admin:order:${orderId.value}`,
  () => api<OrderAdminDetail>(`/admin/orders/${orderId.value}`),
  { server: false },
);
const order = computed(() => orderRaw.value as OrderAdminDetail | null);

useHead({
  title: computed(() => order.value
    ? `${t("admin.orders.detail_title")} — ${order.value.order_number}`
    : t("admin.orders.detail_title"),
  ),
});

const STATUS_TONE: Record<OrderStatus, "success" | "warning" | "neutral" | "error" | "info"> = {
  pending: "warning",
  paid: "success",
  expired: "neutral",
  cancelled: "neutral",
  failed: "error",
  refunded: "info",
};

const PAYMENT_STATUS_TONE: Record<string, "success" | "warning" | "neutral" | "error" | "info"> = {
  created: "neutral",
  pending: "warning",
  paid: "success",
  cancelled: "error",
  failed: "error",
};

function msToDate(ms: number | null): string {
  if (!ms) return "—";
  return formatDate(new Date(ms));
}
</script>

<template>
  <section v-if="order" class="space-y-5">
    <AdminPageHeader
      :title="t('admin.orders.detail_title')"
      :description="order.order_number"
      icon="cart"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('admin.orders.title'), to: localePath('/admin/orders') },
        { label: order.order_number },
      ]"
    >
      <template #actions>
        <AdminStatusPill :tone="STATUS_TONE[order.status]" :label="t(`orders.statuses.${order.status}`)" />
      </template>
    </AdminPageHeader>

    <!-- Meta strip -->
    <div class="rounded-md border border-border bg-bg-card p-4 grid sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs">
      <div>
        <dt class="text-ink-tertiary uppercase tracking-wide text-[10px]">{{ t("admin.orders.fields.buyer") }}</dt>
        <dd class="text-ink mt-0.5">
          <NuxtLink :to="localePath(`/admin/users/${order.user.id}/edit`)" class="hover:text-primary">
            {{ order.user.full_name }}
          </NuxtLink>
          <span class="block text-ink-tertiary text-[11px]">{{ order.user.email }}</span>
        </dd>
      </div>
      <div>
        <dt class="text-ink-tertiary uppercase tracking-wide text-[10px]">{{ t("admin.orders.fields.created_at") }}</dt>
        <dd class="text-ink mt-0.5">{{ formatDate(order.created_at) }}</dd>
      </div>
      <div>
        <dt class="text-ink-tertiary uppercase tracking-wide text-[10px]">{{ t("admin.orders.fields.paid_at") }}</dt>
        <dd class="text-ink mt-0.5">{{ order.paid_at ? formatDate(order.paid_at) : "—" }}</dd>
      </div>
      <div>
        <dt class="text-ink-tertiary uppercase tracking-wide text-[10px]">{{ t("admin.orders.fields.payment_method") }}</dt>
        <dd class="text-ink mt-0.5 uppercase">{{ order.payment_method || "—" }}</dd>
      </div>
    </div>

    <!-- Totals -->
    <div class="rounded-md border border-border bg-bg-card p-4 grid sm:grid-cols-3 gap-3 text-sm">
      <div>
        <dt class="text-ink-tertiary text-xs uppercase tracking-wide">{{ t("admin.orders.fields.subtotal") }}</dt>
        <dd class="text-ink mt-0.5 tabular-nums">{{ formatPrice(order.subtotal) }}</dd>
      </div>
      <div>
        <dt class="text-ink-tertiary text-xs uppercase tracking-wide">{{ t("admin.orders.fields.discount") }}</dt>
        <dd class="text-ink mt-0.5 tabular-nums">{{ formatPrice(order.discount) }}</dd>
      </div>
      <div>
        <dt class="text-ink-tertiary text-xs uppercase tracking-wide">{{ t("admin.orders.fields.total") }}</dt>
        <dd class="text-primary font-serif text-lg mt-0.5 tabular-nums">{{ formatPrice(order.total) }}</dd>
      </div>
    </div>

    <!-- Items -->
    <div class="rounded-md border border-border bg-bg-card overflow-hidden">
      <h2 class="text-sm uppercase tracking-wider text-ink-tertiary px-4 pt-4 pb-2">
        {{ t("admin.orders.section_items") }}
      </h2>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-bg-secondary text-xs uppercase tracking-wider text-ink-tertiary">
            <tr>
              <th class="px-4 py-2.5 text-left font-medium">{{ t("admin.orders.items_table.book") }}</th>
              <th class="px-4 py-2.5 text-left font-medium">{{ t("admin.orders.items_table.author") }}</th>
              <th class="px-4 py-2.5 text-right font-medium">{{ t("admin.orders.items_table.price") }}</th>
              <th class="px-4 py-2.5 text-right font-medium">{{ t("admin.orders.items_table.commission") }}</th>
              <th class="px-4 py-2.5 text-right font-medium">{{ t("admin.orders.items_table.author_earning") }}</th>
              <th class="px-4 py-2.5 text-right font-medium">{{ t("admin.orders.items_table.platform_fee") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in order.items" :key="item.id" class="border-t border-border">
              <td class="px-4 py-2.5">
                <NuxtLink :to="localePath(`/admin/books/${item.book.id}/edit`)" class="text-ink hover:text-primary">
                  {{ localised(item.book.title, item.book.slug) }}
                </NuxtLink>
              </td>
              <td class="px-4 py-2.5 text-ink-secondary">{{ item.book.author.display_name }}</td>
              <td class="px-4 py-2.5 text-right tabular-nums">{{ formatPrice(item.price) }}</td>
              <td class="px-4 py-2.5 text-right tabular-nums text-ink-tertiary">{{ item.commission_rate }}%</td>
              <td class="px-4 py-2.5 text-right tabular-nums text-success">{{ formatPrice(item.author_earning) }}</td>
              <td class="px-4 py-2.5 text-right tabular-nums text-ink-tertiary">{{ formatPrice(item.platform_fee) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Payment attempts -->
    <div class="rounded-md border border-border bg-bg-card overflow-hidden">
      <h2 class="text-sm uppercase tracking-wider text-ink-tertiary px-4 pt-4 pb-2">
        {{ t("admin.orders.section_payments") }}
      </h2>
      <UiEmptyState
        v-if="order.payments.length === 0"
        icon="lock"
        :title="t('admin.orders.no_payments_title')"
        :description="t('admin.orders.no_payments_body')"
      />
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-bg-secondary text-xs uppercase tracking-wider text-ink-tertiary">
            <tr>
              <th class="px-4 py-2.5 text-left font-medium">{{ t("admin.orders.payments_table.provider") }}</th>
              <th class="px-4 py-2.5 text-left font-medium">{{ t("admin.orders.payments_table.provider_id") }}</th>
              <th class="px-4 py-2.5 text-right font-medium">{{ t("admin.orders.payments_table.amount") }}</th>
              <th class="px-4 py-2.5 text-center font-medium">{{ t("admin.orders.payments_table.status") }}</th>
              <th class="px-4 py-2.5 text-left font-medium">{{ t("admin.orders.payments_table.created") }}</th>
              <th class="px-4 py-2.5 text-left font-medium">{{ t("admin.orders.payments_table.performed") }}</th>
              <th class="px-4 py-2.5 text-left font-medium">{{ t("admin.orders.payments_table.cancelled") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in order.payments" :key="p.id" class="border-t border-border">
              <td class="px-4 py-2.5 uppercase text-ink-secondary">{{ p.provider }}</td>
              <td class="px-4 py-2.5 font-mono text-xs text-ink-tertiary">{{ p.provider_id || "—" }}</td>
              <td class="px-4 py-2.5 text-right tabular-nums">{{ formatPrice(p.amount) }}</td>
              <td class="px-4 py-2.5 text-center">
                <AdminStatusPill
                  :tone="PAYMENT_STATUS_TONE[p.status] ?? 'neutral'"
                  :label="t(`admin.orders.payment_statuses.${p.status}`)"
                />
              </td>
              <td class="px-4 py-2.5 text-xs text-ink-tertiary">{{ msToDate(p.create_time) }}</td>
              <td class="px-4 py-2.5 text-xs text-ink-tertiary">{{ msToDate(p.perform_time) }}</td>
              <td class="px-4 py-2.5 text-xs text-ink-tertiary">{{ msToDate(p.cancel_time) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
  <section v-else class="space-y-3">
    <UiSkeleton height="3rem" block />
    <UiSkeleton height="12rem" block />
    <UiSkeleton height="12rem" block />
  </section>
</template>
