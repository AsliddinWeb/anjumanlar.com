<script setup lang="ts">
import type { ReviewCategoryList, ReviewCategoryPublic } from "~/types/api";
import type { Column } from "~/components/admin/AdminDataTable.vue";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin"],
});

const { t } = useI18n();
const localePath = useLocalePath();
const { localised } = useLocaleText();
const api = useApi();
const toast = useToast();

useHead({ title: t("admin.review_categories.title") });

const { data: listRaw, refresh, pending } = await useAsyncData(
  "admin:review-categories:list",
  () => api<ReviewCategoryList>("/admin/review-categories"),
  { server: false },
);
const rows = computed<ReviewCategoryPublic[]>(
  () => ((listRaw.value as ReviewCategoryList | null)?.items ?? []) as ReviewCategoryPublic[],
);

const deleteTarget = ref<ReviewCategoryPublic | null>(null);
const deleting = ref(false);

function askDelete(row: ReviewCategoryPublic) {
  deleteTarget.value = row;
}

async function confirmDelete() {
  if (!deleteTarget.value || deleting.value) return;
  const target = deleteTarget.value;
  deleting.value = true;
  try {
    await api(`/admin/review-categories/${target.id}`, { method: "DELETE" });
    toast.success(t("admin.review_categories.delete_success", { name: localised(target.name, target.slug) }));
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

const columns: Column<ReviewCategoryPublic>[] = [
  { key: "name", label: t("admin.review_categories.table.name") },
  { key: "slug", label: t("admin.review_categories.table.slug") },
  { key: "sort", label: t("admin.review_categories.table.sort"), align: "right", width: "w-16", mobileHidden: true },
  { key: "active", label: t("admin.review_categories.table.active"), align: "center", width: "w-24" },
];
</script>

<template>
  <section>
    <AdminPageHeader
      :title="t('admin.review_categories.title')"
      :description="t('admin.review_categories.subtitle')"
      icon="folder"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('admin.review_categories.title') },
      ]"
    >
      <template #actions>
        <UiButton :to="localePath('/admin/review-categories/new')">
          <Icon name="plus" class="h-4 w-4" />
          {{ t("admin.review_categories.add_button") }}
        </UiButton>
      </template>
    </AdminPageHeader>

    <AdminDataTable
      :columns="columns"
      :rows="rows"
      :row-key="(r) => r.id"
      :loading="pending"
      :empty="{
        icon: 'folder',
        title: t('admin.review_categories.empty_title'),
        description: t('admin.review_categories.empty_body'),
      }"
    >
      <template #cell-name="{ row }">
        <NuxtLink
          :to="localePath(`/admin/review-categories/${row.id}/edit`)"
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
      <template #cell-active="{ row }">
        <AdminStatusPill
          v-if="row.is_active"
          tone="success"
          icon="check"
          :label="t('admin.review_categories.active')"
        />
        <AdminStatusPill
          v-else
          tone="neutral"
          :label="t('admin.review_categories.inactive')"
        />
      </template>
      <template #actions="{ row }">
        <AdminActionMenu
          :items="[
            {
              key: 'edit',
              label: t('admin.actions.edit'),
              icon: 'pencil',
              to: localePath(`/admin/review-categories/${row.id}/edit`),
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
      :description="deleteTarget ? t('admin.review_categories.delete_confirm_body', { name: localised(deleteTarget.name, deleteTarget.slug) }) : ''"
      :confirm-label="t('admin.actions.delete')"
      :cancel-label="t('admin.actions.cancel')"
      :loading="deleting"
      @update:open="(v) => !v && (deleteTarget = null)"
      @confirm="confirmDelete"
    />
  </section>
</template>
