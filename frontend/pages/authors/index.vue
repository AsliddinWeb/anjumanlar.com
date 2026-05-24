<script setup lang="ts">
import type { AuthorList } from "~/types/api";

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const api = useApi();

useSiteSeo({
  title: t("authors.title"),
  description: t("authors.subtitle"),
});

const PAGE_SIZE = 18;

const queryParams = computed(() => ({
  search: ((route.query.q as string) || "").trim() || undefined,
  featured: route.query.featured === "true" ? true : undefined,
  verified: route.query.verified === "true" ? true : undefined,
  page: Math.max(1, Number(route.query.page) || 1),
  page_size: PAGE_SIZE,
}));

const { data: authorsRaw, pending, error: authorsError } = await useAsyncData(
  "authors:list",
  () => api<AuthorList>("/authors", { query: queryParams.value }),
  { watch: [queryParams] },
);

const authors = computed(() => authorsRaw.value as AuthorList | null);
const total = computed(() => authors.value?.total ?? 0);

const searchInput = ref((route.query.q as string) || "");
watch(
  () => route.query.q,
  (v) => {
    searchInput.value = (v as string) || "";
  },
);

function setQuery(updates: Record<string, string | number | boolean | undefined>) {
  const next: Record<string, string> = {};
  for (const [k, v] of Object.entries(route.query)) {
    if (typeof v === "string") next[k] = v;
  }
  for (const [key, value] of Object.entries(updates)) {
    if (value === undefined || value === null || value === "" || value === false) {
      delete next[key];
    }
    else {
      next[key] = String(value);
    }
  }
  if (!("page" in updates)) delete next.page;
  router.push({ query: next });
}

function submitSearch() {
  setQuery({ q: searchInput.value.trim() || undefined });
}

function changePage(page: number) {
  setQuery({ page });
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}

function clearAll() {
  router.push({ query: {} });
}

const hasActiveFilters = computed(
  () => Boolean(queryParams.value.search || queryParams.value.featured || queryParams.value.verified),
);

const activeChips = computed<{ key: string; label: string; clear: () => void }[]>(() => {
  const chips: { key: string; label: string; clear: () => void }[] = [];
  if (queryParams.value.search) {
    chips.push({
      key: "q",
      label: `"${queryParams.value.search}"`,
      clear: () => setQuery({ q: undefined }),
    });
  }
  if (queryParams.value.featured) {
    chips.push({
      key: "featured",
      label: t("authors.featured"),
      clear: () => setQuery({ featured: undefined }),
    });
  }
  if (queryParams.value.verified) {
    chips.push({
      key: "verified",
      label: t("authors.verified"),
      clear: () => setQuery({ verified: undefined }),
    });
  }
  return chips;
});
</script>

<template>
  <section class="bg-bg">
    <!-- Hero -->
    <header class="relative overflow-hidden border-b border-border">
      <div
        aria-hidden="true"
        class="absolute inset-0 -z-10"
        style="background-image:
          radial-gradient(ellipse 60% 50% at 50% 0%, color-mix(in oklab, var(--color-primary) 10%, transparent), transparent 65%);"
      />
      <div class="max-w-3xl mx-auto px-4 py-12 md:py-16 text-center space-y-4">
        <span class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-bg-card/80 backdrop-blur text-xs text-ink-secondary">
          <Icon name="academic" class="h-3.5 w-3.5 text-primary" />
          {{ t("authors.tag") }}
        </span>
        <h1 class="font-serif text-3xl md:text-5xl text-ink leading-tight tracking-tight">
          {{ t("authors.title") }}
        </h1>
        <p class="text-ink-secondary max-w-2xl mx-auto">{{ t("authors.subtitle") }}</p>

        <!-- Search bar -->
        <form class="relative max-w-xl mx-auto pt-2" @submit.prevent="submitSearch">
          <Icon
            name="search"
            class="absolute left-4 top-1/2 -translate-y-1/2 mt-1 h-5 w-5 text-ink-tertiary pointer-events-none"
          />
          <input
            v-model="searchInput"
            type="search"
            :placeholder="t('authors.search_placeholder')"
            class="w-full pl-12 pr-4 py-3 rounded-full border border-border bg-bg-card text-ink text-base placeholder:text-ink-tertiary focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 shadow-sm"
            autocomplete="off"
          >
        </form>
      </div>
    </header>

    <div class="max-w-6xl mx-auto px-4 py-8 md:py-10">
      <!-- Toolbar -->
      <div class="flex flex-wrap items-center gap-2 mb-4">
        <div class="flex flex-wrap items-center gap-2">
          <button
            type="button"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium transition-colors"
            :class="queryParams.featured
              ? 'border-primary bg-primary/10 text-primary'
              : 'border-border bg-bg-card text-ink-secondary hover:border-primary hover:text-primary'"
            @click="setQuery({ featured: !queryParams.featured })"
          >
            <Icon name="star-solid" class="h-3.5 w-3.5" :class="queryParams.featured ? 'text-accent-gold' : ''" />
            {{ t("authors.featured") }}
          </button>
          <button
            type="button"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium transition-colors"
            :class="queryParams.verified
              ? 'border-primary bg-primary/10 text-primary'
              : 'border-border bg-bg-card text-ink-secondary hover:border-primary hover:text-primary'"
            @click="setQuery({ verified: !queryParams.verified })"
          >
            <Icon name="check-circle-solid" class="h-3.5 w-3.5" :class="queryParams.verified ? 'text-success' : ''" />
            {{ t("authors.verified") }}
          </button>
        </div>

        <div class="flex-1" />

        <span class="inline-flex items-center gap-1.5 text-sm text-ink-secondary">
          <Icon name="users" class="h-4 w-4 text-primary" />
          <span class="tabular-nums">{{ t("authors.results", { n: total }) }}</span>
        </span>
      </div>

      <!-- Active filter chips -->
      <div v-if="activeChips.length" class="flex flex-wrap items-center gap-1.5 mb-4">
        <span class="text-xs text-ink-tertiary mr-1">{{ t("catalog.active_filters") }}:</span>
        <button
          v-for="chip in activeChips"
          :key="chip.key"
          type="button"
          class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs hover:bg-primary/20 transition-colors"
          @click="chip.clear()"
        >
          {{ chip.label }}
          <Icon name="close" class="h-3 w-3" />
        </button>
        <button
          type="button"
          class="ml-1 text-xs text-ink-secondary hover:text-error"
          @click="clearAll"
        >
          {{ t("catalog.filters.clear") }}
        </button>
      </div>

      <!-- Loading -->
      <div
        v-if="pending && !authors"
        class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3"
      >
        <div v-for="i in 6" :key="i" class="rounded-md border border-border bg-bg-card p-4 flex items-start gap-3">
          <UiSkeleton width="3rem" height="3rem" rounded="rounded-full" />
          <div class="flex-1 space-y-2">
            <UiSkeleton width="70%" height="0.95rem" block />
            <UiSkeleton width="50%" height="0.7rem" block />
            <UiSkeleton width="40%" height="0.7rem" block />
          </div>
        </div>
      </div>

      <!-- Error -->
      <div
        v-else-if="authorsError"
        class="rounded-md border border-error/30 bg-error/5 p-6 flex items-start gap-4"
      >
        <Icon name="warning-solid" class="h-6 w-6 text-error shrink-0" />
        <div>
          <h2 class="font-serif text-lg text-ink mb-1">{{ t("authors.error_title") }}</h2>
          <p class="text-sm text-ink-secondary">{{ t("authors.error_body") }}</p>
        </div>
      </div>

      <!-- Empty -->
      <UiEmptyState
        v-else-if="(authors?.items.length ?? 0) === 0"
        icon="academic"
        :title="hasActiveFilters ? t('catalog.no_results') : t('authors.no_authors')"
        :description="hasActiveFilters ? t('catalog.no_results_body') : t('authors.no_authors_body')"
      >
        <UiButton v-if="hasActiveFilters" variant="ghost" @click="clearAll">
          <Icon name="close" class="h-4 w-4" />
          {{ t("catalog.filters.clear") }}
        </UiButton>
      </UiEmptyState>

      <!-- Authors grid -->
      <div v-else>
        <div
          class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 transition-opacity"
          :class="pending ? 'opacity-50 pointer-events-none' : ''"
        >
          <AuthorCard
            v-for="author in authors!.items"
            :key="author.id"
            :author="author"
          />
        </div>

        <div v-if="total > PAGE_SIZE" class="mt-8">
          <UiPagination
            :page="queryParams.page"
            :page-size="PAGE_SIZE"
            :total="total"
            @change="changePage"
          />
        </div>
      </div>
    </div>
  </section>
</template>
