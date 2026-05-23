<script setup lang="ts">
import type { DownloadResponse, UserLibraryList } from "~/types/api";

definePageMeta({ middleware: "auth" });

const { t, locale } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const { localised } = useLocaleText();
const api = useApi();

const PAGE_SIZE = 20;
const currentPage = computed(() => Math.max(1, Number(route.query.page) || 1));

const { data: libRaw, pending } = await useAsyncData(
  "account:library",
  () =>
    api<UserLibraryList>("/libraries/me", {
      query: { page: currentPage.value, page_size: PAGE_SIZE },
    }),
  { watch: [currentPage] },
);

const library = computed(() => libRaw.value as UserLibraryList | null);

useHead({ title: t("library.title") });

const breadcrumbs = computed(() => [
  { label: t("nav.home"), to: localePath("/") },
  { label: t("account.title"), to: localePath("/account") },
  { label: t("library.title") },
]);

function changePage(page: number) {
  router.push({ query: { ...route.query, page } });
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}

function formatDate(iso: string) {
  return new Intl.DateTimeFormat(locale.value, {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(iso));
}

const downloading = ref<Set<string>>(new Set());

async function downloadBook(bookId: string) {
  if (downloading.value.has(bookId)) return;
  downloading.value.add(bookId);
  try {
    const resp = await api<DownloadResponse>(`/libraries/me/${bookId}/download`);
    // Open in a new tab — the signed URL is short-lived but a direct
    // navigation gives the cleanest UX with the browser's PDF viewer.
    window.open(resp.url, "_blank", "noopener,noreferrer");
  }
  catch {
    // Phase 4.8 polish will surface a toast here.
  }
  finally {
    downloading.value.delete(bookId);
  }
}
</script>

<template>
  <section class="max-w-6xl mx-auto px-4 py-8 space-y-6">
    <UiBreadcrumbs :items="breadcrumbs" />

    <header class="space-y-1">
      <h1 class="font-serif text-3xl text-ink">{{ t("library.title") }}</h1>
      <p class="text-sm text-ink-secondary">{{ t("library.subtitle") }}</p>
    </header>

    <div
      v-if="pending && !library"
      class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4"
    >
      <div v-for="i in 4" :key="i" class="space-y-2">
        <UiSkeleton class="aspect-[2/3] !block" :rounded="'rounded'" />
        <UiSkeleton :width="'80%'" :height="'1rem'" :block="true" />
      </div>
    </div>

    <UiEmptyState
      v-else-if="(library?.items.length ?? 0) === 0"
      icon="library"
      :title="t('library.empty_title')"
      :description="t('library.empty_body')"
    >
      <UiButton :to="localePath('/books')">{{ t("home.hero.cta_browse") }}</UiButton>
    </UiEmptyState>

    <ul
      v-else
      class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4"
    >
      <li
        v-for="entry in library!.items"
        :key="entry.id"
        class="rounded-md border border-border bg-bg-card shadow-sm overflow-hidden flex flex-col"
      >
        <NuxtLink :to="localePath(`/books/${entry.book.slug}`)">
          <BookCover
            :src="entry.book.cover_url"
            :alt="localised(entry.book.title, entry.book.slug)"
          />
        </NuxtLink>
        <div class="p-3 space-y-2 flex-1 flex flex-col">
          <h3 class="font-serif text-ink leading-snug line-clamp-2">
            <NuxtLink
              :to="localePath(`/books/${entry.book.slug}`)"
              class="hover:text-primary"
            >
              {{ localised(entry.book.title, entry.book.slug) }}
            </NuxtLink>
          </h3>
          <p class="text-xs text-ink-tertiary">
            {{ t("library.acquired", { date: formatDate(entry.acquired_at) }) }}
          </p>
          <div class="mt-auto pt-2">
            <UiButton
              size="sm"
              :block="true"
              :loading="downloading.has(entry.book.id)"
              :disabled="downloading.has(entry.book.id)"
              @click="downloadBook(entry.book.id)"
            >
              {{ t("library.download") }}
            </UiButton>
            <p
              v-if="entry.downloaded_count > 0"
              class="text-[10px] text-ink-tertiary mt-1 text-center"
            >
              {{ t("library.downloaded", { n: entry.downloaded_count }) }}
            </p>
          </div>
        </div>
      </li>
    </ul>

    <div class="pt-4">
      <UiPagination
        :page="currentPage"
        :page-size="PAGE_SIZE"
        :total="library?.total ?? 0"
        @change="changePage"
      />
    </div>
  </section>
</template>
