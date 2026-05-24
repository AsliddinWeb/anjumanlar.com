<script setup lang="ts">
import type { BookList, CategoryList } from "~/types/api";
import type { IconName } from "~/utils/icons";

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

const queryParams = computed(() => {
  const isFree = route.query.is_free === "true";
  const maxFromFree = isFree ? "0" : route.query.max_price;
  return {
    search: ((route.query.q as string) || "").trim() || undefined,
    category: (route.query.category as string) || undefined,
    language: (route.query.language as string) || undefined,
    min_price: route.query.min_price ? Number(route.query.min_price) : undefined,
    max_price: maxFromFree !== undefined && maxFromFree !== "" ? Number(maxFromFree) : undefined,
    featured: route.query.featured === "true" ? true : undefined,
    sort: (route.query.sort as string) || "-published_at",
    page: Math.max(1, Number(route.query.page) || 1),
    page_size: PAGE_SIZE,
  };
});

const { data: books, pending, error: booksError } = await useAsyncData<BookList>(
  "catalog:books",
  () => api<BookList>("/books", { query: queryParams.value }),
  { watch: [queryParams] },
);

const { data: categories } = await useAsyncData<CategoryList>(
  "catalog:categories",
  () => api<CategoryList>("/categories", { query: { active_only: true } }),
);

const categoryOptions = computed(() => {
  const items = categories.value?.items ?? [];
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
  { value: "-published_at", label: t("catalog.sort.newest"), icon: "sparkles" as IconName },
  { value: "published_at", label: t("catalog.sort.oldest"), icon: "arrow-path" as IconName },
  { value: "price", label: t("catalog.sort.price_asc"), icon: "arrow-right" as IconName },
  { value: "-price", label: t("catalog.sort.price_desc"), icon: "arrow-left" as IconName },
  { value: "-average_rating", label: t("catalog.sort.rating"), icon: "star-solid" as IconName },
  { value: "-sales_count", label: t("catalog.sort.sales"), icon: "currency" as IconName },
  { value: "-views_count", label: t("catalog.sort.views"), icon: "eye" as IconName },
]);

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

function changePage(page: number) {
  setQuery({ page });
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}

function clearAll() {
  router.push({ query: {} });
}

const hasActiveFilters = computed(
  () =>
    Boolean(
      queryParams.value.search
      || queryParams.value.category
      || queryParams.value.language
      || queryParams.value.min_price != null
      || (queryParams.value.max_price != null && route.query.is_free !== "true")
      || queryParams.value.featured
      || route.query.is_free === "true",
    ),
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
  if (queryParams.value.category) {
    const cat = categories.value?.items.find((c) => c.slug === queryParams.value.category);
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
  if (route.query.is_free === "true") {
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

const total = computed(() => books.value?.total ?? 0);
const currentPage = computed(() => queryParams.value.page);

// --- search input (debounce-on-change is hard with v-model; we commit on
// Enter or blur to avoid re-issuing on every keystroke).
const searchInput = ref((route.query.q as string) || "");
watch(
  () => route.query.q,
  (v) => {
    searchInput.value = (v as string) || "";
  },
);
function submitSearch() {
  setQuery({ q: searchInput.value.trim() || undefined });
}

// --- mobile drawer
const drawerOpen = ref(false);
watch(
  () => route.fullPath,
  () => {
    drawerOpen.value = false;
  },
);
watch(drawerOpen, (open) => {
  if (import.meta.client) {
    document.body.style.overflow = open ? "hidden" : "";
  }
});
onBeforeUnmount(() => {
  if (import.meta.client) document.body.style.overflow = "";
});
useEscape(() => {
  drawerOpen.value = false;
}, { enabled: drawerOpen });
</script>

<template>
  <section class="bg-bg">
    <!-- Page header -->
    <header class="border-b border-border">
      <div class="max-w-6xl mx-auto px-4 py-8 md:py-10">
        <div class="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 class="font-serif text-3xl md:text-4xl text-ink leading-tight">
              {{ t("catalog.title") }}
            </h1>
            <p class="text-sm text-ink-secondary mt-1">{{ t("catalog.subtitle") }}</p>
          </div>
          <div class="flex items-center gap-2 text-sm text-ink-secondary">
            <Icon name="book" class="h-4 w-4 text-primary" />
            <span class="tabular-nums">{{ t("catalog.results", { n: total }) }}</span>
          </div>
        </div>
      </div>
    </header>

    <div class="max-w-6xl mx-auto px-4 py-6 md:py-8">
      <!-- Toolbar: search + sort + mobile filter trigger -->
      <div class="flex flex-wrap items-center gap-2 mb-4">
        <form
          class="flex-1 min-w-[200px] relative"
          role="search"
          @submit.prevent="submitSearch"
        >
          <Icon
            name="search"
            class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-tertiary pointer-events-none"
          />
          <input
            v-model="searchInput"
            type="search"
            :placeholder="t('catalog.search_placeholder')"
            class="w-full pl-9 pr-3 py-2 rounded-md border border-border bg-bg-card text-sm text-ink placeholder:text-ink-tertiary focus:outline-none focus:border-primary"
            @blur="submitSearch"
          >
        </form>

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

        <div class="relative">
          <Icon
            name="chart"
            class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-tertiary pointer-events-none"
          />
          <select
            :value="queryParams.sort"
            class="appearance-none pl-9 pr-9 py-2 rounded-md border border-border bg-bg-card text-sm text-ink focus:outline-none focus:border-primary transition-colors cursor-pointer"
            @change="setQuery({ sort: ($event.target as HTMLSelectElement).value })"
          >
            <option
              v-for="s in sortOptions"
              :key="s.value"
              :value="s.value"
            >
              {{ s.label }}
            </option>
          </select>
          <Icon
            name="chevron-down"
            class="absolute right-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-tertiary pointer-events-none"
          />
        </div>
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

      <div class="grid md:grid-cols-[260px_1fr] gap-6 md:gap-8">
        <!-- Desktop sidebar -->
        <aside class="hidden md:block">
          <div class="sticky top-20 space-y-6 max-h-[calc(100vh-6rem)] overflow-y-auto pr-1">
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
                    class="px-2.5 py-1.5 rounded border border-border bg-bg text-sm text-ink placeholder:text-ink-tertiary focus:outline-none focus:border-primary"
                    @change="setQuery({ min_price: ($event.target as HTMLInputElement).value })"
                  >
                  <input
                    type="number"
                    :placeholder="t('catalog.filters.max_price')"
                    :value="queryParams.max_price ?? ''"
                    min="0"
                    :disabled="route.query.is_free === 'true'"
                    class="px-2.5 py-1.5 rounded border border-border bg-bg text-sm text-ink placeholder:text-ink-tertiary focus:outline-none focus:border-primary disabled:opacity-50 disabled:cursor-not-allowed"
                    @change="setQuery({ max_price: ($event.target as HTMLInputElement).value })"
                  >
                </div>
              </div>

              <div class="space-y-2 pt-1 border-t border-border">
                <label class="flex items-center gap-2 text-sm text-ink cursor-pointer">
                  <input
                    type="checkbox"
                    class="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                    :checked="route.query.is_free === 'true'"
                    @change="setQuery({ is_free: ($event.target as HTMLInputElement).checked })"
                  >
                  <Icon name="gift" class="h-4 w-4 text-success" />
                  {{ t("catalog.filters.free_only") }}
                </label>

                <label class="flex items-center gap-2 text-sm text-ink cursor-pointer">
                  <input
                    type="checkbox"
                    class="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                    :checked="route.query.featured === 'true'"
                    @change="setQuery({ featured: ($event.target as HTMLInputElement).checked })"
                  >
                  <Icon name="star-solid" class="h-4 w-4 text-accent-gold" />
                  {{ t("catalog.filters.featured_only") }}
                </label>
              </div>
            </div>
          </div>
        </aside>

        <!-- Main column -->
        <div class="relative">
          <!-- Loading skeletons (initial load) -->
          <div
            v-if="pending && !books"
            class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-5"
          >
            <div v-for="i in 6" :key="i" class="space-y-2">
              <UiSkeleton class="aspect-[2/3]" rounded="rounded-md" block />
              <UiSkeleton width="80%" height="0.95rem" block />
              <UiSkeleton width="50%" height="0.7rem" block />
            </div>
          </div>

          <!-- Error -->
          <div
            v-else-if="booksError"
            class="rounded-md border border-error/30 bg-error/5 p-6 flex items-start gap-4"
          >
            <Icon name="warning-solid" class="h-6 w-6 text-error shrink-0" />
            <div>
              <h2 class="font-serif text-lg text-ink mb-1">{{ t("catalog.error_title") }}</h2>
              <p class="text-sm text-ink-secondary">{{ t("catalog.error_body") }}</p>
            </div>
          </div>

          <!-- Empty -->
          <UiEmptyState
            v-else-if="(books?.items.length ?? 0) === 0"
            icon="inbox"
            :title="t('catalog.no_results')"
            :description="t('catalog.no_results_body')"
          >
            <UiButton v-if="hasActiveFilters" variant="ghost" @click="clearAll">
              <Icon name="close" class="h-4 w-4" />
              {{ t("catalog.filters.clear") }}
            </UiButton>
          </UiEmptyState>

          <!-- Results -->
          <div v-else>
            <div
              class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-5 transition-opacity"
              :class="pending ? 'opacity-50 pointer-events-none' : ''"
            >
              <BookCard v-for="book in books!.items" :key="book.id" :book="book" />
            </div>

            <div v-if="total > PAGE_SIZE" class="mt-8">
              <UiPagination
                :page="currentPage"
                :page-size="PAGE_SIZE"
                :total="total"
                @change="changePage"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Mobile filter drawer -->
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
                  :disabled="route.query.is_free === 'true'"
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
                  :checked="route.query.is_free === 'true'"
                  @change="setQuery({ is_free: ($event.target as HTMLInputElement).checked })"
                >
                <Icon name="gift" class="h-4 w-4 text-success" />
                {{ t("catalog.filters.free_only") }}
              </label>
              <label class="flex items-center gap-2 text-sm text-ink cursor-pointer">
                <input
                  type="checkbox"
                  class="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                  :checked="route.query.featured === 'true'"
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
              {{ t("catalog.results", { n: total }) }}
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
