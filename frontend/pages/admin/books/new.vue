<script setup lang="ts">
import type { AuthorList, AuthorPublic, BookOwnerView, CategoryList, PublicationTypeList } from "~/types/api";
import type { BookFormValue } from "~/components/book/BookForm.vue";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin", "admin-scope"],
  adminScope: "books",
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

const { data: publicationTypesRaw } = await useAsyncData(
  "admin:books:new:publication-types",
  () => api<PublicationTypeList>("/publication-types"),
  { server: false },
);
const publicationTypes = computed(() => publicationTypesRaw.value?.items ?? []);

const authors = ref<AuthorPublic[]>([]);
const authorsLoading = ref(false);
// Set once from the unfiltered initial load — distinguishes "no authors
// exist on the platform yet" from "this search query matched nothing".
const hasAnyAuthors = ref(false);
let authorSearchTimer: ReturnType<typeof setTimeout> | null = null;

async function loadAuthors(search?: string) {
  authorsLoading.value = true;
  try {
    const resp = await api<AuthorList>("/authors", {
      query: { page_size: 50, search: search?.trim() || undefined },
    });
    authors.value = resp.items;
    if (!search) hasAnyAuthors.value = resp.total > 0;
  }
  finally {
    authorsLoading.value = false;
  }
}

function onAuthorSearch(query: string) {
  if (authorSearchTimer) clearTimeout(authorSearchTimer);
  authorSearchTimer = setTimeout(() => loadAuthors(query), 300);
}

await loadAuthors();

function emptyForm(): BookFormValue {
  return {
    title_uz: "", title_ru: "", title_en: "",
    subtitle_uz: "", subtitle_ru: "", subtitle_en: "",
    description_uz: "", description_ru: "", description_en: "",
    language: "uz",
    co_authors: "",
    isbn: "",
    publication_year: "",
    publisher: "",
    price: "0",
    discount_price: "",
    category_ids: [],
    publication_type_id: "",
    keywords: "",
    featured: false,
    downloads_enabled: true,
  };
}

const form = ref<BookFormValue>(emptyForm());
const authorId = ref<string>("");
const submitting = ref(false);
const error = ref<string | null>(null);

const authorOptions = computed(() =>
  authors.value.map((a) => ({
    value: a.id,
    label: a.academic_title ? `${a.display_name} — ${a.academic_title}` : a.display_name,
  })),
);

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
      co_authors: form.value.co_authors.trim() || null,
      isbn: form.value.isbn.trim() || null,
      publication_year: form.value.publication_year ? Number(form.value.publication_year) : null,
      publisher: form.value.publisher.trim() || null,
      price: Number(form.value.price) || 0,
      discount_price: form.value.discount_price ? Number(form.value.discount_price) : null,
      category_ids: form.value.category_ids,
      publication_type_id: form.value.publication_type_id || null,
      keywords: form.value.keywords.split(",").map((k) => k.trim()).filter(Boolean),
      featured: form.value.featured,
      downloads_enabled: form.value.downloads_enabled,
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
      v-if="!hasAnyAuthors"
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
        <UiSearchSelect
          v-model="authorId"
          remote
          :loading="authorsLoading"
          :label="t('admin.books.author_field')"
          :placeholder="t('admin.books.author_select_placeholder')"
          :search-placeholder="t('admin.books.author_search_placeholder')"
          :no-results-label="t('common.empty')"
          :options="authorOptions"
          @search="onAuthorSearch"
        />
        <p class="text-xs text-ink-tertiary">{{ t('admin.books.author_field_hint') }}</p>
      </div>

      <BookForm
        v-model="form"
        :categories="categories"
        :publication-types="publicationTypes"
        :loading="submitting"
        :error="error"
        :submit-label="t('admin.actions.create')"
        :cancel-to="localePath('/admin/books')"
        show-featured
        @submit="submit"
      />
    </template>
  </section>
</template>
