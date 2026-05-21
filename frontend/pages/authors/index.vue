<script setup lang="ts">
import type { AuthorList } from "~/types/api";

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const api = useApi();

useHead({ title: t("authors.title") });

const PAGE_SIZE = 24;

const queryParams = computed(() => ({
  search: (route.query.search as string) || undefined,
  featured: route.query.featured === "true" ? true : undefined,
  page: Math.max(1, Number(route.query.page) || 1),
  page_size: PAGE_SIZE,
}));

const { data: authorsRaw, pending } = await useAsyncData(
  "authors:list",
  () => api<AuthorList>("/authors", { query: queryParams.value }),
  { watch: [queryParams] },
);

const authors = computed(() => authorsRaw.value as AuthorList | null);

const searchInput = ref((route.query.search as string) || "");

watch(
  () => route.query.search,
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

function applySearch() {
  setQuery({ search: searchInput.value.trim() || undefined });
}

function changePage(page: number) {
  setQuery({ page });
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}
</script>

<template>
  <section class="max-w-6xl mx-auto px-4 py-8 space-y-6">
    <header class="space-y-1">
      <h1 class="font-serif text-3xl text-ink">{{ t("authors.title") }}</h1>
      <p class="text-sm text-ink-secondary">{{ t("authors.subtitle") }}</p>
    </header>

    <div class="flex flex-wrap items-center gap-3">
      <form class="flex-1 min-w-[260px] max-w-md" @submit.prevent="applySearch">
        <UiInput
          v-model="searchInput"
          :placeholder="t('authors.search_placeholder')"
        />
      </form>
      <label class="inline-flex items-center gap-2 text-sm text-ink cursor-pointer">
        <input
          type="checkbox"
          :checked="route.query.featured === 'true'"
          @change="setQuery({ featured: ($event.target as HTMLInputElement).checked })"
        >
        {{ t("authors.featured") }}
      </label>
      <span class="text-sm text-ink-tertiary ml-auto">
        {{ t("authors.results", { n: authors?.total ?? 0 }) }}
      </span>
    </div>

    <div
      v-if="pending && !authors"
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3"
    >
      <UiSkeleton v-for="i in 9" :key="i" :height="'4.5rem'" :block="true" />
    </div>

    <UiEmptyState
      v-else-if="(authors?.items.length ?? 0) === 0"
      icon="🧑‍🏫"
      :title="t('authors.no_authors')"
      :description="''"
    />

    <div
      v-else
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3"
    >
      <AuthorCard v-for="author in authors!.items" :key="author.id" :author="author" />
    </div>

    <div class="pt-4">
      <UiPagination
        :page="queryParams.page"
        :page-size="PAGE_SIZE"
        :total="authors?.total ?? 0"
        @change="changePage"
      />
    </div>
  </section>
</template>
