<script setup lang="ts">
import type { ReviewRequestPublic, ReviewRequestStatus } from "~/types/api";
import { apiErrorMessage } from "~/composables/useAuth";
import { formatPrice } from "~/composables/useLocaleText";

definePageMeta({ middleware: "auth" });

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const api = useApi();
const toast = useToast();
const { user } = useAuth();
const { formatDate } = useFormatDate();

const requestId = computed(() => route.params.id as string);

const { data: rRaw, refresh } = await useAsyncData(
  `account:review-request:${requestId.value}`,
  () => api<ReviewRequestPublic>(`/review-requests/${requestId.value}`),
  { server: false },
);
const r = computed(() => rRaw.value as ReviewRequestPublic | null);

useHead({
  title: computed(() => r.value
    ? `${t("review_requests.detail_title")} — ${r.value.author.display_name}`
    : t("review_requests.detail_title"),
  ),
});

const isRequester = computed(() => Boolean(user.value && r.value && r.value.requester.id === user.value.id));
const STATUS_TONE: Record<ReviewRequestStatus, string> = {
  pending: "bg-bg-secondary text-ink-tertiary",
  quoted: "bg-warning/10 text-warning",
  paid: "bg-info/10 text-info",
  completed: "bg-success/10 text-success",
  cancelled: "bg-error/10 text-error",
};

// ---- Manuscript upload (requester only) ----
const fileInput = ref<HTMLInputElement | null>(null);
const uploading = ref(false);

async function onPickManuscript(e: Event) {
  if (!r.value) return;
  const file = (e.target as HTMLInputElement).files?.[0];
  if (!file) return;
  if (file.size > 100 * 1024 * 1024) {
    toast.error(t("account_books.upload.size_too_large"));
    return;
  }
  uploading.value = true;
  try {
    const fd = new FormData();
    fd.append("file", file);
    await api(`/review-requests/${r.value.id}/manuscript`, { method: "POST", body: fd });
    toast.success(t("review_requests.success.manuscript_uploaded"));
    await refresh();
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    uploading.value = false;
    if (fileInput.value) fileInput.value.value = "";
  }
}

// ---- Pay (requester only, status=quoted) ----
const payOpen = ref(false);
const paying = ref(false);
async function confirmPay() {
  if (!r.value) return;
  paying.value = true;
  try {
    await api(`/review-requests/${r.value.id}/pay`, { method: "POST" });
    toast.success(t("review_requests.success.paid"));
    payOpen.value = false;
    await refresh();
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    paying.value = false;
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
    await api(`/review-requests/${r.value.id}/cancel`, {
      method: "POST",
      body: { reason: cancelReason.value.trim() || null },
    });
    toast.success(t("review_requests.success.cancelled"));
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

const canUploadManuscript = computed(() =>
  isRequester.value && r.value && ["pending", "quoted"].includes(r.value.status),
);
const canPay = computed(() => isRequester.value && r.value?.status === "quoted");
const canCancel = computed(() =>
  r.value && !["completed", "cancelled"].includes(r.value.status),
);
</script>

<template>
  <AccountShell>
    <section v-if="r" class="space-y-5">
      <nav class="text-xs text-ink-tertiary flex items-center gap-1.5">
        <NuxtLink :to="localePath('/account/review-requests')" class="hover:text-primary">
          {{ t("review_requests.detail_back") }}
        </NuxtLink>
      </nav>

      <header class="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h1 class="font-serif text-2xl md:text-3xl text-ink leading-tight">
            {{ t("review_requests.detail_title") }}
          </h1>
          <p class="text-sm text-ink-secondary mt-1">
            <Icon name="user-circle" class="inline h-4 w-4 align-text-bottom mr-1" />
            {{ r.author.display_name }}
            <span class="text-ink-tertiary mx-1">·</span>
            {{ formatDate(r.created_at) }}
          </p>
        </div>
        <span
          class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium"
          :class="STATUS_TONE[r.status]"
        >
          {{ t(`review_requests.statuses.${r.status}`) }}
        </span>
      </header>

      <!-- Quote awaiting payment -->
      <div
        v-if="r.status === 'quoted' && canPay"
        class="rounded-md border border-warning/30 bg-warning/5 p-4 flex flex-wrap items-center gap-3"
      >
        <Icon name="currency" class="h-5 w-5 text-warning shrink-0" />
        <div class="min-w-0 flex-1">
          <h3 class="font-medium text-ink">
            {{ t("review_requests.actions.pay") }} —
            <span class="text-primary tabular-nums">{{ formatPrice(r.final_price || 0) }}</span>
          </h3>
          <p class="text-xs text-ink-tertiary mt-0.5">{{ t("review_requests.pay_hint") }}</p>
        </div>
        <UiButton @click="payOpen = true">
          <Icon name="currency" class="h-4 w-4" />
          {{ t("review_requests.actions.pay") }}
        </UiButton>
      </div>

      <!-- Completed review -->
      <div
        v-if="r.status === 'completed' && r.review_text"
        class="rounded-md border border-success/30 bg-success/5 p-5 space-y-3"
      >
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

      <!-- Cancellation reason -->
      <p v-if="r.status === 'cancelled' && r.cancellation_reason" class="rounded-md border border-error/20 bg-error/5 p-3 text-sm text-error">
        <strong>{{ t("review_requests.fields.cancellation_reason") }}:</strong> {{ r.cancellation_reason }}
      </p>

      <!-- Meta + manuscript -->
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
            <div class="text-xs text-ink-tertiary">{{ t("review_requests.manuscript_hint") }}</div>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <UiButton
              v-if="canUploadManuscript"
              variant="ghost"
              size="sm"
              :loading="uploading"
              @click="fileInput?.click()"
            >
              <Icon name="upload" class="h-4 w-4" />
              {{ r.manuscript_url
                ? t("review_requests.actions.replace_manuscript")
                : t("review_requests.actions.upload_manuscript") }}
            </UiButton>
            <a
              v-if="r.manuscript_url"
              :href="r.manuscript_url"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center gap-1 text-xs text-primary hover:underline"
            >
              <Icon name="external" class="h-3 w-3" />
              {{ t("review_requests.actions.download_manuscript") }}
            </a>
          </div>
          <input
            ref="fileInput"
            type="file"
            accept="application/pdf"
            class="sr-only"
            @change="onPickManuscript"
          >
        </div>

        <dl class="grid sm:grid-cols-3 gap-3 pt-2 text-sm">
          <div v-if="r.proposed_price != null">
            <dt class="text-xs uppercase tracking-wider text-ink-tertiary">{{ t("review_requests.fields.proposed_price") }}</dt>
            <dd class="text-ink mt-0.5">{{ formatPrice(r.proposed_price) }}</dd>
          </div>
          <div v-if="r.final_price != null">
            <dt class="text-xs uppercase tracking-wider text-ink-tertiary">{{ t("review_requests.fields.final_price") }}</dt>
            <dd class="text-ink mt-0.5 tabular-nums">{{ formatPrice(r.final_price) }}</dd>
          </div>
        </dl>

        <div v-if="r.notes" class="space-y-1 pt-2">
          <h3 class="text-xs uppercase tracking-wider text-ink-tertiary">{{ t("review_requests.fields.notes") }}</h3>
          <p class="text-sm text-ink whitespace-pre-line">{{ r.notes }}</p>
        </div>
      </div>

      <div class="flex justify-end">
        <UiButton v-if="canCancel" variant="ghost" class="text-error hover:text-error" @click="cancelOpen = true">
          <Icon name="close" class="h-4 w-4" />
          {{ t("review_requests.actions.cancel") }}
        </UiButton>
      </div>

      <AdminConfirmDialog
        :open="payOpen"
        tone="primary"
        icon="currency"
        :title="t('review_requests.pay_modal_title')"
        :description="t('review_requests.pay_modal_body', { price: r.final_price != null ? formatPrice(r.final_price) : '—' })"
        :confirm-label="t('review_requests.pay_modal_button')"
        :cancel-label="t('common.cancel')"
        :loading="paying"
        @update:open="(v) => (payOpen = v)"
        @confirm="confirmPay"
      />

      <AdminConfirmDialog
        :open="cancelOpen"
        tone="danger"
        icon="close"
        :title="t('review_requests.cancel_modal_title')"
        :description="t('review_requests.cancel_modal_body')"
        :confirm-label="t('review_requests.actions.cancel')"
        :cancel-label="t('common.cancel')"
        :loading="cancelling"
        @update:open="(v) => { cancelOpen = v; if (!v) cancelReason = ''; }"
        @confirm="confirmCancel"
      >
        <label class="block">
          <span class="block text-sm text-ink-secondary mb-1">{{ t("review_requests.cancel_reason") }}</span>
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
  </AccountShell>
</template>
