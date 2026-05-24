<script setup lang="ts">
import type { BlogPostAdminView } from "~/types/api";
import type { BlogPostFormValue } from "~/components/admin/BlogPostForm.vue";
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

const postId = computed(() => route.params.id as string);

const { data: postRaw } = await useAsyncData(
  `admin:blog:edit:${postId.value}`,
  () => api<BlogPostAdminView>(`/admin/blog/${postId.value}`),
  { server: false },
);

const post = computed(() => postRaw.value as BlogPostAdminView | null);

if (!post.value) {
  throw createError({ statusCode: 404, statusMessage: "Post not found" });
}

useHead({
  title: t("admin.blog.form.edit_title") + " — " + localised(post.value!.title, post.value!.slug),
});

const form = ref<BlogPostFormValue>({
  slug: post.value!.slug,
  title_uz: (post.value!.title?.uz as string) ?? "",
  title_ru: (post.value!.title?.ru as string) ?? "",
  title_en: (post.value!.title?.en as string) ?? "",
  excerpt_uz: (post.value!.excerpt?.uz as string) ?? "",
  excerpt_ru: (post.value!.excerpt?.ru as string) ?? "",
  excerpt_en: (post.value!.excerpt?.en as string) ?? "",
  body_uz: (post.value!.body?.uz as string) ?? "",
  body_ru: (post.value!.body?.ru as string) ?? "",
  body_en: (post.value!.body?.en as string) ?? "",
  cover_url: post.value!.cover_url ?? "",
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
    await api(`/admin/blog/${postId.value}`, {
      method: "PATCH",
      body: {
        slug: form.value.slug.trim(),
        title,
        excerpt: collect("excerpt"),
        body: collect("body"),
        cover_url: form.value.cover_url.trim() || null,
      },
    });
    toast.success(t("admin.blog.update_success"));
    await navigateTo(localePath("/admin/blog"));
  }
  catch (err) {
    error.value = apiErrorMessage(err, t("admin.form.save_failed"));
  }
  finally {
    submitting.value = false;
  }
}

const publishBusy = ref(false);
async function togglePublish() {
  if (!post.value || publishBusy.value) return;
  publishBusy.value = true;
  const path = post.value.status === "published" ? "unpublish" : "publish";
  try {
    await api(`/admin/blog/${postId.value}/${path}`, { method: "POST" });
    toast.success(post.value.status === "published"
      ? t("admin.blog.unpublish_success")
      : t("admin.blog.publish_success"));
    await navigateTo(localePath("/admin/blog"));
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    publishBusy.value = false;
  }
}
</script>

<template>
  <section>
    <AdminPageHeader
      :title="t('admin.blog.form.edit_title')"
      :description="post ? localised(post.title, post.slug) : ''"
      icon="pencil"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('admin.blog.title'), to: localePath('/admin/blog') },
        { label: post ? localised(post.title, post.slug) : '' },
      ]"
    >
      <template #actions>
        <UiButton
          v-if="post"
          variant="ghost"
          :loading="publishBusy"
          @click="togglePublish"
        >
          <Icon :name="post.status === 'published' ? 'eye-slash' : 'check-circle'" class="h-4 w-4" />
          {{ post.status === "published" ? t("admin.blog.actions.unpublish") : t("admin.blog.actions.publish") }}
        </UiButton>
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
        :submit-label="t('admin.blog.form.submit_edit')"
        :cancel-to="localePath('/admin/blog')"
        @submit="onSubmit"
      />
    </div>
  </section>
</template>
