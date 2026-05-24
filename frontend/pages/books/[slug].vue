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

const authorInitials = computed(() => {
  const parts = book.value.author.display_name.trim().split(/\s+/).slice(0, 2);
  return parts.map((p) => p.charAt(0).toUpperCase()).join("");
});

const activeTab = ref("description");
const tabs = computed(() => [
  { id: "description", label: t("book.tabs.description") },
  { id: "author", label: t("book.tabs.author") },
  { id: "reviews", label: t("book.tabs.reviews"), badge: book.value.reviews_count },
]);

const { data: similarRaw } = await useAsyncData(
  `book:${slug.value}:similar`,
  () =>
    primaryCategory.value
      ? api<BookList>("/books", {
          query: {
            category: primaryCategory.value.slug,
            page_size: 8,
            sort: "-published_at",
          },
        })
      : Promise.resolve({ items: [], total: 0, page: 1, page_size: 0 } as BookList),
  { watch: [slug] },
);

const similarBooks = computed<BookPublic[]>(() => {
  const items = ((similarRaw.value as BookList | null)?.items ?? []) as BookPublic[];
  return items.filter((b) => b.id !== book.value.id).slice(0, 4);
});
</script>

<template>
  <article v-if="book" class="bg-bg">
    <!-- Breadcrumbs strip -->
    <div class="border-b border-border bg-bg-secondary/40">
      <div class="max-w-6xl mx-auto px-4 py-3">
        <UiBreadcrumbs :items="breadcrumbs" />
      </div>
    </div>

    <!-- Hero: cover + summary + CTA card -->
    <section class="relative overflow-hidden border-b border-border">
      <div
        aria-hidden="true"
        class="absolute inset-0 -z-10 opacity-60"
        style="background-image:
          radial-gradient(ellipse 50% 60% at 15% 0%, color-mix(in oklab, var(--color-primary) 8%, transparent), transparent 70%);"
      />
      <div class="max-w-6xl mx-auto px-4 py-10 md:py-14 grid md:grid-cols-[280px_1fr] lg:grid-cols-[320px_1fr_300px] gap-8 lg:gap-10">

        <!-- Cover -->
        <div class="flex md:block justify-center">
          <div class="w-48 md:w-full max-w-[280px] relative">
            <div
              aria-hidden="true"
              class="absolute -inset-4 rounded-xl bg-gradient-to-br from-primary/20 to-accent-burgundy/10 blur-2xl opacity-60"
            />
            <div class="relative rounded-md shadow-2xl overflow-hidden ring-1 ring-border">
              <BookCover :src="book.cover_url" :alt="title" eager />
            </div>
          </div>
        </div>

        <!-- Summary -->
        <div class="space-y-5 min-w-0">
          <div class="space-y-2">
            <div class="flex flex-wrap items-center gap-2">
              <NuxtLink
                v-for="cat in book.categories.slice(0, 3)"
                :key="cat.id"
                :to="localePath(`/category/${cat.slug}`)"
                class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs hover:bg-primary/20 transition-colors"
              >
                <Icon name="folder" class="h-3 w-3" />
                {{ localised(cat.name, cat.slug) }}
              </NuxtLink>
              <UiBadge v-if="book.featured" tone="gold" size="sm" class="inline-flex items-center gap-1">
                <Icon name="star-solid" class="h-3 w-3" />
                {{ t("book.featured") }}
              </UiBadge>
            </div>

            <h1 class="font-serif text-3xl md:text-4xl text-ink leading-tight tracking-tight">
              {{ title }}
            </h1>
            <p v-if="subtitle" class="text-lg text-ink-secondary leading-snug">{{ subtitle }}</p>
          </div>

          <!-- Author chip -->
          <NuxtLink
            :to="localePath(`/authors/${book.author.slug}`)"
            class="inline-flex items-center gap-2.5 px-2 py-1 rounded-full border border-border bg-bg-card hover:border-primary transition-colors group"
          >
            <span class="h-7 w-7 rounded-full bg-primary text-ink-inverse flex items-center justify-center text-[11px] font-semibold">
              {{ authorInitials }}
            </span>
            <span class="text-sm text-ink-secondary group-hover:text-primary transition-colors pr-2">
              {{ book.author.display_name }}
            </span>
          </NuxtLink>

          <!-- Rating -->
          <div>
            <BookRating
              :rating="book.average_rating"
              :reviews-count="book.reviews_count"
            />
          </div>

          <!-- Quick info bar -->
          <dl class="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-ink-secondary py-3 border-y border-border">
            <div class="inline-flex items-center gap-1.5">
              <Icon name="document" class="h-3.5 w-3.5 text-ink-tertiary" />
              <span>{{ languageLabel }}</span>
            </div>
            <div v-if="book.pages_count" class="inline-flex items-center gap-1.5">
              <Icon name="book" class="h-3.5 w-3.5 text-ink-tertiary" />
              <span>{{ t("book.pages", { n: book.pages_count }) }}</span>
            </div>
            <div v-if="book.publication_year" class="inline-flex items-center gap-1.5">
              <Icon name="academic" class="h-3.5 w-3.5 text-ink-tertiary" />
              <span>{{ book.publication_year }}</span>
            </div>
            <div v-if="book.publisher" class="inline-flex items-center gap-1.5">
              <Icon name="institution" class="h-3.5 w-3.5 text-ink-tertiary" />
              <span class="truncate max-w-[18ch]">{{ book.publisher }}</span>
            </div>
          </dl>

          <!-- Inline description preview (md+ only; full on Description tab) -->
          <p v-if="description" class="hidden md:block lg:hidden text-sm text-ink-secondary leading-relaxed line-clamp-3">
            {{ description }}
          </p>
        </div>

        <!-- Buy card (lg sidebar) -->
        <aside class="lg:col-start-3 lg:row-start-1 lg:row-end-2">
          <div class="lg:sticky lg:top-20 rounded-lg border border-border bg-bg-card p-5 space-y-4 shadow-sm">
            <BookPriceTag
              :price="book.price"
              :discount-price="book.discount_price"
              :is-free="book.is_free"
              size="lg"
            />

            <div class="flex flex-col gap-2">
              <CartButton
                v-if="!book.is_free"
                :book="book"
                variant="button"
                size="lg"
              />
              <UiButton
                v-else
                size="lg"
                :to="localePath('/account/library')"
                block
              >
                <Icon name="book" class="h-4 w-4" />
                {{ t("book.cta.get_free") }}
              </UiButton>

              <WishlistButton :book-id="book.id" variant="button" size="lg" />

              <BookDemoViewer
                v-if="book.demo_url"
                :demo-url="book.demo_url"
                :title="title"
              />
            </div>

            <ul class="space-y-1.5 pt-3 border-t border-border text-xs text-ink-secondary">
              <li class="flex items-center gap-2">
                <Icon name="check-circle" class="h-3.5 w-3.5 text-success shrink-0" />
                <span>{{ t("book.perks.instant") }}</span>
              </li>
              <li class="flex items-center gap-2">
                <Icon name="check-circle" class="h-3.5 w-3.5 text-success shrink-0" />
                <span>{{ t("book.perks.forever") }}</span>
              </li>
              <li class="flex items-center gap-2">
                <Icon name="check-circle" class="h-3.5 w-3.5 text-success shrink-0" />
                <span>{{ t("book.perks.secure") }}</span>
              </li>
            </ul>
          </div>
        </aside>
      </div>
    </section>

    <!-- Tabs + metadata -->
    <section class="max-w-6xl mx-auto px-4 py-10 md:py-12 grid md:grid-cols-[1fr_280px] gap-8 md:gap-10">
      <div class="min-w-0">
        <UiTabs v-model="activeTab" :tabs="tabs">
          <template #default="{ active }">
            <section
              v-if="active === 'description'"
              class="text-ink leading-relaxed whitespace-pre-line"
            >
              <template v-if="description">{{ description }}</template>
              <p v-else class="text-ink-tertiary italic">{{ t("book.no_description") }}</p>
            </section>

            <section v-else-if="active === 'author'" class="rounded-md border border-border bg-bg-card p-5 space-y-4">
              <div class="flex items-center gap-4">
                <div class="h-14 w-14 rounded-full bg-primary text-ink-inverse flex items-center justify-center text-lg font-semibold shrink-0">
                  {{ authorInitials }}
                </div>
                <div class="min-w-0">
                  <h3 class="font-serif text-xl text-ink">{{ book.author.display_name }}</h3>
                  <p class="text-sm text-ink-secondary">{{ t("book.author_more_link") }}</p>
                </div>
              </div>
              <UiButton variant="ghost" :to="localePath(`/authors/${book.author.slug}`)">
                <Icon name="user-circle" class="h-4 w-4" />
                {{ t("book.author_view_profile") }}
                <Icon name="arrow-right" class="h-4 w-4" />
              </UiButton>
            </section>

            <section v-else-if="active === 'reviews'">
              <BookReviewsSection :book-id="book.id" />
            </section>
          </template>
        </UiTabs>
      </div>

      <aside class="space-y-4">
        <div class="rounded-md border border-border bg-bg-card overflow-hidden">
          <div class="px-4 py-2.5 bg-bg-secondary/60 border-b border-border">
            <h4 class="text-xs uppercase tracking-wider text-ink-tertiary font-medium">
              {{ t("book.details") }}
            </h4>
          </div>
          <dl class="text-sm divide-y divide-border">
            <div v-if="book.publisher" class="flex justify-between gap-3 px-4 py-2.5">
              <dt class="text-ink-tertiary inline-flex items-center gap-1.5">
                <Icon name="institution" class="h-3.5 w-3.5" />
                {{ t("book.publisher") }}
              </dt>
              <dd class="text-ink text-right">{{ book.publisher }}</dd>
            </div>
            <div v-if="book.publication_year" class="flex justify-between gap-3 px-4 py-2.5">
              <dt class="text-ink-tertiary inline-flex items-center gap-1.5">
                <Icon name="academic" class="h-3.5 w-3.5" />
                {{ t("book.published_year") }}
              </dt>
              <dd class="text-ink text-right">{{ book.publication_year }}</dd>
            </div>
            <div v-if="book.pages_count" class="flex justify-between gap-3 px-4 py-2.5">
              <dt class="text-ink-tertiary inline-flex items-center gap-1.5">
                <Icon name="document" class="h-3.5 w-3.5" />
                {{ t("book.pages_label") }}
              </dt>
              <dd class="text-ink text-right">{{ book.pages_count }}</dd>
            </div>
            <div class="flex justify-between gap-3 px-4 py-2.5">
              <dt class="text-ink-tertiary inline-flex items-center gap-1.5">
                <Icon name="document" class="h-3.5 w-3.5" />
                {{ t("book.language") }}
              </dt>
              <dd class="text-ink text-right">{{ languageLabel }}</dd>
            </div>
            <div v-if="book.isbn" class="flex justify-between gap-3 px-4 py-2.5">
              <dt class="text-ink-tertiary inline-flex items-center gap-1.5">
                <Icon name="key" class="h-3.5 w-3.5" />
                {{ t("book.isbn") }}
              </dt>
              <dd class="text-ink text-right font-mono text-xs">{{ book.isbn }}</dd>
            </div>
            <div v-if="book.published_at" class="flex justify-between gap-3 px-4 py-2.5">
              <dt class="text-ink-tertiary inline-flex items-center gap-1.5">
                <Icon name="sparkles" class="h-3.5 w-3.5" />
                {{ t("book.released_on") }}
              </dt>
              <dd class="text-ink text-right">{{ formatDate(book.published_at) }}</dd>
            </div>
          </dl>
        </div>

        <NuxtLink
          v-if="primaryCategory"
          :to="localePath(`/category/${primaryCategory.slug}`)"
          class="block rounded-md border border-border bg-bg-card p-4 hover:border-primary transition-colors group"
        >
          <div class="text-xs text-ink-tertiary mb-1">{{ t("book.more_in_category") }}</div>
          <div class="flex items-center gap-2 font-medium text-ink group-hover:text-primary transition-colors">
            <Icon name="folder" class="h-4 w-4" />
            <span class="truncate">{{ localised(primaryCategory.name, primaryCategory.slug) }}</span>
            <Icon name="arrow-right" class="h-3.5 w-3.5 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </NuxtLink>
      </aside>
    </section>

    <!-- Similar books -->
    <section v-if="similarBooks.length > 0" class="border-t border-border bg-bg-secondary/40">
      <div class="max-w-6xl mx-auto px-4 py-10 md:py-12 space-y-5">
        <div class="flex items-end justify-between gap-3">
          <div>
            <h2 class="font-serif text-2xl md:text-3xl text-ink leading-tight">
              {{ t("book.similar_books") }}
            </h2>
            <p v-if="primaryCategory" class="text-sm text-ink-secondary mt-1">
              {{ t("book.similar_subtitle", { category: localised(primaryCategory.name, primaryCategory.slug) }) }}
            </p>
          </div>
          <NuxtLink
            v-if="primaryCategory"
            :to="localePath(`/category/${primaryCategory.slug}`)"
            class="hidden sm:inline-flex items-center gap-1 text-sm text-primary hover:underline shrink-0"
          >
            {{ t("book.see_all_in_category") }}
            <Icon name="arrow-right" class="h-4 w-4" />
          </NuxtLink>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-5">
          <BookCard v-for="b in similarBooks" :key="b.id" :book="b" />
        </div>
      </div>
    </section>
  </article>
</template>
