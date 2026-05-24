<script setup lang="ts">
import type { BookList, BookPublic } from "~/types/api";
import { formatPrice } from "~/composables/useLocaleText";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin"],
});

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const { localised } = useLocaleText();
const api = useApi();
const toast = useToast();

useHead({ title: t("admin.books.title") });

const PAGE_SIZE = 20;
const currentPage = computed(() => Math.max(1, Number(route.query.page) || 1));
const searchQuery = computed(() => (route.query.q as string) || "");
const demoFilter = computed(() => (route.query.demo as string) || "");

const { data: queueRaw, pending, refresh } = await useAsyncData(
  "admin:books:moderation",
  () =>
    api<BookList>("/books/admin/moderation", {
      query: { page: currentPage.value, page_size: PAGE_SIZE },
    }),
  { server: false, watch: [currentPage] },
);

const queue = computed(() => queueRaw.value as BookList | null);

const filteredBooks = computed<BookPublic[]>(() => {
  const items = queue.value?.items ?? [];
  const q = searchQuery.value.trim().toLowerCase();
  return items.filter((b) => {
    if (demoFilter.value === "yes" && !b.demo_url) return false;
    if (demoFilter.value === "no" && b.demo_url) return false;
    if (!q) return true;
    return localised(b.title, b.slug).toLowerCase().includes(q)
      || b.author.display_name.toLowerCase().includes(q)
      || b.slug.toLowerCase().includes(q);
  });
});

function setQuery(updates: Record<string, string | number | undefined>) {
  const next: Record<string, string> = {};
  for (const [k, v] of Object.entries(route.query)) {
    if (typeof v === "string") next[k] = v;
  }
  for (const [k, v] of Object.entries(updates)) {
    if (v === undefined || v === null || v === "") delete next[k];
    else next[k] = String(v);
  }
  if (!("page" in updates)) delete next.page;
  router.push({ query: next });
}

function changePage(page: number) {
  setQuery({ page });
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}

function resetFilters() {
  router.replace({ query: {} });
}

const filtersDirty = computed(() => Boolean(searchQuery.value || demoFilter.value));

// --- Approve --------------------------------------------------------------
const approveTarget = ref<BookPublic | null>(null);
const approving = ref(false);

async function confirmApprove() {
  if (!approveTarget.value || approving.value) return;
  const target = approveTarget.value;
  approving.value = true;
  try {
    await api(`/books/admin/${target.id}/approve`, { method: "POST" });
    toast.success(t("admin.books.approve_success", { title: localised(target.title, target.slug) }));
    approveTarget.value = null;
    await refresh();
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    approving.value = false;
  }
}

// --- Reject ---------------------------------------------------------------
const rejectTarget = ref<BookPublic | null>(null);
const rejectReason = ref("");
const rejectSubmitting = ref(false);
const rejectError = ref<string | null>(null);

function openReject(book: BookPublic) {
  rejectTarget.value = book;
  rejectReason.value = "";
  rejectError.value = null;
}

function closeReject() {
  rejectTarget.value = null;
  rejectReason.value = "";
  rejectError.value = null;
}

async function submitReject() {
  if (!rejectTarget.value || rejectSubmitting.value) return;
  const reason = rejectReason.value.trim();
  if (!reason) {
    rejectError.value = t("admin.books.reject_reason_required");
    return;
  }
  rejectSubmitting.value = true;
  rejectError.value = null;
  try {
    const target = rejectTarget.value;
    await api(`/books/admin/${target.id}/reject`, {
      method: "POST",
      body: { reason },
    });
    toast.warning(t("admin.books.reject_success", { title: localised(target.title, target.slug) }));
    closeReject();
    await refresh();
  }
  catch (err) {
    rejectError.value = apiErrorMessage(err, t("common.error"));
  }
  finally {
    rejectSubmitting.value = false;
  }
}
</script>

<template>
  <section>
    <AdminPageHeader
      :title="t('admin.books.title')"
      :description="t('admin.books.subtitle')"
      icon="book"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('admin.books.title') },
      ]"
    >
      <template #actions>
        <AdminStatusPill
          tone="warning"
          icon="clipboard-list"
          :label="t('admin.books.queue_count', { n: queue?.total ?? 0 })"
        />
      </template>
    </AdminPageHeader>

    <AdminFilterBar
      :search="searchQuery"
      :search-placeholder="t('admin.books.search_placeholder')"
      :dirty="filtersDirty"
      @update:search="(v) => setQuery({ q: v })"
      @reset="resetFilters"
    >
      <UiSelect
        :model-value="demoFilter"
        size="sm"
        :options="[
          { value: '', label: t('admin.books.filter_demo_any') },
          { value: 'yes', label: t('admin.books.filter_demo_yes') },
          { value: 'no', label: t('admin.books.filter_demo_no') },
        ]"
        @update:model-value="(v) => setQuery({ demo: v })"
      />
    </AdminFilterBar>

    <div v-if="pending && !queue" class="space-y-3">
      <UiSkeleton v-for="i in 3" :key="i" height="11rem" block />
    </div>

    <UiEmptyState
      v-else-if="filteredBooks.length === 0 && !filtersDirty"
      icon="inbox-stack"
      :title="t('admin.books.empty_title')"
      :description="t('admin.books.empty_body')"
    />

    <UiEmptyState
      v-else-if="filteredBooks.length === 0"
      icon="search"
      :title="t('admin.filters.no_results')"
      :description="t('admin.filters.no_results_desc')"
    />

    <ul v-else class="space-y-4">
      <li
        v-for="book in filteredBooks"
        :key="book.id"
        class="rounded-md border border-border bg-bg-card overflow-hidden hover:border-primary/40 transition-colors"
      >
        <div class="grid sm:grid-cols-[140px_1fr] gap-4 p-4">
          <div class="w-[140px]">
            <BookCover :src="book.cover_url" :alt="localised(book.title, book.slug)" />
          </div>

          <div class="space-y-3 min-w-0">
            <div class="flex items-start justify-between gap-3 flex-wrap">
              <div class="min-w-0 space-y-1">
                <div class="flex items-center gap-2 flex-wrap">
                  <h2 class="font-serif text-lg text-ink leading-snug">
                    {{ localised(book.title, book.slug) }}
                  </h2>
                  <AdminStatusPill
                    tone="warning"
                    icon="arrow-path"
                    :label="t('admin.books.status_pending')"
                  />
                </div>
                <p class="text-sm text-ink-secondary truncate">
                  <Icon name="user-circle" class="inline h-3.5 w-3.5 mr-1 align-text-bottom" />
                  {{ book.author.display_name }}
                </p>
              </div>
              <BookPriceTag
                :price="book.price"
                :discount-price="book.discount_price"
                :is-free="book.is_free"
                size="sm"
              />
            </div>

            <div v-if="book.categories.length" class="flex flex-wrap gap-1.5">
              <UiBadge
                v-for="cat in book.categories"
                :key="cat.id"
                tone="neutral"
                size="sm"
              >
                <Icon name="folder" class="h-3 w-3" />
                {{ localised(cat.name, cat.slug) }}
              </UiBadge>
            </div>

            <dl class="grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-2 text-xs">
              <div>
                <dt class="text-ink-tertiary uppercase tracking-wide text-[10px]">{{ t("admin.books.language_label") }}</dt>
                <dd class="text-ink mt-0.5">{{ book.language }}</dd>
              </div>
              <div v-if="book.publication_year">
                <dt class="text-ink-tertiary uppercase tracking-wide text-[10px]">{{ t("admin.books.publication_year_label") }}</dt>
                <dd class="text-ink mt-0.5">{{ book.publication_year }}</dd>
              </div>
              <div v-if="book.publisher">
                <dt class="text-ink-tertiary uppercase tracking-wide text-[10px]">{{ t("admin.books.publisher_label") }}</dt>
                <dd class="text-ink truncate mt-0.5">{{ book.publisher }}</dd>
              </div>
              <div>
                <dt class="text-ink-tertiary uppercase tracking-wide text-[10px]">{{ t("admin.books.price_label") }}</dt>
                <dd class="text-ink mt-0.5">{{ formatPrice(book.price) }}</dd>
              </div>
            </dl>

            <p v-if="localised(book.description)" class="text-sm text-ink-secondary line-clamp-3">
              {{ localised(book.description) }}
            </p>
          </div>
        </div>

        <footer class="flex flex-wrap items-center gap-2 px-4 py-2.5 bg-bg-secondary/50 border-t border-border">
          <a
            v-if="book.demo_url"
            :href="book.demo_url"
            target="_blank"
            rel="noopener noreferrer"
            class="inline-flex items-center gap-1.5 text-xs text-primary hover:underline"
          >
            <Icon name="eye" class="h-3.5 w-3.5" />
            {{ t("admin.books.view_preview") }}
            <Icon name="external" class="h-3 w-3" />
          </a>
          <span v-else class="inline-flex items-center gap-1.5 text-xs text-ink-tertiary">
            <Icon name="warning" class="h-3.5 w-3.5" />
            {{ t("admin.books.no_demo") }}
          </span>

          <span class="flex-1" />

          <UiButton size="sm" variant="ghost" @click="openReject(book)">
            <Icon name="close" class="h-4 w-4" />
            {{ t("admin.books.reject") }}
          </UiButton>
          <UiButton size="sm" @click="approveTarget = book">
            <Icon name="check" class="h-4 w-4" />
            {{ t("admin.books.approve") }}
          </UiButton>
        </footer>
      </li>
    </ul>

    <div v-if="queue && queue.total > PAGE_SIZE" class="pt-4">
      <UiPagination
        :page="currentPage"
        :page-size="PAGE_SIZE"
        :total="queue.total"
        @change="changePage"
      />
    </div>

    <AdminConfirmDialog
      :open="!!approveTarget"
      tone="primary"
      icon="check-circle-solid"
      :title="t('admin.books.approve_modal_title')"
      :description="approveTarget ? t('admin.books.approve_modal_body', { title: localised(approveTarget.title, approveTarget.slug) }) : ''"
      :confirm-label="t('admin.books.approve')"
      :cancel-label="t('admin.actions.cancel')"
      :loading="approving"
      @update:open="(v) => !v && (approveTarget = null)"
      @confirm="confirmApprove"
    />

    <AdminConfirmDialog
      :open="!!rejectTarget"
      tone="danger"
      icon="close"
      :title="t('admin.books.reject_modal_title')"
      :description="rejectTarget ? localised(rejectTarget.title, rejectTarget.slug) : ''"
      :confirm-label="t('admin.books.reject_submit')"
      :cancel-label="t('admin.books.reject_cancel')"
      :loading="rejectSubmitting"
      :disabled="!rejectReason.trim()"
      @update:open="(v) => !v && closeReject()"
      @cancel="closeReject"
      @confirm="submitReject"
    >
      <label class="block">
        <span class="block text-sm text-ink-secondary mb-1">
          {{ t("admin.books.reject_reason") }}
          <span class="text-error">*</span>
        </span>
        <textarea
          v-model="rejectReason"
          rows="4"
          maxlength="2000"
          :placeholder="t('admin.books.reject_reason_placeholder')"
          class="w-full px-3 py-2 rounded border border-border bg-bg text-ink placeholder:text-ink-tertiary focus:outline-none focus:border-error text-sm"
        />
      </label>
      <p v-if="rejectError" class="mt-2 text-sm text-error">{{ rejectError }}</p>
    </AdminConfirmDialog>
  </section>
</template>
