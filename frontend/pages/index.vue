<script setup lang="ts">
import type { BookList, CategoryList } from "~/types/api";
import { getOrnament } from "~/utils/ornaments";

const { t } = useI18n();
const localePath = useLocalePath();
const { localised } = useLocaleText();
const api = useApi();
const theme = useTheme();

// Toggle .in-view on .reveal elements as they enter the viewport.
useScrollReveal();

// The hero's single tiny ornament accent — divider body of the
// currently-selected motif. Reactive: switching the ornament in
// /admin/settings updates this without a refresh.
const heroOrnament = computed(() => getOrnament(theme.currentOrnament.value).divider);

useSiteSeo({
  title: t("home.hero.title"),
  description: t("home.hero.subtitle"),
});

const runtime = useRuntimeConfig();
useStructuredData(
  buildOrganizationSchema({
    siteUrl: runtime.public.siteUrl as string,
    siteName: runtime.public.siteName as string,
  }),
);

// NOTE: $fetch reads URL params from `query:`, not `params:` — the old
// code silently dropped the filters, so `featured` returned every book.
const { data: featuredData, error: featuredErr } = await useAsyncData(
  "home:featured",
  () => api<BookList>("/books", { query: { featured: true, page_size: 8 } }),
);
const { data: recentData, error: recentErr } = await useAsyncData(
  "home:recent",
  () => api<BookList>("/books", { query: { sort: "-published_at", page_size: 8 } }),
);
const { data: catData, error: catErr } = await useAsyncData(
  "home:categories",
  () => api<CategoryList>("/categories", { query: { active_only: true } }),
);

const featured = computed(() => (featuredData.value as BookList | null)?.items ?? []);
const recent = computed(() => (recentData.value as BookList | null)?.items ?? []);
const topCategories = computed(() =>
  ((catData.value as CategoryList | null)?.items ?? [])
    .filter((c) => c.parent_id === null)
    .slice(0, 8),
);

// `featured` returns a filtered subset (small count), so the catalogue
// total must come from the unfiltered `recent` query. Falling back to
// featured's total used to show 2 even when 4 books existed.
const totals = computed(() => ({
  books: (recentData.value as BookList | null)?.total
    ?? (featuredData.value as BookList | null)?.total
    ?? 0,
  categories: (catData.value as CategoryList | null)?.items.length ?? 0,
}));

// Hero stack uses up to 3 featured covers; falls back to recent so the
// stack still renders on a brand-new install where nothing is featured.
const heroBooks = computed(() => {
  const pool = featured.value.length ? featured.value : recent.value;
  return pool.slice(0, 3);
});

const hasAnyData = computed(() =>
  featured.value.length > 0 || recent.value.length > 0 || topCategories.value.length > 0,
);

const hasError = computed(() =>
  Boolean(featuredErr.value && recentErr.value && catErr.value),
);
</script>

<template>
  <div class="bg-bg">
    <!-- HERO -->
    <section class="relative overflow-hidden border-b border-border isolate">
      <!-- Layer 1: soft brand gradient -->
      <div
        aria-hidden="true"
        class="absolute inset-0 -z-30"
        style="background-image:
          radial-gradient(ellipse 60% 60% at 18% -10%, color-mix(in oklab, var(--color-primary) 12%, transparent), transparent 70%),
          radial-gradient(ellipse 40% 50% at 100% 110%, color-mix(in oklab, var(--color-accent-gold, var(--color-primary)) 10%, transparent), transparent 70%);"
      />
      <!-- Layer 2: very faint ornament watermark — texture without
           shouting. tile-size + 0.05 opacity keeps it elegant. -->
      <UiOrnamentPattern
        class="absolute inset-0 -z-20"
        :tile-size="100"
        :opacity="0.05"
      />
      <!-- Layer 3: gradient fade so the pattern only shows at the
           edges, leaving the centre clean for the headline copy. -->
      <div
        aria-hidden="true"
        class="absolute inset-0 -z-10"
        style="background-image:
          radial-gradient(ellipse 60% 70% at 50% 50%, var(--color-bg) 30%, transparent 80%);"
      />

      <div class="max-w-6xl mx-auto px-4 py-16 sm:py-20 md:py-28 lg:py-32 grid md:grid-cols-[1.15fr_1fr] gap-10 lg:gap-16 items-center">
        <div class="space-y-6">
          <div class="flex items-center gap-3">
            <span class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-bg-card/80 backdrop-blur text-xs text-ink-secondary shadow-sm">
              <span class="relative inline-flex h-2 w-2">
                <span class="absolute inset-0 rounded-full bg-success opacity-75 animate-ping" />
                <span class="relative inline-flex h-2 w-2 rounded-full bg-success" />
              </span>
              {{ t("home.hero.tagline") }}
            </span>
            <!-- One small ornament accent — uses the active motif but
                 stays tiny and decorative, not a wallpaper. -->
            <svg
              width="28"
              height="28"
              viewBox="0 0 42 42"
              fill="none"
              stroke="currentColor"
              stroke-width="1.2"
              class="text-primary opacity-50 hidden sm:block shrink-0"
              aria-hidden="true"
            >
              <g v-html="heroOrnament" />
            </svg>
          </div>

          <h1
            class="font-serif font-black leading-[1.1] tracking-[-0.02em] text-ink"
            style="font-size: clamp(2.125rem, 4.5vw, 3.625rem);"
          >
            {{ t("home.hero.title_line_1") }}<br>
            <em class="italic font-bold" style="color: #1d6a5a;">{{ t("home.hero.title_line_2") }}</em><br>
            {{ t("home.hero.title_line_3_prefix") }}
            <span style="color: var(--color-accent-gold);">{{ t("home.hero.title_line_3_accent") }}</span>
          </h1>

          <p class="text-base sm:text-lg text-ink-secondary leading-relaxed max-w-[42ch]">
            {{ t("home.hero.subtitle") }}
          </p>

          <div class="flex flex-wrap gap-3 pt-1">
            <UiButton :to="localePath('/books')" size="lg">
              <Icon name="book" class="h-4 w-4" />
              {{ t("home.hero.cta_browse") }}
              <Icon name="arrow-right" class="h-4 w-4" />
            </UiButton>
            <UiButton variant="ghost" size="lg" :to="localePath('/authors/me')">
              <Icon name="pencil" class="h-4 w-4" />
              {{ t("home.hero.cta_become_author") }}
            </UiButton>
          </div>

          <div class="pt-6 border-t border-border max-w-xl">
            <div class="text-[11px] uppercase tracking-wider text-ink-tertiary mb-2">
              {{ t("home.hero.languages_label") }}
            </div>
            <div class="flex flex-wrap gap-1.5">
              <span
                v-for="code in ['uz', 'kk', 'ky', 'tr', 'kaa', 'tk', 'tg', 'ru', 'en']"
                :key="code"
                class="inline-flex items-center px-2.5 py-1 rounded-full border border-border bg-bg-card/60 text-xs text-ink-secondary"
              >
                {{ t(`home.languages.${code}`) }}
              </span>
            </div>
          </div>
        </div>

        <div class="hidden md:flex justify-center lg:justify-end relative">
          <div
            aria-hidden="true"
            class="absolute -inset-12 rounded-full opacity-60 blur-3xl"
            style="background-image: radial-gradient(circle, color-mix(in oklab, var(--color-primary) 14%, transparent), transparent 70%);"
          />

          <div class="relative h-[22rem] w-[26rem] lg:w-[28rem]">
            <template v-if="heroBooks.length">
              <div
                v-for="(book, i) in heroBooks"
                :key="book.id"
                class="absolute top-0 left-1/2 h-[22rem] w-48 lg:w-52 rounded-md shadow-2xl overflow-hidden border border-border bg-bg-card transition-all duration-500 hover:-translate-y-2 hover:rotate-0 hover:z-20"
                :style="{
                  transform: `translate(-50%, 0) translateX(${(i - 1) * 90}px) rotate(${(i - 1) * 6}deg)`,
                  zIndex: 10 - i,
                }"
              >
                <img
                  v-if="book.cover_url"
                  :src="book.cover_url"
                  :alt="localised(book.title, book.slug)"
                  loading="eager"
                  class="h-full w-full object-cover"
                >
                <div
                  v-else
                  class="h-full w-full flex flex-col items-center justify-center gap-3 p-4 text-center"
                  :class="[
                    i === 0 ? 'bg-gradient-to-br from-primary/15 via-primary/5 to-bg-card text-primary'
                      : i === 1 ? 'bg-gradient-to-br from-accent-burgundy/15 via-accent-burgundy/5 to-bg-card text-accent-burgundy'
                      : 'bg-gradient-to-br from-accent-gold/15 via-accent-gold/5 to-bg-card text-accent-gold',
                  ]"
                >
                  <Icon name="book" class="h-10 w-10 opacity-60" />
                  <div class="font-serif text-sm text-ink/80 line-clamp-3 leading-snug">
                    {{ localised(book.title, book.slug) }}
                  </div>
                </div>
              </div>
            </template>
            <div
              v-else
              class="absolute inset-0 flex items-center justify-center rounded-md border border-dashed border-border bg-bg-card/60"
            >
              <Icon name="library" class="h-20 w-20 text-primary/30" />
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- STATS -->
    <section class="border-b border-border bg-bg-secondary/40">
      <div class="max-w-6xl mx-auto px-4 py-10 md:py-14">
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 md:gap-6">
          <div
            v-for="(s, i) in [
              { value: 1000, key: 'home.stats.books' },
              { value: 500,  key: 'home.stats.authors' },
              { value: 9,    key: 'home.stats.langs' },
              { value: 30,   key: 'home.stats.categories' },
              { value: 300,  key: 'home.stats.monographs' },
              { value: 1000, key: 'home.stats.doi_works' },
            ]"
            :key="s.key"
            class="reveal text-center sm:text-left"
            :class="`reveal-delay-${(i % 5) + 1}`"
          >
            <div class="font-serif text-3xl md:text-4xl text-primary">
              <UiCounter :target="s.value" />
            </div>
            <div class="text-xs uppercase tracking-wider text-ink-tertiary mt-1">{{ t(s.key) }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- HARD FAILURE FALLBACK -->
    <section v-if="hasError" class="border-b border-border">
      <div class="max-w-3xl mx-auto px-4 py-16">
        <div class="rounded-md border border-error/30 bg-error/5 p-6 flex items-start gap-4">
          <Icon name="warning-solid" class="h-6 w-6 text-error shrink-0" />
          <div>
            <h2 class="font-serif text-lg text-ink mb-1">{{ t("home.error.title") }}</h2>
            <p class="text-sm text-ink-secondary">{{ t("home.error.body") }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- FEATURED -->
    <section v-if="featured.length" class="border-b border-border">
      <div class="max-w-6xl mx-auto px-4 py-12 md:py-16">
        <div class="reveal flex items-end justify-between gap-3 mb-6">
          <div>
            <h2 class="font-serif text-2xl md:text-3xl text-ink leading-tight">
              {{ t("home.featured") }}
            </h2>
            <p class="text-sm text-ink-secondary mt-1">{{ t("home.featured_subtitle") }}</p>
          </div>
          <NuxtLink
            :to="localePath('/books') + '?featured=true'"
            class="hidden sm:inline-flex items-center gap-1 text-sm text-primary hover:underline shrink-0"
          >
            {{ t("home.see_all") }}
            <Icon name="arrow-right" class="h-4 w-4" />
          </NuxtLink>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-4 gap-4 md:gap-5">
          <div
            v-for="(book, i) in featured.slice(0, 4)"
            :key="book.id"
            class="reveal"
            :class="`reveal-delay-${(i % 5) + 1}`"
          >
            <BookCard :book="book" />
          </div>
        </div>
        <NuxtLink
          :to="localePath('/books') + '?featured=true'"
          class="sm:hidden inline-flex items-center gap-1 mt-4 text-sm text-primary hover:underline"
        >
          {{ t("home.see_all") }}
          <Icon name="arrow-right" class="h-4 w-4" />
        </NuxtLink>
      </div>
    </section>

    <!-- CATEGORIES -->
    <section v-if="topCategories.length" class="border-b border-border bg-bg-secondary">
      <div class="max-w-6xl mx-auto px-4 py-12 md:py-16">
        <div class="flex items-end justify-between gap-3 mb-6">
          <div>
            <h2 class="font-serif text-2xl md:text-3xl text-ink leading-tight">
              {{ t("home.categories") }}
            </h2>
            <p class="text-sm text-ink-secondary mt-1">{{ t("home.categories_subtitle") }}</p>
          </div>
          <NuxtLink
            :to="localePath('/books')"
            class="hidden sm:inline-flex items-center gap-1 text-sm text-primary hover:underline shrink-0"
          >
            {{ t("home.see_all") }}
            <Icon name="arrow-right" class="h-4 w-4" />
          </NuxtLink>
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          <NuxtLink
            v-for="cat in topCategories"
            :key="cat.id"
            :to="localePath(`/category/${cat.slug}`)"
            class="group flex items-center gap-3 p-4 rounded-md border border-border bg-bg-card hover:border-primary hover:shadow-sm transition-all"
          >
            <span class="h-10 w-10 rounded-md bg-primary/10 text-primary flex items-center justify-center shrink-0 group-hover:bg-primary group-hover:text-ink-inverse transition-colors">
              <Icon :name="cat.icon" fallback="book" class="h-5 w-5" />
            </span>
            <div class="min-w-0 flex-1">
              <div class="font-medium text-ink truncate group-hover:text-primary transition-colors">
                {{ localised(cat.name, cat.slug) }}
              </div>
              <div class="text-xs text-ink-tertiary mt-0.5">
                {{ t("home.categories_books", { n: cat.book_count }) }}
              </div>
            </div>
            <Icon name="arrow-right" class="h-4 w-4 text-ink-tertiary shrink-0 opacity-0 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all" />
          </NuxtLink>
        </div>
      </div>
    </section>

    <!-- RECENT -->
    <section v-if="recent.length" class="border-b border-border">
      <div class="max-w-6xl mx-auto px-4 py-12 md:py-16">
        <div class="flex items-end justify-between gap-3 mb-6">
          <div>
            <h2 class="font-serif text-2xl md:text-3xl text-ink leading-tight">
              {{ t("home.recent_books") }}
            </h2>
            <p class="text-sm text-ink-secondary mt-1">{{ t("home.recent_subtitle") }}</p>
          </div>
          <NuxtLink
            :to="localePath('/books')"
            class="hidden sm:inline-flex items-center gap-1 text-sm text-primary hover:underline shrink-0"
          >
            {{ t("home.see_all") }}
            <Icon name="arrow-right" class="h-4 w-4" />
          </NuxtLink>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-5">
          <BookCard v-for="book in recent.slice(0, 4)" :key="book.id" :book="book" />
        </div>
        <NuxtLink
          :to="localePath('/books')"
          class="sm:hidden inline-flex items-center gap-1 mt-4 text-sm text-primary hover:underline"
        >
          {{ t("home.see_all") }}
          <Icon name="arrow-right" class="h-4 w-4" />
        </NuxtLink>
      </div>
    </section>

    <!-- FEATURES -->
    <section class="border-b border-border">
      <div class="max-w-6xl mx-auto px-4 py-14 md:py-20">
        <div class="flex justify-center mb-6 reveal">
          <UiOrnamentDivider />
        </div>
        <div class="text-center max-w-2xl mx-auto mb-10 md:mb-14 reveal reveal-delay-1">
          <span class="inline-block px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-medium uppercase tracking-wider">
            {{ t("home.platform.eyebrow") }}
          </span>
          <h2 class="font-serif text-3xl md:text-4xl text-ink leading-tight mt-3">
            {{ t("home.platform.title") }}
          </h2>
          <p class="text-ink-secondary mt-3">{{ t("home.platform.subtitle") }}</p>
        </div>
        <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-5">
          <div
            v-for="(item, i) in [
              { icon: 'sparkles', titleKey: 'home.platform.f1_title', bodyKey: 'home.platform.f1_body' },
              { icon: 'library', titleKey: 'home.platform.f2_title', bodyKey: 'home.platform.f2_body' },
              { icon: 'external-link', titleKey: 'home.platform.f3_title', bodyKey: 'home.platform.f3_body' },
              { icon: 'chart', titleKey: 'home.platform.f4_title', bodyKey: 'home.platform.f4_body' },
              { icon: 'search', titleKey: 'home.platform.f5_title', bodyKey: 'home.platform.f5_body' },
              { icon: 'pencil', titleKey: 'home.platform.f6_title', bodyKey: 'home.platform.f6_body' },
              { icon: 'sparkles', titleKey: 'home.platform.f7_title', bodyKey: 'home.platform.f7_body' },
              { icon: 'academic', titleKey: 'home.platform.f8_title', bodyKey: 'home.platform.f8_body' },
            ]"
            :key="i"
            class="reveal tilt-card rounded-md border border-border bg-bg-card p-5 hover:border-primary/40"
            :class="`reveal-delay-${(i % 5) + 1}`"
          >
            <div class="h-10 w-10 rounded-md bg-primary/10 text-primary flex items-center justify-center mb-3">
              <Icon :name="item.icon as any" class="h-5 w-5" />
            </div>
            <h3 class="font-serif text-lg text-ink leading-snug mb-1.5">{{ t(item.titleKey) }}</h3>
            <p class="text-sm text-ink-secondary leading-relaxed">{{ t(item.bodyKey) }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- MISSION -->
    <section class="relative overflow-hidden border-b border-border bg-ink text-ink-inverse">
      <div
        aria-hidden="true"
        class="absolute inset-0 -z-10 opacity-20"
        style="background-image:
          radial-gradient(ellipse 60% 60% at 80% 20%, var(--color-accent-gold, #c9a961), transparent 65%),
          radial-gradient(ellipse 50% 50% at 10% 80%, var(--color-primary), transparent 60%);"
      />
      <UiOrnamentPattern
        class="absolute inset-0 -z-10"
        tone="gold"
        :tile-size="120"
        :opacity="0.1"
      />
      <UiOrnamentCorner class="absolute top-0 left-0 opacity-30" tone="gold" />
      <UiOrnamentCorner class="absolute bottom-0 right-0 opacity-30" tone="gold" flip />
      <div class="max-w-6xl mx-auto px-4 py-16 md:py-24 grid md:grid-cols-2 gap-10 md:gap-16">
        <div class="reveal">
          <span class="inline-block px-3 py-1 rounded-full bg-white/10 text-white/80 text-xs font-medium uppercase tracking-wider">
            {{ t("home.mission.eyebrow") }}
          </span>
          <h2 class="font-serif text-3xl md:text-5xl text-white leading-tight mt-4">
            {{ t("home.mission.title") }}
          </h2>
          <p class="text-white/80 leading-relaxed mt-5">{{ t("home.mission.body_1") }}</p>
          <p class="text-white/80 leading-relaxed mt-4">{{ t("home.mission.body_2") }}</p>
        </div>
        <div class="reveal reveal-delay-2 rounded-md border border-white/15 bg-white/5 backdrop-blur p-6 md:p-8">
          <h3 class="font-serif text-xl text-white mb-5 inline-flex items-center gap-2">
            <Icon name="sparkles" class="h-5 w-5" />
            {{ t("home.mission.vision_title") }}
          </h3>
          <ul class="space-y-3">
            <li
              v-for="(key, i) in ['library', 'sparkles', 'external-link', 'sparkles', 'search']"
              :key="i"
              class="flex items-start gap-3 text-white/85"
            >
              <span class="h-7 w-7 rounded-full bg-white/10 text-white inline-flex items-center justify-center shrink-0 mt-0.5">
                <Icon :name="key as any" class="h-3.5 w-3.5" />
              </span>
              <span class="leading-relaxed">{{ t(`home.mission.vision_${i + 1}`) }}</span>
            </li>
          </ul>
        </div>
      </div>
    </section>

    <!-- REVIEW REQUEST CTA -->
    <section class="border-b border-border">
      <div class="max-w-6xl mx-auto px-4 py-14 md:py-20">
        <div class="grid md:grid-cols-[1fr_auto] gap-8 md:gap-12 items-center rounded-md border border-primary/20 bg-primary/5 p-6 md:p-10 reveal">
          <div class="space-y-3 min-w-0">
            <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-medium uppercase tracking-wider">
              <Icon name="chat" class="h-3.5 w-3.5" />
              {{ t("home.review_cta.eyebrow") }}
            </span>
            <h2 class="font-serif text-2xl md:text-3xl text-ink leading-tight">
              {{ t("home.review_cta.title") }}
            </h2>
            <p class="text-ink-secondary leading-relaxed max-w-xl">
              {{ t("home.review_cta.body") }}
            </p>
            <ul class="grid sm:grid-cols-3 gap-3 pt-2">
              <li class="flex items-start gap-2 text-sm text-ink">
                <Icon name="upload" class="h-4 w-4 text-primary shrink-0 mt-0.5" />
                <span>{{ t("home.review_cta.step_1") }}</span>
              </li>
              <li class="flex items-start gap-2 text-sm text-ink">
                <Icon name="currency" class="h-4 w-4 text-primary shrink-0 mt-0.5" />
                <span>{{ t("home.review_cta.step_2") }}</span>
              </li>
              <li class="flex items-start gap-2 text-sm text-ink">
                <Icon name="check-circle-solid" class="h-4 w-4 text-primary shrink-0 mt-0.5" />
                <span>{{ t("home.review_cta.step_3") }}</span>
              </li>
            </ul>
          </div>
          <div class="flex md:flex-col gap-3 shrink-0">
            <UiButton :to="localePath('/review-request/new')" size="lg">
              <Icon name="chat" class="h-4 w-4" />
              {{ t("home.review_cta.button") }}
            </UiButton>
          </div>
        </div>
      </div>
    </section>

    <!-- CONTENT TYPES -->
    <section class="border-b border-border">
      <div class="max-w-6xl mx-auto px-4 py-14 md:py-20">
        <div class="flex justify-center mb-8 reveal">
          <UiOrnamentDivider tone="gold" />
        </div>
        <div class="grid md:grid-cols-[1.1fr_1fr] gap-10 md:gap-16 items-start">
          <div class="reveal">
            <span class="inline-block px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-medium uppercase tracking-wider">
              {{ t("home.content_types.eyebrow") }}
            </span>
            <h2 class="font-serif text-3xl md:text-4xl text-ink leading-tight mt-3">
              {{ t("home.content_types.title") }}
            </h2>
            <p class="text-ink-secondary mt-3">{{ t("home.content_types.subtitle") }}</p>
          </div>
          <ul class="space-y-2 reveal reveal-delay-2">
            <li
              v-for="(item, i) in [
                { key: 'monographs', count: '300+', icon: 'book' },
                { key: 'journals', count: '80+', icon: 'news' },
                { key: 'conferences', count: '150+', icon: 'document' },
                { key: 'textbooks', count: '200+', icon: 'library' },
                { key: 'dissertations', count: '120+', icon: 'academic' },
                { key: 'ebooks', count: '100+', icon: 'desktop' },
                { key: 'articles', count: '50+', icon: 'document' },
              ]"
              :key="i"
              class="flex items-center gap-3 rounded-md border border-border bg-bg-card p-3 hover:border-primary/40 hover:translate-x-1 transition-all"
            >
              <span class="h-9 w-9 rounded-md bg-primary/10 text-primary inline-flex items-center justify-center shrink-0">
                <Icon :name="item.icon as any" class="h-4 w-4" />
              </span>
              <span class="flex-1 text-ink">{{ t(`home.content_types.${item.key}`) }}</span>
              <span class="font-serif text-lg text-primary tabular-nums">{{ item.count }}</span>
            </li>
          </ul>
        </div>
      </div>
    </section>

    <!-- EMPTY STATE — show only if no data and no error -->
    <section v-if="!hasAnyData && !hasError" class="border-b border-border">
      <div class="max-w-3xl mx-auto px-4 py-16 text-center">
        <UiEmptyState
          icon="library"
          :title="t('home.empty.title')"
          :description="t('home.empty.body')"
        >
          <UiButton :to="localePath('/authors/me')">
            <Icon name="pencil" class="h-4 w-4" />
            {{ t("home.hero.cta_become_author") }}
          </UiButton>
        </UiEmptyState>
      </div>
    </section>

    <!-- BECOME AUTHOR CTA -->
    <section class="relative overflow-hidden bg-primary/5">
      <div
        aria-hidden="true"
        class="absolute inset-0 -z-10"
        style="background-image:
          radial-gradient(ellipse 50% 80% at 50% 50%, color-mix(in oklab, var(--color-primary) 12%, transparent), transparent 70%);"
      />
      <div class="max-w-5xl mx-auto px-4 py-16 md:py-20">
        <div class="text-center max-w-2xl mx-auto space-y-4 mb-10">
          <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-medium">
            <Icon name="sparkles" class="h-3.5 w-3.5" />
            {{ t("home.become_author_cta.tag") }}
          </span>
          <h2 class="font-serif text-3xl md:text-4xl text-ink leading-tight">
            {{ t("home.become_author_cta.title") }}
          </h2>
          <p class="text-ink-secondary text-base">
            {{ t("home.become_author_cta.body") }}
          </p>
        </div>

        <div class="grid sm:grid-cols-3 gap-4 mb-10 text-center sm:text-left">
          <div class="p-4 rounded-md bg-bg-card border border-border">
            <Icon name="currency" class="h-6 w-6 text-success mb-2 mx-auto sm:mx-0" />
            <div class="font-medium text-ink text-sm">{{ t("home.become_author_cta.perks.earn_title") }}</div>
            <div class="text-xs text-ink-tertiary mt-0.5">{{ t("home.become_author_cta.perks.earn_body") }}</div>
          </div>
          <div class="p-4 rounded-md bg-bg-card border border-border">
            <Icon name="users" class="h-6 w-6 text-primary mb-2 mx-auto sm:mx-0" />
            <div class="font-medium text-ink text-sm">{{ t("home.become_author_cta.perks.reach_title") }}</div>
            <div class="text-xs text-ink-tertiary mt-0.5">{{ t("home.become_author_cta.perks.reach_body") }}</div>
          </div>
          <div class="p-4 rounded-md bg-bg-card border border-border">
            <Icon name="chart" class="h-6 w-6 text-info mb-2 mx-auto sm:mx-0" />
            <div class="font-medium text-ink text-sm">{{ t("home.become_author_cta.perks.insights_title") }}</div>
            <div class="text-xs text-ink-tertiary mt-0.5">{{ t("home.become_author_cta.perks.insights_body") }}</div>
          </div>
        </div>

        <div class="text-center">
          <UiButton :to="localePath('/authors/me')" size="lg">
            <Icon name="pencil" class="h-4 w-4" />
            {{ t("home.become_author_cta.button") }}
          </UiButton>
        </div>
      </div>
    </section>
  </div>
</template>
