<script setup lang="ts">
import type { OrderPublic } from "~/types/api";

definePageMeta({ middleware: "auth" });

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const api = useApi();

const orderId = computed(() => (route.query.order as string) || "");

const { data: orderRaw } = await useAsyncData(
  "checkout:order",
  () => {
    if (!orderId.value) return Promise.resolve(null as OrderPublic | null);
    return api<OrderPublic>(`/orders/${orderId.value}`).catch(() => null);
  },
  { watch: [orderId] },
);

const order = computed(() => orderRaw.value as OrderPublic | null);

const isPaid = computed(() => order.value?.status === "paid");

useHead({ title: t(isPaid.value ? "checkout.success_title" : "checkout.success_pending_title") });
</script>

<template>
  <section class="max-w-md mx-auto px-4 py-16 text-center space-y-4">
    <div class="text-5xl" aria-hidden="true">
      {{ isPaid ? "✅" : "⏳" }}
    </div>
    <h1 class="font-serif text-2xl text-ink">
      {{ isPaid ? t("checkout.success_title") : t("checkout.success_pending_title") }}
    </h1>
    <p class="text-ink-secondary">
      {{ isPaid ? t("checkout.success_body") : t("checkout.success_pending_body") }}
    </p>
    <p v-if="order" class="text-xs text-ink-tertiary">
      {{ order.order_number }}
    </p>
    <div class="flex flex-wrap justify-center gap-3 pt-2">
      <UiButton :to="localePath('/account/library')">
        {{ t("checkout.go_library") }}
      </UiButton>
      <UiButton variant="ghost" :to="localePath('/account/orders')">
        {{ t("checkout.go_orders") }}
      </UiButton>
    </div>
  </section>
</template>
