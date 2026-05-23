<script setup lang="ts">
import type { AuthorBalance, WithdrawalList } from "~/types/api";
import { formatPrice } from "~/composables/useLocaleText";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({ middleware: "auth" });

const { t } = useI18n();
const localePath = useLocalePath();
const api = useApi();

const balance = ref<AuthorBalance | null>(null);
const noProfile = ref(false);
const loadError = ref<string | null>(null);

async function loadBalance() {
  try {
    balance.value = await api<AuthorBalance>("/authors/me/balance");
    noProfile.value = false;
  }
  catch (err: unknown) {
    const code = (err as { data?: { error?: { details?: { code?: string } } } })
      ?.data?.error?.details?.code;
    if (code === "author_profile_missing") {
      noProfile.value = true;
    }
    else {
      loadError.value = apiErrorMessage(err, t("common.error"));
    }
  }
}

await loadBalance();

const { data: withdrawalsRaw, refresh: refreshWithdrawals } = await useAsyncData(
  "account:withdrawals",
  () =>
    noProfile.value
      ? Promise.resolve(null as WithdrawalList | null)
      : api<WithdrawalList>("/authors/me/withdrawals", { query: { page: 1, page_size: 5 } }),
);

const recentWithdrawals = computed(() => withdrawalsRaw.value as WithdrawalList | null);

useHead({ title: t("balance.title") });

const breadcrumbs = computed(() => [
  { label: t("nav.home"), to: localePath("/") },
  { label: t("account.title"), to: localePath("/account") },
  { label: t("balance.title") },
]);

// Withdrawal request form
const formOpen = ref(false);
const formAmount = ref("");
const submitting = ref(false);
const formError = ref<string | null>(null);
const formSuccess = ref(false);

const minAmount = 50000;

function resetForm() {
  formAmount.value = "";
  formError.value = null;
}

async function submitWithdrawal() {
  if (submitting.value) return;
  const amount = Number(formAmount.value);
  if (!Number.isFinite(amount) || amount < minAmount) {
    formError.value = t("withdrawals.amount_min", { n: minAmount });
    return;
  }
  if (balance.value && amount > balance.value.available_balance) {
    formError.value = t("balance.available") + ": " + formatPrice(balance.value.available_balance);
    return;
  }
  submitting.value = true;
  formError.value = null;
  try {
    await api("/authors/me/withdrawals", { method: "POST", body: { amount } });
    formSuccess.value = true;
    resetForm();
    formOpen.value = false;
    await loadBalance();
    await refreshWithdrawals();
  }
  catch (err) {
    formError.value = apiErrorMessage(err, t("common.error"));
  }
  finally {
    submitting.value = false;
  }
}
</script>

<template>
  <section class="max-w-3xl mx-auto px-4 py-8 space-y-6">
    <UiBreadcrumbs :items="breadcrumbs" />

    <header class="space-y-1">
      <h1 class="font-serif text-3xl text-ink">{{ t("balance.title") }}</h1>
      <p class="text-sm text-ink-secondary">{{ t("balance.subtitle") }}</p>
    </header>

    <UiEmptyState
      v-if="noProfile"
      icon="pencil"
      :title="t('balance.no_author_profile_title')"
      :description="t('balance.no_author_profile_body')"
    >
      <UiButton :to="localePath('/authors/me')">
        {{ t("home.hero.cta_become_author") }}
      </UiButton>
    </UiEmptyState>

    <template v-else-if="balance">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div class="rounded border border-border bg-bg-card p-4 text-center">
          <div class="text-xs text-ink-tertiary">{{ t("balance.available") }}</div>
          <div class="font-serif text-2xl text-success mt-1">
            {{ formatPrice(balance.available_balance) }}
          </div>
        </div>
        <div class="rounded border border-border bg-bg-card p-4 text-center">
          <div class="text-xs text-ink-tertiary">{{ t("balance.pending") }}</div>
          <div class="font-serif text-2xl text-warning mt-1">
            {{ formatPrice(balance.pending_balance) }}
          </div>
        </div>
        <div class="rounded border border-border bg-bg-card p-4 text-center">
          <div class="text-xs text-ink-tertiary">{{ t("balance.total_revenue") }}</div>
          <div class="font-serif text-2xl text-ink mt-1">
            {{ formatPrice(balance.total_revenue) }}
          </div>
        </div>
        <div class="rounded border border-border bg-bg-card p-4 text-center">
          <div class="text-xs text-ink-tertiary">{{ t("balance.total_sales") }}</div>
          <div class="font-serif text-2xl text-ink mt-1">
            {{ balance.total_sales }}
          </div>
        </div>
      </div>

      <p class="text-xs text-ink-tertiary">
        {{ t("balance.commission_rate") }}: {{ balance.commission_rate }}%
      </p>

      <!-- Request form -->
      <div class="rounded border border-border bg-bg-card p-4 space-y-3">
        <div class="flex items-center justify-between gap-2">
          <h2 class="font-medium text-ink">{{ t("withdrawals.request_title") }}</h2>
          <NuxtLink
            :to="localePath('/account/withdrawals')"
            class="inline-flex items-center gap-1 text-xs text-primary hover:underline"
          >
            {{ t("withdrawals.title") }}
            <Icon name="arrow-right" class="h-3.5 w-3.5" />
          </NuxtLink>
        </div>

        <div v-if="formSuccess" class="flex items-center gap-1 text-sm text-success">
          <Icon name="check-circle-solid" class="h-4 w-4" />
          {{ t("common.loading") /* placeholder; success shown by refresh */ }}
        </div>

        <form v-if="formOpen" class="space-y-3" @submit.prevent="submitWithdrawal">
          <UiInput
            v-model="formAmount"
            type="number"
            :label="t('withdrawals.amount')"
            :hint="t('withdrawals.amount_min', { n: minAmount })"
            :placeholder="String(minAmount)"
          />
          <p v-if="formError" class="text-sm text-error">{{ formError }}</p>
          <div class="flex gap-2">
            <UiButton type="submit" :loading="submitting" :disabled="submitting">
              {{ submitting ? t("withdrawals.submitting") : t("withdrawals.submit") }}
            </UiButton>
            <UiButton variant="ghost" type="button" :disabled="submitting" @click="formOpen = false; resetForm()">
              {{ t("common.cancel") }}
            </UiButton>
          </div>
        </form>

        <UiButton v-else @click="formOpen = true; formSuccess = false">
          {{ t("balance.request_withdrawal") }}
        </UiButton>
      </div>

      <!-- Recent withdrawals -->
      <section
        v-if="(recentWithdrawals?.items.length ?? 0) > 0"
        class="space-y-2"
      >
        <ul class="space-y-2">
          <li
            v-for="w in recentWithdrawals!.items"
            :key="w.id"
            class="rounded border border-border bg-bg-card px-4 py-3 flex items-center justify-between gap-3 text-sm"
          >
            <div class="min-w-0">
              <div class="font-medium text-ink">{{ formatPrice(w.amount) }}</div>
              <div class="text-xs text-ink-tertiary">
                {{ new Date(w.created_at).toLocaleString() }}
              </div>
            </div>
            <UiBadge size="sm" tone="neutral">
              {{ t(`withdrawals.statuses.${w.status}`) }}
            </UiBadge>
          </li>
        </ul>
      </section>
    </template>

    <p v-else-if="loadError" class="text-sm text-error">{{ loadError }}</p>
  </section>
</template>
