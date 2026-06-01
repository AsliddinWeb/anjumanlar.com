<script setup lang="ts">
import type { ReviewRequestList, ReviewRequestPublic, ReviewRequestStatus } from "~/types/api";
import { apiErrorMessage } from "~/composables/useAuth";
import { formatPrice } from "~/composables/useLocaleText";

definePageMeta({ middleware: "auth" });

const { t, locale } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const api = useApi();
const toast = useToast();
const { hasRole } = useAuth();

useHead({ title: t("review_requests.incoming_title") });

const PAGE_SIZE = 20;
const queryParams = computed(() => ({
  page: Math.max(1, Number(route.query.page) || 1),
  page_size: PAGE_SIZE,
  status: ((route.query.status as string) || undefined) as ReviewRequestStatus | undefined,
}));

const isAuthor = computed(() => hasRole("author"));

const { data: listRaw, pending, refresh } = await useAsyncData(
  "account:incoming-reviews",
  () => isAuthor.value
    ? api<ReviewRequestList>("/review-requests/incoming", { query: queryParams.value })
    : Promise.resolve(null),
  { server: false, watch: [queryParams, isAuthor] },
);
const list = computed(() => listRaw.value as ReviewRequestList | null);
const items = computed(() => list.value?.items ?? []);

const STATUS_TONE: Record<ReviewRequestStatus, string> = {
  pending: "bg-bg-secondary text-ink-tertiary",
  quoted: "bg-warning/10 text-warning",
  paid: "bg-info/10 text-info",
  completed: "bg-success/10 text-success",
  cancelled: "bg-error/10 text-error",
};

const formatDate = (iso: string) =>
  new Intl.DateTimeFormat(locale.value, {
    year: "numeric", month: "short", day: "numeric",
  }).format(new Date(iso));

function setStatus(s: string) {
  const next: Record<string, string> = {};
  for (const [k, v] of Object.entries(route.query)) {
    if (typeof v === "string") next[k] = v;
  }
  if (s) next.status = s; else delete next.status;
  delete next.page;
  router.push({ query: next });
}

// ---- Quote ----
const quoteTarget = ref<ReviewRequestPublic | null>(null);
const quoteValue = ref("");
const quoting = ref(false);

async function confirmQuote() {
  if (!quoteTarget.value || !quoteValue.value) return;
  quoting.value = true;
  try {
    await api(`/review-requests/${quoteTarget.value.id}/quote`, {
      method: "POST",
      body: { final_price: Number(quoteValue.value) },
    });
    toast.success(t("review_requests.success.quoted"));
    quoteTarget.value = null;
    quoteValue.value = "";
    await refresh();
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    quoting.value = false;
  }
}

// ---- Submit review ----
const submitTarget = ref<ReviewRequestPublic | null>(null);
const reviewText = ref("");
const reviewFileInput = ref<HTMLInputElement | null>(null);
const reviewFile = ref<File | null>(null);
const submitting = ref(false);
const submitError = ref<string | null>(null);

function pickReviewFile(e: Event) {
  reviewFile.value = (e.target as HTMLInputElement).files?.[0] ?? null;
}

async function confirmSubmit() {
  if (!submitTarget.value) return;
  if (!reviewText.value.trim()) {
    submitError.value = t("review_requests.errors.no_review_text");
    return;
  }
  submitting.value = true;
  submitError.value = null;
  try {
    const fd = new FormData();
    fd.append("review_text", reviewText.value);
    if (reviewFile.value) fd.append("file", reviewFile.value);
    await api(`/review-requests/${submitTarget.value.id}/submit-review`, {
      method: "POST",
      body: fd,
    });
    toast.success(t("review_requests.success.submitted"));
    submitTarget.value = null;
    reviewText.value = "";
    reviewFile.value = null;
    if (reviewFileInput.value) reviewFileInput.value.value = "";
    await refresh();
  }
  catch (err) {
    submitError.value = apiErrorMessage(err, t("common.error"));
  }
  finally {
    submitting.value = false;
  }
}
</script>

<template>
  <AccountShell>
    <section class="space-y-5">
      <header>
        <h1 class="font-serif text-2xl md:text-3xl text-ink leading-tight">
          {{ t("review_requests.incoming_title") }}
        </h1>
        <p class="text-sm text-ink-secondary mt-1">{{ t("review_requests.incoming_subtitle") }}</p>
      </header>

      <UiEmptyState
        v-if="!isAuthor"
        icon="pencil"
        :title="t('account_books.must_be_author_title')"
        :description="t('account_books.must_be_author_body')"
      >
        <UiButton :to="localePath('/authors/me')">{{ t('account_books.go_to_profile') }}</UiButton>
      </UiEmptyState>

      <template v-else>
        <div class="rounded-md border border-border bg-bg-card p-3 flex flex-wrap items-center gap-2">
          <UiSelect
            :model-value="(route.query.status as string) || ''"
            size="sm"
            :options="[
              { value: '', label: t('review_requests.filter_status_any') },
              { value: 'pending', label: t('review_requests.statuses.pending') },
              { value: 'quoted', label: t('review_requests.statuses.quoted') },
              { value: 'paid', label: t('review_requests.statuses.paid') },
              { value: 'completed', label: t('review_requests.statuses.completed') },
              { value: 'cancelled', label: t('review_requests.statuses.cancelled') },
            ]"
            @update:model-value="setStatus"
          />
        </div>

        <div v-if="pending && !list" class="space-y-3">
          <UiSkeleton v-for="i in 3" :key="i" height="6rem" block />
        </div>

        <UiEmptyState
          v-else-if="items.length === 0"
          icon="chat"
          :title="t('review_requests.empty_title')"
          :description="t('review_requests.empty_body')"
        />

        <ul v-else class="space-y-3">
          <li
            v-for="r in items"
            :key="r.id"
            class="rounded-md border border-border bg-bg-card p-4 space-y-3"
          >
            <header class="flex items-start justify-between gap-3 flex-wrap">
              <div class="min-w-0">
                <div class="text-sm font-medium text-ink">{{ r.requester.full_name }}</div>
                <div class="text-xs text-ink-tertiary">{{ formatDate(r.created_at) }}</div>
              </div>
              <span
                class="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium"
                :class="STATUS_TONE[r.status]"
              >
                {{ t(`review_requests.statuses.${r.status}`) }}
              </span>
            </header>
            <p v-if="r.notes" class="text-sm text-ink-secondary line-clamp-3 whitespace-pre-line">{{ r.notes }}</p>
            <div class="flex flex-wrap items-center gap-3 text-xs text-ink-tertiary">
              <span v-if="r.proposed_price != null">
                {{ t("review_requests.fields.proposed_price") }}: <strong class="text-ink">{{ formatPrice(r.proposed_price) }}</strong>
              </span>
              <span v-if="r.final_price != null" class="text-primary tabular-nums">
                {{ t("review_requests.fields.final_price") }}: <strong>{{ formatPrice(r.final_price) }}</strong>
              </span>
            </div>
            <footer class="flex flex-wrap items-center gap-2 pt-2 border-t border-border">
              <a
                v-if="r.manuscript_url"
                :href="r.manuscript_url"
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center gap-1 text-xs text-primary hover:underline"
              >
                <Icon name="document" class="h-3.5 w-3.5" />
                {{ t("review_requests.actions.download_manuscript") }}
              </a>
              <span class="flex-1" />
              <UiButton
                v-if="['pending', 'quoted'].includes(r.status) && r.manuscript_url"
                size="sm"
                variant="ghost"
                @click="quoteTarget = r; quoteValue = String(r.final_price ?? r.proposed_price ?? '')"
              >
                <Icon name="currency" class="h-3.5 w-3.5" />
                {{ t("review_requests.actions.set_price") }}
              </UiButton>
              <UiButton
                v-if="r.status === 'paid'"
                size="sm"
                @click="submitTarget = r; reviewText = ''; reviewFile = null"
              >
                <Icon name="pencil" class="h-3.5 w-3.5" />
                {{ t("review_requests.actions.write_review") }}
              </UiButton>
            </footer>
          </li>
        </ul>

        <!-- Quote modal -->
        <AdminConfirmDialog
          :open="!!quoteTarget"
          tone="primary"
          icon="currency"
          :title="t('review_requests.quote_modal_title')"
          :description="quoteTarget ? t('review_requests.quote_modal_body', { proposed: quoteTarget.proposed_price != null ? formatPrice(quoteTarget.proposed_price) : '—' }) : ''"
          :confirm-label="t('review_requests.actions.save_quote')"
          :cancel-label="t('common.cancel')"
          :loading="quoting"
          :disabled="!quoteValue"
          @update:open="(v) => !v && (quoteTarget = null)"
          @confirm="confirmQuote"
        >
          <UiInput
            v-model="quoteValue"
            type="number"
            :label="t('review_requests.quote_field')"
            required
          />
        </AdminConfirmDialog>

        <!-- Submit-review modal -->
        <AdminConfirmDialog
          :open="!!submitTarget"
          tone="primary"
          icon="check-circle-solid"
          :title="t('review_requests.submit_modal_title')"
          :description="t('review_requests.submit_modal_body')"
          :confirm-label="t('review_requests.actions.submit_review')"
          :cancel-label="t('common.cancel')"
          :loading="submitting"
          @update:open="(v) => { if (!v) { submitTarget = null; submitError = null; } }"
          @confirm="confirmSubmit"
        >
          <div class="space-y-3">
            <label class="block">
              <span class="block text-sm text-ink-secondary mb-1">{{ t("review_requests.submit_text_field") }}</span>
              <textarea
                v-model="reviewText"
                rows="10"
                maxlength="20000"
                class="w-full px-3 py-2 rounded border border-border bg-bg text-sm text-ink focus:outline-none focus:border-primary"
              />
            </label>
            <label class="block">
              <span class="block text-sm text-ink-secondary mb-1">{{ t("review_requests.submit_file_field") }}</span>
              <input
                ref="reviewFileInput"
                type="file"
                accept="application/pdf"
                class="text-sm"
                @change="pickReviewFile"
              >
            </label>
            <p v-if="submitError" class="text-xs text-error">{{ submitError }}</p>
          </div>
        </AdminConfirmDialog>
      </template>
    </section>
  </AccountShell>
</template>
