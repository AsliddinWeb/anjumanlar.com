<script setup lang="ts">
import type { PublicationTypeFormValue } from "~/components/admin/PublicationTypeForm.vue";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin", "admin-scope"],
  adminScope: "categories",
});

const { t } = useI18n();
const localePath = useLocalePath();
const api = useApi();
const toast = useToast();

useHead({ title: t("admin.publication_types.form.create_title") });

const form = ref<PublicationTypeFormValue>({
  slug: "",
  name_uz: "",
  name_ru: "",
  name_en: "",
  sort_order: 0,
  is_active: true,
});

const submitting = ref(false);
const error = ref<string | null>(null);

async function onSubmit() {
  if (submitting.value) return;
  error.value = null;

  if (!form.value.slug.trim()) {
    error.value = t("admin.publication_types.form.slug_required");
    return;
  }
  const name: Record<string, string> = {};
  if (form.value.name_uz.trim()) name.uz = form.value.name_uz.trim();
  if (form.value.name_ru.trim()) name.ru = form.value.name_ru.trim();
  if (form.value.name_en.trim()) name.en = form.value.name_en.trim();
  if (Object.keys(name).length === 0) {
    error.value = t("admin.publication_types.form.name_required");
    return;
  }

  submitting.value = true;
  try {
    await api("/publication-types", {
      method: "POST",
      body: {
        slug: form.value.slug.trim(),
        name,
        sort_order: Number(form.value.sort_order) || 0,
        is_active: form.value.is_active,
      },
    });
    toast.success(t("admin.publication_types.create_success"));
    await navigateTo(localePath("/admin/publication-types"));
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
      :title="t('admin.publication_types.form.create_title')"
      :description="t('admin.publication_types.form.create_subtitle')"
      icon="plus"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('admin.publication_types.title'), to: localePath('/admin/publication-types') },
        { label: t('admin.publication_types.form.create_title') },
      ]"
    >
      <template #actions>
        <UiButton variant="ghost" :to="localePath('/admin/publication-types')">
          <Icon name="arrow-left" class="h-4 w-4" />
          {{ t("admin.actions.back") }}
        </UiButton>
      </template>
    </AdminPageHeader>

    <div class="max-w-3xl">
      <PublicationTypeForm
        v-model="form"
        :loading="submitting"
        :error="error"
        :submit-label="t('admin.publication_types.form.submit_create')"
        :cancel-to="localePath('/admin/publication-types')"
        @submit="onSubmit"
      />
    </div>
  </section>
</template>
