<script setup lang="ts">
import type { PublicationTypeList, PublicationTypePublic } from "~/types/api";
import type { Column } from "~/components/admin/AdminDataTable.vue";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin", "admin-scope"],
  adminScope: "categories",
});

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const { localised } = useLocaleText();
const api = useApi();
const toast = useToast();

useHead({ title: t("admin.publication_types.title") });

const searchQuery = computed(() => (route.query.q as string) || "");
const activeOnly = computed(() => route.query.active === "1");

const { data: ptRaw, refresh, pending } = await useAsyncData(
  "admin:publication-types:list",
  () => api<PublicationTypeList>("/publication-types", {
    query: { active_only: activeOnly.value },
  }),
  { server: false, watch: [activeOnly] },
);

const allTypes = computed<PublicationTypePublic[]>(
  () => ((ptRaw.value as PublicationTypeList | null)?.items ?? []) as PublicationTypePublic[],
);

const types = computed<PublicationTypePublic[]>(() => {
  const q = searchQuery.value.trim().toLowerCase();
  if (!q) return allTypes.value;
  return allTypes.value.filter((pt) => {
    const name = localised(pt.name, pt.slug).toLowerCase();
    return name.includes(q) || pt.slug.toLowerCase().includes(q);
  });
});

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
const deleteTarget = ref<PublicationTypePublic | null>(null);
const deleting = ref(false);

function askDelete(pt: PublicationTypePublic) {
  deleteTarget.value = pt;
}

async function confirmDelete() {
  if (!deleteTarget.value || deleting.value) return;
  const target = deleteTarget.value;
  deleting.value = true;
  try {
    await api(`/publication-types/${target.id}`, { method: "DELETE" });
    toast.success(t("admin.publication_types.delete_success", { name: localised(target.name, target.slug) }));
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

const columns: Column<PublicationTypePublic>[] = [
  { key: "name", label: t("admin.publication_types.table.name") },
  { key: "slug", label: t("admin.publication_types.table.slug") },
  { key: "sort", label: t("admin.publication_types.table.sort"), align: "right", width: "w-16", mobileHidden: true },
  { key: "books", label: t("admin.publication_types.table.books"), align: "right", width: "w-20" },
  { key: "active", label: t("admin.publication_types.table.active"), align: "center", width: "w-24" },
];
</script>

<template>
  <section>
    <AdminPageHeader
      :title="t('admin.publication_types.title')"
      :description="t('admin.publication_types.subtitle')"
      icon="book"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('admin.publication_types.title') },
      ]"
    >
      <template #actions>
        <UiButton :to="localePath('/admin/publication-types/new')">
          <Icon name="plus" class="h-4 w-4" />
          {{ t("admin.publication_types.add_button") }}
        </UiButton>
      </template>
    </AdminPageHeader>

    <AdminFilterBar
      :search="searchQuery"
      :search-placeholder="t('admin.publication_types.search_placeholder')"
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
        {{ t("admin.publication_types.filter_active_only") }}
      </button>
    </AdminFilterBar>

    <AdminDataTable
      :columns="columns"
      :rows="types"
      :row-key="(r) => r.id"
      :loading="pending"
      :empty="{
        icon: 'book',
        title: t('admin.publication_types.empty_title'),
        description: t('admin.publication_types.empty_body'),
      }"
    >
      <template #cell-name="{ row }">
        <NuxtLink
          :to="localePath(`/admin/publication-types/${row.id}/edit`)"
          class="font-medium text-ink hover:text-primary"
        >
          {{ localised(row.name, row.slug) }}
        </NuxtLink>
      </template>
      <template #cell-slug="{ row }">
        <code class="text-xs text-ink-secondary font-mono">{{ row.slug }}</code>
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
          :label="t('admin.publication_types.active')"
        />
        <AdminStatusPill
          v-else
          tone="neutral"
          :label="t('admin.publication_types.inactive')"
        />
      </template>
      <template #actions="{ row }">
        <AdminActionMenu
          :items="[
            {
              key: 'edit',
              label: t('admin.actions.edit'),
              icon: 'pencil',
              to: localePath(`/admin/publication-types/${row.id}/edit`),
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
      :description="deleteTarget ? t('admin.publication_types.delete_confirm_body', { name: localised(deleteTarget.name, deleteTarget.slug) }) : ''"
      :confirm-label="t('admin.actions.delete')"
      :cancel-label="t('admin.actions.cancel')"
      :loading="deleting"
      @update:open="(v) => !v && (deleteTarget = null)"
      @confirm="confirmDelete"
    />
  </section>
</template>
