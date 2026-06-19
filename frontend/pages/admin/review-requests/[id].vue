<script setup lang="ts">
import type { ReviewRequestPublic, ReviewRequestStatus } from "~/types/api";
import { apiErrorMessage } from "~/composables/useAuth";
import { formatPrice } from "~/composables/useLocaleText";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin"],
});

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const api = useApi();
const toast = useToast();
const { localised } = useLocaleText();
const { formatDate } = useFormatDate();

const requestId = computed(() => route.params.id as string);

const { data: rRaw, refresh } = await useAsyncData(
  `admin:review-request:${requestId.value}`,
  () => api<ReviewRequestPublic>(`/admin/review-requests/${requestId.value}`),
  { server: false },
);
const r = computed(() => rRaw.value as ReviewRequestPublic | null);

useHead({
  title: computed(() => r.value
    ? `${t("review_requests.detail_title")} — ${r.value.requester.full_name}`
    : t("review_requests.detail_title"),
  ),
});

const STATUS_TONE: Record<ReviewRequestStatus, string> = {
  pending: "bg-bg-secondary text-ink-tertiary",
  quoted: "bg-warning/10 text-warning",
  paid: "bg-info/10 text-info",
  completed: "bg-success/10 text-success",
  cancelled: "bg-error/10 text-error",
};

// ---- Quote (set final price) ----
const quoteOpen = ref(false);
const quotePrice = ref("");
const quoting = ref(false);

function openQuote() {
  if (r.value?.final_price != null) {
    quotePrice.value = String(r.value.final_price);
  }
  quoteOpen.value = true;
}

async function confirmQuote() {
  if (!r.value) return;
  const price = Number(quotePrice.value);
  if (!Number.isFinite(price) || price < 0) {
    toast.error(t("admin.review_requests.errors.invalid_price"));
    return;
  }
  quoting.value = true;
  try {
    await api(`/admin/review-requests/${r.value.id}/quote`, {
      method: "POST",
      body: { final_price: price },
    });
    toast.success(t("admin.review_requests.success.quoted"));
    quoteOpen.value = false;
    quotePrice.value = "";
    await refresh();
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    quoting.value = false;
  }
}

// ---- Mark paid (manual stub) ----
const marking = ref(false);
async function markPaid() {
  if (!r.value || marking.value) return;
  marking.value = true;
  try {
    await api(`/admin/review-requests/${r.value.id}/mark-paid`, { method: "POST" });
    toast.success(t("admin.review_requests.success.paid"));
    await refresh();
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    marking.value = false;
  }
}

// ---- Submit review ----
const submitOpen = ref(false);
const reviewText = ref("");
const reviewFile = ref<File | null>(null);
const submitting = ref(false);

function onPickReviewFile(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0] ?? null;
  reviewFile.value = file;
}

async function confirmSubmit() {
  if (!r.value) return;
  if (!reviewText.value.trim()) {
    toast.error(t("admin.review_requests.errors.review_required"));
    return;
  }
  submitting.value = true;
  try {
    const fd = new FormData();
    fd.append("review_text", reviewText.value.trim());
    if (reviewFile.value) fd.append("file", reviewFile.value);
    await api(`/admin/review-requests/${r.value.id}/submit-review`, {
      method: "POST",
      body: fd,
    });
    toast.success(t("admin.review_requests.success.submitted"));
    submitOpen.value = false;
    reviewText.value = "";
    reviewFile.value = null;
    await refresh();
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    submitting.value = false;
  }
}

// ---- Cancel ----
const cancelOpen = ref(false);
const cancelReason = ref("");
const cancelling = ref(false);

async function confirmCancel() {
  if (!r.value) return;
  cancelling.value = true;
  try {
    await api(`/admin/review-requests/${r.value.id}/cancel`, {
      method: "POST",
      body: { reason: cancelReason.value.trim() || null },
    });
    toast.success(t("admin.review_requests.success.cancelled"));
    cancelOpen.value = false;
    cancelReason.value = "";
    await refresh();
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    cancelling.value = false;
  }
}

const canQuote = computed(() => r.value && ["pending", "quoted"].includes(r.value.status));
const canMarkPaid = computed(() => r.value?.status === "quoted" && r.value?.final_price != null);
const canSubmitReview = computed(() => r.value?.status === "paid");
const canCancel = computed(() => r.value && !["completed", "cancelled"].includes(r.value.status));
</script>

<template>
  <section v-if="r" class="space-y-5">
    <AdminPageHeader
      :title="t('review_requests.detail_title')"
      :description="r.requester.full_name"
      icon="chat"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('review_requests.title'), to: localePath('/admin/review-requests') },
        { label: t('review_requests.detail_title') },
      ]"
    >
      <template #actions>
        <span
          class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium"
          :class="STATUS_TONE[r.status]"
        >
          {{ t(`review_requests.statuses.${r.status}`) }}
        </span>
      </template>
    </AdminPageHeader>

    <!-- Meta strip -->
    <div class="rounded-md border border-border bg-bg-card p-4 grid sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs">
      <div>
        <dt class="text-ink-tertiary uppercase tracking-wide text-[10px]">{{ t("review_requests.fields.requester") }}</dt>
        <dd class="text-ink mt-0.5">
          {{ r.requester.full_name }}
          <span class="block text-ink-tertiary text-[11px]">{{ r.requester.email }}</span>
        </dd>
      </div>
      <div>
        <dt class="text-ink-tertiary uppercase tracking-wide text-[10px]">{{ t("review_requests.fields.category") }}</dt>
        <dd class="text-ink mt-0.5">
          {{ r.category ? localised(r.category.name, r.category.slug) : "—" }}
        </dd>
      </div>
      <div>
        <dt class="text-ink-tertiary uppercase tracking-wide text-[10px]">{{ t("review_requests.fields.international") }}</dt>
        <dd class="text-ink mt-0.5">
          <span v-if="r.is_international" class="inline-flex items-center gap-1 text-primary">
            <Icon name="sparkles" class="h-3.5 w-3.5" />
            {{ t("common.yes") }}
          </span>
          <span v-else class="text-ink-tertiary">{{ t("common.no") }}</span>
        </dd>
      </div>
      <div>
        <dt class="text-ink-tertiary uppercase tracking-wide text-[10px]">{{ t("review_requests.fields.created_at") }}</dt>
        <dd class="text-ink mt-0.5">{{ formatDate(r.created_at) }}</dd>
      </div>
    </div>

    <!-- Workflow actions -->
    <div class="grid md:grid-cols-3 gap-3">
      <!-- Quote -->
      <div class="rounded-md border border-border bg-bg-card p-4 space-y-3">
        <div class="flex items-center gap-2">
          <Icon name="currency" class="h-5 w-5 text-primary" />
          <h3 class="font-medium text-ink">{{ t("admin.review_requests.section_quote") }}</h3>
        </div>
        <p v-if="r.final_price != null" class="text-2xl font-serif text-primary tabular-nums">
          {{ formatPrice(r.final_price) }}
        </p>
        <p v-else class="text-sm text-ink-tertiary">{{ t("admin.review_requests.not_quoted_yet") }}</p>
        <UiButton size="sm" :disabled="!canQuote" @click="openQuote">
          <Icon name="pencil" class="h-3.5 w-3.5" />
          {{ r.final_price != null ? t("admin.review_requests.actions.update_quote") : t("admin.review_requests.actions.set_quote") }}
        </UiButton>
      </div>

      <!-- Mark paid -->
      <div class="rounded-md border border-border bg-bg-card p-4 space-y-3">
        <div class="flex items-center gap-2">
          <Icon name="check-circle" class="h-5 w-5 text-info" />
          <h3 class="font-medium text-ink">{{ t("admin.review_requests.section_paid") }}</h3>
        </div>
        <p v-if="r.paid_at" class="text-sm text-ink">{{ formatDate(r.paid_at) }}</p>
        <p v-else class="text-sm text-ink-tertiary">{{ t("admin.review_requests.not_paid_yet") }}</p>
        <UiButton size="sm" variant="ghost" :disabled="!canMarkPaid" :loading="marking" @click="markPaid">
          <Icon name="check" class="h-3.5 w-3.5" />
          {{ t("admin.review_requests.actions.mark_paid") }}
        </UiButton>
      </div>

      <!-- Submit review -->
      <div class="rounded-md border border-border bg-bg-card p-4 space-y-3">
        <div class="flex items-center gap-2">
          <Icon name="document" class="h-5 w-5 text-success" />
          <h3 class="font-medium text-ink">{{ t("admin.review_requests.section_review") }}</h3>
        </div>
        <p v-if="r.review_text" class="text-sm text-ink-tertiary line-clamp-2">{{ r.review_text }}</p>
        <p v-else class="text-sm text-ink-tertiary">{{ t("admin.review_requests.no_review_yet") }}</p>
        <UiButton size="sm" :disabled="!canSubmitReview" @click="submitOpen = true">
          <Icon name="upload" class="h-3.5 w-3.5" />
          {{ t("admin.review_requests.actions.submit_review") }}
        </UiButton>
      </div>
    </div>

    <!-- Manuscript + notes -->
    <div class="rounded-md border border-border bg-bg-card p-5 space-y-4">
      <h2 class="text-sm uppercase tracking-wider text-ink-tertiary">
        {{ t("review_requests.section_manuscript") }}
      </h2>
      <div class="flex flex-wrap items-center gap-3">
        <div class="h-14 w-12 rounded border border-border bg-bg-secondary flex items-center justify-center shrink-0">
          <Icon :name="r.manuscript_url ? 'document' : 'inbox'" class="h-5 w-5" :class="r.manuscript_url ? 'text-primary' : 'text-ink-tertiary'" />
        </div>
        <div class="flex-1 min-w-0">
          <div class="text-sm text-ink truncate">
            {{ r.manuscript_filename || (r.manuscript_url ? "manuscript.pdf" : t("account_books.upload.no_file")) }}
          </div>
        </div>
        <a
          v-if="r.manuscript_url"
          :href="r.manuscript_url"
          target="_blank"
          rel="noopener noreferrer"
          class="inline-flex items-center gap-1 text-sm text-primary hover:underline"
        >
          <Icon name="external" class="h-3.5 w-3.5" />
          {{ t("review_requests.actions.download_manuscript") }}
        </a>
      </div>

      <div v-if="r.notes" class="space-y-1 pt-2">
        <h3 class="text-xs uppercase tracking-wider text-ink-tertiary">{{ t("review_requests.fields.notes") }}</h3>
        <p class="text-sm text-ink whitespace-pre-line">{{ r.notes }}</p>
      </div>
    </div>

    <!-- Completed review preview -->
    <div v-if="r.status === 'completed' && r.review_text" class="rounded-md border border-success/30 bg-success/5 p-5 space-y-3">
      <h3 class="font-medium text-ink inline-flex items-center gap-2">
        <Icon name="check-circle-solid" class="h-5 w-5 text-success" />
        {{ t("review_requests.fields.review_text") }}
      </h3>
      <p class="text-sm text-ink leading-relaxed whitespace-pre-line">{{ r.review_text }}</p>
      <a
        v-if="r.review_file_url"
        :href="r.review_file_url"
        target="_blank"
        rel="noopener noreferrer"
        class="inline-flex items-center gap-1.5 text-sm text-primary hover:underline"
      >
        <Icon name="document" class="h-4 w-4" />
        {{ t("review_requests.actions.download_review_file") }}
      </a>
    </div>

    <div class="flex justify-end">
      <UiButton v-if="canCancel" variant="ghost" class="text-error hover:text-error" @click="cancelOpen = true">
        <Icon name="close" class="h-4 w-4" />
        {{ t("admin.review_requests.actions.cancel") }}
      </UiButton>
    </div>

    <!-- Quote modal -->
    <AdminConfirmDialog
      :open="quoteOpen"
      tone="primary"
      icon="currency"
      :title="t('admin.review_requests.quote_modal_title')"
      :confirm-label="t('admin.actions.save')"
      :cancel-label="t('common.cancel')"
      :loading="quoting"
      @update:open="(v) => (quoteOpen = v)"
      @confirm="confirmQuote"
    >
      <UiInput
        v-model="quotePrice"
        type="number"
        :label="t('admin.review_requests.quote_price_field')"
        :hint="t('admin.review_requests.quote_price_hint')"
      />
    </AdminConfirmDialog>

    <!-- Submit review modal -->
    <AdminConfirmDialog
      :open="submitOpen"
      tone="primary"
      icon="document"
      :title="t('admin.review_requests.submit_modal_title')"
      :confirm-label="t('admin.review_requests.actions.submit_review')"
      :cancel-label="t('common.cancel')"
      :loading="submitting"
      @update:open="(v) => (submitOpen = v)"
      @confirm="confirmSubmit"
    >
      <label class="block mb-3">
        <span class="block text-sm text-ink-secondary mb-1">{{ t("admin.review_requests.review_text_field") }}</span>
        <textarea
          v-model="reviewText"
          rows="8"
          maxlength="20000"
          class="w-full px-3 py-2 rounded border border-border bg-bg text-sm text-ink focus:outline-none focus:border-primary"
        />
      </label>
      <label class="block">
        <span class="block text-sm text-ink-secondary mb-1">{{ t("admin.review_requests.review_file_field") }}</span>
        <input
          type="file"
          accept="application/pdf"
          class="block w-full text-sm text-ink"
          @change="onPickReviewFile"
        >
        <span class="block text-xs text-ink-tertiary mt-1">{{ t("admin.review_requests.review_file_hint") }}</span>
      </label>
    </AdminConfirmDialog>

    <!-- Cancel modal -->
    <AdminConfirmDialog
      :open="cancelOpen"
      tone="danger"
      icon="close"
      :title="t('admin.review_requests.cancel_modal_title')"
      :description="t('admin.review_requests.cancel_modal_body')"
      :confirm-label="t('admin.review_requests.actions.cancel')"
      :cancel-label="t('common.cancel')"
      :loading="cancelling"
      @update:open="(v) => { cancelOpen = v; if (!v) cancelReason = ''; }"
      @confirm="confirmCancel"
    >
      <label class="block">
        <span class="block text-sm text-ink-secondary mb-1">{{ t("admin.review_requests.cancel_reason_field") }}</span>
        <textarea
          v-model="cancelReason"
          rows="3"
          class="w-full px-3 py-2 rounded border border-border bg-bg text-sm text-ink focus:outline-none focus:border-primary"
        />
      </label>
    </AdminConfirmDialog>
  </section>
  <section v-else class="space-y-3">
    <UiSkeleton height="3rem" block />
    <UiSkeleton height="12rem" block />
  </section>
</template>
