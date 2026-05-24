<script setup lang="ts">
import type { WithdrawalList, WithdrawalPublic } from "~/types/api";
import type { IconName } from "~/components/ui/Icon.vue";
import { formatPrice } from "~/composables/useLocaleText";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({ middleware: "auth" });

const { t, locale } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const api = useApi();
const toast = useToast();

useSiteSeo({ title: t("withdrawals.title"), noindex: true });

const PAGE_SIZE = 10;
const currentPage = computed(() => Math.max(1, Number(route.query.page) || 1));
const statusFilter = computed(() => (route.query.status as string) || "");

// Treat `author_profile_missing` 404 as a known state, not an error.
const noProfile = ref(false);
const { data: dataRaw, pending, refresh, error: listError } = await useAsyncData(
  "account:withdrawals:list",
  () =>
    api<WithdrawalList>("/authors/me/withdrawals", {
      query: { page: currentPage.value, page_size: PAGE_SIZE },
    }).catch((err: unknown) => {
      const code = (err as { data?: { error?: { details?: { code?: string } } } })
        ?.data?.error?.details?.code;
      if (code === "author_profile_missing") {
        noProfile.value = true;
        return null;
      }
      throw err;
    }),
  { watch: [currentPage] },
);

const list = computed(() => dataRaw.value as WithdrawalList | null);
const total = computed(() => list.value?.total ?? 0);

const filtered = computed<WithdrawalPublic[]>(() => {
  const items = list.value?.items ?? [];
  if (!statusFilter.value) return items;
  return items.filter((w) => w.status === statusFilter.value);
});

const STATUS_META: Record<WithdrawalPublic["status"], { tone: string; icon: IconName }> = {
  requested: { tone: "bg-warning/10 text-warning border-warning/20", icon: "inbox" },
  approved: { tone: "bg-info/10 text-info border-info/20", icon: "check" },
  processing: { tone: "bg-info/10 text-info border-info/20", icon: "arrow-path" },
  completed: { tone: "bg-success/10 text-success border-success/20", icon: "check-circle-solid" },
  rejected: { tone: "bg-error/10 text-error border-error/20", icon: "close" },
  cancelled: { tone: "bg-bg-secondary text-ink-secondary border-border", icon: "close" },
};

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

function changePage(page: number) {
  setQuery({ page });
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}

const cancelTarget = ref<WithdrawalPublic | null>(null);
const cancelling = ref(false);

async function confirmCancel() {
  if (!cancelTarget.value || cancelling.value) return;
  const target = cancelTarget.value;
  cancelling.value = true;
  try {
    await api(`/authors/me/withdrawals/${target.id}/cancel`, { method: "POST" });
    toast.success(t("withdrawals.cancel_success"));
    cancelTarget.value = null;
    await refresh();
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("withdrawals.cancel_failed")));
  }
  finally {
    cancelling.value = false;
  }
}

const statusOptions = computed(() => [
  { value: "", label: t("withdrawals.filter_all") },
  { value: "requested", label: t("withdrawals.statuses.requested") },
  { value: "approved", label: t("withdrawals.statuses.approved") },
  { value: "processing", label: t("withdrawals.statuses.processing") },
  { value: "completed", label: t("withdrawals.statuses.completed") },
  { value: "rejected", label: t("withdrawals.statuses.rejected") },
  { value: "cancelled", label: t("withdrawals.statuses.cancelled") },
]);
</script>

<template>
  <AccountShell>
    <header class="space-y-2 mb-6">
      <div class="flex items-center gap-3">
        <span class="h-10 w-10 rounded-md bg-warning/10 text-warning inline-flex items-center justify-center shrink-0">
          <Icon name="money" class="h-5 w-5" />
        </span>
        <div>
          <h1 class="font-serif text-2xl md:text-3xl text-ink leading-tight">
            {{ t("withdrawals.title") }}
          </h1>
          <p class="text-sm text-ink-secondary">{{ t("withdrawals.subtitle") }}</p>
        </div>
      </div>
    </header>

    <!-- Filter toolbar -->
    <div v-if="!noProfile && total > 0" class="flex flex-wrap items-center gap-2 mb-4">
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

      <UiButton
        size="sm"
        variant="ghost"
        :to="localePath('/account/balance')"
      >
        <Icon name="plus" class="h-4 w-4" />
        {{ t("balance.request_withdrawal") }}
      </UiButton>

      <span class="text-sm text-ink-secondary tabular-nums">
        {{ t("withdrawals.results", { n: total }) }}
      </span>
    </div>

    <!-- No author profile -->
    <UiEmptyState
      v-if="noProfile"
      icon="pencil"
      :title="t('balance.no_author_profile_title')"
      :description="t('balance.no_author_profile_body')"
    >
      <UiButton :to="localePath('/authors/me')">
        <Icon name="pencil" class="h-4 w-4" />
        {{ t("balance.become_author") }}
      </UiButton>
    </UiEmptyState>

    <!-- Loading -->
    <div v-else-if="pending && !list" class="space-y-3">
      <UiSkeleton v-for="i in 3" :key="i" height="5rem" block rounded="rounded-md" />
    </div>

    <!-- Error -->
    <div
      v-else-if="listError"
      class="rounded-md border border-error/30 bg-error/5 p-6 flex items-start gap-4"
    >
      <Icon name="warning-solid" class="h-6 w-6 text-error shrink-0" />
      <div>
        <h3 class="font-serif text-lg text-ink mb-1">{{ t("withdrawals.error_title") }}</h3>
        <p class="text-sm text-ink-secondary">{{ t("withdrawals.error_body") }}</p>
      </div>
    </div>

    <!-- Empty (no withdrawals at all) -->
    <UiEmptyState
      v-else-if="total === 0"
      icon="money"
      :title="t('withdrawals.empty_title')"
      :description="t('withdrawals.empty_body')"
    >
      <UiButton :to="localePath('/account/balance')">
        <Icon name="currency" class="h-4 w-4" />
        {{ t("balance.request_withdrawal") }}
      </UiButton>
    </UiEmptyState>

    <!-- Filter empty -->
    <UiEmptyState
      v-else-if="filtered.length === 0"
      icon="search"
      :title="t('withdrawals.no_filter_match_title')"
      :description="t('withdrawals.no_filter_match_body')"
    >
      <UiButton variant="ghost" @click="setQuery({ status: undefined })">
        <Icon name="close" class="h-4 w-4" />
        {{ t("withdrawals.clear_filter") }}
      </UiButton>
    </UiEmptyState>

    <!-- List -->
    <ul v-else class="space-y-3">
      <li
        v-for="w in filtered"
        :key="w.id"
        class="rounded-md border border-border bg-bg-card p-4 space-y-3"
      >
        <div class="flex items-start justify-between gap-3 flex-wrap">
          <div class="min-w-0">
            <div class="font-serif text-2xl text-ink tabular-nums">{{ formatPrice(w.amount) }}</div>
            <div class="text-xs text-ink-tertiary mt-0.5 inline-flex items-center gap-1.5">
              <Icon name="sparkles" class="h-3.5 w-3.5" />
              {{ formatDate(w.created_at) }}
              <template v-if="w.processed_at">
                <span class="mx-1">·</span>
                <Icon name="check" class="h-3.5 w-3.5" />
                {{ formatDate(w.processed_at) }}
              </template>
            </div>
          </div>
          <span
            class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-xs font-medium"
            :class="STATUS_META[w.status].tone"
          >
            <Icon :name="STATUS_META[w.status].icon" class="h-3 w-3" />
            {{ t(`withdrawals.statuses.${w.status}`) }}
          </span>
        </div>

        <div v-if="w.admin_notes || w.transaction_ref" class="space-y-1.5 pt-2 border-t border-border">
          <p v-if="w.admin_notes" class="inline-flex items-start gap-1.5 text-xs text-ink-secondary">
            <Icon name="chat" class="h-3.5 w-3.5 mt-0.5 shrink-0 text-ink-tertiary" />
            <span>{{ w.admin_notes }}</span>
          </p>
          <p v-if="w.transaction_ref" class="inline-flex items-center gap-1.5 text-xs text-ink-tertiary font-mono">
            <Icon name="key" class="h-3.5 w-3.5" />
            {{ w.transaction_ref }}
          </p>
        </div>

        <div v-if="w.status === 'requested'" class="flex justify-end pt-1">
          <UiButton
            size="sm"
            variant="ghost"
            :disabled="cancelling"
            @click="cancelTarget = w"
          >
            <Icon name="close" class="h-4 w-4" />
            {{ t("withdrawals.cancel") }}
          </UiButton>
        </div>
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
      :title="t('withdrawals.cancel_modal_title')"
      :description="cancelTarget ? t('withdrawals.cancel_modal_body', { amount: formatPrice(cancelTarget.amount) }) : ''"
      :confirm-label="t('withdrawals.cancel_modal_confirm')"
      :cancel-label="t('withdrawals.cancel_modal_keep')"
      :loading="cancelling"
      @update:open="(v) => !v && (cancelTarget = null)"
      @confirm="confirmCancel"
    />
  </AccountShell>
</template>
