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
const route = useRoute();
const api = useApi();
const toast = useToast();
const { localised } = useLocaleText();

const categoryId = computed(() => route.params.id as string);

const { data: catRaw } = await useAsyncData(
  "admin:categories:edit",
  () => api<CategoryList>("/categories", { query: { active_only: false } }),
  { server: false },
);

const allCategories = computed<CategoryPublic[]>(
  () => ((catRaw.value as CategoryList | null)?.items ?? []) as CategoryPublic[],
);

const current = computed<CategoryPublic | null>(
  () => allCategories.value.find((c) => c.id === categoryId.value) ?? null,
);

if (!current.value) {
  throw createError({ statusCode: 404, statusMessage: "Category not found" });
}

useHead({
  title: t("admin.categories.form.edit_title") + " — " + localised(current.value!.name, current.value!.slug),
});

const form = ref<CategoryFormValue>({
  slug: current.value!.slug,
  name_uz: (current.value!.name?.uz as string) ?? "",
  name_ru: (current.value!.name?.ru as string) ?? "",
  name_en: (current.value!.name?.en as string) ?? "",
  icon: current.value!.icon ?? "",
  parent_id: current.value!.parent_id ?? "",
  sort_order: current.value!.sort_order,
  is_active: current.value!.is_active,
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
    await api(`/categories/${categoryId.value}`, {
      method: "PATCH",
      body: {
        slug: form.value.slug.trim(),
        name,
        icon: form.value.icon.trim() || null,
        parent_id: form.value.parent_id || null,
        sort_order: Number(form.value.sort_order) || 0,
        is_active: form.value.is_active,
      },
    });
    toast.success(t("admin.categories.update_success"));
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
      :title="t('admin.categories.form.edit_title')"
      :description="current ? localised(current.name, current.slug) : ''"
      icon="pencil"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('admin.categories.title'), to: localePath('/admin/categories') },
        { label: current ? localised(current.name, current.slug) : '' },
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
        :parents="allCategories"
        :exclude-id="categoryId"
        :loading="submitting"
        :error="error"
        :submit-label="t('admin.categories.form.submit_edit')"
        :cancel-to="localePath('/admin/categories')"
        @submit="onSubmit"
      />
    </div>
  </section>
</template>
