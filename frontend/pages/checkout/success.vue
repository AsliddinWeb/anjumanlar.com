<script setup lang="ts">
import type { OrderPublic } from "~/types/api";
import { formatPrice } from "~/composables/useLocaleText";

definePageMeta({ middleware: "auth" });

const { t } = useI18n();
const localePath = useLocalePath();
const { localised } = useLocaleText();
const { formatDate } = useFormatDate();
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
const isPending = computed(() => order.value?.status === "pending");

useSiteSeo({
  title: t(isPaid.value ? "checkout.success_title" : "checkout.success_pending_title"),
  noindex: true,
});

</script>

<template>
  <section class="bg-bg">
    <div class="max-w-2xl mx-auto px-4 py-12 md:py-16">
      <!-- Hero -->
      <div class="text-center space-y-5 mb-8">
        <div
          class="inline-flex h-20 w-20 items-center justify-center rounded-full relative"
          :class="isPaid ? 'bg-success/10' : 'bg-warning/10'"
        >
          <span
            v-if="isPaid"
            aria-hidden="true"
            class="absolute inset-0 rounded-full bg-success/15 animate-ping"
          />
          <Icon
            :name="isPaid ? 'check-circle-solid' : 'arrow-path'"
            class="relative h-10 w-10"
            :class="isPaid ? 'text-success' : 'text-warning'"
          />
        </div>

        <div class="space-y-2">
          <h1 class="font-serif text-3xl md:text-4xl text-ink leading-tight tracking-tight">
            {{ isPaid ? t("checkout.success_title") : t("checkout.success_pending_title") }}
          </h1>
          <p class="text-ink-secondary leading-relaxed max-w-lg mx-auto">
            {{ isPaid ? t("checkout.success_body") : t("checkout.success_pending_body") }}
          </p>
        </div>
      </div>

      <!-- Order summary card -->
      <div v-if="order" class="rounded-lg border border-border bg-bg-card overflow-hidden mb-6">
        <header class="px-5 py-3 border-b border-border bg-bg-secondary/40 flex items-center justify-between gap-3 flex-wrap">
          <div>
            <p class="text-xs uppercase tracking-wider text-ink-tertiary">
              {{ t("checkout.order_number") }}
            </p>
            <p class="font-mono text-sm text-ink mt-0.5">{{ order.order_number }}</p>
          </div>
          <span
            class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-xs font-medium"
            :class="isPaid ? 'bg-success/10 text-success border-success/20' : 'bg-warning/10 text-warning border-warning/20'"
          >
            <Icon :name="isPaid ? 'check-circle-solid' : 'arrow-path'" class="h-3 w-3" />
            {{ t(`orders.statuses.${order.status}`) }}
          </span>
        </header>

        <ul class="divide-y divide-border">
          <li
            v-for="item in order.items"
            :key="item.id"
            class="flex items-center gap-3 px-5 py-3"
          >
            <NuxtLink
              :to="localePath(`/books/${item.book.slug}`)"
              class="w-12 shrink-0 rounded overflow-hidden ring-1 ring-border"
            >
              <BookCover :src="item.book.cover_url" :alt="localised(item.book.title, item.book.slug)" />
            </NuxtLink>
            <div class="min-w-0 flex-1">
              <NuxtLink
                :to="localePath(`/books/${item.book.slug}`)"
                class="text-sm text-ink hover:text-primary line-clamp-1 font-medium"
              >
                {{ localised(item.book.title, item.book.slug) }}
              </NuxtLink>
              <p class="text-xs text-ink-tertiary truncate">{{ item.book.author.display_name }}</p>
            </div>
            <div class="text-sm text-ink-secondary tabular-nums shrink-0">
              {{ formatPrice(item.price) }}
            </div>
          </li>
        </ul>

        <footer class="px-5 py-3 border-t border-border flex items-center justify-between">
          <span class="text-sm text-ink-secondary">{{ t("orders.total") }}</span>
          <span class="font-serif text-xl text-primary tabular-nums">
            {{ formatPrice(order.total) }}
          </span>
        </footer>
      </div>

      <!-- Pending hint -->
      <div
        v-if="isPending"
        class="rounded-md border border-warning/30 bg-warning/5 p-4 flex items-start gap-3 mb-6"
      >
        <Icon name="warning" class="h-5 w-5 text-warning shrink-0 mt-0.5" />
        <div class="text-sm">
          <p class="text-ink font-medium">{{ t("checkout.pending_hint_title") }}</p>
          <p class="text-ink-secondary mt-0.5">{{ t("checkout.pending_hint_body") }}</p>
        </div>
      </div>

      <!-- CTAs -->
      <div class="flex flex-wrap justify-center gap-2">
        <UiButton :to="localePath('/account/library')" size="lg">
          <Icon name="library" class="h-4 w-4" />
          {{ t("checkout.go_library") }}
        </UiButton>
        <UiButton variant="ghost" :to="localePath('/account/orders')" size="lg">
          <Icon name="clipboard-check" class="h-4 w-4" />
          {{ t("checkout.go_orders") }}
        </UiButton>
      </div>

      <!-- Meta -->
      <p v-if="order" class="text-center text-xs text-ink-tertiary mt-6">
        {{ t("checkout.created_at", { date: formatDate(order.created_at) }) }}
      </p>
    </div>
  </section>
</template>
