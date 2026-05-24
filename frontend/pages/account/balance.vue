<script setup lang="ts">
import type { AuthorBalance, WithdrawalList, WithdrawalPublic } from "~/types/api";
import type { IconName } from "~/utils/icons";
import { formatPrice } from "~/composables/useLocaleText";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({ middleware: "auth" });

const { t, locale } = useI18n();
const localePath = useLocalePath();
const api = useApi();
const toast = useToast();

useSiteSeo({ title: t("balance.title"), noindex: true });

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
    const status = (err as { statusCode?: number; status?: number }).statusCode
      ?? (err as { status?: number }).status;
    if (code === "author_profile_missing" || status === 404) {
      noProfile.value = true;
    }
    else {
      loadError.value = apiErrorMessage(err, t("common.error"));
    }
  }
}

await loadBalance();

const { data: withdrawalsRaw, refresh: refreshWithdrawals } = await useAsyncData(
  "account:balance:recent",
  () =>
    noProfile.value
      ? Promise.resolve(null as WithdrawalList | null)
      : api<WithdrawalList>("/authors/me/withdrawals", { query: { page: 1, page_size: 5 } }),
  { server: false },
);

const recentWithdrawals = computed(() => (withdrawalsRaw.value as WithdrawalList | null)?.items ?? []);

// Withdrawal form
const minAmount = 50000;
const formOpen = ref(false);
const formAmount = ref("");
const formSubmitting = ref(false);
const formError = ref<string | null>(null);

const availableCap = computed(() => balance.value?.available_balance ?? 0);
const amountNumber = computed(() => {
  const n = Number(formAmount.value);
  return Number.isFinite(n) ? n : 0;
});
const amountValid = computed(() =>
  amountNumber.value >= minAmount && amountNumber.value <= availableCap.value,
);

function resetForm() {
  formAmount.value = "";
  formError.value = null;
}

async function submitWithdrawal() {
  if (formSubmitting.value) return;
  if (!Number.isFinite(amountNumber.value) || amountNumber.value < minAmount) {
    formError.value = t("withdrawals.amount_min", { n: minAmount });
    return;
  }
  if (amountNumber.value > availableCap.value) {
    formError.value = t("balance.amount_exceeds", { available: formatPrice(availableCap.value) });
    return;
  }
  formSubmitting.value = true;
  formError.value = null;
  try {
    await api("/authors/me/withdrawals", {
      method: "POST",
      body: { amount: amountNumber.value },
    });
    toast.success(t("balance.request_success"));
    resetForm();
    formOpen.value = false;
    await loadBalance();
    await refreshWithdrawals();
  }
  catch (err) {
    formError.value = apiErrorMessage(err, t("common.error"));
  }
  finally {
    formSubmitting.value = false;
  }
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

const STATUS_META: Record<WithdrawalPublic["status"], { tone: string; icon: IconName; label: string }> = {
  requested: { tone: "bg-warning/10 text-warning border-warning/20", icon: "inbox", label: "withdrawals.statuses.requested" },
  approved: { tone: "bg-info/10 text-info border-info/20", icon: "check", label: "withdrawals.statuses.approved" },
  processing: { tone: "bg-info/10 text-info border-info/20", icon: "arrow-path", label: "withdrawals.statuses.processing" },
  completed: { tone: "bg-success/10 text-success border-success/20", icon: "check-circle-solid", label: "withdrawals.statuses.completed" },
  rejected: { tone: "bg-error/10 text-error border-error/20", icon: "close", label: "withdrawals.statuses.rejected" },
  cancelled: { tone: "bg-bg-secondary text-ink-secondary border-border", icon: "close", label: "withdrawals.statuses.cancelled" },
};

// Quick-fill buttons
const presets = computed(() => {
  const cap = availableCap.value;
  if (cap < minAmount) return [];
  const out: { label: string; value: number }[] = [];
  out.push({ label: `${minAmount.toLocaleString(locale.value)}`, value: minAmount });
  const half = Math.floor(cap / 2);
  if (half >= minAmount && half !== minAmount) {
    out.push({ label: `½ · ${half.toLocaleString(locale.value)}`, value: half });
  }
  out.push({ label: `${t("balance.preset_max")} · ${cap.toLocaleString(locale.value)}`, value: cap });
  return out;
});
</script>

<template>
  <AccountShell>
    <header class="space-y-2 mb-6">
      <div class="flex items-center gap-3">
        <span class="h-10 w-10 rounded-md bg-success/10 text-success inline-flex items-center justify-center shrink-0">
          <Icon name="currency" class="h-5 w-5" />
        </span>
        <div>
          <h1 class="font-serif text-2xl md:text-3xl text-ink leading-tight">
            {{ t("balance.title") }}
          </h1>
          <p class="text-sm text-ink-secondary">{{ t("balance.subtitle") }}</p>
        </div>
      </div>
    </header>

    <!-- NO AUTHOR PROFILE -->
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

    <!-- LOAD ERROR -->
    <div
      v-else-if="loadError"
      class="rounded-md border border-error/30 bg-error/5 p-6 flex items-start gap-4"
    >
      <Icon name="warning-solid" class="h-6 w-6 text-error shrink-0" />
      <div>
        <h2 class="font-serif text-lg text-ink mb-1">{{ t("balance.error_title") }}</h2>
        <p class="text-sm text-ink-secondary">{{ loadError }}</p>
      </div>
    </div>

    <!-- BALANCE -->
    <template v-else-if="balance">
      <!-- Stat tiles -->
      <section class="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        <div class="rounded-md border border-border bg-bg-card p-4">
          <div class="flex items-center mb-3">
            <span class="h-9 w-9 rounded-md flex items-center justify-center bg-success/10 text-success">
              <Icon name="currency" class="h-4 w-4" />
            </span>
          </div>
          <div class="font-serif text-2xl text-success tabular-nums">
            {{ formatPrice(balance.available_balance) }}
          </div>
          <div class="text-xs uppercase tracking-wider text-ink-tertiary mt-1">
            {{ t("balance.available") }}
          </div>
        </div>

        <div class="rounded-md border border-border bg-bg-card p-4">
          <div class="flex items-center mb-3">
            <span class="h-9 w-9 rounded-md flex items-center justify-center bg-warning/10 text-warning">
              <Icon name="arrow-path" class="h-4 w-4" />
            </span>
          </div>
          <div class="font-serif text-2xl text-warning tabular-nums">
            {{ formatPrice(balance.pending_balance) }}
          </div>
          <div class="text-xs uppercase tracking-wider text-ink-tertiary mt-1">
            {{ t("balance.pending") }}
          </div>
        </div>

        <div class="rounded-md border border-border bg-bg-card p-4">
          <div class="flex items-center mb-3">
            <span class="h-9 w-9 rounded-md flex items-center justify-center bg-info/10 text-info">
              <Icon name="chart" class="h-4 w-4" />
            </span>
          </div>
          <div class="font-serif text-2xl text-ink tabular-nums">
            {{ formatPrice(balance.total_revenue) }}
          </div>
          <div class="text-xs uppercase tracking-wider text-ink-tertiary mt-1">
            {{ t("balance.total_revenue") }}
          </div>
        </div>

        <div class="rounded-md border border-border bg-bg-card p-4">
          <div class="flex items-center mb-3">
            <span class="h-9 w-9 rounded-md flex items-center justify-center bg-primary/10 text-primary">
              <Icon name="clipboard-check" class="h-4 w-4" />
            </span>
          </div>
          <div class="font-serif text-2xl text-ink tabular-nums">
            {{ balance.total_sales }}
          </div>
          <div class="text-xs uppercase tracking-wider text-ink-tertiary mt-1">
            {{ t("balance.total_sales") }}
          </div>
        </div>
      </section>

      <p class="text-xs text-ink-tertiary mb-8 inline-flex items-center gap-1.5">
        <Icon name="scale" class="h-3.5 w-3.5" />
        {{ t("balance.commission_rate") }}: <span class="tabular-nums">{{ balance.commission_rate }}%</span>
      </p>

      <!-- Withdrawal request -->
      <section class="rounded-md border border-border bg-bg-card overflow-hidden mb-8">
        <header class="flex items-center justify-between gap-3 px-5 py-4 border-b border-border">
          <div>
            <h2 class="font-serif text-lg text-ink">{{ t("withdrawals.request_title") }}</h2>
            <p class="text-xs text-ink-secondary mt-0.5">
              {{ t("balance.request_subtitle", { min: formatPrice(minAmount) }) }}
            </p>
          </div>
          <NuxtLink
            :to="localePath('/account/withdrawals')"
            class="inline-flex items-center gap-1 text-xs text-primary hover:underline shrink-0"
          >
            {{ t("balance.full_history") }}
            <Icon name="arrow-right" class="h-3.5 w-3.5" />
          </NuxtLink>
        </header>

        <div class="p-5">
          <!-- Disabled state if no balance -->
          <div
            v-if="availableCap < minAmount"
            class="text-center py-6 space-y-2"
          >
            <Icon name="warning" class="h-8 w-8 text-warning mx-auto" />
            <p class="text-sm text-ink-secondary">
              {{ t("balance.insufficient", { current: formatPrice(availableCap), min: formatPrice(minAmount) }) }}
            </p>
          </div>

          <UiButton
            v-else-if="!formOpen"
            @click="formOpen = true"
          >
            <Icon name="money" class="h-4 w-4" />
            {{ t("balance.request_withdrawal") }}
          </UiButton>

          <form v-else class="space-y-4" novalidate @submit.prevent="submitWithdrawal">
            <UiInput
              v-model="formAmount"
              type="number"
              :label="t('withdrawals.amount')"
              :hint="t('balance.amount_hint', {
                min: formatPrice(minAmount),
                max: formatPrice(availableCap),
              })"
              :placeholder="String(minAmount)"
              required
            />

            <div v-if="presets.length > 0" class="flex flex-wrap items-center gap-1.5">
              <span class="text-xs text-ink-tertiary mr-1">{{ t("balance.quick") }}:</span>
              <button
                v-for="p in presets"
                :key="p.value"
                type="button"
                class="px-2.5 py-1 rounded-full border border-border bg-bg text-xs text-ink-secondary hover:border-primary hover:text-primary transition-colors tabular-nums"
                @click="formAmount = String(p.value)"
              >
                {{ p.label }}
              </button>
            </div>

            <p v-if="formError" class="flex items-center gap-2 text-sm text-error">
              <Icon name="warning-solid" class="h-4 w-4" />
              {{ formError }}
            </p>

            <div class="flex items-center justify-end gap-2">
              <UiButton variant="ghost" type="button" :disabled="formSubmitting" @click="formOpen = false; resetForm()">
                {{ t("common.cancel") }}
              </UiButton>
              <UiButton
                type="submit"
                :loading="formSubmitting"
                :disabled="formSubmitting || !amountValid"
              >
                <Icon name="check" class="h-4 w-4" />
                {{ t("withdrawals.submit") }}
              </UiButton>
            </div>
          </form>
        </div>
      </section>

      <!-- Recent withdrawals -->
      <section v-if="recentWithdrawals.length > 0" class="space-y-3">
        <div class="flex items-end justify-between gap-3">
          <h2 class="font-serif text-xl text-ink leading-tight">
            {{ t("balance.recent_withdrawals") }}
          </h2>
          <NuxtLink
            :to="localePath('/account/withdrawals')"
            class="inline-flex items-center gap-1 text-sm text-primary hover:underline"
          >
            {{ t("balance.see_all") }}
            <Icon name="arrow-right" class="h-4 w-4" />
          </NuxtLink>
        </div>
        <ul class="space-y-2">
          <li
            v-for="w in recentWithdrawals"
            :key="w.id"
            class="rounded-md border border-border bg-bg-card px-4 py-3 flex items-center justify-between gap-3"
          >
            <div class="min-w-0">
              <div class="font-medium text-ink tabular-nums">{{ formatPrice(w.amount) }}</div>
              <div class="text-xs text-ink-tertiary mt-0.5 inline-flex items-center gap-1.5">
                <Icon name="sparkles" class="h-3 w-3" />
                {{ formatDate(w.created_at) }}
              </div>
            </div>
            <span
              class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-xs font-medium"
              :class="STATUS_META[w.status].tone"
            >
              <Icon :name="STATUS_META[w.status].icon" class="h-3 w-3" />
              {{ t(STATUS_META[w.status].label) }}
            </span>
          </li>
        </ul>
      </section>
    </template>
  </AccountShell>
</template>
