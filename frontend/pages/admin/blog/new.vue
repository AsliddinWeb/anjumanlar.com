<script setup lang="ts">
import type { BlogPostFormValue } from "~/components/admin/BlogPostForm.vue";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin"],
});

const { t } = useI18n();
const localePath = useLocalePath();
const api = useApi();
const toast = useToast();

useHead({ title: t("admin.blog.form.create_title") });

const form = ref<BlogPostFormValue>({
  slug: "",
  title_uz: "",
  title_ru: "",
  title_en: "",
  excerpt_uz: "",
  excerpt_ru: "",
  excerpt_en: "",
  body_uz: "",
  body_ru: "",
  body_en: "",
  cover_url: "",
});

const submitting = ref(false);
const error = ref<string | null>(null);

function collect(prefix: "title" | "excerpt" | "body"): Record<string, string> {
  const out: Record<string, string> = {};
  for (const k of ["uz", "ru", "en"] as const) {
    const v = (form.value as Record<string, string>)[`${prefix}_${k}`].trim();
    if (v) out[k] = v;
  }
  return out;
}

async function onSubmit() {
  if (submitting.value) return;
  error.value = null;
  if (!form.value.slug.trim()) {
    error.value = t("admin.blog.form.slug_required");
    return;
  }
  const title = collect("title");
  if (Object.keys(title).length === 0) {
    error.value = t("admin.blog.form.title_required");
    return;
  }

  submitting.value = true;
  try {
    await api("/admin/blog", {
      method: "POST",
      body: {
        slug: form.value.slug.trim(),
        title,
        excerpt: collect("excerpt"),
        body: collect("body"),
        cover_url: form.value.cover_url.trim() || null,
      },
    });
    toast.success(t("admin.blog.create_success"));
    await navigateTo(localePath("/admin/blog"));
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
      :title="t('admin.blog.form.create_title')"
      :description="t('admin.blog.form.create_subtitle')"
      icon="plus"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('admin.blog.title'), to: localePath('/admin/blog') },
        { label: t('admin.blog.form.create_title') },
      ]"
    >
      <template #actions>
        <UiButton variant="ghost" :to="localePath('/admin/blog')">
          <Icon name="arrow-left" class="h-4 w-4" />
          {{ t("admin.actions.back") }}
        </UiButton>
      </template>
    </AdminPageHeader>

    <div class="max-w-4xl">
      <BlogPostForm
        v-model="form"
        :loading="submitting"
        :error="error"
        :submit-label="t('admin.blog.form.submit_create')"
        :cancel-to="localePath('/admin/blog')"
        @submit="onSubmit"
      />
    </div>
  </section>
</template>
