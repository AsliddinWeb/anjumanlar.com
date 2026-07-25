<script setup lang="ts">
import type { BookOwnerList, BookOwnerView, BookStatus } from "~/types/api";
import type { Column } from "~/components/admin/AdminDataTable.vue";
import { apiErrorMessage } from "~/composables/useAuth";
import { formatPrice } from "~/composables/useLocaleText";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin", "admin-scope"],
  adminScope: "books",
});

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const api = useApi();
const toast = useToast();
const { localised } = useLocaleText();
const { formatDate } = useFormatDate();

useHead({ title: t("admin.books.title") });

const PAGE_SIZE = 20;

const sort = computed(() => (route.query.sort as string) || "-created_at");

const queryParams = computed(() => ({
  page: Math.max(1, Number(route.query.page) || 1),
  page_size: PAGE_SIZE,
  search: ((route.query.q as string) || "").trim() || undefined,
  status: ((route.query.status as string) || undefined) as BookStatus | undefined,
  sort: sort.value,
}));

const { data: listRaw, pending, refresh } = await useAsyncData(
  "admin:books:list",
  () => api<BookOwnerList>("/books/admin/all", { query: queryParams.value }),
  { server: false, watch: [queryParams] },
);

const list = computed(() => listRaw.value as BookOwnerList | null);
const items = computed<BookOwnerView[]>(() => list.value?.items ?? []);

const filtersDirty = computed(() => Boolean(route.query.q || route.query.status));

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

const STATUS_TONE: Record<BookStatus, "success" | "warning" | "neutral" | "error" | "info"> = {
  draft: "neutral",
  pending: "warning",
  approved: "success",
  rejected: "error",
  archived: "neutral",
};

// ---- Delete ----
const deleteTarget = ref<BookOwnerView | null>(null);
const deleting = ref(false);

async function confirmDelete() {
  if (!deleteTarget.value || deleting.value) return;
  const target = deleteTarget.value;
  deleting.value = true;
  try {
    await api(`/books/${target.id}`, { method: "DELETE" });
    toast.success(t("admin.books.delete_success"));
    deleteTarget.value = null;
    await refresh();
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    deleting.value = false;
  }
}

// ---- Bulk selection ----
const selected = ref<(string | number)[]>([]);

watch(items, (newItems) => {
  const ids = new Set<string | number>(newItems.map((b) => b.id));
  selected.value = selected.value.filter((id) => ids.has(id));
});

function isPendingRow(row: BookOwnerView) {
  return row.status === "pending";
}

const selectedBooks = computed(() => items.value.filter((b) => selected.value.includes(b.id)));

const bulkAction = ref<"approve" | "reject" | null>(null);
const bulkReason = ref("");
const bulkReasonError = ref<string | null>(null);
const bulkBusy = ref(false);

function closeBulkDialog(open: boolean) {
  if (open) return;
  bulkAction.value = null;
  bulkReason.value = "";
  bulkReasonError.value = null;
}

async function confirmBulkAction() {
  if (!bulkAction.value || bulkBusy.value) return;
  if (bulkAction.value === "reject" && !bulkReason.value.trim()) {
    bulkReasonError.value = t("admin.bulk.reject_reason_required");
    return;
  }
  bulkBusy.value = true;
  const targets = selectedBooks.value;
  const results = await Promise.allSettled(
    targets.map((b) =>
      bulkAction.value === "approve"
        ? api(`/books/admin/${b.id}/approve`, { method: "POST" })
        : api(`/books/admin/${b.id}/reject`, { method: "POST", body: { reason: bulkReason.value.trim() } }),
    ),
  );
  const ok = results.filter((r) => r.status === "fulfilled").length;
  const fail = results.length - ok;
  if (fail === 0) toast.success(t("admin.bulk.done_success", { n: ok }));
  else toast.warning(t("admin.bulk.done_partial", { ok, fail }));
  selected.value = [];
  bulkBusy.value = false;
  closeBulkDialog(false);
  await refresh();
}

// ---- Excel export (walks every page of the current filter) ----
const exporting = ref(false);

async function exportExcel() {
  if (exporting.value) return;
  exporting.value = true;
  try {
    const all = await fetchAllPages<BookOwnerView>(
      (page, page_size) => api<BookOwnerList>("/books/admin/all", { query: { ...queryParams.value, page, page_size } }),
      100,
    );
    const rows = all.map((b) => ({
      [t("account_books.table.title_col")]: localised(b.title, b.slug),
      [t("admin.books.author_field")]: b.author.display_name,
      [t("account_books.table.status")]: t(`account_books.status.${b.status}`),
      [t("account_books.table.price")]: b.price,
      [t("account_books.table.updated_at")]: formatDate(b.created_at, { withTime: false }),
    }));
    await exportToExcel(`monografiya-books-${new Date().toISOString().slice(0, 10)}`, "Kitoblar", rows);
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    exporting.value = false;
  }
}

const columns: Column<BookOwnerView>[] = [
  { key: "title", label: t("account_books.table.title_col") },
  { key: "status", label: t("account_books.table.status"), align: "center", width: "w-32" },
  { key: "price", label: t("account_books.table.price"), align: "right", width: "w-28", mobileHidden: true, sortKey: "price" },
  { key: "created", label: t("account_books.table.updated_at"), width: "w-32", mobileHidden: true, sortKey: "created_at" },
];
</script>

<template>
  <section>
    <AdminPageHeader
      :title="t('admin.books.title')"
      :description="t('admin.books.subtitle')"
      icon="book"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('admin.books.title') },
      ]"
    >
      <template #actions>
        <AdminStatusPill
          v-if="list"
          tone="info"
          icon="book"
          :label="t('admin.books.results', { n: list.total })"
        />
        <UiButton variant="ghost" size="sm" :loading="exporting" @click="exportExcel">
          <Icon name="document" class="h-3.5 w-3.5" />
          {{ t('admin.finance.export_excel') }}
        </UiButton>
        <UiButton :to="localePath('/admin/books/new')">
          <Icon name="plus" class="h-4 w-4" />
          {{ t('admin.books.new_button') }}
        </UiButton>
      </template>
    </AdminPageHeader>

    <AdminFilterBar
      :search="(route.query.q as string) || ''"
      :search-placeholder="t('admin.books.search_placeholder')"
      :dirty="filtersDirty"
      @update:search="(v) => setQuery({ q: v })"
      @reset="resetFilters"
    >
      <UiSelect
        :model-value="(route.query.status as string) || ''"
        size="sm"
        :options="[
          { value: '', label: t('admin.books.filter_status_any') },
          { value: 'draft', label: t('account_books.status.draft') },
          { value: 'pending', label: t('account_books.status.pending') },
          { value: 'approved', label: t('account_books.status.approved') },
          { value: 'rejected', label: t('account_books.status.rejected') },
          { value: 'archived', label: t('account_books.status.archived') },
        ]"
        @update:model-value="(v) => setQuery({ status: v })"
      />
    </AdminFilterBar>

    <div
      v-if="selected.length > 0"
      class="flex items-center gap-3 mb-3 px-3 py-2 rounded-md border border-primary/30 bg-primary/5"
    >
      <span class="text-sm text-ink">{{ t('admin.bulk.selected_count', { n: selected.length }) }}</span>
      <span class="flex-1" />
      <UiButton size="sm" variant="ghost" @click="selected = []">
        {{ t('admin.bulk.clear') }}
      </UiButton>
      <UiButton size="sm" variant="ghost" @click="bulkAction = 'reject'">
        <Icon name="close" class="h-4 w-4" />
        {{ t('admin.bulk.reject_selected') }}
      </UiButton>
      <UiButton size="sm" @click="bulkAction = 'approve'">
        <Icon name="check" class="h-4 w-4" />
        {{ t('admin.bulk.approve_selected') }}
      </UiButton>
    </div>

    <AdminDataTable
      :columns="columns"
      :rows="items"
      :row-key="(r) => r.id"
      :loading="pending"
      selectable
      :selected="selected"
      :is-selectable="isPendingRow"
      :sort="sort"
      :empty="{
        icon: 'book',
        title: filtersDirty ? t('admin.filters.no_results') : t('admin.books.empty_title'),
        description: filtersDirty ? t('admin.filters.no_results_desc') : t('admin.books.empty_body'),
      }"
      @update:selected="(v) => (selected = v)"
      @update:sort="(v) => setQuery({ sort: v })"
    >
      <template #cell-title="{ row }">
        <div class="flex items-center gap-3 min-w-0">
          <div class="h-12 w-9 rounded bg-bg-secondary border border-border overflow-hidden shrink-0">
            <img v-if="row.cover_url" :src="row.cover_url" :alt="localised(row.title, row.slug)" class="h-full w-full object-cover" >
            <div v-else class="h-full w-full flex items-center justify-center">
              <Icon name="book" class="h-4 w-4 text-ink-tertiary" />
            </div>
          </div>
          <div class="min-w-0">
            <NuxtLink
              :to="localePath(`/admin/books/${row.id}/edit`)"
              class="font-medium text-ink hover:text-primary truncate block"
            >
              {{ localised(row.title, row.slug) }}
            </NuxtLink>
            <div class="text-xs text-ink-tertiary truncate">
              <Icon name="user-circle" class="inline h-3 w-3 align-text-bottom mr-0.5" />
              {{ row.author.display_name }}
            </div>
          </div>
        </div>
      </template>
      <template #cell-status="{ row }">
        <span
          class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium"
          :class="{
            'bg-success/10 text-success': STATUS_TONE[row.status] === 'success',
            'bg-warning/10 text-warning': STATUS_TONE[row.status] === 'warning',
            'bg-error/10 text-error': STATUS_TONE[row.status] === 'error',
            'bg-bg-secondary text-ink-tertiary': STATUS_TONE[row.status] === 'neutral',
          }"
        >
          {{ t(`account_books.status.${row.status}`) }}
        </span>
      </template>
      <template #cell-price="{ row }">
        <span class="tabular-nums text-sm">{{ formatPrice(row.price) }}</span>
      </template>
      <template #cell-created="{ row }">
        <span class="text-xs text-ink-tertiary">{{ formatDate(row.created_at, { withTime: false }) }}</span>
      </template>
      <template #actions="{ row }">
        <AdminActionMenu
          :items="[
            {
              key: 'edit',
              label: t('admin.actions.edit'),
              icon: 'pencil' as const,
              to: localePath(`/admin/books/${row.id}/edit`),
            },
            ...(row.status === 'approved'
              ? [{
                  key: 'view',
                  label: t('admin.books.view_full'),
                  icon: 'external' as const,
                  to: localePath(`/books/${row.slug}`),
                }]
              : []),
            {
              key: 'delete',
              label: t('admin.books.delete_button'),
              icon: 'trash' as const,
              danger: true,
              divider: true,
            },
          ]"
          @action="(k) => k === 'delete' && (deleteTarget = row)"
        />
      </template>
    </AdminDataTable>

    <div v-if="list && list.total > PAGE_SIZE" class="pt-4">
      <UiPagination
        :page="queryParams.page"
        :page-size="PAGE_SIZE"
        :total="list.total"
        @change="changePage"
      />
    </div>

    <AdminConfirmDialog
      :open="!!deleteTarget"
      tone="danger"
      icon="trash"
      :title="t('admin.books.delete_modal_title')"
      :description="deleteTarget ? t('admin.books.delete_modal_body', { title: localised(deleteTarget.title, deleteTarget.slug) }) : ''"
      :confirm-label="t('admin.books.delete_button')"
      :cancel-label="t('admin.actions.cancel')"
      :loading="deleting"
      @update:open="(v) => !v && (deleteTarget = null)"
      @confirm="confirmDelete"
    />

    <AdminConfirmDialog
      :open="!!bulkAction"
      :tone="bulkAction === 'approve' ? 'primary' : 'danger'"
      :icon="bulkAction === 'approve' ? 'check-circle-solid' : 'close'"
      :title="bulkAction === 'approve'
        ? t('admin.bulk.approve_confirm_title', { n: selected.length })
        : t('admin.bulk.reject_confirm_title', { n: selected.length })"
      :description="bulkAction === 'approve'
        ? t('admin.bulk.approve_confirm_body', { n: selected.length })
        : t('admin.bulk.reject_confirm_body', { n: selected.length })"
      :confirm-label="bulkAction === 'approve' ? t('admin.bulk.approve_selected') : t('admin.bulk.reject_selected')"
      :cancel-label="t('admin.actions.cancel')"
      :loading="bulkBusy"
      @update:open="closeBulkDialog"
      @confirm="confirmBulkAction"
    >
      <label v-if="bulkAction === 'reject'" class="block">
        <span class="block text-sm text-ink-secondary mb-1">{{ t('admin.bulk.reject_reason_label') }}</span>
        <textarea
          v-model="bulkReason"
          rows="3"
          :placeholder="t('admin.bulk.reject_reason_placeholder')"
          class="w-full px-3 py-2 rounded border border-border bg-bg text-sm text-ink focus:outline-none focus:border-primary"
        />
        <span v-if="bulkReasonError" class="block text-xs text-error mt-1">{{ bulkReasonError }}</span>
      </label>
    </AdminConfirmDialog>
  </section>
</template>
