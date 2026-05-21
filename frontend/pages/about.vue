<script setup lang="ts">
import type { AuthorList, BookList, CategoryList } from "~/types/api";

const { t } = useI18n();
const localePath = useLocalePath();
const api = useApi();

useHead({
  title: t("about.title"),
  meta: [{ name: "description", content: t("about.subtitle") }],
});

const { data: stats } = await useAsyncData("about:stats", async () => {
  const [books, authors, categories] = await Promise.all([
    api<BookList>("/books", { query: { page_size: 1 } }),
    api<AuthorList>("/authors", { query: { page_size: 1 } }),
    api<CategoryList>("/categories", { query: { active_only: true } }),
  ]);
  return {
    books: books.total,
    authors: authors.total,
    categories: categories.total,
  };
});
</script>

<template>
  <article class="bg-bg">
    <!-- Hero -->
    <section class="border-b border-border">
      <div class="max-w-4xl mx-auto px-4 py-16 text-center">
        <h1 class="font-serif text-3xl md:text-5xl text-ink leading-tight mb-3">
          {{ t("about.title") }}
        </h1>
        <p class="text-lg text-ink-secondary">{{ t("about.subtitle") }}</p>
      </div>
    </section>

    <!-- Mission -->
    <section class="border-b border-border">
      <div class="max-w-3xl mx-auto px-4 py-12 space-y-3">
        <h2 class="font-serif text-2xl text-ink">{{ t("about.mission_title") }}</h2>
        <p class="text-ink-secondary leading-relaxed">{{ t("about.mission_body") }}</p>
      </div>
    </section>

    <!-- For authors / For readers -->
    <section class="border-b border-border bg-bg-secondary">
      <div class="max-w-5xl mx-auto px-4 py-12 grid md:grid-cols-2 gap-8">
        <div class="space-y-3">
          <div class="text-3xl" aria-hidden="true">✍️</div>
          <h3 class="font-serif text-xl text-ink">{{ t("about.for_authors_title") }}</h3>
          <p class="text-sm text-ink-secondary leading-relaxed">
            {{ t("about.for_authors_body") }}
          </p>
          <NuxtLink
            :to="localePath('/authors/me')"
            class="inline-block text-sm text-primary hover:underline"
          >
            {{ t("home.hero.cta_become_author") }} →
          </NuxtLink>
        </div>
        <div class="space-y-3">
          <div class="text-3xl" aria-hidden="true">📖</div>
          <h3 class="font-serif text-xl text-ink">{{ t("about.for_readers_title") }}</h3>
          <p class="text-sm text-ink-secondary leading-relaxed">
            {{ t("about.for_readers_body") }}
          </p>
          <NuxtLink
            :to="localePath('/books')"
            class="inline-block text-sm text-primary hover:underline"
          >
            {{ t("home.hero.cta_browse") }} →
          </NuxtLink>
        </div>
      </div>
    </section>

    <!-- Stats -->
    <section class="border-b border-border">
      <div class="max-w-5xl mx-auto px-4 py-12">
        <h2 class="font-serif text-2xl text-ink text-center mb-8">
          {{ t("about.stats_title") }}
        </h2>
        <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div class="rounded border border-border bg-bg-card p-6 text-center">
            <div class="font-serif text-3xl md:text-4xl text-primary">
              {{ stats?.books ?? 0 }}
            </div>
            <div class="text-sm text-ink-tertiary mt-1">{{ t("about.stat_books") }}</div>
          </div>
          <div class="rounded border border-border bg-bg-card p-6 text-center">
            <div class="font-serif text-3xl md:text-4xl text-primary">
              {{ stats?.authors ?? 0 }}
            </div>
            <div class="text-sm text-ink-tertiary mt-1">{{ t("about.stat_authors") }}</div>
          </div>
          <div class="rounded border border-border bg-bg-card p-6 text-center col-span-2 md:col-span-1">
            <div class="font-serif text-3xl md:text-4xl text-primary">
              {{ stats?.categories ?? 0 }}
            </div>
            <div class="text-sm text-ink-tertiary mt-1">{{ t("about.stat_categories") }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Contact -->
    <section>
      <div class="max-w-3xl mx-auto px-4 py-12 space-y-3">
        <h2 class="font-serif text-2xl text-ink">{{ t("about.contact_title") }}</h2>
        <dl class="text-sm space-y-1">
          <div class="flex gap-2">
            <dt class="text-ink-tertiary min-w-24">{{ t("about.contact_email") }}:</dt>
            <dd>
              <a
                href="mailto:info@anjumanlar.com"
                class="text-primary hover:underline"
              >
                info@anjumanlar.com
              </a>
            </dd>
          </div>
          <div class="flex gap-2">
            <dt class="text-ink-tertiary min-w-24">{{ t("about.contact_telegram") }}:</dt>
            <dd>
              <a
                href="https://t.me/anjumanlar"
                target="_blank"
                rel="noopener noreferrer"
                class="text-primary hover:underline"
              >
                @anjumanlar
              </a>
            </dd>
          </div>
        </dl>
      </div>
    </section>
  </article>
</template>
