<script setup lang="ts">
import type { WithdrawalList, WithdrawalPublic, WithdrawalStatus } from "~/types/api";
import type { IconName } from "~/components/ui/Icon.vue";
import { formatPrice } from "~/composables/useLocaleText";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin"],
});

const { t, locale } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const api = useApi();
const toast = useToast();

useHead({ title: t("admin.withdrawals.title") });

const PAGE_SIZE = 20;
const currentPage = computed(() => Math.max(1, Number(route.query.page) || 1));
const statusFilter = computed(() => (route.query.status as string) || "");

const queryParams = computed(() => {
  const params: Record<string, string | number> = {
    page: currentPage.value,
    page_size: PAGE_SIZE,
  };
  if (statusFilter.value) params.status = statusFilter.value;
  return params;
});

const { data: listRaw, pending, refresh } = await useAsyncData(
  "admin:withdrawals",
  () => api<WithdrawalList>("/admin/withdrawals", { query: queryParams.value }),
  { server: false, watch: [queryParams] },
);

const list = computed(() => listRaw.value as WithdrawalList | null);

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

function changePage(page: number) {
  setQuery({ page });
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}

function resetFilters() {
  router.replace({ query: {} });
}

const filtersDirty = computed(() => Boolean(statusFilter.value));

const STATUS_TONE: Record<WithdrawalStatus, "warning" | "info" | "success" | "neutral" | "error"> = {
  requested: "warning",
  approved: "info",
  processing: "info",
  completed: "success",
  rejected: "error",
  cancelled: "neutral",
};

const STATUS_ICON: Record<WithdrawalStatus, IconName> = {
  requested: "inbox",
  approved: "check",
  processing: "arrow-path",
  completed: "check-circle-solid",
  rejected: "close",
  cancelled: "close",
};

const formatDate = (iso: string | null) => {
  if (!iso) return "—";
  return new Intl.DateTimeFormat(locale.value, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
};

const processingBusy = ref<Set<string>>(new Set());
const processingTarget = ref<WithdrawalPublic | null>(null);

async function confirmProcessing() {
  if (!processingTarget.value) return;
  const target = processingTarget.value;
  if (processingBusy.value.has(target.id)) return;
  processingBusy.value.add(target.id);
  try {
    await api(`/admin/withdrawals/${target.id}/processing`, { method: "POST" });
    toast.success(t("admin.withdrawals.process_success"));
    processingTarget.value = null;
    await refresh();
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    processingBusy.value.delete(target.id);
  }
}

// ---- Modal (approve / complete / reject) -----------------------------------
type ActionKind = "approve" | "complete" | "reject";
const modalTarget = ref<WithdrawalPublic | null>(null);
const modalAction = ref<ActionKind | null>(null);
const modalNotes = ref("");
const modalRef = ref("");
const modalSubmitting = ref(false);
const modalError = ref<string | null>(null);

function openModal(target: WithdrawalPublic, action: ActionKind) {
  modalTarget.value = target;
  modalAction.value = action;
  modalNotes.value = target.admin_notes ?? "";
  modalRef.value = target.transaction_ref ?? "";
  modalError.value = null;
}

function closeModal() {
  if (modalSubmitting.value) return;
  modalTarget.value = null;
  modalAction.value = null;
  modalNotes.value = "";
  modalRef.value = "";
  modalError.value = null;
}

async function submitModal() {
  if (!modalTarget.value || !modalAction.value || modalSubmitting.value) return;
  const action = modalAction.value;
  if (action === "complete" && !modalRef.value.trim()) {
    modalError.value = t("admin.withdrawals.modal.transaction_ref_required");
    return;
  }

  modalSubmitting.value = true;
  modalError.value = null;
  try {
    const body: Record<string, unknown> = {};
    if (action === "approve" || action === "reject") {
      body.admin_notes = modalNotes.value.trim() || null;
    }
    else if (action === "complete") {
      body.transaction_ref = modalRef.value.trim();
    }
    await api(`/admin/withdrawals/${modalTarget.value.id}/${action}`, {
      method: "POST",
      body,
    });
    const successKey = `admin.withdrawals.${action}_success`;
    if (action === "reject") toast.warning(t(successKey));
    else toast.success(t(successKey));
    closeModal();
    await refresh();
  }
  catch (err) {
    modalError.value = apiErrorMessage(err, t("common.error"));
  }
  finally {
    modalSubmitting.value = false;
  }
}

const modalConfig = computed(() => {
  if (!modalAction.value) return null;
  const cfg = {
    approve: {
      title: t("admin.withdrawals.modal.approve_title"),
      icon: "check-circle" as IconName,
      tone: "primary" as const,
      submit: t("admin.withdrawals.actions.approve"),
    },
    complete: {
      title: t("admin.withdrawals.modal.complete_title"),
      icon: "check-circle-solid" as IconName,
      tone: "primary" as const,
      submit: t("admin.withdrawals.actions.complete"),
    },
    reject: {
      title: t("admin.withdrawals.modal.reject_title"),
      icon: "close" as IconName,
      tone: "danger" as const,
      submit: t("admin.withdrawals.actions.reject"),
    },
  };
  return cfg[modalAction.value];
});

const statusOptions = [
  { value: "requested", labelKey: "withdrawals.statuses.requested" },
  { value: "approved", labelKey: "withdrawals.statuses.approved" },
  { value: "processing", labelKey: "withdrawals.statuses.processing" },
  { value: "completed", labelKey: "withdrawals.statuses.completed" },
  { value: "rejected", labelKey: "withdrawals.statuses.rejected" },
  { value: "cancelled", labelKey: "withdrawals.statuses.cancelled" },
];

const stats = computed(() => {
  const items = list.value?.items ?? [];
  return {
    pending: items.filter((w) => w.status === "requested").length,
    processing: items.filter((w) => w.status === "processing" || w.status === "approved").length,
  };
});
</script>

<template>
  <section>
    <AdminPageHeader
      :title="t('admin.withdrawals.title')"
      :description="t('admin.withdrawals.subtitle')"
      icon="money"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('admin.withdrawals.title') },
      ]"
    >
      <template #actions>
        <AdminStatusPill
          v-if="stats.pending"
          tone="warning"
          icon="inbox"
          :label="t('admin.withdrawals.queue_pending', { n: stats.pending })"
        />
        <AdminStatusPill
          v-if="stats.processing"
          tone="info"
          icon="arrow-path"
          pulse
          :label="t('admin.withdrawals.queue_processing', { n: stats.processing })"
        />
      </template>
    </AdminPageHeader>

    <AdminFilterBar
      :search="undefined"
      :dirty="filtersDirty"
      @reset="resetFilters"
    >
      <UiSelect
        :model-value="statusFilter"
        size="sm"
        :options="[
          { value: '', label: t('admin.filters.all') },
          ...statusOptions.map((s) => ({ value: s.value, label: t(s.labelKey) })),
        ]"
        @update:model-value="(v) => setQuery({ status: v })"
      />
      <span v-if="list" class="text-xs text-ink-tertiary ml-1">
        {{ t("admin.withdrawals.total", { n: list.total }) }}
      </span>
    </AdminFilterBar>

    <div v-if="pending && !list" class="space-y-3">
      <UiSkeleton v-for="i in 3" :key="i" height="8rem" block />
    </div>

    <UiEmptyState
      v-else-if="(list?.items.length ?? 0) === 0"
      icon="money"
      :title="t('admin.withdrawals.empty_title')"
      :description="t('admin.withdrawals.empty_body')"
    />

    <ul v-else class="space-y-3">
      <li
        v-for="w in list!.items"
        :key="w.id"
        class="rounded-md border border-border bg-bg-card overflow-hidden"
      >
        <div class="p-4 space-y-3">
          <header class="flex items-start justify-between gap-3 flex-wrap">
            <div class="space-y-1">
              <div class="flex items-center gap-2 flex-wrap">
                <div class="font-serif text-xl text-ink">{{ formatPrice(w.amount) }}</div>
                <AdminStatusPill
                  :tone="STATUS_TONE[w.status]"
                  :icon="STATUS_ICON[w.status]"
                  :pulse="w.status === 'processing'"
                  :label="t(`withdrawals.statuses.${w.status}`)"
                />
              </div>
              <div class="text-xs text-ink-tertiary flex flex-wrap gap-x-3 gap-y-0.5">
                <span class="inline-flex items-center gap-1">
                  <Icon name="inbox" class="h-3 w-3" />
                  {{ formatDate(w.created_at) }}
                </span>
                <span v-if="w.processed_at" class="inline-flex items-center gap-1">
                  <Icon name="check" class="h-3 w-3" />
                  {{ formatDate(w.processed_at) }}
                </span>
              </div>
            </div>
          </header>

          <details class="text-xs text-ink-secondary group">
            <summary class="cursor-pointer inline-flex items-center gap-1.5 list-none hover:text-primary transition-colors">
              <Icon name="chevron-down" class="h-3.5 w-3.5 transition-transform group-open:rotate-180" />
              {{ t("admin.withdrawals.bank_details") }}
            </summary>
            <pre class="mt-2 p-3 rounded bg-bg text-[11px] overflow-x-auto border border-border">{{ JSON.stringify(w.bank_details, null, 2) }}</pre>
          </details>

          <div v-if="w.admin_notes || w.transaction_ref" class="space-y-1.5">
            <p v-if="w.admin_notes" class="flex items-start gap-1.5 text-xs text-ink-secondary p-2 rounded bg-bg-secondary">
              <Icon name="pencil" class="h-3.5 w-3.5 mt-0.5 shrink-0 text-warning" />
              <span class="whitespace-pre-line">{{ w.admin_notes }}</span>
            </p>
            <p v-if="w.transaction_ref" class="inline-flex items-center gap-1.5 text-xs text-ink-tertiary font-mono">
              <Icon name="key" class="h-3.5 w-3.5" />
              {{ w.transaction_ref }}
            </p>
          </div>
        </div>

        <footer class="flex flex-wrap gap-2 px-4 py-2.5 bg-bg-secondary/50 border-t border-border">
          <span class="flex-1" />
          <template v-if="w.status === 'requested'">
            <UiButton size="sm" variant="ghost" @click="openModal(w, 'reject')">
              <Icon name="close" class="h-4 w-4" />
              {{ t("admin.withdrawals.actions.reject") }}
            </UiButton>
            <UiButton size="sm" @click="openModal(w, 'approve')">
              <Icon name="check" class="h-4 w-4" />
              {{ t("admin.withdrawals.actions.approve") }}
            </UiButton>
          </template>
          <template v-else-if="w.status === 'approved'">
            <UiButton size="sm" variant="ghost" @click="openModal(w, 'reject')">
              <Icon name="close" class="h-4 w-4" />
              {{ t("admin.withdrawals.actions.reject") }}
            </UiButton>
            <UiButton size="sm" @click="processingTarget = w">
              <Icon name="arrow-right" class="h-4 w-4" />
              {{ t("admin.withdrawals.actions.mark_processing") }}
            </UiButton>
          </template>
          <template v-else-if="w.status === 'processing'">
            <UiButton size="sm" @click="openModal(w, 'complete')">
              <Icon name="check-circle-solid" class="h-4 w-4" />
              {{ t("admin.withdrawals.actions.complete") }}
            </UiButton>
          </template>
        </footer>
      </li>
    </ul>

    <div v-if="list && list.total > PAGE_SIZE" class="pt-4">
      <UiPagination
        :page="currentPage"
        :page-size="PAGE_SIZE"
        :total="list.total"
        @change="changePage"
      />
    </div>

    <AdminConfirmDialog
      :open="!!processingTarget"
      tone="primary"
      icon="arrow-right"
      :title="t('admin.withdrawals.process_title')"
      :description="processingTarget ? t('admin.withdrawals.process_body', { amount: formatPrice(processingTarget.amount) }) : ''"
      :confirm-label="t('admin.withdrawals.actions.mark_processing')"
      :cancel-label="t('admin.actions.cancel')"
      :loading="processingTarget ? processingBusy.has(processingTarget.id) : false"
      @update:open="(v) => !v && (processingTarget = null)"
      @confirm="confirmProcessing"
    />

    <AdminConfirmDialog
      :open="!!modalTarget"
      :tone="modalConfig?.tone ?? 'primary'"
      :icon="modalConfig?.icon"
      :title="modalConfig?.title ?? ''"
      :description="modalTarget ? formatPrice(modalTarget.amount) : ''"
      :confirm-label="modalConfig?.submit ?? ''"
      :cancel-label="t('admin.actions.cancel')"
      :loading="modalSubmitting"
      :disabled="modalAction === 'complete' && !modalRef.trim()"
      @update:open="(v) => !v && closeModal()"
      @cancel="closeModal"
      @confirm="submitModal"
    >
      <label v-if="modalAction === 'approve' || modalAction === 'reject'" class="block">
        <span class="block text-sm text-ink-secondary mb-1">
          {{ t("admin.withdrawals.modal.admin_notes") }}
        </span>
        <textarea
          v-model="modalNotes"
          rows="3"
          maxlength="2000"
          :placeholder="t('admin.withdrawals.modal.admin_notes_placeholder')"
          class="w-full px-3 py-2 rounded border border-border bg-bg text-ink placeholder:text-ink-tertiary focus:outline-none focus:border-primary text-sm"
        />
      </label>

      <UiInput
        v-if="modalAction === 'complete'"
        v-model="modalRef"
        :label="t('admin.withdrawals.modal.transaction_ref')"
        :placeholder="t('admin.withdrawals.modal.transaction_ref_placeholder')"
        required
      />

      <p v-if="modalError" class="mt-2 flex items-center gap-1.5 text-sm text-error">
        <Icon name="warning-solid" class="h-4 w-4" />
        {{ modalError }}
      </p>
    </AdminConfirmDialog>
  </section>
</template>
