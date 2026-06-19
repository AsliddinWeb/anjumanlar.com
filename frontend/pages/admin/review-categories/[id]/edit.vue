<script setup lang="ts">
import type { ReviewCategoryPublic } from "~/types/api";
import type { ReviewCategoryFormValue } from "~/components/admin/ReviewCategoryForm.vue";
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

const { data: rawCat, refresh: refreshCat } = await useAsyncData(
  `admin:review-categories:edit:${categoryId.value}`,
  async () => {
    const list = await api<{ items: ReviewCategoryPublic[] }>(`/admin/review-categories`);
    return list.items.find((c) => c.id === categoryId.value) ?? null;
  },
  { server: false },
);
const cat = computed<ReviewCategoryPublic | null>(() => rawCat.value as ReviewCategoryPublic | null);

useHead({
  title: computed(() => cat.value
    ? `${localised(cat.value.name, cat.value.slug)} — ${t("admin.review_categories.edit_page_title")}`
    : t("admin.review_categories.edit_page_title"),
  ),
});

function modelFromCategory(c: ReviewCategoryPublic): ReviewCategoryFormValue {
  const name = (c.name ?? {}) as Record<string, string>;
  const description = (c.description ?? {}) as Record<string, string>;
  return {
    slug: c.slug,
    name_uz: name.uz ?? "",
    name_ru: name.ru ?? "",
    name_en: name.en ?? "",
    description_uz: description.uz ?? "",
    description_ru: description.ru ?? "",
    description_en: description.en ?? "",
    sort_order: String(c.sort_order ?? 0),
    is_active: c.is_active,
  };
}

const form = ref<ReviewCategoryFormValue | null>(null);
watch(cat, (c) => { if (c && !form.value) form.value = modelFromCategory(c); }, { immediate: true });

const submitting = ref(false);
const error = ref<string | null>(null);

function packLocalised(uz: string, ru: string, en: string) {
  const out: Record<string, string> = {};
  if (uz.trim()) out.uz = uz.trim();
  if (ru.trim()) out.ru = ru.trim();
  if (en.trim()) out.en = en.trim();
  return out;
}

async function save() {
  if (!form.value || !cat.value) return;
  error.value = null;
  if (!form.value.slug.trim()) {
    error.value = t("admin.review_categories.errors.slug_required");
    return;
  }
  const name = packLocalised(form.value.name_uz, form.value.name_ru, form.value.name_en);
  if (Object.keys(name).length === 0) {
    error.value = t("admin.review_categories.errors.name_required");
    return;
  }
  submitting.value = true;
  try {
    await api(`/admin/review-categories/${cat.value.id}`, {
      method: "PATCH",
      body: {
        slug: form.value.slug.trim(),
        name,
        description: packLocalised(form.value.description_uz, form.value.description_ru, form.value.description_en),
        sort_order: Number(form.value.sort_order) || 0,
        is_active: form.value.is_active,
      },
    });
    toast.success(t("admin.review_categories.update_success"));
    await refreshCat();
  }
  catch (err) {
    error.value = apiErrorMessage(err, t("common.error"));
    toast.error(error.value);
  }
  finally {
    submitting.value = false;
  }
}
</script>

<template>
  <section v-if="cat">
    <AdminPageHeader
      :title="t('admin.review_categories.edit_page_title')"
      :description="localised(cat.name, cat.slug)"
      icon="folder"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('admin.review_categories.title'), to: localePath('/admin/review-categories') },
        { label: t('admin.review_categories.edit_page_title') },
      ]"
    />
    <ReviewCategoryForm
      v-if="form"
      v-model="form"
      :loading="submitting"
      :error="error"
      :submit-label="t('admin.actions.save')"
      :cancel-to="localePath('/admin/review-categories')"
      @submit="save"
    />
  </section>
  <section v-else class="space-y-3">
    <UiSkeleton height="3rem" block />
    <UiSkeleton height="20rem" block />
  </section>
</template>
