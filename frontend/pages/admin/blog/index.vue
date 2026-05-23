<script setup lang="ts">
import type { BlogPostAdminList, BlogPostAdminView, BlogPostStatus } from "~/types/api";
import type { Column } from "~/components/admin/AdminDataTable.vue";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin"],
});

const { t, locale } = useI18n();
const localePath = useLocalePath();
const { localised } = useLocaleText();
const route = useRoute();
const router = useRouter();
const api = useApi();
const toast = useToast();

useHead({ title: t("admin.blog.title") });

const PAGE_SIZE = 20;
const currentPage = computed(() => Math.max(1, Number(route.query.page) || 1));
const statusFilter = computed(() => (route.query.status as string) || "");
const searchQuery = computed(() => (route.query.q as string) || "");

const queryParams = computed(() => {
  const p: Record<string, string | number> = {
    page: currentPage.value,
    page_size: PAGE_SIZE,
  };
  if (statusFilter.value) p.status = statusFilter.value;
  return p;
});

const { data: listRaw, pending, refresh } = await useAsyncData(
  "admin:blog:list",
  () => api<BlogPostAdminList>("/admin/blog", { query: queryParams.value }),
  { watch: [queryParams] },
);

const list = computed(() => listRaw.value as BlogPostAdminList | null);

const filtered = computed<BlogPostAdminView[]>(() => {
  const items = list.value?.items ?? [];
  const q = searchQuery.value.trim().toLowerCase();
  if (!q) return items;
  return items.filter((p) =>
    localised(p.title, p.slug).toLowerCase().includes(q)
    || p.slug.toLowerCase().includes(q),
  );
});

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

const filtersDirty = computed(() => Boolean(statusFilter.value || searchQuery.value));

const formatDate = (iso: string | null) => {
  if (!iso) return "—";
  return new Intl.DateTimeFormat(locale.value, {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(iso));
};

const STATUS_TONE: Record<BlogPostStatus, "success" | "neutral" | "warning"> = {
  draft: "neutral",
  published: "success",
  archived: "warning",
};

// ---- Actions --------
const busy = ref<Set<string>>(new Set());
const deleteTarget = ref<BlogPostAdminView | null>(null);
const deleting = ref(false);

async function publishPost(p: BlogPostAdminView) {
  if (busy.value.has(p.id)) return;
  busy.value.add(p.id);
  try {
    await api(`/admin/blog/${p.id}/publish`, { method: "POST" });
    toast.success(t("admin.blog.publish_success"));
    await refresh();
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    busy.value.delete(p.id);
  }
}

async function unpublishPost(p: BlogPostAdminView) {
  if (busy.value.has(p.id)) return;
  busy.value.add(p.id);
  try {
    await api(`/admin/blog/${p.id}/unpublish`, { method: "POST" });
    toast.success(t("admin.blog.unpublish_success"));
    await refresh();
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    busy.value.delete(p.id);
  }
}

async function confirmDelete() {
  if (!deleteTarget.value || deleting.value) return;
  const target = deleteTarget.value;
  deleting.value = true;
  try {
    await api(`/admin/blog/${target.id}`, { method: "DELETE" });
    toast.success(t("admin.blog.delete_success"));
    deleteTarget.value = null;
    await refresh();
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("admin.form.delete_failed")));
  }
  finally {
    deleting.value = false;
  }
}

const statusOptions = [
  { value: "draft", labelKey: "admin.blog.statuses.draft" },
  { value: "published", labelKey: "admin.blog.statuses.published" },
  { value: "archived", labelKey: "admin.blog.statuses.archived" },
];

const columns: Column<BlogPostAdminView>[] = [
  { key: "title", label: t("admin.blog.table.title_col") },
  { key: "slug", label: t("admin.blog.table.slug") },
  { key: "status", label: t("admin.blog.table.status"), align: "center", width: "w-28" },
  { key: "published_at", label: t("admin.blog.table.published_at"), width: "w-32" },
];
</script>

<template>
  <section>
    <AdminPageHeader
      :title="t('admin.blog.title')"
      :description="t('admin.blog.subtitle')"
      icon="news"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('admin.blog.title') },
      ]"
    >
      <template #actions>
        <UiButton :to="localePath('/admin/blog/new')">
          <Icon name="plus" class="h-4 w-4" />
          {{ t("admin.blog.add_button") }}
        </UiButton>
      </template>
    </AdminPageHeader>

    <AdminFilterBar
      :search="searchQuery"
      :search-placeholder="t('admin.blog.search_placeholder')"
      :dirty="filtersDirty"
      @update:search="(v) => setQuery({ q: v })"
      @reset="resetFilters"
    >
      <UiSelect
        :model-value="statusFilter"
        :options="[
          { value: '', label: t('admin.filters.all') },
          ...statusOptions.map((s) => ({ value: s.value, label: t(s.labelKey) })),
        ]"
        size="sm"
        @update:model-value="(v) => setQuery({ status: v })"
      />
      <span v-if="list" class="text-xs text-ink-tertiary ml-1">
        {{ t("admin.blog.total", { n: list.total }) }}
      </span>
    </AdminFilterBar>

    <AdminDataTable
      :columns="columns"
      :rows="filtered"
      :row-key="(r) => r.id"
      :loading="pending"
      :empty="{
        icon: 'news',
        title: t('admin.blog.empty_title'),
        description: t('admin.blog.empty_body'),
      }"
    >
      <template #cell-title="{ row }">
        <NuxtLink
          :to="localePath(`/admin/blog/${row.id}/edit`)"
          class="font-medium text-ink hover:text-primary"
        >
          {{ localised(row.title, row.slug) }}
        </NuxtLink>
      </template>
      <template #cell-slug="{ row }">
        <code class="text-xs text-ink-secondary font-mono">{{ row.slug }}</code>
      </template>
      <template #cell-status="{ row }">
        <AdminStatusPill
          :tone="STATUS_TONE[row.status]"
          :label="t(`admin.blog.statuses.${row.status}`)"
        />
      </template>
      <template #cell-published_at="{ row }">
        <span class="text-xs text-ink-tertiary">{{ formatDate(row.published_at) }}</span>
      </template>
      <template #actions="{ row }">
        <AdminActionMenu
          :items="[
            { key: 'edit', label: t('admin.actions.edit'), icon: 'pencil', to: localePath(`/admin/blog/${row.id}/edit`) },
            ...(row.status !== 'published'
              ? [{ key: 'publish', label: t('admin.blog.actions.publish'), icon: 'check-circle' as const }]
              : [{ key: 'unpublish', label: t('admin.blog.actions.unpublish'), icon: 'eye-slash' as const }]),
            { key: 'delete', label: t('admin.actions.delete'), icon: 'trash', danger: true, divider: true },
          ]"
          @action="(k) => {
            if (k === 'publish') publishPost(row);
            else if (k === 'unpublish') unpublishPost(row);
            else if (k === 'delete') deleteTarget = row;
          }"
        />
      </template>
    </AdminDataTable>

    <div v-if="list && list.total > PAGE_SIZE" class="pt-4">
      <UiPagination
        :page="currentPage"
        :page-size="PAGE_SIZE"
        :total="list.total"
        @change="changePage"
      />
    </div>

    <AdminConfirmDialog
      :open="!!deleteTarget"
      tone="danger"
      icon="trash"
      :title="t('admin.actions.delete_confirm_title')"
      :description="deleteTarget ? t('admin.blog.delete_confirm_body', { title: localised(deleteTarget.title, deleteTarget.slug) }) : ''"
      :confirm-label="t('admin.actions.delete')"
      :cancel-label="t('admin.actions.cancel')"
      :loading="deleting"
      @update:open="(v) => !v && (deleteTarget = null)"
      @confirm="confirmDelete"
    />
  </section>
</template>
