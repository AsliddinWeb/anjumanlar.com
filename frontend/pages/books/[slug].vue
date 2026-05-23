<script setup lang="ts">
import type { BookList, BookPublic } from "~/types/api";

const { t, locale } = useI18n();
const route = useRoute();
const localePath = useLocalePath();
const { localised } = useLocaleText();
const api = useApi();

const slug = computed(() => route.params.slug as string);

const { data: bookRaw, error } = await useAsyncData(
  `book:${slug.value}`,
  () => api<BookPublic>(`/books/${slug.value}`),
  { watch: [slug] },
);

if (error.value || !bookRaw.value) {
  throw createError({
    statusCode: 404,
    statusMessage: t("book.not_found"),
    fatal: true,
  });
}

const book = computed(() => bookRaw.value as BookPublic);

const title = computed(() => localised(book.value.title, book.value.slug));
const subtitle = computed(() => localised(book.value.subtitle));
const description = computed(() => localised(book.value.description));

useSiteSeo({
  title: title.value,
  description: description.value.slice(0, 160) || t("site.tagline"),
  image: book.value.cover_url ?? undefined,
  ogType: "book",
});

const runtime = useRuntimeConfig();
const siteUrl = runtime.public.siteUrl as string;
useStructuredData([
  buildBookSchema({
    name: title.value,
    description: description.value || title.value,
    url: `${siteUrl}/${locale.value}/books/${book.value.slug}`,
    image: book.value.cover_url,
    isbn: book.value.isbn,
    inLanguage: book.value.language,
    datePublished: book.value.published_at,
    authorName: book.value.author.display_name,
    authorUrl: `${siteUrl}/${locale.value}/authors/${book.value.author.slug}`,
    publisher: book.value.publisher,
    priceUzs: book.value.is_free ? 0 : (book.value.discount_price ?? book.value.price),
    isFree: book.value.is_free,
    ratingValue: book.value.average_rating > 0 ? book.value.average_rating : null,
    ratingCount: book.value.reviews_count,
  }),
  buildBreadcrumbList([
    { name: t("nav.home"), url: `${siteUrl}/${locale.value}` },
    { name: t("nav.books"), url: `${siteUrl}/${locale.value}/books` },
    { name: title.value, url: `${siteUrl}/${locale.value}/books/${book.value.slug}` },
  ]),
]);

const primaryCategory = computed(() => book.value.categories[0] ?? null);

const breadcrumbs = computed(() => {
  const items: { label: string; to?: string }[] = [
    { label: t("nav.home"), to: localePath("/") },
    { label: t("nav.books"), to: localePath("/books") },
  ];
  if (primaryCategory.value) {
    items.push({
      label: localised(primaryCategory.value.name, primaryCategory.value.slug),
      to: localePath(`/category/${primaryCategory.value.slug}`),
    });
  }
  items.push({ label: title.value });
  return items;
});

const languageLabel = computed(() => {
  const map: Record<string, string> = {
    uz: "O'zbekcha",
    ru: "Русский",
    en: "English",
    mixed: t("book.lang_mixed"),
  };
  return map[book.value.language] ?? book.value.language;
});

const formatDate = (iso: string | null) => {
  if (!iso) return "";
  return new Intl.DateTimeFormat(locale.value, {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(iso));
};

const activeTab = ref("description");
const tabs = computed(() => [
  { id: "description", label: t("book.tabs.description") },
  { id: "author", label: t("book.tabs.author") },
  { id: "reviews", label: t("book.tabs.reviews"), badge: book.value.reviews_count },
]);

// Similar books — pulls from the primary category, drops the current book.
const { data: similarRaw } = await useAsyncData(
  `book:${slug.value}:similar`,
  () =>
    primaryCategory.value
      ? api<BookList>("/books", {
          query: {
            category: primaryCategory.value.slug,
            page_size: 7,
            sort: "-published_at",
          },
        })
      : Promise.resolve({ items: [], total: 0, page: 1, page_size: 0 } as BookList),
  { watch: [slug] },
);

const similarBooks = computed<BookPublic[]>(() => {
  const items = ((similarRaw.value as BookList | null)?.items ?? []) as BookPublic[];
  return items.filter((b) => b.id !== book.value.id).slice(0, 6);
});
</script>

<template>
  <article v-if="book" class="max-w-6xl mx-auto px-4 py-8 space-y-8">
    <UiBreadcrumbs :items="breadcrumbs" />

    <!-- Header: cover + summary + CTA -->
    <header class="grid md:grid-cols-[260px_1fr] gap-8">
      <div class="max-w-[260px]">
        <BookCover :src="book.cover_url" :alt="title" eager />
      </div>

      <div class="space-y-4">
        <div class="space-y-1">
          <h1 class="font-serif text-3xl md:text-4xl text-ink leading-tight">{{ title }}</h1>
          <p v-if="subtitle" class="text-lg text-ink-secondary">{{ subtitle }}</p>
        </div>

        <NuxtLink
          :to="localePath(`/authors/${book.author.slug}`)"
          class="inline-flex items-center text-sm text-primary hover:underline"
        >
          {{ t("book.by_author", { name: book.author.display_name }) }}
        </NuxtLink>

        <div class="flex flex-wrap items-center gap-3">
          <BookRating
            :rating="book.average_rating"
            :reviews-count="book.reviews_count"
          />
          <span v-if="book.featured" class="inline-flex">
            <UiBadge tone="warning" size="sm">{{ t("book.featured") }}</UiBadge>
          </span>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <NuxtLink
            v-for="cat in book.categories"
            :key="cat.id"
            :to="localePath(`/category/${cat.slug}`)"
            class="inline-flex"
          >
            <UiBadge tone="neutral" size="sm">
              {{ localised(cat.name, cat.slug) }}
            </UiBadge>
          </NuxtLink>
        </div>

        <div class="pt-2">
          <BookPriceTag
            :price="book.price"
            :discount-price="book.discount_price"
            :is-free="book.is_free"
            size="lg"
          />
        </div>

        <div class="flex flex-wrap gap-3 pt-2">
          <UiButton
            v-if="book.is_free"
            size="lg"
            :to="localePath('/account/library')"
            :disabled="true"
          >
            {{ t("book.cta.read") }}
          </UiButton>
          <CartButton v-else :book="book" variant="button" size="lg" />
          <BookDemoViewer :demo-url="book.demo_url" :title="title" />
          <WishlistButton :book-id="book.id" variant="button" size="lg" />
        </div>
        <p class="text-xs text-ink-tertiary">{{ t("book.cta.coming_soon") }}</p>
      </div>
    </header>

    <!-- Body: tabs + metadata sidebar -->
    <div class="grid md:grid-cols-[1fr_280px] gap-8">
      <UiTabs v-model="activeTab" :tabs="tabs">
        <template #default="{ active }">
          <section v-if="active === 'description'" class="prose-anjuman whitespace-pre-line text-ink leading-relaxed">
            <template v-if="description">{{ description }}</template>
            <p v-else class="text-ink-tertiary italic">{{ t("book.no_description") }}</p>
          </section>

          <section v-else-if="active === 'author'" class="space-y-3">
            <h3 class="font-serif text-xl text-ink">{{ book.author.display_name }}</h3>
            <p class="text-sm text-ink-secondary">{{ t("book.author_more_link") }}</p>
            <NuxtLink
              :to="localePath(`/authors/${book.author.slug}`)"
              class="inline-flex"
            >
              <UiButton variant="ghost" size="sm">{{ t("book.author_view_profile") }}</UiButton>
            </NuxtLink>
          </section>

          <section v-else-if="active === 'reviews'">
            <BookReviewsSection :book-id="book.id" />
          </section>
        </template>
      </UiTabs>

      <aside class="space-y-4">
        <dl class="rounded border border-border bg-bg-card p-4 text-sm space-y-3">
          <div v-if="book.publisher" class="flex justify-between gap-3">
            <dt class="text-ink-tertiary">{{ t("book.publisher") }}</dt>
            <dd class="text-ink text-right">{{ book.publisher }}</dd>
          </div>
          <div v-if="book.publication_year" class="flex justify-between gap-3">
            <dt class="text-ink-tertiary">{{ t("book.published_year") }}</dt>
            <dd class="text-ink text-right">{{ book.publication_year }}</dd>
          </div>
          <div v-if="book.pages_count" class="flex justify-between gap-3">
            <dt class="text-ink-tertiary">{{ t("book.pages_label") }}</dt>
            <dd class="text-ink text-right">{{ book.pages_count }}</dd>
          </div>
          <div class="flex justify-between gap-3">
            <dt class="text-ink-tertiary">{{ t("book.language") }}</dt>
            <dd class="text-ink text-right">{{ languageLabel }}</dd>
          </div>
          <div v-if="book.isbn" class="flex justify-between gap-3">
            <dt class="text-ink-tertiary">{{ t("book.isbn") }}</dt>
            <dd class="text-ink text-right font-mono text-xs">{{ book.isbn }}</dd>
          </div>
          <div v-if="book.published_at" class="flex justify-between gap-3">
            <dt class="text-ink-tertiary">{{ t("book.released_on") }}</dt>
            <dd class="text-ink text-right">{{ formatDate(book.published_at) }}</dd>
          </div>
        </dl>
      </aside>
    </div>

    <!-- Similar books -->
    <section v-if="similarBooks.length > 0" class="space-y-4 pt-4 border-t border-border">
      <h2 class="font-serif text-2xl text-ink">{{ t("book.similar_books") }}</h2>
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <BookCard v-for="b in similarBooks" :key="b.id" :book="b" />
      </div>
    </section>
  </article>
</template>
