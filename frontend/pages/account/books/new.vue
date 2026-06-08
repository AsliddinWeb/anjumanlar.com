<script setup lang="ts">
import type { BookOwnerView, CategoryList } from "~/types/api";
import type { BookFormValue } from "~/components/book/BookForm.vue";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({ middleware: "auth" });

const { t } = useI18n();
const localePath = useLocalePath();
const router = useRouter();
const api = useApi();
const toast = useToast();

useHead({ title: t("account_books.new_page_title") });

const { data: categoriesRaw } = await useAsyncData(
  "account:books:new:categories",
  () => api<CategoryList>("/categories"),
  { server: false },
);
const categories = computed(() => categoriesRaw.value?.items ?? []);

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
    keywords: "",
    featured: false,
  };
}

const form = ref<BookFormValue>(emptyForm());
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
  const title = packLocalised(form.value.title_uz, form.value.title_ru, form.value.title_en);
  if (Object.keys(title).length === 0) {
    error.value = t("account_books.errors.title_required");
    return;
  }

  submitting.value = true;
  try {
    const payload = {
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
      keywords: form.value.keywords
        .split(",")
        .map((k) => k.trim())
        .filter(Boolean),
    };
    const created = await api<BookOwnerView>("/books", { method: "POST", body: payload });
    toast.success(t("account_books.create_success"));
    await router.push(localePath(`/account/books/${created.id}/edit`));
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
  <AccountShell>
    <section class="space-y-5">
      <header>
        <nav class="text-xs text-ink-tertiary mb-1 flex items-center gap-1.5">
          <NuxtLink :to="localePath('/account/books')" class="hover:text-primary">
            {{ t("account_books.title") }}
          </NuxtLink>
          <Icon name="chevron-down" class="h-3 w-3 -rotate-90" />
          <span>{{ t("account_books.new_page_title") }}</span>
        </nav>
        <h1 class="font-serif text-2xl md:text-3xl text-ink leading-tight">
          {{ t("account_books.new_page_title") }}
        </h1>
        <p class="text-sm text-ink-secondary mt-1">{{ t("account_books.new_page_subtitle") }}</p>
      </header>

      <BookForm
        v-model="form"
        :categories="categories"
        :loading="submitting"
        :error="error"
        :submit-label="t('admin.actions.create')"
        :cancel-to="localePath('/account/books')"
        @submit="submit"
      />
    </section>
  </AccountShell>
</template>
