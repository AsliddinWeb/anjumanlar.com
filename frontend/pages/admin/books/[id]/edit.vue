<script setup lang="ts">
import type { BookOwnerView, BookStatus, CategoryList } from "~/types/api";
import type { BookFormValue } from "~/components/book/BookForm.vue";
import { apiErrorMessage } from "~/composables/useAuth";
import { formatPrice } from "~/composables/useLocaleText";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin"],
});

const { t, locale } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const api = useApi();
const toast = useToast();
const { localised } = useLocaleText();

const bookId = computed(() => route.params.id as string);

const { data: bookRaw, refresh: refreshBook } = await useAsyncData(
  `admin:books:edit:${bookId.value}`,
  () => api<BookOwnerView>(`/books/owner/${bookId.value}`),
  { server: false },
);
const book = computed(() => bookRaw.value as BookOwnerView | null);

const { data: categoriesRaw } = await useAsyncData(
  "admin:books:edit:categories",
  () => api<CategoryList>("/categories"),
  { server: false },
);
const categories = computed(() => categoriesRaw.value?.items ?? []);

useHead({
  title: computed(() => book.value
    ? `${localised(book.value.title, book.value.slug)} — ${t("admin.books.edit_page_title")}`
    : t("admin.books.edit_page_title"),
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
    isbn: b.isbn ?? "",
    publication_year: b.publication_year ? String(b.publication_year) : "",
    publisher: b.publisher ?? "",
    price: String(b.price ?? 0),
    discount_price: b.discount_price != null ? String(b.discount_price) : "",
    category_ids: b.categories.map((c) => c.id),
    keywords: b.keywords.join(", "),
  };
}

const form = ref<BookFormValue | null>(null);
watch(book, (b) => { if (b && !form.value) form.value = modelFromBook(b); }, { immediate: true });

const submitting = ref(false);
const deleting = ref(false);
const approving = ref(false);
const error = ref<string | null>(null);

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
      isbn: form.value.isbn.trim() || null,
      publication_year: form.value.publication_year ? Number(form.value.publication_year) : null,
      publisher: form.value.publisher.trim() || null,
      price: Number(form.value.price) || 0,
      discount_price: form.value.discount_price ? Number(form.value.discount_price) : null,
      category_ids: form.value.category_ids,
      keywords: form.value.keywords.split(",").map((k) => k.trim()).filter(Boolean),
    };
    await api(`/books/admin/${book.value.id}`, { method: "PATCH", body: payload });
    toast.success(t("admin.books.update_success"));
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
    toast.success(t("admin.books.delete_success"));
    deleteOpen.value = false;
    await router.push(localePath("/admin/books"));
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    deleting.value = false;
  }
}

// ---- Approve / reject (pending only) ----
async function approveBook() {
  if (!book.value || approving.value) return;
  approving.value = true;
  try {
    await api(`/books/admin/${book.value.id}/approve`, { method: "POST" });
    toast.success(t("admin.books.approve_success", { title: localised(book.value.title, book.value.slug) }));
    await refreshBook();
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    approving.value = false;
  }
}

const rejectOpen = ref(false);
const rejectReason = ref("");
const rejectError = ref<string | null>(null);
const rejecting = ref(false);

async function confirmReject() {
  if (!book.value) return;
  if (!rejectReason.value.trim()) {
    rejectError.value = t("admin.books.reject_reason_required");
    return;
  }
  rejecting.value = true;
  rejectError.value = null;
  try {
    await api(`/books/admin/${book.value.id}/reject`, {
      method: "POST",
      body: { reason: rejectReason.value.trim() },
    });
    toast.warning(t("admin.books.reject_success", { title: localised(book.value.title, book.value.slug) }));
    rejectOpen.value = false;
    rejectReason.value = "";
    await refreshBook();
  }
  catch (err) {
    rejectError.value = apiErrorMessage(err, t("common.error"));
  }
  finally {
    rejecting.value = false;
  }
}

function onCoverUploaded(url: string) {
  if (book.value) book.value.cover_url = url;
}
function onFileUploaded(url: string) {
  if (book.value) book.value.file_url = url;
}

const STATUS_TONE: Record<BookStatus, "success" | "warning" | "neutral" | "error"> = {
  draft: "neutral",
  pending: "warning",
  approved: "success",
  rejected: "error",
  archived: "neutral",
};

const formatDate = (iso: string) =>
  new Intl.DateTimeFormat(locale.value, {
    year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  }).format(new Date(iso));
</script>

<template>
  <section v-if="book" class="space-y-5">
    <AdminPageHeader
      :title="t('admin.books.edit_page_title')"
      :description="localised(book.title, book.slug)"
      icon="book"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('admin.books.title'), to: localePath('/admin/books') },
        { label: t('admin.books.edit_page_title') },
      ]"
    >
      <template #actions>
        <span
          class="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium"
          :class="{
            'bg-success/10 text-success': STATUS_TONE[book.status] === 'success',
            'bg-warning/10 text-warning': STATUS_TONE[book.status] === 'warning',
            'bg-error/10 text-error': STATUS_TONE[book.status] === 'error',
            'bg-bg-secondary text-ink-tertiary': STATUS_TONE[book.status] === 'neutral',
          }"
        >
          {{ t(`account_books.status.${book.status}`) }}
        </span>
      </template>
    </AdminPageHeader>

    <!-- Pending → approve/reject CTAs -->
    <div
      v-if="book.status === 'pending'"
      class="rounded-md border border-warning/30 bg-warning/5 p-4 flex flex-wrap items-center gap-3"
    >
      <Icon name="arrow-path" class="h-5 w-5 text-warning shrink-0" />
      <div class="min-w-0 flex-1">
        <h3 class="font-medium text-ink">{{ t("admin.books.status_pending") }}</h3>
        <p class="text-xs text-ink-tertiary mt-0.5">{{ t("admin.books.moderation_subtitle") }}</p>
      </div>
      <UiButton variant="ghost" :loading="rejecting" @click="rejectOpen = true">
        <Icon name="close" class="h-4 w-4" />
        {{ t("admin.books.reject") }}
      </UiButton>
      <UiButton :loading="approving" @click="approveBook">
        <Icon name="check" class="h-4 w-4" />
        {{ t("admin.books.approve") }}
      </UiButton>
    </div>

    <!-- Author + meta summary -->
    <div class="rounded-md border border-border bg-bg-card p-4 grid sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs">
      <div>
        <dt class="text-ink-tertiary uppercase tracking-wide text-[10px]">{{ t("admin.users.title") }}</dt>
        <dd class="text-ink mt-0.5 inline-flex items-center gap-1.5">
          <Icon name="user-circle" class="h-3.5 w-3.5 text-ink-tertiary" />
          {{ book.author.display_name }}
        </dd>
      </div>
      <div>
        <dt class="text-ink-tertiary uppercase tracking-wide text-[10px]">{{ t("admin.books.price_label") }}</dt>
        <dd class="text-ink mt-0.5">{{ formatPrice(book.price) }}</dd>
      </div>
      <div>
        <dt class="text-ink-tertiary uppercase tracking-wide text-[10px]">{{ t("admin.books.language_label") }}</dt>
        <dd class="text-ink mt-0.5">{{ book.language }}</dd>
      </div>
      <div>
        <dt class="text-ink-tertiary uppercase tracking-wide text-[10px]">{{ t("account_books.table.updated_at") }}</dt>
        <dd class="text-ink mt-0.5">{{ formatDate(book.created_at) }}</dd>
      </div>
    </div>

    <p v-if="book.status === 'rejected' && book.rejection_reason" class="rounded-md border border-error/20 bg-error/5 p-3 text-sm text-error">
      <strong>{{ t("account_books.rejection_reason_label") }}:</strong>
      {{ book.rejection_reason }}
    </p>

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
          @uploaded="onFileUploaded"
        />
      </div>
    </section>

    <!-- Metadata form -->
    <BookForm
      v-if="form"
      v-model="form"
      :categories="categories"
      :loading="submitting"
      :error="error"
      :submit-label="t('admin.actions.save')"
      :cancel-to="localePath('/admin/books')"
      show-delete
      :deleting="deleting"
      @submit="save"
      @delete="deleteOpen = true"
    />

    <!-- Delete -->
    <AdminConfirmDialog
      :open="deleteOpen"
      tone="danger"
      icon="trash"
      :title="t('admin.books.delete_modal_title')"
      :description="t('admin.books.delete_modal_body', { title: localised(book.title, book.slug) })"
      :confirm-label="t('admin.books.delete_button')"
      :cancel-label="t('admin.actions.cancel')"
      :loading="deleting"
      @update:open="(v) => (deleteOpen = v)"
      @confirm="confirmDelete"
    />

    <!-- Reject modal -->
    <AdminConfirmDialog
      :open="rejectOpen"
      tone="danger"
      icon="close"
      :title="t('admin.books.reject_modal_title')"
      :confirm-label="t('admin.books.reject_submit')"
      :cancel-label="t('admin.books.reject_cancel')"
      :loading="rejecting"
      @update:open="(v) => { rejectOpen = v; if (!v) { rejectReason = ''; rejectError = null; } }"
      @confirm="confirmReject"
    >
      <label class="block">
        <span class="block text-sm text-ink-secondary mb-1">{{ t("admin.books.reject_reason") }}</span>
        <textarea
          v-model="rejectReason"
          rows="4"
          :placeholder="t('admin.books.reject_reason_placeholder')"
          class="w-full px-3 py-2 rounded border border-border bg-bg text-sm text-ink focus:outline-none focus:border-primary"
        />
        <span v-if="rejectError" class="block text-xs text-error mt-1">{{ rejectError }}</span>
      </label>
    </AdminConfirmDialog>
  </section>
  <section v-else class="space-y-3">
    <UiSkeleton height="3rem" block />
    <UiSkeleton height="14rem" block />
    <UiSkeleton height="20rem" block />
  </section>
</template>
