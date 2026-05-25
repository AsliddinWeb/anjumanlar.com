<script setup lang="ts">
import type { BookOwnerList, BookOwnerView, BookStatus } from "~/types/api";
import { apiErrorMessage } from "~/composables/useAuth";
import { formatPrice } from "~/composables/useLocaleText";

definePageMeta({ middleware: "auth" });

const { t, locale } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const api = useApi();
const toast = useToast();
const { localised } = useLocaleText();

useHead({ title: t("account_books.title") });

const PAGE_SIZE = 20;

const queryParams = computed(() => ({
  page: Math.max(1, Number(route.query.page) || 1),
  page_size: PAGE_SIZE,
  status: ((route.query.status as string) || undefined) as BookStatus | undefined,
}));

const { hasRole } = useAuth();
const isAuthor = computed(() => hasRole("author"));

const { data: listRaw, pending, refresh } = await useAsyncData(
  "account:books",
  () => isAuthor.value
    ? api<BookOwnerList>("/books/me", { query: queryParams.value })
    : Promise.resolve(null),
  { server: false, watch: [queryParams, isAuthor] },
);

const list = computed(() => listRaw.value as BookOwnerList | null);
const items = computed<BookOwnerView[]>(() => list.value?.items ?? []);

const searchQuery = ref("");
const filteredItems = computed(() => {
  const q = searchQuery.value.trim().toLowerCase();
  if (!q) return items.value;
  return items.value.filter((b) => localised(b.title, b.slug).toLowerCase().includes(q));
});

const filtersDirty = computed(() => Boolean(route.query.status || searchQuery.value));

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

function resetFilters() {
  searchQuery.value = "";
  router.replace({ query: {} });
}

function changePage(page: number) {
  setQuery({ page });
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}

const STATUS_TONE: Record<BookStatus, "success" | "warning" | "neutral" | "error" | "info"> = {
  draft: "neutral",
  pending: "warning",
  approved: "success",
  rejected: "error",
  archived: "neutral",
};

const formatDate = (iso: string) =>
  new Intl.DateTimeFormat(locale.value, {
    year: "numeric", month: "short", day: "numeric",
  }).format(new Date(iso));

// ---- Delete ----
const deleteTarget = ref<BookOwnerView | null>(null);
const deleting = ref(false);

async function confirmDelete() {
  if (!deleteTarget.value || deleting.value) return;
  const target = deleteTarget.value;
  deleting.value = true;
  try {
    await api(`/books/${target.id}`, { method: "DELETE" });
    toast.success(t("account_books.delete_success"));
    deleteTarget.value = null;
    await refresh();
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    deleting.value = false;
  }
}

</script>

<template>
  <AccountShell>
  <section class="space-y-5">
    <header class="flex items-end justify-between gap-3 flex-wrap">
      <div>
        <h1 class="font-serif text-2xl md:text-3xl text-ink leading-tight">
          {{ t("account_books.title") }}
        </h1>
        <p class="text-sm text-ink-secondary mt-1">
          {{ t("account_books.subtitle") }}
        </p>
      </div>
      <UiButton v-if="isAuthor" :to="localePath('/account/books/new')">
        <Icon name="plus" class="h-4 w-4" />
        {{ t("account_books.new_button") }}
      </UiButton>
    </header>

    <UiEmptyState
      v-if="!isAuthor"
      icon="pencil"
      :title="t('account_books.must_be_author_title')"
      :description="t('account_books.must_be_author_body')"
    >
      <UiButton :to="localePath('/authors/me')">
        {{ t('account_books.go_to_profile') }}
      </UiButton>
    </UiEmptyState>

    <template v-else>
      <div class="rounded-md border border-border bg-bg-card p-3 flex flex-wrap items-center gap-2">
        <div class="relative w-full sm:w-auto sm:flex-1 sm:min-w-[200px]">
          <Icon name="search" class="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-tertiary pointer-events-none" />
          <input
            v-model="searchQuery"
            type="search"
            :placeholder="t('account_books.search_placeholder')"
            class="w-full pl-8 pr-3 py-1.5 rounded border border-border bg-bg text-sm text-ink placeholder:text-ink-tertiary focus:outline-none focus:border-primary"
          >
        </div>
        <UiSelect
          :model-value="(route.query.status as string) || ''"
          size="sm"
          :options="[
            { value: '', label: t('account_books.filter_status_any') },
            { value: 'draft', label: t('account_books.status.draft') },
            { value: 'pending', label: t('account_books.status.pending') },
            { value: 'approved', label: t('account_books.status.approved') },
            { value: 'rejected', label: t('account_books.status.rejected') },
          ]"
          @update:model-value="(v) => setQuery({ status: v })"
        />
        <div class="flex-1" />
        <span v-if="list" class="text-xs text-ink-tertiary">
          {{ t("account_books.results", { n: list.total }) }}
        </span>
        <button
          v-if="filtersDirty"
          type="button"
          class="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs text-ink-secondary hover:text-error transition-colors"
          @click="resetFilters"
        >
          <Icon name="close" class="h-3.5 w-3.5" />
          {{ t("admin.filters.reset") }}
        </button>
      </div>

      <div v-if="pending && !list" class="space-y-3">
        <UiSkeleton v-for="i in 3" :key="i" height="6rem" block />
      </div>

      <UiEmptyState
        v-else-if="filteredItems.length === 0"
        icon="book"
        :title="t('account_books.empty_title')"
        :description="t('account_books.empty_body')"
      />

      <ul v-else class="space-y-3">
        <li
          v-for="book in filteredItems"
          :key="book.id"
          class="rounded-md border border-border bg-bg-card overflow-hidden hover:border-primary/40 transition-colors"
        >
          <div class="grid sm:grid-cols-[80px_1fr_auto] gap-4 p-4 items-start">
            <NuxtLink
              :to="localePath(`/account/books/${book.id}/edit`)"
              class="block w-20"
            >
              <BookCover :src="book.cover_url" :alt="localised(book.title, book.slug)" />
            </NuxtLink>

            <div class="min-w-0 space-y-2">
              <div class="flex items-center gap-2 flex-wrap">
                <NuxtLink
                  :to="localePath(`/account/books/${book.id}/edit`)"
                  class="font-serif text-lg text-ink hover:text-primary truncate"
                >
                  {{ localised(book.title, book.slug) }}
                </NuxtLink>
                <span
                  class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium"
                  :class="{
                    'bg-success/10 text-success': STATUS_TONE[book.status] === 'success',
                    'bg-warning/10 text-warning': STATUS_TONE[book.status] === 'warning',
                    'bg-error/10 text-error': STATUS_TONE[book.status] === 'error',
                    'bg-bg-secondary text-ink-tertiary': STATUS_TONE[book.status] === 'neutral',
                  }"
                >
                  {{ t(`account_books.status.${book.status}`) }}
                </span>
              </div>
              <p
                v-if="book.status === 'rejected' && book.rejection_reason"
                class="text-xs text-error bg-error/5 border border-error/20 p-2 rounded"
              >
                <strong>{{ t("account_books.rejection_reason_label") }}:</strong>
                {{ book.rejection_reason }}
              </p>
              <div class="flex flex-wrap gap-3 text-xs text-ink-tertiary">
                <span class="inline-flex items-center gap-1">
                  <Icon name="currency" class="h-3 w-3" />
                  {{ formatPrice(book.price) }}
                </span>
                <span v-if="book.categories.length" class="inline-flex items-center gap-1">
                  <Icon name="folder" class="h-3 w-3" />
                  {{ book.categories.map(c => localised(c.name, c.slug)).join(", ") }}
                </span>
                <span class="inline-flex items-center gap-1">
                  <Icon name="arrow-path" class="h-3 w-3" />
                  {{ formatDate(book.created_at) }}
                </span>
              </div>
            </div>

            <div class="flex flex-col gap-2 items-stretch sm:items-end">
              <UiButton
                size="sm"
                variant="ghost"
                :to="localePath(`/account/books/${book.id}/edit`)"
              >
                <Icon name="pencil" class="h-3.5 w-3.5" />
                {{ t("admin.actions.edit") }}
              </UiButton>
              <UiButton
                size="sm"
                variant="ghost"
                class="text-error hover:text-error"
                @click="deleteTarget = book"
              >
                <Icon name="trash" class="h-3.5 w-3.5" />
                {{ t("account_books.delete_button") }}
              </UiButton>
            </div>
          </div>
        </li>
      </ul>

      <div v-if="list && list.total > PAGE_SIZE" class="pt-2">
        <UiPagination
          :page="queryParams.page"
          :page-size="PAGE_SIZE"
          :total="list.total"
          @change="changePage"
        />
      </div>
    </template>

    <AdminConfirmDialog
      :open="!!deleteTarget"
      tone="danger"
      icon="trash"
      :title="t('account_books.delete_modal_title')"
      :description="deleteTarget ? t('account_books.delete_modal_body', { title: localised(deleteTarget.title, deleteTarget.slug) }) : ''"
      :confirm-label="t('account_books.delete_button')"
      :cancel-label="t('common.cancel')"
      :loading="deleting"
      @update:open="(v) => !v && (deleteTarget = null)"
      @confirm="confirmDelete"
    />
  </section>
  </AccountShell>
</template>
