<script setup lang="ts">
import type { CategoryList, CategoryPublic } from "~/types/api";
import type { Column } from "~/components/admin/AdminDataTable.vue";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin"],
});

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const { localised } = useLocaleText();
const api = useApi();
const toast = useToast();

useHead({ title: t("admin.categories.title") });

const searchQuery = computed(() => (route.query.q as string) || "");
const activeOnly = computed(() => route.query.active === "1");

const { data: catRaw, refresh, pending } = await useAsyncData(
  "admin:categories:list",
  () => api<CategoryList>("/categories", {
    query: { active_only: activeOnly.value },
  }),
  { server: false, watch: [activeOnly] },
);

const allCategories = computed<CategoryPublic[]>(
  () => ((catRaw.value as CategoryList | null)?.items ?? []) as CategoryPublic[],
);

const categories = computed<CategoryPublic[]>(() => {
  const q = searchQuery.value.trim().toLowerCase();
  if (!q) return allCategories.value;
  return allCategories.value.filter((c) => {
    const name = localised(c.name, c.slug).toLowerCase();
    return name.includes(q) || c.slug.toLowerCase().includes(q);
  });
});

const byId = computed(() => {
  const map = new Map<string, CategoryPublic>();
  for (const c of allCategories.value) map.set(c.id, c);
  return map;
});

function parentLabel(c: CategoryPublic): string {
  if (!c.parent_id) return "—";
  const p = byId.value.get(c.parent_id);
  return p ? localised(p.name, p.slug) : "?";
}

const filtersDirty = computed(() => Boolean(searchQuery.value || activeOnly.value));

function updateQuery(patch: Record<string, string | null | undefined>) {
  const q = { ...route.query };
  for (const [k, v] of Object.entries(patch)) {
    if (v === null || v === undefined || v === "") delete q[k];
    else q[k] = v;
  }
  router.replace({ query: q });
}

function onSearch(v: string) {
  updateQuery({ q: v });
}

function resetFilters() {
  router.replace({ query: {} });
}

function toggleActiveOnly() {
  updateQuery({ active: activeOnly.value ? null : "1" });
}

// ---- Delete ---------------------------------------------------------------
const deleteTarget = ref<CategoryPublic | null>(null);
const deleting = ref(false);

function askDelete(c: CategoryPublic) {
  deleteTarget.value = c;
}

async function confirmDelete() {
  if (!deleteTarget.value || deleting.value) return;
  const target = deleteTarget.value;
  deleting.value = true;
  try {
    await api(`/categories/${target.id}`, { method: "DELETE" });
    toast.success(t("admin.categories.delete_success", { name: localised(target.name, target.slug) }));
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

const columns: Column<CategoryPublic>[] = [
  { key: "name", label: t("admin.categories.table.name") },
  { key: "icon", label: t("admin.categories.table.icon"), width: "w-12", mobileHidden: true },
  { key: "slug", label: t("admin.categories.table.slug") },
  { key: "parent", label: t("admin.categories.table.parent") },
  { key: "sort", label: t("admin.categories.table.sort"), align: "right", width: "w-16", mobileHidden: true },
  { key: "books", label: t("admin.categories.table.books"), align: "right", width: "w-20" },
  { key: "active", label: t("admin.categories.table.active"), align: "center", width: "w-24" },
];
</script>

<template>
  <section>
    <AdminPageHeader
      :title="t('admin.categories.title')"
      :description="t('admin.categories.subtitle')"
      icon="folder"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('admin.categories.title') },
      ]"
    >
      <template #actions>
        <UiButton :to="localePath('/admin/categories/new')">
          <Icon name="plus" class="h-4 w-4" />
          {{ t("admin.categories.add_button") }}
        </UiButton>
      </template>
    </AdminPageHeader>

    <AdminFilterBar
      :search="searchQuery"
      :search-placeholder="t('admin.categories.search_placeholder')"
      :dirty="filtersDirty"
      @update:search="onSearch"
      @reset="resetFilters"
    >
      <button
        type="button"
        class="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded border text-xs font-medium transition-colors"
        :class="activeOnly
          ? 'border-primary bg-primary/10 text-primary'
          : 'border-border text-ink-secondary hover:border-primary hover:text-primary'"
        @click="toggleActiveOnly"
      >
        <Icon name="check-circle" class="h-3.5 w-3.5" />
        {{ t("admin.categories.filter_active_only") }}
      </button>
    </AdminFilterBar>

    <AdminDataTable
      :columns="columns"
      :rows="categories"
      :row-key="(r) => r.id"
      :loading="pending"
      :empty="{
        icon: 'folder',
        title: t('admin.categories.empty_title'),
        description: t('admin.categories.empty_body'),
      }"
    >
      <template #cell-icon="{ row }">
        <span class="inline-flex h-8 w-8 items-center justify-center rounded bg-bg-secondary text-primary">
          <Icon :name="row.icon" fallback="book" class="h-4 w-4" />
        </span>
      </template>
      <template #cell-name="{ row }">
        <NuxtLink
          :to="localePath(`/admin/categories/${row.id}/edit`)"
          class="font-medium text-ink hover:text-primary"
        >
          {{ localised(row.name, row.slug) }}
        </NuxtLink>
      </template>
      <template #cell-slug="{ row }">
        <code class="text-xs text-ink-secondary font-mono">{{ row.slug }}</code>
      </template>
      <template #cell-parent="{ row }">
        <span class="text-ink-secondary">{{ parentLabel(row) }}</span>
      </template>
      <template #cell-sort="{ row }">
        <span class="text-ink-tertiary">{{ row.sort_order }}</span>
      </template>
      <template #cell-books="{ row }">
        <span class="text-ink-tertiary">{{ row.book_count }}</span>
      </template>
      <template #cell-active="{ row }">
        <AdminStatusPill
          v-if="row.is_active"
          tone="success"
          icon="check"
          :label="t('admin.categories.active')"
        />
        <AdminStatusPill
          v-else
          tone="neutral"
          :label="t('admin.categories.inactive')"
        />
      </template>
      <template #actions="{ row }">
        <AdminActionMenu
          :items="[
            {
              key: 'edit',
              label: t('admin.actions.edit'),
              icon: 'pencil',
              to: localePath(`/admin/categories/${row.id}/edit`),
            },
            { key: 'delete', label: t('admin.actions.delete'), icon: 'trash', danger: true, divider: true },
          ]"
          @action="(k) => k === 'delete' && askDelete(row)"
        />
      </template>
    </AdminDataTable>

    <AdminConfirmDialog
      :open="!!deleteTarget"
      tone="danger"
      icon="trash"
      :title="t('admin.actions.delete_confirm_title')"
      :description="deleteTarget ? t('admin.categories.delete_confirm_body', { name: localised(deleteTarget.name, deleteTarget.slug) }) : ''"
      :confirm-label="t('admin.actions.delete')"
      :cancel-label="t('admin.actions.cancel')"
      :loading="deleting"
      @update:open="(v) => !v && (deleteTarget = null)"
      @confirm="confirmDelete"
    />
  </section>
</template>
