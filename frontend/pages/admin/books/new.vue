<script setup lang="ts">
import type { AuthorList, AuthorPublic, BookOwnerView, CategoryList } from "~/types/api";
import type { BookFormValue } from "~/components/book/BookForm.vue";
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

useHead({ title: t("admin.books.new_page_title") });

const { data: categoriesRaw } = await useAsyncData(
  "admin:books:new:categories",
  () => api<CategoryList>("/categories"),
  { server: false },
);
const categories = computed(() => categoriesRaw.value?.items ?? []);

const { data: authorsRaw } = await useAsyncData(
  "admin:books:new:authors",
  () => api<AuthorList>("/authors", { query: { page_size: 100 } }),
  { server: false },
);
const authors = computed<AuthorPublic[]>(() => authorsRaw.value?.items ?? []);

function emptyForm(): BookFormValue {
  return {
    title_uz: "", title_ru: "", title_en: "",
    subtitle_uz: "", subtitle_ru: "", subtitle_en: "",
    description_uz: "", description_ru: "", description_en: "",
    language: "uz",
    isbn: "",
    publication_year: "",
    publisher: "",
    price: "0",
    discount_price: "",
    category_ids: [],
    keywords: "",
  };
}

const form = ref<BookFormValue>(emptyForm());
const authorId = ref<string>("");
const submitting = ref(false);
const error = ref<string | null>(null);

const authorOptions = computed(() => [
  { value: "", label: t("admin.books.author_select_placeholder") },
  ...authors.value.map((a) => ({
    value: a.id,
    label: a.academic_title ? `${a.display_name} — ${a.academic_title}` : a.display_name,
  })),
]);

function packLocalised(uz: string, ru: string, en: string) {
  const out: Record<string, string> = {};
  if (uz.trim()) out.uz = uz.trim();
  if (ru.trim()) out.ru = ru.trim();
  if (en.trim()) out.en = en.trim();
  return out;
}

async function submit() {
  error.value = null;
  if (!authorId.value) {
    error.value = t("admin.books.author_required");
    return;
  }
  const title = packLocalised(form.value.title_uz, form.value.title_ru, form.value.title_en);
  if (Object.keys(title).length === 0) {
    error.value = t("account_books.errors.title_required");
    return;
  }

  submitting.value = true;
  try {
    const payload = {
      author_id: authorId.value,
      title,
      subtitle: packLocalised(form.value.subtitle_uz, form.value.subtitle_ru, form.value.subtitle_en),
      description: packLocalised(form.value.description_uz, form.value.description_ru, form.value.description_en),
      language: form.value.language,
      isbn: form.value.isbn.trim() || null,
      publication_year: form.value.publication_year ? Number(form.value.publication_year) : null,
      publisher: form.value.publisher.trim() || null,
      price: Number(form.value.price) || 0,
      discount_price: form.value.discount_price ? Number(form.value.discount_price) : null,
      category_ids: form.value.category_ids,
      keywords: form.value.keywords.split(",").map((k) => k.trim()).filter(Boolean),
    };
    const created = await api<BookOwnerView>("/books/admin", { method: "POST", body: payload });
    toast.success(t("admin.books.create_success"));
    await router.push(localePath(`/admin/books/${created.id}/edit`));
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
      :title="t('admin.books.new_page_title')"
      :description="t('admin.books.subtitle')"
      icon="book"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('admin.books.title'), to: localePath('/admin/books') },
        { label: t('admin.books.new_page_title') },
      ]"
    />

    <UiEmptyState
      v-if="authors.length === 0"
      icon="users"
      :title="t('admin.books.no_authors_title')"
      :description="t('admin.books.no_authors_body')"
    >
      <UiButton :to="localePath('/admin/users')">
        {{ t("admin.users.title") }}
      </UiButton>
    </UiEmptyState>

    <template v-else>
      <div class="rounded-md border border-border bg-bg-card p-5 mb-5 space-y-2">
        <UiSelect
          v-model="authorId"
          :label="t('admin.books.author_field')"
          :options="authorOptions"
        />
        <p class="text-xs text-ink-tertiary">{{ t('admin.books.author_field_hint') }}</p>
      </div>

      <BookForm
        v-model="form"
        :categories="categories"
        :loading="submitting"
        :error="error"
        :submit-label="t('admin.actions.create')"
        :cancel-to="localePath('/admin/books')"
        @submit="submit"
      />
    </template>
  </section>
</template>
