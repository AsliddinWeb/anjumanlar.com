<script setup lang="ts">
import type { BookList, CategoryList } from "~/types/api";

const { t } = useI18n();
const { localised } = useLocaleText();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const api = useApi();

useSiteSeo({
  title: t("catalog.title"),
  description: t("catalog.subtitle"),
});

const PAGE_SIZE = 20;

/** All filters live in the URL so the page is shareable + back-button friendly. */
const queryParams = computed(() => {
  const isFree = route.query.is_free === "true";
  const maxFromFree = isFree ? 0 : route.query.max_price;
  return {
    category: (route.query.category as string) || undefined,
    language: (route.query.language as string) || undefined,
    min_price: route.query.min_price ? Number(route.query.min_price) : undefined,
    max_price: maxFromFree !== undefined ? Number(maxFromFree) : undefined,
    featured: route.query.featured === "true" ? true : undefined,
    sort: (route.query.sort as string) || "-published_at",
    page: Math.max(1, Number(route.query.page) || 1),
    page_size: PAGE_SIZE,
  };
});

const { data: books, pending } = await useAsyncData<BookList>(
  "catalog:books",
  () => api<BookList>("/books", { query: queryParams.value }),
  { watch: [queryParams] },
);

const { data: categories } = await useAsyncData<CategoryList>(
  "catalog:categories",
  () => api<CategoryList>("/categories", { query: { active_only: true } }),
);

/** Build a flat dropdown of categories — children get a leading "—". */
const categoryOptions = computed(() => {
  const items = categories.value?.items ?? [];
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
  { value: "published_at", label: t("catalog.sort.oldest") },
  { value: "price", label: t("catalog.sort.price_asc") },
  { value: "-price", label: t("catalog.sort.price_desc") },
  { value: "-average_rating", label: t("catalog.sort.rating") },
  { value: "-sales_count", label: t("catalog.sort.sales") },
  { value: "-views_count", label: t("catalog.sort.views") },
]);

function setQuery(updates: Record<string, string | number | boolean | undefined>) {
  const next: Record<string, string> = {};
  for (const [k, v] of Object.entries(route.query)) {
    if (typeof v === "string") next[k] = v;
  }
  for (const [key, value] of Object.entries(updates)) {
    if (value === undefined || value === null || value === "" || value === false) {
      delete next[key];
    } else {
      next[key] = String(value);
    }
  }
  // Anything other than ``page`` resets pagination.
  if (!("page" in updates)) delete next.page;
  router.push({ query: next });
}

function changePage(page: number) {
  setQuery({ page });
  if (import.meta.client) {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
}

function clearAll() {
  router.push({ query: {} });
}

const hasActiveFilters = computed(
  () =>
    !!queryParams.value.category
    || !!queryParams.value.language
    || queryParams.value.min_price != null
    || queryParams.value.max_price != null
    || !!queryParams.value.featured
    || route.query.is_free === "true",
);

const total = computed(() => books.value?.total ?? 0);
const currentPage = computed(() => queryParams.value.page);
</script>

<template>
  <section class="max-w-6xl mx-auto px-4 py-8">
    <header class="mb-6">
      <h1 class="font-serif text-3xl text-ink">{{ t("catalog.title") }}</h1>
      <p class="text-sm text-ink-secondary">{{ t("catalog.subtitle") }}</p>
    </header>

    <div class="grid md:grid-cols-[260px_1fr] gap-6">
      <!-- Sidebar: filters -->
      <aside class="space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="font-medium text-ink">{{ t("catalog.filters.label") }}</h2>
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

      <!-- Main column: sort + grid + pagination -->
      <div>
        <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div class="text-sm text-ink-secondary">
            {{ t("catalog.results", { n: total }) }}
          </div>
          <div class="min-w-[200px]">
            <UiSelect
              :model-value="queryParams.sort"
              :options="sortOptions"
              :label="undefined"
              @update:model-value="(v) => setQuery({ sort: v })"
            />
          </div>
        </div>

        <!-- Loading skeletons -->
        <div
          v-if="pending && !books"
          class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4"
        >
          <div v-for="i in 8" :key="i" class="space-y-2">
            <UiSkeleton class="aspect-[2/3] !block" :rounded="'rounded'" />
            <UiSkeleton :width="'80%'" :height="'1rem'" :block="true" />
            <UiSkeleton :width="'50%'" :height="'0.75rem'" :block="true" />
          </div>
        </div>

        <!-- Empty -->
        <UiEmptyState
          v-else-if="(books?.items.length ?? 0) === 0"
          icon="inbox"
          :title="t('catalog.no_results')"
          :description="t('catalog.no_results_body')"
        >
          <UiButton variant="ghost" @click="clearAll">
            {{ t("catalog.filters.clear") }}
          </UiButton>
        </UiEmptyState>

        <!-- Results grid -->
        <div
          v-else
          class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4"
        >
          <BookCard v-for="book in books!.items" :key="book.id" :book="book" />
        </div>

        <div class="mt-8">
          <UiPagination
            :page="currentPage"
            :page-size="PAGE_SIZE"
            :total="total"
            @change="changePage"
          />
        </div>
      </div>
    </div>
  </section>
</template>
