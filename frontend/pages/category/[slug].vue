<script setup lang="ts">
import type { BookList, CategoryList, CategoryPublic } from "~/types/api";

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const localePath = useLocalePath();
const { localised } = useLocaleText();
const api = useApi();

const slug = computed(() => route.params.slug as string);

const PAGE_SIZE = 20;

const currentPage = computed(() =>
  Math.max(1, Number(route.query.page) || 1),
);

const { data: categoryRaw, error: categoryErr } = await useAsyncData(
  `category:${slug.value}`,
  () => api<CategoryPublic>(`/categories/${slug.value}`),
  { watch: [slug] },
);

if (categoryErr.value || !categoryRaw.value) {
  throw createError({
    statusCode: 404,
    statusMessage: t("category.not_found"),
    fatal: true,
  });
}

const category = computed(() => categoryRaw.value as CategoryPublic);

const { data: allCategoriesRaw } = await useAsyncData(
  "category:all",
  () => api<CategoryList>("/categories", { query: { active_only: true } }),
);

const subcategories = computed<CategoryPublic[]>(() => {
  const items = ((allCategoriesRaw.value as CategoryList | null)?.items ?? []) as CategoryPublic[];
  return items.filter((c) => c.parent_id === category.value.id);
});

const parent = computed<CategoryPublic | null>(() => {
  if (!category.value.parent_id) return null;
  const items = ((allCategoriesRaw.value as CategoryList | null)?.items ?? []) as CategoryPublic[];
  return items.find((c) => c.id === category.value.parent_id) ?? null;
});

const { data: booksRaw, pending } = await useAsyncData(
  `category:${slug.value}:books`,
  () =>
    api<BookList>("/books", {
      query: {
        category: slug.value,
        page: currentPage.value,
        page_size: PAGE_SIZE,
      },
    }),
  { watch: [slug, currentPage] },
);

const books = computed(() => booksRaw.value as BookList | null);

const categoryName = computed(() => localised(category.value.name, category.value.slug));
const categoryDescription = computed(() => localised(category.value.description));

useSiteSeo({
  title: categoryName.value,
  description: categoryDescription.value.slice(0, 160) || t("site.tagline"),
  image: category.value.image_url ?? undefined,
});

const breadcrumbs = computed(() => {
  const items: { label: string; to?: string }[] = [
    { label: t("nav.home"), to: localePath("/") },
    { label: t("nav.books"), to: localePath("/books") },
  ];
  if (parent.value) {
    items.push({
      label: localised(parent.value.name, parent.value.slug),
      to: localePath(`/category/${parent.value.slug}`),
    });
  }
  items.push({ label: categoryName.value });
  return items;
});

function changePage(page: number) {
  router.push({ query: { ...route.query, page } });
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}
</script>

<template>
  <section class="max-w-6xl mx-auto px-4 py-8 space-y-8">
    <UiBreadcrumbs :items="breadcrumbs" />

    <header class="space-y-2">
      <div class="flex items-center gap-3">
        <span v-if="category.icon" class="text-3xl" aria-hidden="true">{{ category.icon }}</span>
        <h1 class="font-serif text-3xl text-ink">{{ categoryName }}</h1>
      </div>
      <p v-if="categoryDescription" class="text-ink-secondary max-w-3xl">
        {{ categoryDescription }}
      </p>
      <p class="text-sm text-ink-tertiary">
        {{ t("category.books_count", { n: category.book_count }) }}
      </p>
    </header>

    <!-- Subcategories -->
    <section v-if="subcategories.length > 0" class="space-y-3">
      <h2 class="font-medium text-ink">{{ t("category.subcategories") }}</h2>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <UiCard
          v-for="sub in subcategories"
          :key="sub.id"
          :to="localePath(`/category/${sub.slug}`)"
          hoverable
          class="flex items-center gap-3"
        >
          <div class="text-2xl" aria-hidden="true">{{ sub.icon ?? "📖" }}</div>
          <div class="min-w-0">
            <div class="font-medium text-ink truncate">
              {{ localised(sub.name, sub.slug) }}
            </div>
            <div class="text-xs text-ink-tertiary">
              {{ t("category.books_count", { n: sub.book_count }) }}
            </div>
          </div>
        </UiCard>
      </div>
    </section>

    <!-- Books -->
    <section class="space-y-4">
      <h2 class="font-medium text-ink">{{ t("category.books_in_category") }}</h2>

      <div
        v-if="pending && !books"
        class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4"
      >
        <div v-for="i in 8" :key="i" class="space-y-2">
          <UiSkeleton class="aspect-[2/3] !block" :rounded="'rounded'" />
          <UiSkeleton :width="'80%'" :height="'1rem'" :block="true" />
        </div>
      </div>

      <UiEmptyState
        v-else-if="(books?.items.length ?? 0) === 0"
        icon="📭"
        :title="t('category.no_books')"
        :description="''"
      />

      <div
        v-else
        class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4"
      >
        <BookCard v-for="b in books!.items" :key="b.id" :book="b" />
      </div>

      <div class="pt-4">
        <UiPagination
          :page="currentPage"
          :page-size="PAGE_SIZE"
          :total="books?.total ?? 0"
          @change="changePage"
        />
      </div>
    </section>
  </section>
</template>
