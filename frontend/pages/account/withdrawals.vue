<script setup lang="ts">
import type { WithdrawalList, WithdrawalPublic } from "~/types/api";
import { formatPrice } from "~/composables/useLocaleText";

definePageMeta({ middleware: "auth" });

const { t, locale } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const api = useApi();

const PAGE_SIZE = 20;
const currentPage = computed(() => Math.max(1, Number(route.query.page) || 1));

const { data: dataRaw, pending, refresh } = await useAsyncData(
  "account:withdrawals:list",
  () =>
    api<WithdrawalList>("/authors/me/withdrawals", {
      query: { page: currentPage.value, page_size: PAGE_SIZE },
    }),
  { watch: [currentPage] },
);

const list = computed(() => dataRaw.value as WithdrawalList | null);

useHead({ title: t("withdrawals.title") });

const breadcrumbs = computed(() => [
  { label: t("nav.home"), to: localePath("/") },
  { label: t("account.title"), to: localePath("/account") },
  { label: t("balance.title"), to: localePath("/account/balance") },
  { label: t("withdrawals.title") },
]);

function statusTone(status: WithdrawalPublic["status"]) {
  return (
    {
      requested: "warning",
      approved: "info",
      processing: "info",
      completed: "success",
      rejected: "neutral",
      cancelled: "neutral",
    } as const
  )[status];
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

function changePage(page: number) {
  router.push({ query: { ...route.query, page } });
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}

const cancelling = ref<Set<string>>(new Set());

async function cancelOne(w: WithdrawalPublic) {
  if (!confirm(t("withdrawals.cancel_confirm"))) return;
  if (cancelling.value.has(w.id)) return;
  cancelling.value.add(w.id);
  try {
    await api(`/authors/me/withdrawals/${w.id}/cancel`, { method: "POST" });
    await refresh();
  }
  catch {
    // surface via global toast in 4.8 polish
  }
  finally {
    cancelling.value.delete(w.id);
  }
}
</script>

<template>
  <section class="max-w-4xl mx-auto px-4 py-8 space-y-6">
    <UiBreadcrumbs :items="breadcrumbs" />

    <header class="space-y-1">
      <h1 class="font-serif text-3xl text-ink">{{ t("withdrawals.title") }}</h1>
      <p class="text-sm text-ink-secondary">{{ t("withdrawals.subtitle") }}</p>
    </header>

    <div v-if="pending && !list" class="space-y-2">
      <UiSkeleton v-for="i in 3" :key="i" :height="'4rem'" :block="true" />
    </div>

    <UiEmptyState
      v-else-if="(list?.items.length ?? 0) === 0"
      icon="💸"
      :title="t('withdrawals.empty_title')"
      :description="t('withdrawals.empty_body')"
    >
      <UiButton :to="localePath('/account/balance')">
        {{ t("balance.request_withdrawal") }}
      </UiButton>
    </UiEmptyState>

    <ul v-else class="space-y-3">
      <li
        v-for="w in list!.items"
        :key="w.id"
        class="rounded border border-border bg-bg-card p-4 space-y-2"
      >
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <div class="font-medium text-ink text-lg">{{ formatPrice(w.amount) }}</div>
            <div class="text-xs text-ink-tertiary">{{ formatDate(w.created_at) }}</div>
          </div>
          <UiBadge size="sm" :tone="statusTone(w.status)">
            {{ t(`withdrawals.statuses.${w.status}`) }}
          </UiBadge>
        </div>

        <p v-if="w.admin_notes" class="text-xs text-ink-secondary">
          {{ t("withdrawals.notes", { notes: w.admin_notes }) }}
        </p>
        <p v-if="w.transaction_ref" class="text-xs text-ink-tertiary">
          {{ t("withdrawals.ref", { ref: w.transaction_ref }) }}
        </p>

        <div v-if="w.status === 'requested'" class="pt-1">
          <UiButton
            size="sm"
            variant="ghost"
            :disabled="cancelling.has(w.id)"
            @click="cancelOne(w)"
          >
            {{ t("withdrawals.cancel") }}
          </UiButton>
        </div>
      </li>
    </ul>

    <div class="pt-4">
      <UiPagination
        :page="currentPage"
        :page-size="PAGE_SIZE"
        :total="list?.total ?? 0"
        @change="changePage"
      />
    </div>
  </section>
</template>
