<script setup lang="ts">
import type { BookList, CategoryList } from "~/types/api";

const { t } = useI18n();
const { localised } = useLocaleText();
const route = useRoute();
const router = useRouter();
const api = useApi();

useSiteSeo({
  title: t("search.title"),
  description: t("search.placeholder"),
  noindex: true,
});

const PAGE_SIZE = 20;

const queryParams = computed(() => {
  const isFree = route.query.is_free === "true";
  const maxFromFree = isFree ? 0 : route.query.max_price;
  return {
    q: ((route.query.q as string) || "").trim() || undefined,
    category: (route.query.category as string) || undefined,
    language: (route.query.language as string) || undefined,
    min_price: route.query.min_price ? Number(route.query.min_price) : undefined,
    max_price: maxFromFree !== undefined ? Number(maxFromFree) : undefined,
    is_free: isFree ? true : undefined,
    featured: route.query.featured === "true" ? true : undefined,
    sort: (route.query.sort as string) || "-published_at",
    page: Math.max(1, Number(route.query.page) || 1),
    page_size: PAGE_SIZE,
  };
});

const { data: resultsRaw, pending } = await useAsyncData(
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
  return items.map((c) => {
    const prefix = c.parent_id && byId.has(c.parent_id) ? "— " : "";
    return {
      value: c.slug,
      label: `${prefix}${localised(c.name, c.slug)}`,
    };
  });
});

const languageOptions = [
  { value: "uz", label: "O'zbekcha" },
  { value: "ru", label: "Русский" },
  { value: "en", label: "English" },
  { value: "mixed", label: "Mixed" },
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

const hasQuery = computed(() => !!queryParams.value.q);
const total = computed(() => results.value?.total ?? 0);
</script>

<template>
  <section class="max-w-6xl mx-auto px-4 py-8 space-y-6">
    <header class="space-y-3">
      <h1 class="font-serif text-3xl text-ink">{{ t("search.title") }}</h1>

      <form class="flex gap-2 max-w-2xl" @submit.prevent="submitSearch">
        <div class="flex-1">
          <UiInput
            v-model="searchInput"
            :placeholder="t('search.placeholder')"
            autocomplete="off"
          />
        </div>
        <UiButton type="submit">{{ t("search.submit") }}</UiButton>
      </form>

      <p v-if="hasQuery" class="text-sm text-ink-secondary">
        <span>{{ t("search.results_for", { q: queryParams.q }) }}</span>
        <span class="text-ink-tertiary"> · {{ t("search.results_count", { n: total }) }}</span>
      </p>
    </header>

    <!-- Empty query state -->
    <UiEmptyState
      v-if="!hasQuery"
      icon="🔎"
      :title="t('search.empty_query_title')"
      :description="t('search.empty_query_body')"
    />

    <div v-else class="grid md:grid-cols-[260px_1fr] gap-6">
      <!-- Filters -->
      <aside class="space-y-4">
        <h2 class="font-medium text-ink">{{ t("catalog.filters.label") }}</h2>

        <UiSelect
          :model-value="queryParams.category ?? ''"
          :label="t('catalog.filters.category')"
          :options="categoryOptions"
          :placeholder="t('catalog.filters.category_any')"
          @update:model-value="(v) => setQuery({ category: v })"
        />

        <UiSelect
          :model-value="queryParams.language ?? ''"
          :label="t('catalog.filters.language')"
          :options="languageOptions"
          :placeholder="t('catalog.filters.language_any')"
          @update:model-value="(v) => setQuery({ language: v })"
        />

        <div>
          <span class="block text-sm text-ink-secondary mb-1">
            {{ t("catalog.filters.price_range") }}
          </span>
          <div class="grid grid-cols-2 gap-2">
            <input
              type="number"
              :placeholder="t('catalog.filters.min_price')"
              :value="queryParams.min_price ?? ''"
              min="0"
              class="px-2 py-1.5 rounded border border-border bg-bg-card text-sm text-ink focus:outline-none focus:border-primary"
              @change="setQuery({ min_price: ($event.target as HTMLInputElement).value })"
            >
            <input
              type="number"
              :placeholder="t('catalog.filters.max_price')"
              :value="queryParams.max_price ?? ''"
              min="0"
              :disabled="route.query.is_free === 'true'"
              class="px-2 py-1.5 rounded border border-border bg-bg-card text-sm text-ink focus:outline-none focus:border-primary disabled:opacity-50"
              @change="setQuery({ max_price: ($event.target as HTMLInputElement).value })"
            >
          </div>
        </div>

        <label class="flex items-center gap-2 text-sm text-ink cursor-pointer">
          <input
            type="checkbox"
            :checked="route.query.is_free === 'true'"
            @change="setQuery({ is_free: ($event.target as HTMLInputElement).checked })"
          >
          {{ t("catalog.filters.free_only") }}
        </label>

        <label class="flex items-center gap-2 text-sm text-ink cursor-pointer">
          <input
            type="checkbox"
            :checked="route.query.featured === 'true'"
            @change="setQuery({ featured: ($event.target as HTMLInputElement).checked })"
          >
          {{ t("catalog.filters.featured_only") }}
        </label>
      </aside>

      <!-- Results -->
      <div>
        <div class="flex flex-wrap items-center justify-end gap-3 mb-4">
          <div class="min-w-[200px]">
            <UiSelect
              :model-value="queryParams.sort"
              :options="sortOptions"
              :label="undefined"
              @update:model-value="(v) => setQuery({ sort: v })"
            />
          </div>
        </div>

        <div
          v-if="pending && !results"
          class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4"
        >
          <div v-for="i in 8" :key="i" class="space-y-2">
            <UiSkeleton class="aspect-[2/3] !block" :rounded="'rounded'" />
            <UiSkeleton :width="'80%'" :height="'1rem'" :block="true" />
          </div>
        </div>

        <UiEmptyState
          v-else-if="(results?.items.length ?? 0) === 0"
          icon="📭"
          :title="t('search.no_results')"
          :description="t('search.no_results_body')"
        />

        <div
          v-else
          class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4"
        >
          <BookCard v-for="b in results!.items" :key="b.id" :book="b" />
        </div>

        <div class="mt-8">
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
