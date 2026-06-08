<script setup lang="ts">
import type { BookOwnerView, BookStatus, CategoryList } from "~/types/api";
import type { BookFormValue } from "~/components/book/BookForm.vue";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({ middleware: "auth" });

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const api = useApi();
const toast = useToast();
const { localised } = useLocaleText();

const bookId = computed(() => route.params.id as string);

const { data: bookRaw, refresh: refreshBook } = await useAsyncData(
  `account:books:edit:${bookId.value}`,
  () => api<BookOwnerView>(`/books/owner/${bookId.value}`),
  { server: false },
);
const book = computed(() => bookRaw.value as BookOwnerView | null);

const { data: categoriesRaw } = await useAsyncData(
  "account:books:edit:categories",
  () => api<CategoryList>("/categories"),
  { server: false },
);
const categories = computed(() => categoriesRaw.value?.items ?? []);

useHead({
  title: computed(() => book.value
    ? `${localised(book.value.title, book.value.slug)} — ${t("account_books.edit_page_title")}`
    : t("account_books.edit_page_title"),
  ),
});

function modelFromBook(b: BookOwnerView): BookFormValue {
  const title = (b.title ?? {}) as Record<string, string>;
  const subtitle = (b.subtitle ?? {}) as Record<string, string>;
  const description = (b.description ?? {}) as Record<string, string>;
  return {
    title_uz: title.uz ?? "",
    title_ru: title.ru ?? "",
    title_en: title.en ?? "",
    subtitle_uz: subtitle.uz ?? "",
    subtitle_ru: subtitle.ru ?? "",
    subtitle_en: subtitle.en ?? "",
    description_uz: description.uz ?? "",
    description_ru: description.ru ?? "",
    description_en: description.en ?? "",
    language: b.language,
    co_authors: b.co_authors ?? "",
    isbn: b.isbn ?? "",
    publication_year: b.publication_year ? String(b.publication_year) : "",
    publisher: b.publisher ?? "",
    price: String(b.price ?? 0),
    discount_price: b.discount_price != null ? String(b.discount_price) : "",
    category_ids: b.categories.map((c) => c.id),
    keywords: b.keywords.join(", "),
    featured: b.featured,
  };
}

const form = ref<BookFormValue | null>(null);
watch(book, (b) => { if (b && !form.value) form.value = modelFromBook(b); }, { immediate: true });

const submitting = ref(false);
const deleting = ref(false);
const submittingReview = ref(false);
const error = ref<string | null>(null);

const isEditable = computed(() => {
  if (!book.value) return false;
  return book.value.status === "draft" || book.value.status === "rejected";
});

const canSubmitForReview = computed(() => {
  if (!book.value || !isEditable.value) return false;
  return Boolean(book.value.file_url) && book.value.categories.length > 0
    && Object.values(book.value.title ?? {}).some((v) => typeof v === "string" && v.trim());
});

function packLocalised(uz: string, ru: string, en: string) {
  const out: Record<string, string> = {};
  if (uz.trim()) out.uz = uz.trim();
  if (ru.trim()) out.ru = ru.trim();
  if (en.trim()) out.en = en.trim();
  return out;
}

async function save() {
  if (!form.value || !book.value) return;
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
    await api(`/books/${book.value.id}`, { method: "PATCH", body: payload });
    toast.success(t("account_books.update_success"));
    await refreshBook();
  }
  catch (err) {
    error.value = apiErrorMessage(err, t("common.error"));
    toast.error(error.value);
  }
  finally {
    submitting.value = false;
  }
}

const deleteOpen = ref(false);
async function confirmDelete() {
  if (!book.value || deleting.value) return;
  deleting.value = true;
  try {
    await api(`/books/${book.value.id}`, { method: "DELETE" });
    toast.success(t("account_books.delete_success"));
    deleteOpen.value = false;
    await router.push(localePath("/account/books"));
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    deleting.value = false;
  }
}

async function submitForReview() {
  if (!book.value || submittingReview.value) return;
  submittingReview.value = true;
  try {
    await api(`/books/${book.value.id}/submit`, { method: "POST" });
    toast.success(t("account_books.submit_success"));
    await refreshBook();
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    submittingReview.value = false;
  }
}

function onCoverUploaded(url: string) {
  if (book.value) book.value.cover_url = url;
}
function onFileUploaded(url: string) {
  if (book.value) book.value.file_url = url;
}
function onDemoUploaded(url: string) {
  if (book.value) book.value.demo_url = url;
}

const STATUS_BANNER: Record<BookStatus, { tone: string; iconBg: string; title: string; body: string } | null> = {
  draft: null,
  pending: {
    tone: "warning",
    iconBg: "bg-warning/10 text-warning",
    title: "account_books.pending_banner.title",
    body: "account_books.pending_banner.body",
  },
  approved: {
    tone: "success",
    iconBg: "bg-success/10 text-success",
    title: "account_books.approved_banner.title",
    body: "account_books.approved_banner.body",
  },
  rejected: {
    tone: "error",
    iconBg: "bg-error/10 text-error",
    title: "account_books.rejected_banner.title",
    body: "account_books.rejected_banner.body",
  },
  archived: null,
};
</script>

<template>
  <AccountShell>
    <section v-if="book" class="space-y-5">
      <header>
        <nav class="text-xs text-ink-tertiary mb-1 flex items-center gap-1.5 flex-wrap">
          <NuxtLink :to="localePath('/account/books')" class="hover:text-primary">
            {{ t("account_books.title") }}
          </NuxtLink>
          <Icon name="chevron-down" class="h-3 w-3 -rotate-90" />
          <span class="truncate">{{ localised(book.title, book.slug) }}</span>
        </nav>
        <h1 class="font-serif text-2xl md:text-3xl text-ink leading-tight">
          {{ t("account_books.edit_page_title") }}
        </h1>
        <p class="text-sm text-ink-secondary mt-1">{{ t("account_books.edit_page_subtitle") }}</p>
      </header>

      <!-- Status banner -->
      <div
        v-if="STATUS_BANNER[book.status]"
        class="rounded-md border p-4 flex items-start gap-3"
        :class="{
          'border-warning/30 bg-warning/5': book.status === 'pending',
          'border-success/30 bg-success/5': book.status === 'approved',
          'border-error/30 bg-error/5': book.status === 'rejected',
        }"
      >
        <div :class="['h-9 w-9 rounded flex items-center justify-center shrink-0', STATUS_BANNER[book.status]?.iconBg]">
          <Icon
            :name="book.status === 'approved' ? 'check-circle-solid' : (book.status === 'rejected' ? 'warning-solid' : 'arrow-path')"
            class="h-5 w-5"
          />
        </div>
        <div class="min-w-0">
          <h3 class="font-medium text-ink">{{ t(STATUS_BANNER[book.status]!.title) }}</h3>
          <p class="text-sm text-ink-secondary mt-0.5">{{ t(STATUS_BANNER[book.status]!.body) }}</p>
          <p v-if="book.status === 'rejected' && book.rejection_reason" class="text-sm text-error mt-2">
            <strong>{{ t("account_books.rejection_reason_label") }}:</strong> {{ book.rejection_reason }}
          </p>
        </div>
      </div>

      <!-- File uploads -->
      <section class="space-y-3">
        <h2 class="text-sm uppercase tracking-wider text-ink-tertiary">
          {{ t("account_books.section_files") }}
        </h2>
        <div class="grid md:grid-cols-2 gap-3">
          <BookFileUpload
            :title="t('account_books.upload.cover_title')"
            :hint="t('account_books.upload.cover_hint')"
            :url="book.cover_url"
            variant="image"
            accept="image/jpeg,image/png,image/webp"
            :max-size-mb="5"
            :endpoint="`/books/${book.id}/cover`"
            :read-only="!isEditable"
            @uploaded="onCoverUploaded"
          />
          <BookFileUpload
            :title="t('account_books.upload.file_title')"
            :hint="t('account_books.upload.file_hint')"
            :url="book.file_url"
            variant="pdf"
            accept="application/pdf"
            :max-size-mb="100"
            :endpoint="`/books/${book.id}/file`"
            :read-only="!isEditable"
            @uploaded="onFileUploaded"
          />
          <BookFileUpload
            :title="t('account_books.upload.demo_title')"
            :hint="t('account_books.upload.demo_hint_manual')"
            :url="book.demo_url"
            variant="pdf"
            accept="application/pdf"
            :max-size-mb="50"
            :endpoint="`/books/${book.id}/demo`"
            :read-only="!isEditable"
            @uploaded="onDemoUploaded"
          />
        </div>
      </section>

      <!-- Submit for review CTA -->
      <div
        v-if="isEditable"
        class="rounded-md border border-primary/30 bg-primary/5 p-4 flex flex-wrap items-center gap-3"
      >
        <div class="min-w-0 flex-1">
          <h3 class="font-medium text-ink">{{ t("account_books.submit_for_review") }}</h3>
          <p v-if="!canSubmitForReview" class="text-xs text-ink-tertiary mt-0.5">
            {{ t("account_books.submit_disabled_reason") }}
          </p>
        </div>
        <UiButton
          :disabled="!canSubmitForReview"
          :loading="submittingReview"
          @click="submitForReview"
        >
          <Icon name="upload" class="h-4 w-4" />
          {{ t("account_books.submit_for_review") }}
        </UiButton>
      </div>

      <!-- Metadata form -->
      <BookForm
        v-if="form"
        v-model="form"
        :categories="categories"
        :loading="submitting"
        :error="error"
        :submit-label="t('admin.actions.save')"
        :cancel-to="localePath('/account/books')"
        show-delete
        :deleting="deleting"
        @submit="save"
        @delete="deleteOpen = true"
      />

      <AdminConfirmDialog
        :open="deleteOpen"
        tone="danger"
        icon="trash"
        :title="t('account_books.delete_modal_title')"
        :description="t('account_books.delete_modal_body', { title: localised(book.title, book.slug) })"
        :confirm-label="t('account_books.delete_button')"
        :cancel-label="t('common.cancel')"
        :loading="deleting"
        @update:open="(v) => (deleteOpen = v)"
        @confirm="confirmDelete"
      />
    </section>
    <section v-else class="space-y-3">
      <UiSkeleton height="3rem" block />
      <UiSkeleton height="14rem" block />
      <UiSkeleton height="20rem" block />
    </section>
  </AccountShell>
</template>
