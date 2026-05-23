<script setup lang="ts">
import type { WithdrawalList, WithdrawalPublic, WithdrawalStatus } from "~/types/api";
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
  { watch: [queryParams] },
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

function statusTone(s: WithdrawalStatus) {
  return (
    {
      requested: "warning",
      approved: "info",
      processing: "info",
      completed: "success",
      rejected: "neutral",
      cancelled: "neutral",
    } as const
  )[s];
}

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

const busy = ref<Set<string>>(new Set());

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

useEscape(() => closeModal(), {
  enabled: computed(() => modalTarget.value !== null),
});

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

// ---- Direct action: mark processing ---------------------------------------
async function markProcessing(target: WithdrawalPublic) {
  if (!confirm(t("admin.withdrawals.process_confirm"))) return;
  if (busy.value.has(target.id)) return;
  busy.value.add(target.id);
  try {
    await api(`/admin/withdrawals/${target.id}/processing`, { method: "POST" });
    await refresh();
  }
  catch {
    // toast in 5.9
  }
  finally {
    busy.value.delete(target.id);
  }
}

const modalTitle = computed(() => {
  if (!modalAction.value) return "";
  return {
    approve: t("admin.withdrawals.modal.approve_title"),
    complete: t("admin.withdrawals.modal.complete_title"),
    reject: t("admin.withdrawals.modal.reject_title"),
  }[modalAction.value];
});

const breadcrumbs = computed(() => [
  { label: t("admin.title"), to: localePath("/admin") },
  { label: t("admin.withdrawals.title") },
]);

const statusOptions = [
  { value: "requested", labelKey: "withdrawals.statuses.requested" },
  { value: "approved", labelKey: "withdrawals.statuses.approved" },
  { value: "processing", labelKey: "withdrawals.statuses.processing" },
  { value: "completed", labelKey: "withdrawals.statuses.completed" },
  { value: "rejected", labelKey: "withdrawals.statuses.rejected" },
  { value: "cancelled", labelKey: "withdrawals.statuses.cancelled" },
];
</script>

<template>
  <section class="space-y-6">
    <UiBreadcrumbs :items="breadcrumbs" />

    <header class="space-y-1">
      <h1 class="font-serif text-2xl text-ink">{{ t("admin.withdrawals.title") }}</h1>
      <p class="text-sm text-ink-secondary">{{ t("admin.withdrawals.subtitle") }}</p>
    </header>

    <div class="flex flex-wrap items-end gap-3">
      <UiSelect
        :model-value="statusFilter"
        :label="t('admin.withdrawals.filter_status')"
        :placeholder="t('admin.withdrawals.filter_status_any')"
        :options="statusOptions.map((s) => ({ value: s.value, label: t(s.labelKey) }))"
        @update:model-value="(v) => setQuery({ status: v })"
      />
      <span class="text-sm text-ink-tertiary ml-auto">
        {{ list?.total ?? 0 }}
      </span>
    </div>

    <div v-if="pending && !list" class="space-y-3">
      <UiSkeleton v-for="i in 3" :key="i" :height="'7rem'" :block="true" />
    </div>

    <UiEmptyState
      v-else-if="(list?.items.length ?? 0) === 0"
      icon="💸"
      :title="t('admin.withdrawals.empty_title')"
      :description="t('admin.withdrawals.empty_body')"
    />

    <ul v-else class="space-y-3">
      <li
        v-for="w in list!.items"
        :key="w.id"
        class="rounded border border-border bg-bg-card p-4 space-y-3"
      >
        <header class="flex items-start justify-between gap-3 flex-wrap">
          <div>
            <div class="font-serif text-lg text-ink">{{ formatPrice(w.amount) }}</div>
            <div class="text-xs text-ink-tertiary">
              {{ t("admin.withdrawals.submitted_at") }}: {{ formatDate(w.created_at) }}
              <span v-if="w.processed_at">
                · {{ t("admin.withdrawals.processed_at") }}: {{ formatDate(w.processed_at) }}
              </span>
            </div>
          </div>
          <UiBadge size="sm" :tone="statusTone(w.status)">
            {{ t(`withdrawals.statuses.${w.status}`) }}
          </UiBadge>
        </header>

        <details class="text-xs text-ink-secondary">
          <summary class="cursor-pointer">
            {{ t("admin.withdrawals.bank_details") }}
          </summary>
          <pre class="mt-2 p-2 rounded bg-bg text-[11px] overflow-x-auto">{{ JSON.stringify(w.bank_details, null, 2) }}</pre>
        </details>

        <p v-if="w.admin_notes" class="text-xs text-ink-secondary">
          📝 {{ w.admin_notes }}
        </p>
        <p v-if="w.transaction_ref" class="text-xs text-ink-tertiary font-mono">
          ref: {{ w.transaction_ref }}
        </p>

        <footer class="flex flex-wrap gap-2 pt-2 border-t border-border">
          <span class="flex-1" />
          <template v-if="w.status === 'requested'">
            <UiButton
              size="sm"
              variant="ghost"
              :disabled="busy.has(w.id)"
              @click="openModal(w, 'reject')"
            >
              {{ t("admin.withdrawals.actions.reject") }}
            </UiButton>
            <UiButton size="sm" :disabled="busy.has(w.id)" @click="openModal(w, 'approve')">
              ✓ {{ t("admin.withdrawals.actions.approve") }}
            </UiButton>
          </template>
          <template v-else-if="w.status === 'approved'">
            <UiButton
              size="sm"
              variant="ghost"
              :disabled="busy.has(w.id)"
              @click="openModal(w, 'reject')"
            >
              {{ t("admin.withdrawals.actions.reject") }}
            </UiButton>
            <UiButton
              size="sm"
              :loading="busy.has(w.id)"
              :disabled="busy.has(w.id)"
              @click="markProcessing(w)"
            >
              → {{ t("admin.withdrawals.actions.mark_processing") }}
            </UiButton>
          </template>
          <template v-else-if="w.status === 'processing'">
            <UiButton size="sm" @click="openModal(w, 'complete')">
              ✓ {{ t("admin.withdrawals.actions.complete") }}
            </UiButton>
          </template>
        </footer>
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

    <!-- Modal -->
    <Teleport v-if="modalTarget" to="body">
      <div
        class="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4"
        role="dialog"
        aria-modal="true"
        @click.self="closeModal"
      >
        <div class="w-full max-w-md rounded bg-bg-card border border-border shadow-xl p-5 space-y-4">
          <header class="space-y-1">
            <h3 class="font-serif text-lg text-ink">{{ modalTitle }}</h3>
            <p class="text-sm text-ink-secondary">
              {{ formatPrice(modalTarget.amount) }}
            </p>
          </header>

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

          <p v-if="modalError" class="text-sm text-error">{{ modalError }}</p>

          <div class="flex justify-end gap-2 pt-1">
            <UiButton variant="ghost" :disabled="modalSubmitting" @click="closeModal">
              {{ t("admin.withdrawals.modal.cancel") }}
            </UiButton>
            <UiButton
              :variant="modalAction === 'reject' ? 'danger' : 'primary'"
              :loading="modalSubmitting"
              :disabled="modalSubmitting"
              @click="submitModal"
            >
              {{ t("admin.withdrawals.modal.submit") }}
            </UiButton>
          </div>
        </div>
      </div>
    </Teleport>
  </section>
</template>
