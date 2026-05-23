<script setup lang="ts">
import type { BookList, CategoryList } from "~/types/api";

const { t } = useI18n();
const localePath = useLocalePath();
const { localised } = useLocaleText();
const api = useApi();

useSiteSeo({
  title: t("home.hero.title"),
  description: t("home.hero.subtitle"),
});

// Organization schema lives only on the homepage so search engines
// associate it with the brand's primary URL.
const runtime = useRuntimeConfig();
useStructuredData(
  buildOrganizationSchema({
    siteUrl: runtime.public.siteUrl as string,
    siteName: runtime.public.siteName as string,
  }),
);

const { data: featured } = await useAsyncData("home:featured", () =>
  api<BookList>("/books", { params: { featured: true, page_size: 6 } }),
);
const { data: recent } = await useAsyncData("home:recent", () =>
  api<BookList>("/books", { params: { sort: "-published_at", page_size: 8 } }),
);
const { data: categories } = await useAsyncData("home:categories", () =>
  api<CategoryList>("/categories", { params: { active_only: true } }),
);

/** Hide subcategories on the homepage grid — only top-level. */
const topCategories = computed(
  () => categories.value?.items.filter((c) => c.parent_id === null).slice(0, 8) ?? [],
);
</script>

<template>
  <div class="bg-bg">
    <!-- HERO -->
    <section class="border-b border-border">
      <div class="max-w-6xl mx-auto px-4 py-16 md:py-24 grid md:grid-cols-2 gap-8 items-center">
        <div>
          <h1 class="font-serif text-3xl md:text-5xl text-ink leading-tight mb-4">
            {{ t("home.hero.title") }}
          </h1>
          <p class="text-lg text-ink-secondary mb-8">
            {{ t("home.hero.subtitle") }}
          </p>
          <div class="flex flex-wrap gap-3">
            <UiButton :to="localePath('/books')" size="lg">
              {{ t("home.hero.cta_browse") }}
            </UiButton>
            <UiButton variant="ghost" size="lg" :to="localePath('/authors/me')">
              {{ t("home.hero.cta_become_author") }}
            </UiButton>
          </div>
        </div>
        <div class="hidden md:flex justify-end">
          <!-- decorative stack of book covers from the featured set -->
          <div class="relative h-72 w-56">
            <template v-for="(book, i) in (featured?.items ?? []).slice(0, 3)" :key="book.id">
              <div
                class="absolute h-72 w-48 rounded shadow-book overflow-hidden border border-border bg-bg-card"
                :style="{
                  transform: `translateX(${i * 16}px) rotate(${(i - 1) * 4}deg)`,
                  zIndex: 10 - i,
                }"
              >
                <BookCover :src="book.cover_url" :alt="localised(book.title, book.slug)" eager />
              </div>
            </template>
          </div>
        </div>
      </div>
    </section>

    <!-- FEATURED -->
    <section v-if="featured?.items.length" class="border-b border-border">
      <div class="max-w-6xl mx-auto px-4 py-12">
        <div class="flex items-end justify-between mb-6">
          <div>
            <h2 class="font-serif text-2xl text-ink">{{ t("home.featured") }}</h2>
            <p class="text-sm text-ink-secondary">{{ t("home.featured_subtitle") }}</p>
          </div>
          <NuxtLink
            :to="localePath('/books') + '?featured=true'"
            class="text-sm text-primary hover:underline"
          >
            {{ t("home.see_all") }} →
          </NuxtLink>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <BookCard v-for="book in featured.items" :key="book.id" :book="book" />
        </div>
      </div>
    </section>

    <!-- CATEGORIES -->
    <section v-if="topCategories.length" class="border-b border-border bg-bg-secondary">
      <div class="max-w-6xl mx-auto px-4 py-12">
        <div class="mb-6">
          <h2 class="font-serif text-2xl text-ink">{{ t("home.categories") }}</h2>
          <p class="text-sm text-ink-secondary">{{ t("home.categories_subtitle") }}</p>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <UiCard
            v-for="cat in topCategories"
            :key="cat.id"
            :to="localePath(`/category/${cat.slug}`)"
            hoverable
            class="flex items-center gap-3"
          >
            <div class="text-2xl" aria-hidden="true">{{ cat.icon ?? "📖" }}</div>
            <div class="min-w-0">
              <div class="font-medium text-ink truncate">
                {{ localised(cat.name, cat.slug) }}
              </div>
              <div class="text-xs text-ink-tertiary">
                {{ t("home.categories_books", { n: cat.book_count }) }}
              </div>
            </div>
          </UiCard>
        </div>
      </div>
    </section>

    <!-- RECENT -->
    <section v-if="recent?.items.length" class="border-b border-border">
      <div class="max-w-6xl mx-auto px-4 py-12">
        <div class="flex items-end justify-between mb-6">
          <div>
            <h2 class="font-serif text-2xl text-ink">{{ t("home.recent_books") }}</h2>
            <p class="text-sm text-ink-secondary">{{ t("home.recent_subtitle") }}</p>
          </div>
          <NuxtLink :to="localePath('/books')" class="text-sm text-primary hover:underline">
            {{ t("home.see_all") }} →
          </NuxtLink>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-4 gap-4">
          <BookCard v-for="book in recent.items.slice(0, 4)" :key="book.id" :book="book" />
        </div>
      </div>
    </section>

    <!-- BECOME AUTHOR CTA -->
    <section class="bg-primary/5">
      <div class="max-w-4xl mx-auto px-4 py-16 text-center">
        <h2 class="font-serif text-2xl md:text-3xl text-ink mb-3">
          {{ t("home.become_author_cta.title") }}
        </h2>
        <p class="text-ink-secondary mb-6 max-w-2xl mx-auto">
          {{ t("home.become_author_cta.body") }}
        </p>
        <UiButton :to="localePath('/authors/me')" size="lg">
          {{ t("home.become_author_cta.button") }}
        </UiButton>
      </div>
    </section>
  </div>
</template>
