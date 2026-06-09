<script setup lang="ts">
import type { BookOwnerList, BookOwnerView, BookStatus } from "~/types/api";
import type { Column } from "~/components/admin/AdminDataTable.vue";
import { apiErrorMessage } from "~/composables/useAuth";
import { formatPrice } from "~/composables/useLocaleText";

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
const { localised } = useLocaleText();
const { formatDate } = useFormatDate();

useHead({ title: t("admin.books.title") });

const PAGE_SIZE = 20;

const queryParams = computed(() => ({
  page: Math.max(1, Number(route.query.page) || 1),
  page_size: PAGE_SIZE,
  search: ((route.query.q as string) || "").trim() || undefined,
  status: ((route.query.status as string) || undefined) as BookStatus | undefined,
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

const columns: Column<BookOwnerView>[] = [
  { key: "title", label: t("account_books.table.title_col") },
  { key: "status", label: t("account_books.table.status"), align: "center", width: "w-32" },
  { key: "price", label: t("account_books.table.price"), align: "right", width: "w-28", mobileHidden: true },
  { key: "created", label: t("account_books.table.updated_at"), width: "w-32", mobileHidden: true },
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

    <AdminDataTable
      :columns="columns"
      :rows="items"
      :row-key="(r) => r.id"
      :loading="pending"
      :empty="{
        icon: 'book',
        title: filtersDirty ? t('admin.filters.no_results') : t('admin.books.empty_title'),
        description: filtersDirty ? t('admin.filters.no_results_desc') : t('admin.books.empty_body'),
      }"
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
  </section>
</template>
