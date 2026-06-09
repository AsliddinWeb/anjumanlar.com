<script setup lang="ts">
import type { ReviewAdminList, ReviewAdminView, ReviewStatus } from "~/types/api";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin"],
});

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const api = useApi();
const toast = useToast();
const { formatDate } = useFormatDate();

useHead({ title: t("admin.reviews.title") });

const PAGE_SIZE = 20;

const queryParams = computed(() => ({
  page: Math.max(1, Number(route.query.page) || 1),
  page_size: PAGE_SIZE,
  status: ((route.query.status as string) || "pending") as ReviewStatus,
}));

const { data: listRaw, pending: loading, refresh } = await useAsyncData(
  "admin:reviews:list",
  () => api<ReviewAdminList>("/admin/reviews", { query: queryParams.value }),
  { server: false, watch: [queryParams] },
);

const list = computed(() => listRaw.value as ReviewAdminList | null);
const allItems = computed<ReviewAdminView[]>(() => list.value?.items ?? []);

const searchQuery = computed(() => (route.query.q as string) || "");
const ratingFilter = computed(() => (route.query.rating as string) || "");
const statusFilter = computed(() => (route.query.status as string) || "pending");

const items = computed<ReviewAdminView[]>(() => {
  const q = searchQuery.value.trim().toLowerCase();
  const r = ratingFilter.value ? Number(ratingFilter.value) : 0;
  return allItems.value.filter((rev) => {
    if (r && rev.rating !== r) return false;
    if (!q) return true;
    return rev.user.full_name.toLowerCase().includes(q)
      || (rev.title ?? "").toLowerCase().includes(q)
      || rev.body.toLowerCase().includes(q);
  });
});

const filtersDirty = computed(() =>
  Boolean(searchQuery.value || ratingFilter.value || statusFilter.value !== "pending"),
);

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

function resetFilters() {
  router.replace({ query: {} });
}

function changePage(page: number) {
  setQuery({ page });
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}

// ---- Approve / reject ----
const actionTarget = ref<{ review: ReviewAdminView; action: "approve" | "reject" } | null>(null);
const deleteTarget = ref<ReviewAdminView | null>(null);
const busy = ref(false);

async function confirmAction() {
  if (!actionTarget.value || busy.value) return;
  const { review, action } = actionTarget.value;
  busy.value = true;
  try {
    const opts: { method: "POST"; body?: Record<string, unknown> } = { method: "POST" };
    if (action === "reject") opts.body = {};
    await api(`/admin/reviews/${review.id}/${action}`, opts);
    if (action === "approve") {
      toast.success(t("admin.reviews.approve_success"));
    }
    else {
      toast.warning(t("admin.reviews.reject_success"));
    }
    actionTarget.value = null;
    await refresh();
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    busy.value = false;
  }
}

async function confirmDelete() {
  if (!deleteTarget.value || busy.value) return;
  const target = deleteTarget.value;
  busy.value = true;
  try {
    await api(`/reviews/${target.id}`, { method: "DELETE" });
    toast.success(t("admin.reviews.delete_success"));
    deleteTarget.value = null;
    await refresh();
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    busy.value = false;
  }
}

const STATUS_TONE: Record<ReviewStatus, "success" | "warning" | "neutral" | "error"> = {
  pending: "warning",
  approved: "success",
  rejected: "error",
};
</script>

<template>
  <section>
    <AdminPageHeader
      :title="t('admin.reviews.title')"
      :description="t('admin.reviews.subtitle')"
      icon="chat"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('admin.reviews.title') },
      ]"
    >
      <template #actions>
        <AdminStatusPill
          v-if="list"
          :tone="statusFilter === 'pending' ? 'warning' : 'info'"
          icon="clipboard-list"
          :label="t('admin.reviews.results', { n: list.total })"
        />
      </template>
    </AdminPageHeader>

    <AdminFilterBar
      :search="searchQuery"
      :search-placeholder="t('admin.reviews.search_placeholder')"
      :dirty="filtersDirty"
      @update:search="(v) => setQuery({ q: v })"
      @reset="resetFilters"
    >
      <UiSelect
        :model-value="statusFilter"
        size="sm"
        :options="[
          { value: 'pending', label: t('admin.reviews.statuses.pending') },
          { value: 'approved', label: t('admin.reviews.statuses.approved') },
          { value: 'rejected', label: t('admin.reviews.statuses.rejected') },
        ]"
        @update:model-value="(v) => setQuery({ status: v })"
      />
      <UiSelect
        :model-value="ratingFilter"
        size="sm"
        :options="[
          { value: '', label: t('admin.reviews.rating_any') },
          { value: '5', label: '★★★★★' },
          { value: '4', label: '★★★★' },
          { value: '3', label: '★★★' },
          { value: '2', label: '★★' },
          { value: '1', label: '★' },
        ]"
        @update:model-value="(v) => setQuery({ rating: v })"
      />
    </AdminFilterBar>

    <div v-if="loading && allItems.length === 0" class="space-y-3">
      <UiSkeleton v-for="i in 3" :key="i" height="7rem" block />
    </div>

    <UiEmptyState
      v-else-if="items.length === 0 && !filtersDirty"
      icon="chat"
      :title="t('admin.reviews.empty_title')"
      :description="t('admin.reviews.empty_body')"
    />

    <UiEmptyState
      v-else-if="items.length === 0"
      icon="search"
      :title="t('admin.filters.no_results')"
      :description="t('admin.filters.no_results_desc')"
    />

    <ul v-else class="space-y-3">
      <li
        v-for="r in items"
        :key="r.id"
        class="rounded-md border border-border bg-bg-card overflow-hidden hover:border-primary/40 transition-colors"
      >
        <div class="p-4 space-y-3">
          <header class="flex items-start justify-between gap-3 flex-wrap">
            <div class="flex items-center gap-3 min-w-0">
              <div
                class="h-9 w-9 rounded-full bg-primary/10 text-primary flex items-center justify-center text-sm font-semibold shrink-0"
              >
                {{ (r.user.full_name || "?").trim().charAt(0).toUpperCase() }}
              </div>
              <div class="min-w-0">
                <div class="text-sm font-medium text-ink truncate">
                  {{ r.user.full_name }}
                </div>
                <div class="text-xs text-ink-tertiary">{{ formatDate(r.created_at) }}</div>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <StarRating :value="r.rating" size="sm" />
              <span
                class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium"
                :class="{
                  'bg-success/10 text-success': STATUS_TONE[r.status] === 'success',
                  'bg-warning/10 text-warning': STATUS_TONE[r.status] === 'warning',
                  'bg-error/10 text-error': STATUS_TONE[r.status] === 'error',
                }"
              >
                {{ t(`admin.reviews.statuses.${r.status}`) }}
              </span>
            </div>
          </header>

          <h3 v-if="r.title" class="font-medium text-ink">{{ r.title }}</h3>
          <p class="text-sm text-ink-secondary whitespace-pre-line leading-relaxed">{{ r.body }}</p>
        </div>

        <footer class="flex flex-wrap items-center gap-2 px-4 py-2.5 bg-bg-secondary/50 border-t border-border">
          <span class="inline-flex items-center gap-1.5 text-xs text-ink-tertiary">
            <Icon name="book" class="h-3.5 w-3.5" />
            <code class="font-mono text-[11px]">{{ r.book_id.slice(0, 8) }}…</code>
          </span>
          <span class="flex-1" />
          <UiButton
            v-if="r.status === 'pending'"
            size="sm"
            variant="ghost"
            :disabled="busy"
            @click="actionTarget = { review: r, action: 'reject' }"
          >
            <Icon name="close" class="h-4 w-4" />
            {{ t("admin.reviews.reject") }}
          </UiButton>
          <UiButton
            v-if="r.status === 'pending'"
            size="sm"
            :disabled="busy"
            @click="actionTarget = { review: r, action: 'approve' }"
          >
            <Icon name="check" class="h-4 w-4" />
            {{ t("admin.reviews.approve") }}
          </UiButton>
          <UiButton
            size="sm"
            variant="ghost"
            class="text-error hover:text-error"
            :disabled="busy"
            @click="deleteTarget = r"
          >
            <Icon name="trash" class="h-4 w-4" />
            {{ t("admin.reviews.delete_button") }}
          </UiButton>
        </footer>
      </li>
    </ul>

    <div v-if="list && list.total > PAGE_SIZE" class="pt-4">
      <UiPagination
        :page="queryParams.page"
        :page-size="PAGE_SIZE"
        :total="list.total"
        @change="changePage"
      />
    </div>

    <AdminConfirmDialog
      :open="!!actionTarget"
      :tone="actionTarget?.action === 'approve' ? 'primary' : 'danger'"
      :icon="actionTarget?.action === 'approve' ? 'check-circle-solid' : 'close'"
      :title="actionTarget?.action === 'approve'
        ? t('admin.reviews.approve_modal_title')
        : t('admin.reviews.reject_modal_title')"
      :description="actionTarget?.action === 'approve'
        ? t('admin.reviews.approve_modal_body')
        : t('admin.reviews.reject_modal_body')"
      :confirm-label="actionTarget?.action === 'approve' ? t('admin.reviews.approve') : t('admin.reviews.reject')"
      :cancel-label="t('admin.actions.cancel')"
      :loading="busy"
      @update:open="(v) => !v && (actionTarget = null)"
      @confirm="confirmAction"
    />

    <AdminConfirmDialog
      :open="!!deleteTarget"
      tone="danger"
      icon="trash"
      :title="t('admin.reviews.delete_modal_title')"
      :description="t('admin.reviews.delete_modal_body')"
      :confirm-label="t('admin.reviews.delete_button')"
      :cancel-label="t('admin.actions.cancel')"
      :loading="busy"
      @update:open="(v) => !v && (deleteTarget = null)"
      @confirm="confirmDelete"
    />
  </section>
</template>
