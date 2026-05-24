<script setup lang="ts">
import type { DownloadResponse, UserLibraryList } from "~/types/api";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({ middleware: "auth" });

const { t, locale } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const { localised } = useLocaleText();
const api = useApi();
const toast = useToast();

useSiteSeo({ title: t("library.title"), noindex: true });

const PAGE_SIZE = 12;
const currentPage = computed(() => Math.max(1, Number(route.query.page) || 1));
const searchQuery = computed(() => (route.query.q as string) || "");

const { data: libRaw, pending, error: libError } = await useAsyncData(
  "account:library",
  () =>
    api<UserLibraryList>("/libraries/me", {
      query: { page: currentPage.value, page_size: PAGE_SIZE },
    }),
  { server: false, watch: [currentPage] },
);

const library = computed(() => libRaw.value as UserLibraryList | null);
const total = computed(() => library.value?.total ?? 0);

// Local filter (client-side) — the endpoint doesn't accept search yet so
// we filter within the current page. Good enough for small libraries.
const items = computed(() => {
  const all = library.value?.items ?? [];
  const q = searchQuery.value.trim().toLowerCase();
  if (!q) return all;
  return all.filter((entry) =>
    localised(entry.book.title, entry.book.slug).toLowerCase().includes(q)
    || entry.book.author.display_name.toLowerCase().includes(q),
  );
});

function changePage(page: number) {
  router.push({ query: { ...route.query, page } });
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}

function setQuery(updates: Record<string, string | undefined>) {
  const next: Record<string, string> = {};
  for (const [k, v] of Object.entries(route.query)) {
    if (typeof v === "string") next[k] = v;
  }
  for (const [k, v] of Object.entries(updates)) {
    if (v === undefined || v === "") delete next[k];
    else next[k] = v;
  }
  router.push({ query: next });
}

function formatDate(iso: string) {
  return new Intl.DateTimeFormat(locale.value, {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(iso));
}

const downloading = ref<Set<string>>(new Set());
async function downloadBook(bookId: string, bookTitle: string) {
  if (downloading.value.has(bookId)) return;
  downloading.value.add(bookId);
  try {
    const resp = await api<DownloadResponse>(`/libraries/me/${bookId}/download`);
    window.open(resp.url, "_blank", "noopener,noreferrer");
    toast.success(t("library.download_started", { title: bookTitle }));
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("library.download_failed")));
  }
  finally {
    downloading.value.delete(bookId);
  }
}
</script>

<template>
  <AccountShell>
    <header class="space-y-2 mb-6">
      <div class="flex items-center gap-3">
        <span class="h-10 w-10 rounded-md bg-primary/10 text-primary inline-flex items-center justify-center shrink-0">
          <Icon name="library" class="h-5 w-5" />
        </span>
        <div>
          <h1 class="font-serif text-2xl md:text-3xl text-ink leading-tight">
            {{ t("library.title") }}
          </h1>
          <p class="text-sm text-ink-secondary">{{ t("library.subtitle") }}</p>
        </div>
      </div>
    </header>

    <!-- Search + count -->
    <div v-if="total > 0" class="flex flex-wrap items-center gap-2 mb-4">
      <div class="relative flex-1 min-w-[200px]">
        <Icon
          name="search"
          class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-tertiary pointer-events-none"
        />
        <input
          :value="searchQuery"
          type="search"
          :placeholder="t('library.search_placeholder')"
          class="w-full pl-9 pr-3 py-2 rounded-md border border-border bg-bg-card text-sm text-ink placeholder:text-ink-tertiary focus:outline-none focus:border-primary"
          @input="setQuery({ q: ($event.target as HTMLInputElement).value })"
        >
      </div>
      <span class="text-sm text-ink-secondary tabular-nums">
        {{ t("library.results", { n: total }) }}
      </span>
    </div>

    <!-- Loading -->
    <div
      v-if="pending && !library"
      class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4"
    >
      <div v-for="i in 4" :key="i" class="space-y-2">
        <UiSkeleton class="aspect-[2/3]" rounded="rounded-md" block />
        <UiSkeleton width="80%" height="0.9rem" block />
        <UiSkeleton width="50%" height="0.7rem" block />
      </div>
    </div>

    <!-- Error -->
    <div
      v-else-if="libError"
      class="rounded-md border border-error/30 bg-error/5 p-6 flex items-start gap-4"
    >
      <Icon name="warning-solid" class="h-6 w-6 text-error shrink-0" />
      <div>
        <h3 class="font-serif text-lg text-ink mb-1">{{ t("library.error_title") }}</h3>
        <p class="text-sm text-ink-secondary">{{ t("library.error_body") }}</p>
      </div>
    </div>

    <!-- Empty -->
    <UiEmptyState
      v-else-if="total === 0"
      icon="library"
      :title="t('library.empty_title')"
      :description="t('library.empty_body')"
    >
      <UiButton :to="localePath('/books')">
        <Icon name="book" class="h-4 w-4" />
        {{ t("library.empty_cta") }}
      </UiButton>
    </UiEmptyState>

    <UiEmptyState
      v-else-if="items.length === 0"
      icon="search"
      :title="t('library.no_match_title')"
      :description="t('library.no_match_body')"
    >
      <UiButton variant="ghost" @click="setQuery({ q: undefined })">
        <Icon name="close" class="h-4 w-4" />
        {{ t("library.clear_search") }}
      </UiButton>
    </UiEmptyState>

    <!-- Library grid -->
    <ul
      v-else
      class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4"
    >
      <li
        v-for="entry in items"
        :key="entry.id"
        class="rounded-md border border-border bg-bg-card overflow-hidden flex flex-col hover:border-primary transition-colors"
      >
        <NuxtLink :to="localePath(`/books/${entry.book.slug}`)" class="block">
          <BookCover
            :src="entry.book.cover_url"
            :alt="localised(entry.book.title, entry.book.slug)"
          />
        </NuxtLink>
        <div class="p-3 space-y-2 flex-1 flex flex-col">
          <NuxtLink
            :to="localePath(`/books/${entry.book.slug}`)"
            class="font-serif text-sm text-ink leading-snug line-clamp-2 hover:text-primary transition-colors"
          >
            {{ localised(entry.book.title, entry.book.slug) }}
          </NuxtLink>
          <p class="text-[11px] text-ink-tertiary truncate">
            {{ entry.book.author.display_name }}
          </p>
          <p class="inline-flex items-center gap-1 text-[10px] text-ink-tertiary">
            <Icon name="sparkles" class="h-3 w-3" />
            {{ t("library.acquired", { date: formatDate(entry.acquired_at) }) }}
          </p>
          <div class="mt-auto pt-2">
            <UiButton
              size="sm"
              block
              :loading="downloading.has(entry.book.id)"
              :disabled="downloading.has(entry.book.id)"
              @click="downloadBook(entry.book.id, localised(entry.book.title, entry.book.slug))"
            >
              <Icon name="document" class="h-4 w-4" />
              {{ t("library.download") }}
            </UiButton>
            <p
              v-if="entry.downloaded_count > 0"
              class="text-[10px] text-ink-tertiary mt-1.5 text-center"
            >
              {{ t("library.downloaded", { n: entry.downloaded_count }) }}
            </p>
          </div>
        </div>
      </li>
    </ul>

    <div v-if="total > PAGE_SIZE" class="mt-8">
      <UiPagination
        :page="currentPage"
        :page-size="PAGE_SIZE"
        :total="total"
        @change="changePage"
      />
    </div>
  </AccountShell>
</template>
