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
const router = useRouter();
const api = useApi();
const toast = useToast();

useHead({ title: t("admin.review_categories.new_page_title") });

function emptyForm(): ReviewCategoryFormValue {
  return {
    slug: "",
    name_uz: "", name_ru: "", name_en: "",
    description_uz: "", description_ru: "", description_en: "",
    sort_order: "0",
    is_active: true,
  };
}

const form = ref<ReviewCategoryFormValue>(emptyForm());
const submitting = ref(false);
const error = ref<string | null>(null);

function packLocalised(uz: string, ru: string, en: string) {
  const out: Record<string, string> = {};
  if (uz.trim()) out.uz = uz.trim();
  if (ru.trim()) out.ru = ru.trim();
  if (en.trim()) out.en = en.trim();
  return out;
}

async function submit() {
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
    const created = await api<ReviewCategoryPublic>("/admin/review-categories", {
      method: "POST",
      body: {
        slug: form.value.slug.trim(),
        name,
        description: packLocalised(form.value.description_uz, form.value.description_ru, form.value.description_en),
        sort_order: Number(form.value.sort_order) || 0,
        is_active: form.value.is_active,
      },
    });
    toast.success(t("admin.review_categories.create_success"));
    await router.push(localePath(`/admin/review-categories/${created.id}/edit`));
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
  <section>
    <AdminPageHeader
      :title="t('admin.review_categories.new_page_title')"
      :description="t('admin.review_categories.subtitle')"
      icon="folder"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('admin.review_categories.title'), to: localePath('/admin/review-categories') },
        { label: t('admin.review_categories.new_page_title') },
      ]"
    />
    <ReviewCategoryForm
      v-model="form"
      :loading="submitting"
      :error="error"
      :submit-label="t('admin.actions.create')"
      :cancel-to="localePath('/admin/review-categories')"
      @submit="submit"
    />
  </section>
</template>
