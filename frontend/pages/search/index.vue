<script setup lang="ts">
import type { BookList, CategoryList } from "~/types/api";

const { t } = useI18n();
const { localised } = useLocaleText();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const api = useApi();

useSiteSeo({
  title: t("search.title"),
  description: t("search.placeholder"),
  noindex: true,
});

const PAGE_SIZE = 18;

const queryParams = computed(() => {
  const isFree = route.query.is_free === "true";
  return {
    q: ((route.query.q as string) || "").trim() || undefined,
    category: (route.query.category as string) || undefined,
    language: (route.query.language as string) || undefined,
    min_price: route.query.min_price ? Number(route.query.min_price) : undefined,
    max_price: !isFree && route.query.max_price ? Number(route.query.max_price) : undefined,
    is_free: isFree ? true : undefined,
    featured: route.query.featured === "true" ? true : undefined,
    sort: (route.query.sort as string) || "-published_at",
    page: Math.max(1, Number(route.query.page) || 1),
    page_size: PAGE_SIZE,
  };
});

const { data: resultsRaw, pending, error: searchError } = await useAsyncData(
  "search:books",
  () => {
    if (!queryParams.value.q) {
      return Promise.resolve({ items: [], total: 0, page: 1, page_size: PAGE_SIZE } as BookList);
    }
    return api<BookList>("/search", { query: queryParams.value });
  },
  { watch: [queryParams] },
);

const results = computed(() => resultsRaw.value as BookList | null);

const { data: categoriesRaw } = await useAsyncData(
  "search:categories",
  () => api<CategoryList>("/categories", { query: { active_only: true } }),
);

const categoryOptions = computed(() => {
  const items = ((categoriesRaw.value as CategoryList | null)?.items ?? []);
  const byId = new Map(items.map((c) => [c.id, c]));
  return [
    { value: "", label: t("catalog.filters.category_any") },
    ...items.map((c) => {
      const prefix = c.parent_id && byId.has(c.parent_id) ? "— " : "";
      return {
        value: c.slug,
        label: `${prefix}${localised(c.name, c.slug)}`,
      };
    }),
  ];
});

const languageOptions = [
  { value: "", label: t("catalog.filters.language_any") },
  { value: "uz", label: "O'zbekcha" },
  { value: "ru", label: "Русский" },
  { value: "en", label: "English" },
  { value: "mixed", label: t("catalog.filters.language_mixed") },
];

const sortOptions = computed(() => [
  { value: "-published_at", label: t("catalog.sort.newest") },
  { value: "price", label: t("catalog.sort.price_asc") },
  { value: "-price", label: t("catalog.sort.price_desc") },
  { value: "-average_rating", label: t("catalog.sort.rating") },
  { value: "-sales_count", label: t("catalog.sort.sales") },
]);

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
  router.push({ query: queryParams.value.q ? { q: queryParams.value.q } : {} });
}

const hasQuery = computed(() => !!queryParams.value.q);
const total = computed(() => results.value?.total ?? 0);

const hasActiveFilters = computed(
  () =>
    Boolean(
      queryParams.value.category
      || queryParams.value.language
      || queryParams.value.min_price != null
      || queryParams.value.max_price != null
      || queryParams.value.featured
      || queryParams.value.is_free,
    ),
);

const activeChips = computed<{ key: string; label: string; clear: () => void }[]>(() => {
  const chips: { key: string; label: string; clear: () => void }[] = [];
  if (queryParams.value.category) {
    const cat = (categoriesRaw.value as CategoryList | null)?.items.find(
      (c) => c.slug === queryParams.value.category,
    );
    chips.push({
      key: "category",
      label: cat ? localised(cat.name, cat.slug) : queryParams.value.category,
      clear: () => setQuery({ category: undefined }),
    });
  }
  if (queryParams.value.language) {
    const lang = languageOptions.find((l) => l.value === queryParams.value.language);
    chips.push({
      key: "language",
      label: lang?.label ?? queryParams.value.language,
      clear: () => setQuery({ language: undefined }),
    });
  }
  if (queryParams.value.is_free) {
    chips.push({
      key: "free",
      label: t("catalog.filters.free_only"),
      clear: () => setQuery({ is_free: undefined }),
    });
  }
  else {
    if (queryParams.value.min_price != null) {
      chips.push({
        key: "min_price",
        label: `${t("catalog.filters.min_price")}: ${queryParams.value.min_price}`,
        clear: () => setQuery({ min_price: undefined }),
      });
    }
    if (queryParams.value.max_price != null) {
      chips.push({
        key: "max_price",
        label: `${t("catalog.filters.max_price")}: ${queryParams.value.max_price}`,
        clear: () => setQuery({ max_price: undefined }),
      });
    }
  }
  if (queryParams.value.featured) {
    chips.push({
      key: "featured",
      label: t("catalog.filters.featured_only"),
      clear: () => setQuery({ featured: undefined }),
    });
  }
  return chips;
});

// Recent searches in localStorage
const RECENT_KEY = "monografiya:search:recent";
const recentSearches = ref<string[]>([]);

function loadRecent() {
  if (!import.meta.client) return;
  try {
    const raw = window.localStorage.getItem(RECENT_KEY);
    if (raw) recentSearches.value = (JSON.parse(raw) as string[]).slice(0, 6);
  }
  catch { /* ignore */ }
}
function persistRecent(q: string) {
  if (!import.meta.client) return;
  const cleaned = q.trim();
  if (!cleaned) return;
  const next = [cleaned, ...recentSearches.value.filter((x) => x !== cleaned)].slice(0, 6);
  recentSearches.value = next;
  try {
    window.localStorage.setItem(RECENT_KEY, JSON.stringify(next));
  }
  catch { /* ignore */ }
}
function clearRecent() {
  recentSearches.value = [];
  if (import.meta.client) window.localStorage.removeItem(RECENT_KEY);
}

onMounted(loadRecent);
watch(
  () => queryParams.value.q,
  (v) => {
    if (v) persistRecent(v);
  },
);

// Popular categories (top 4 by book_count) — shown when query is empty
const popularCategories = computed(() => {
  const items = ((categoriesRaw.value as CategoryList | null)?.items ?? [])
    .filter((c) => c.parent_id === null)
    .slice()
    .sort((a, b) => b.book_count - a.book_count)
    .slice(0, 6);
  return items;
});

// Mobile filter drawer
const drawerOpen = ref(false);
watch(() => route.fullPath, () => { drawerOpen.value = false; });
watch(drawerOpen, (open) => {
  if (import.meta.client) document.body.style.overflow = open ? "hidden" : "";
});
onBeforeUnmount(() => {
  if (import.meta.client) document.body.style.overflow = "";
});
useEscape(() => { drawerOpen.value = false; }, { enabled: drawerOpen });
</script>

<template>
  <section class="bg-bg">
    <!-- Hero search -->
    <header class="relative overflow-hidden border-b border-border">
      <div
        aria-hidden="true"
        class="absolute inset-0 -z-10"
        style="background-image:
          radial-gradient(ellipse 60% 50% at 50% 0%, color-mix(in oklab, var(--color-primary) 10%, transparent), transparent 65%);"
      />
      <div class="max-w-3xl mx-auto px-4 py-12 md:py-16 space-y-5">
        <div class="text-center space-y-2">
          <h1 class="font-serif text-3xl md:text-5xl text-ink leading-tight tracking-tight">
            {{ t("search.title") }}
          </h1>
          <p class="text-ink-secondary">{{ t("search.subtitle") }}</p>
        </div>

        <form class="relative max-w-2xl mx-auto" @submit.prevent="submitSearch">
          <Icon
            name="search"
            class="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-ink-tertiary pointer-events-none"
          />
          <input
            v-model="searchInput"
            type="search"
            autofocus
            :placeholder="t('search.placeholder')"
            class="w-full pl-12 pr-28 py-3.5 rounded-full border border-border bg-bg-card text-ink text-base placeholder:text-ink-tertiary focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 shadow-sm"
            autocomplete="off"
          >
          <button
            type="submit"
            class="absolute right-1.5 top-1/2 -translate-y-1/2 inline-flex items-center gap-1 px-4 py-2 rounded-full bg-primary text-ink-inverse text-sm font-medium hover:bg-primary-hover transition-colors"
          >
            {{ t("search.submit") }}
            <Icon name="arrow-right" class="h-4 w-4" />
          </button>
        </form>

        <p v-if="hasQuery" class="text-sm text-ink-secondary text-center">
          <span class="text-ink">{{ t("search.results_for", { q: queryParams.q }) }}</span>
          <span class="text-ink-tertiary"> · {{ t("search.results_count", { n: total }) }}</span>
        </p>
      </div>
    </header>

    <div class="max-w-6xl mx-auto px-4 py-8 md:py-10">
      <!-- EMPTY QUERY STATE -->
      <template v-if="!hasQuery">
        <div class="grid md:grid-cols-2 gap-6 md:gap-8">
          <!-- Recent searches -->
          <section
            v-if="recentSearches.length > 0"
            class="rounded-md border border-border bg-bg-card p-5 space-y-3"
          >
            <div class="flex items-center justify-between">
              <h2 class="inline-flex items-center gap-2 text-sm uppercase tracking-wider text-ink-tertiary">
                <Icon name="arrow-path" class="h-4 w-4" />
                {{ t("search.recent") }}
              </h2>
              <button
                type="button"
                class="text-xs text-ink-tertiary hover:text-error"
                @click="clearRecent"
              >
                {{ t("search.clear_recent") }}
              </button>
            </div>
            <div class="flex flex-wrap gap-1.5">
              <button
                v-for="q in recentSearches"
                :key="q"
                type="button"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-border bg-bg text-sm text-ink-secondary hover:border-primary hover:text-primary transition-colors"
                @click="searchInput = q; submitSearch()"
              >
                <Icon name="search" class="h-3.5 w-3.5" />
                {{ q }}
              </button>
            </div>
          </section>

          <!-- Popular categories -->
          <section
            v-if="popularCategories.length > 0"
            class="rounded-md border border-border bg-bg-card p-5 space-y-3"
            :class="recentSearches.length === 0 ? 'md:col-span-2' : ''"
          >
            <h2 class="inline-flex items-center gap-2 text-sm uppercase tracking-wider text-ink-tertiary">
              <Icon name="sparkles" class="h-4 w-4" />
              {{ t("search.popular_topics") }}
            </h2>
            <div class="grid grid-cols-2 gap-2">
              <NuxtLink
                v-for="cat in popularCategories"
                :key="cat.id"
                :to="localePath(`/category/${cat.slug}`)"
                class="group flex items-center gap-2 px-3 py-2 rounded-md border border-border bg-bg hover:border-primary transition-colors"
              >
                <Icon :name="cat.icon" fallback="book" class="h-4 w-4 text-primary shrink-0" />
                <span class="text-sm text-ink-secondary group-hover:text-primary truncate flex-1">
                  {{ localised(cat.name, cat.slug) }}
                </span>
                <span class="text-xs text-ink-tertiary tabular-nums shrink-0">
                  {{ cat.book_count }}
                </span>
              </NuxtLink>
            </div>
          </section>
        </div>

        <UiEmptyState
          v-if="recentSearches.length === 0 && popularCategories.length === 0"
          icon="search"
          :title="t('search.empty_query_title')"
          :description="t('search.empty_query_body')"
        />
      </template>

      <!-- RESULTS -->
      <template v-else>
        <!-- Toolbar: filter trigger (mobile) + sort + chips -->
        <div class="flex flex-wrap items-center gap-2 mb-4">
          <button
            type="button"
            class="md:hidden inline-flex items-center gap-1.5 px-3 py-2 rounded-md border border-border bg-bg-card text-sm text-ink-secondary hover:border-primary hover:text-primary"
            @click="drawerOpen = true"
          >
            <Icon name="settings" class="h-4 w-4" />
            {{ t("catalog.filters.label") }}
            <span
              v-if="activeChips.length"
              class="inline-flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full bg-primary text-ink-inverse text-[10px] font-semibold"
            >
              {{ activeChips.length }}
            </span>
          </button>

          <div class="flex-1" />

          <div class="relative">
            <Icon
              name="chart"
              class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-tertiary pointer-events-none"
            />
            <select
              :value="queryParams.sort"
              class="appearance-none pl-9 pr-9 py-2 rounded-md border border-border bg-bg-card text-sm text-ink focus:outline-none focus:border-primary cursor-pointer"
              @change="setQuery({ sort: ($event.target as HTMLSelectElement).value })"
            >
              <option v-for="s in sortOptions" :key="s.value" :value="s.value">
                {{ s.label }}
              </option>
            </select>
            <Icon
              name="chevron-down"
              class="absolute right-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-tertiary pointer-events-none"
            />
          </div>
        </div>

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

        <div class="grid md:grid-cols-[260px_1fr] gap-6 md:gap-8">
          <!-- Desktop sidebar -->
          <aside class="hidden md:block">
            <div class="sticky top-20 space-y-4">
              <div class="rounded-md border border-border bg-bg-card p-4 space-y-5">
                <div class="flex items-center justify-between">
                  <h2 class="text-sm uppercase tracking-wider text-ink-tertiary">
                    {{ t("catalog.filters.label") }}
                  </h2>
                  <button
                    v-if="hasActiveFilters"
                    type="button"
                    class="text-xs text-primary hover:underline"
                    @click="clearAll"
                  >
                    {{ t("catalog.filters.clear") }}
                  </button>
                </div>

                <UiSelect
                  :model-value="queryParams.category ?? ''"
                  :label="t('catalog.filters.category')"
                  :options="categoryOptions"
                  @update:model-value="(v) => setQuery({ category: v })"
                />

                <UiSelect
                  :model-value="queryParams.language ?? ''"
                  :label="t('catalog.filters.language')"
                  :options="languageOptions"
                  @update:model-value="(v) => setQuery({ language: v })"
                />

                <div>
                  <span class="block text-sm text-ink-secondary mb-1.5">
                    {{ t("catalog.filters.price_range") }}
                  </span>
                  <div class="grid grid-cols-2 gap-2">
                    <input
                      type="number"
                      :placeholder="t('catalog.filters.min_price')"
                      :value="queryParams.min_price ?? ''"
                      min="0"
                      class="px-2.5 py-1.5 rounded border border-border bg-bg text-sm focus:outline-none focus:border-primary"
                      @change="setQuery({ min_price: ($event.target as HTMLInputElement).value })"
                    >
                    <input
                      type="number"
                      :placeholder="t('catalog.filters.max_price')"
                      :value="queryParams.max_price ?? ''"
                      min="0"
                      :disabled="queryParams.is_free === true"
                      class="px-2.5 py-1.5 rounded border border-border bg-bg text-sm focus:outline-none focus:border-primary disabled:opacity-50"
                      @change="setQuery({ max_price: ($event.target as HTMLInputElement).value })"
                    >
                  </div>
                </div>

                <div class="space-y-2 pt-1 border-t border-border">
                  <label class="flex items-center gap-2 text-sm text-ink cursor-pointer">
                    <input
                      type="checkbox"
                      class="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                      :checked="queryParams.is_free === true"
                      @change="setQuery({ is_free: ($event.target as HTMLInputElement).checked })"
                    >
                    <Icon name="gift" class="h-4 w-4 text-success" />
                    {{ t("catalog.filters.free_only") }}
                  </label>
                  <label class="flex items-center gap-2 text-sm text-ink cursor-pointer">
                    <input
                      type="checkbox"
                      class="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                      :checked="queryParams.featured === true"
                      @change="setQuery({ featured: ($event.target as HTMLInputElement).checked })"
                    >
                    <Icon name="star-solid" class="h-4 w-4 text-accent-gold" />
                    {{ t("catalog.filters.featured_only") }}
                  </label>
                </div>
              </div>
            </div>
          </aside>

          <!-- Results column -->
          <div class="min-w-0">
            <div
              v-if="pending && !results"
              class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-5"
            >
              <div v-for="i in 6" :key="i" class="space-y-2">
                <UiSkeleton class="aspect-[2/3]" rounded="rounded-md" block />
                <UiSkeleton width="80%" height="0.95rem" block />
                <UiSkeleton width="50%" height="0.7rem" block />
              </div>
            </div>

            <div
              v-else-if="searchError"
              class="rounded-md border border-error/30 bg-error/5 p-6 flex items-start gap-4"
            >
              <Icon name="warning-solid" class="h-6 w-6 text-error shrink-0" />
              <div>
                <h3 class="font-serif text-lg text-ink mb-1">{{ t("search.error_title") }}</h3>
                <p class="text-sm text-ink-secondary">{{ t("search.error_body") }}</p>
              </div>
            </div>

            <UiEmptyState
              v-else-if="(results?.items.length ?? 0) === 0"
              icon="search"
              :title="t('search.no_results')"
              :description="t('search.no_results_body')"
            >
              <UiButton v-if="hasActiveFilters" variant="ghost" @click="clearAll">
                <Icon name="close" class="h-4 w-4" />
                {{ t("catalog.filters.clear") }}
              </UiButton>
            </UiEmptyState>

            <div v-else>
              <div
                class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-5 transition-opacity"
                :class="pending ? 'opacity-50 pointer-events-none' : ''"
              >
                <BookCard v-for="b in results!.items" :key="b.id" :book="b" />
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
        </div>
      </template>
    </div>

    <!-- Mobile drawer -->
    <Teleport v-if="drawerOpen" to="body">
      <Transition
        appear
        enter-active-class="transition duration-150"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
      >
        <div
          class="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden"
          @click="drawerOpen = false"
        />
      </Transition>
      <Transition
        appear
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="translate-y-full"
        enter-to-class="translate-y-0"
      >
        <aside
          class="fixed bottom-0 inset-x-0 z-50 bg-bg-elevated border-t border-border rounded-t-xl shadow-2xl md:hidden max-h-[85vh] flex flex-col"
          role="dialog"
          aria-modal="true"
        >
          <header class="flex items-center justify-between p-4 border-b border-border">
            <h2 class="font-medium text-ink">{{ t("catalog.filters.label") }}</h2>
            <button
              type="button"
              class="h-8 w-8 inline-flex items-center justify-center rounded text-ink-secondary hover:bg-bg-secondary hover:text-ink"
              :aria-label="t('common.cancel')"
              @click="drawerOpen = false"
            >
              <Icon name="close" class="h-5 w-5" />
            </button>
          </header>
          <div class="overflow-y-auto p-4 space-y-5 flex-1">
            <UiSelect
              :model-value="queryParams.category ?? ''"
              :label="t('catalog.filters.category')"
              :options="categoryOptions"
              @update:model-value="(v) => setQuery({ category: v })"
            />
            <UiSelect
              :model-value="queryParams.language ?? ''"
              :label="t('catalog.filters.language')"
              :options="languageOptions"
              @update:model-value="(v) => setQuery({ language: v })"
            />
            <div>
              <span class="block text-sm text-ink-secondary mb-1.5">
                {{ t("catalog.filters.price_range") }}
              </span>
              <div class="grid grid-cols-2 gap-2">
                <input
                  type="number"
                  :placeholder="t('catalog.filters.min_price')"
                  :value="queryParams.min_price ?? ''"
                  min="0"
                  class="px-2.5 py-2 rounded border border-border bg-bg text-sm focus:outline-none focus:border-primary"
                  @change="setQuery({ min_price: ($event.target as HTMLInputElement).value })"
                >
                <input
                  type="number"
                  :placeholder="t('catalog.filters.max_price')"
                  :value="queryParams.max_price ?? ''"
                  min="0"
                  :disabled="queryParams.is_free === true"
                  class="px-2.5 py-2 rounded border border-border bg-bg text-sm focus:outline-none focus:border-primary disabled:opacity-50"
                  @change="setQuery({ max_price: ($event.target as HTMLInputElement).value })"
                >
              </div>
            </div>
            <div class="space-y-2 pt-2 border-t border-border">
              <label class="flex items-center gap-2 text-sm text-ink cursor-pointer">
                <input
                  type="checkbox"
                  class="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                  :checked="queryParams.is_free === true"
                  @change="setQuery({ is_free: ($event.target as HTMLInputElement).checked })"
                >
                <Icon name="gift" class="h-4 w-4 text-success" />
                {{ t("catalog.filters.free_only") }}
              </label>
              <label class="flex items-center gap-2 text-sm text-ink cursor-pointer">
                <input
                  type="checkbox"
                  class="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                  :checked="queryParams.featured === true"
                  @change="setQuery({ featured: ($event.target as HTMLInputElement).checked })"
                >
                <Icon name="star-solid" class="h-4 w-4 text-accent-gold" />
                {{ t("catalog.filters.featured_only") }}
              </label>
            </div>
          </div>
          <footer class="p-4 border-t border-border flex items-center justify-between gap-3">
            <button
              v-if="hasActiveFilters"
              type="button"
              class="text-sm text-error hover:underline"
              @click="clearAll"
            >
              {{ t("catalog.filters.clear") }}
            </button>
            <span v-else class="text-xs text-ink-tertiary">
              {{ t("search.results_count", { n: total }) }}
            </span>
            <UiButton @click="drawerOpen = false">
              <Icon name="check" class="h-4 w-4" />
              {{ t("catalog.filters.apply") }}
            </UiButton>
          </footer>
        </aside>
      </Transition>
    </Teleport>
  </section>
</template>
