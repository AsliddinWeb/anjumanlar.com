<script setup lang="ts">
import type { CategoryList, CategoryPublic } from "~/types/api";
import type { CategoryFormValue } from "~/components/admin/CategoryForm.vue";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin"],
});

const { t } = useI18n();
const localePath = useLocalePath();
const api = useApi();
const toast = useToast();

useHead({ title: t("admin.categories.form.create_title") });

const { data: catRaw } = await useAsyncData(
  "admin:categories:parents",
  () => api<CategoryList>("/categories", { query: { active_only: false } }),
);

const parents = computed<CategoryPublic[]>(
  () => ((catRaw.value as CategoryList | null)?.items ?? []) as CategoryPublic[],
);

const form = ref<CategoryFormValue>({
  slug: "",
  name_uz: "",
  name_ru: "",
  name_en: "",
  icon: "",
  parent_id: "",
  sort_order: 0,
  is_active: true,
});

const submitting = ref(false);
const error = ref<string | null>(null);

async function onSubmit() {
  if (submitting.value) return;
  error.value = null;

  if (!form.value.slug.trim()) {
    error.value = t("admin.categories.form.slug_required");
    return;
  }
  const name: Record<string, string> = {};
  if (form.value.name_uz.trim()) name.uz = form.value.name_uz.trim();
  if (form.value.name_ru.trim()) name.ru = form.value.name_ru.trim();
  if (form.value.name_en.trim()) name.en = form.value.name_en.trim();
  if (Object.keys(name).length === 0) {
    error.value = t("admin.categories.form.name_required");
    return;
  }

  submitting.value = true;
  try {
    await api("/categories", {
      method: "POST",
      body: {
        slug: form.value.slug.trim(),
        name,
        icon: form.value.icon.trim() || null,
        parent_id: form.value.parent_id || null,
        sort_order: Number(form.value.sort_order) || 0,
        is_active: form.value.is_active,
      },
    });
    toast.success(t("admin.categories.create_success"));
    await navigateTo(localePath("/admin/categories"));
  }
  catch (err) {
    error.value = apiErrorMessage(err, t("admin.form.save_failed"));
  }
  finally {
    submitting.value = false;
  }
}
</script>

<template>
  <section>
    <AdminPageHeader
      :title="t('admin.categories.form.create_title')"
      :description="t('admin.categories.form.create_subtitle')"
      icon="plus"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('admin.categories.title'), to: localePath('/admin/categories') },
        { label: t('admin.categories.form.create_title') },
      ]"
    >
      <template #actions>
        <UiButton variant="ghost" :to="localePath('/admin/categories')">
          <Icon name="arrow-left" class="h-4 w-4" />
          {{ t("admin.actions.back") }}
        </UiButton>
      </template>
    </AdminPageHeader>

    <div class="max-w-3xl">
      <CategoryForm
        v-model="form"
        :parents="parents"
        :loading="submitting"
        :error="error"
        :submit-label="t('admin.categories.form.submit_create')"
        :cancel-to="localePath('/admin/categories')"
        @submit="onSubmit"
      />
    </div>
  </section>
</template>
