<script setup lang="ts">
import type { BookList, CategoryList, CategoryPublic } from "~/types/api";

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const localePath = useLocalePath();
const { localised } = useLocaleText();
const api = useApi();

const slug = computed(() => route.params.slug as string);

const PAGE_SIZE = 18;

const currentPage = computed(() => Math.max(1, Number(route.query.page) || 1));
const sortValue = computed(() => (route.query.sort as string) || "-published_at");

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

const siblings = computed<CategoryPublic[]>(() => {
  const items = ((allCategoriesRaw.value as CategoryList | null)?.items ?? []) as CategoryPublic[];
  // top-level siblings are other root categories; child sibling = same parent
  const ref = category.value;
  return items
    .filter((c) => c.id !== ref.id && c.parent_id === ref.parent_id)
    .slice(0, 6);
});

const { data: booksRaw, pending, error: booksError } = await useAsyncData(
  `category:${slug.value}:books`,
  () =>
    api<BookList>("/books", {
      query: {
        category: slug.value,
        page: currentPage.value,
        page_size: PAGE_SIZE,
        sort: sortValue.value,
      },
    }),
  { watch: [slug, currentPage, sortValue] },
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

function setSort(v: string) {
  const next: Record<string, string> = {};
  for (const [k, val] of Object.entries(route.query)) {
    if (typeof val === "string") next[k] = val;
  }
  next.sort = v;
  delete next.page;
  router.push({ query: next });
}

const sortOptions = computed(() => [
  { value: "-published_at", label: t("catalog.sort.newest") },
  { value: "published_at", label: t("catalog.sort.oldest") },
  { value: "price", label: t("catalog.sort.price_asc") },
  { value: "-price", label: t("catalog.sort.price_desc") },
  { value: "-average_rating", label: t("catalog.sort.rating") },
  { value: "-sales_count", label: t("catalog.sort.sales") },
]);

const total = computed(() => books.value?.total ?? 0);
</script>

<template>
  <section v-if="category" class="bg-bg">
    <!-- Breadcrumbs strip -->
    <div class="border-b border-border bg-bg-secondary/40">
      <div class="max-w-6xl mx-auto px-4 py-3">
        <UiBreadcrumbs :items="breadcrumbs" />
      </div>
    </div>

    <!-- Hero -->
    <header class="relative overflow-hidden border-b border-border">
      <div
        aria-hidden="true"
        class="absolute inset-0 -z-10"
        style="background-image:
          radial-gradient(ellipse 60% 50% at 15% 0%, color-mix(in oklab, var(--color-primary) 10%, transparent), transparent 65%);"
      />
      <div class="max-w-6xl mx-auto px-4 py-12 md:py-16 grid md:grid-cols-[auto_1fr] gap-6 md:gap-8 items-start">
        <div class="h-16 w-16 md:h-20 md:w-20 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
          <Icon :name="category.icon" fallback="book" class="h-8 w-8 md:h-10 md:w-10" />
        </div>

        <div class="space-y-3 min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-[11px] uppercase tracking-wider text-primary font-medium">
              {{ parent ? t("category.subcategory_of", { parent: localised(parent.name, parent.slug) }) : t("category.top_level") }}
            </span>
          </div>
          <h1 class="font-serif text-3xl md:text-5xl text-ink leading-[1.1] tracking-tight">
            {{ categoryName }}
          </h1>
          <p v-if="categoryDescription" class="text-ink-secondary max-w-3xl leading-relaxed">
            {{ categoryDescription }}
          </p>
          <div class="flex flex-wrap items-center gap-4 text-sm text-ink-secondary pt-1">
            <span class="inline-flex items-center gap-1.5">
              <Icon name="book" class="h-4 w-4 text-primary" />
              <span class="tabular-nums">{{ t("category.books_count", { n: category.book_count }) }}</span>
            </span>
            <span v-if="subcategories.length > 0" class="inline-flex items-center gap-1.5">
              <Icon name="folder" class="h-4 w-4 text-ink-tertiary" />
              <span>{{ t("category.subcategories_count", { n: subcategories.length }) }}</span>
            </span>
          </div>
        </div>
      </div>
    </header>

    <div class="max-w-6xl mx-auto px-4 py-8 md:py-10 space-y-10">
      <!-- Subcategories -->
      <section v-if="subcategories.length > 0" class="space-y-4">
        <div class="flex items-end justify-between gap-3">
          <div>
            <h2 class="font-serif text-2xl text-ink leading-tight">
              {{ t("category.subcategories") }}
            </h2>
            <p class="text-sm text-ink-secondary mt-1">{{ t("category.subcategories_subtitle") }}</p>
          </div>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          <NuxtLink
            v-for="sub in subcategories"
            :key="sub.id"
            :to="localePath(`/category/${sub.slug}`)"
            class="group flex items-center gap-3 p-3.5 rounded-md border border-border bg-bg-card hover:border-primary hover:shadow-sm transition-all"
          >
            <span class="h-10 w-10 rounded-md bg-primary/10 text-primary flex items-center justify-center shrink-0 group-hover:bg-primary group-hover:text-ink-inverse transition-colors">
              <Icon :name="sub.icon" fallback="book" class="h-5 w-5" />
            </span>
            <div class="min-w-0 flex-1">
              <div class="font-medium text-ink truncate group-hover:text-primary transition-colors">
                {{ localised(sub.name, sub.slug) }}
              </div>
              <div class="text-xs text-ink-tertiary mt-0.5">
                {{ t("category.books_count", { n: sub.book_count }) }}
              </div>
            </div>
            <Icon name="arrow-right" class="h-4 w-4 text-ink-tertiary shrink-0 opacity-0 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all" />
          </NuxtLink>
        </div>
      </section>

      <!-- Books -->
      <section class="space-y-4">
        <div class="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 class="font-serif text-2xl text-ink leading-tight">
              {{ t("category.books_in_category") }}
            </h2>
            <p class="text-sm text-ink-secondary mt-1 tabular-nums">
              {{ t("catalog.results", { n: total }) }}
            </p>
          </div>

          <div class="relative">
            <Icon
              name="chart"
              class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-tertiary pointer-events-none"
            />
            <select
              :value="sortValue"
              class="appearance-none pl-9 pr-9 py-2 rounded-md border border-border bg-bg-card text-sm text-ink focus:outline-none focus:border-primary transition-colors cursor-pointer"
              @change="setSort(($event.target as HTMLSelectElement).value)"
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

        <!-- Loading -->
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
            <h3 class="font-serif text-lg text-ink mb-1">{{ t("category.error_title") }}</h3>
            <p class="text-sm text-ink-secondary">{{ t("category.error_body") }}</p>
          </div>
        </div>

        <!-- Empty -->
        <UiEmptyState
          v-else-if="(books?.items.length ?? 0) === 0"
          icon="inbox"
          :title="t('category.no_books')"
          :description="t('category.no_books_body')"
        >
          <UiButton variant="ghost" :to="localePath('/books')">
            <Icon name="arrow-left" class="h-4 w-4" />
            {{ t("category.back_to_catalog") }}
          </UiButton>
        </UiEmptyState>

        <!-- Books grid -->
        <div v-else>
          <div
            class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-5 transition-opacity"
            :class="pending ? 'opacity-50 pointer-events-none' : ''"
          >
            <BookCard v-for="b in books!.items" :key="b.id" :book="b" />
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
      </section>

      <!-- Sibling categories (other topics) -->
      <section v-if="siblings.length > 0" class="space-y-4 pt-4 border-t border-border">
        <h2 class="font-serif text-2xl text-ink leading-tight">
          {{ parent ? t("category.other_in_parent") : t("category.other_topics") }}
        </h2>
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
          <NuxtLink
            v-for="sib in siblings"
            :key="sib.id"
            :to="localePath(`/category/${sib.slug}`)"
            class="group flex items-center gap-2 px-3 py-2 rounded-md border border-border bg-bg-card hover:border-primary transition-colors text-sm"
          >
            <Icon :name="sib.icon" fallback="book" class="h-4 w-4 text-ink-tertiary group-hover:text-primary shrink-0" />
            <span class="truncate text-ink-secondary group-hover:text-primary transition-colors">
              {{ localised(sib.name, sib.slug) }}
            </span>
          </NuxtLink>
        </div>
      </section>
    </div>
  </section>
</template>
