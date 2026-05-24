<script setup lang="ts">
import type { AuthorList, BookList, CategoryList } from "~/types/api";

const { t } = useI18n();
const localePath = useLocalePath();
const api = useApi();

useSiteSeo({
  title: t("about.hero.title"),
  description: t("about.hero.subtitle"),
});

const { data: statsRaw } = await useAsyncData("about:stats", async () => {
  const [books, authors, categories] = await Promise.allSettled([
    api<BookList>("/books", { query: { page_size: 1 } }),
    api<AuthorList>("/authors", { query: { page_size: 1 } }),
    api<CategoryList>("/categories", { query: { active_only: true } }),
  ]);
  return {
    books: books.status === "fulfilled" ? books.value.total : 0,
    authors: authors.status === "fulfilled" ? authors.value.total : 0,
    categories: categories.status === "fulfilled" ? categories.value.total : 0,
  };
});

const stats = computed(() => statsRaw.value ?? { books: 0, authors: 0, categories: 0 });

const values = computed(() => [
  { icon: "check-circle" as const, key: "transparency" },
  { icon: "lock" as const, key: "access" },
  { icon: "scale" as const, key: "fair" },
  { icon: "academic" as const, key: "scholarship" },
]);

const steps = computed(() => [
  { num: 1, key: "upload" },
  { num: 2, key: "moderate" },
  { num: 3, key: "sell" },
]);
</script>

<template>
  <article class="bg-bg">
    <!-- HERO -->
    <section class="relative overflow-hidden border-b border-border">
      <div
        aria-hidden="true"
        class="absolute inset-0 -z-10"
        style="background-image:
          radial-gradient(ellipse 60% 50% at 50% 0%, color-mix(in oklab, var(--color-primary) 12%, transparent), transparent 65%);"
      />
      <div class="max-w-3xl mx-auto px-4 py-20 md:py-28 text-center space-y-5">
        <span class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-bg-card/80 backdrop-blur text-xs text-ink-secondary">
          <Icon name="sparkles" class="h-3.5 w-3.5 text-primary" />
          {{ t("about.hero.tag") }}
        </span>
        <h1 class="font-serif text-4xl sm:text-5xl md:text-6xl text-ink leading-[1.1] tracking-tight">
          {{ t("about.hero.title") }}
        </h1>
        <p class="text-lg text-ink-secondary leading-relaxed max-w-2xl mx-auto">
          {{ t("about.hero.subtitle") }}
        </p>
      </div>
    </section>

    <!-- MISSION QUOTE -->
    <section class="border-b border-border">
      <div class="max-w-3xl mx-auto px-4 py-16 md:py-20">
        <div class="space-y-4 text-center">
          <span class="text-[11px] uppercase tracking-wider text-primary font-medium">
            {{ t("about.mission_tag") }}
          </span>
          <blockquote class="font-serif text-2xl md:text-3xl text-ink leading-snug">
            <span class="text-primary text-4xl leading-none">"</span>{{ t("about.mission_quote") }}<span class="text-primary text-4xl leading-none">"</span>
          </blockquote>
          <p class="text-ink-secondary leading-relaxed max-w-2xl mx-auto pt-2">
            {{ t("about.mission_body") }}
          </p>
        </div>
      </div>
    </section>

    <!-- STATS -->
    <section class="border-b border-border bg-bg-secondary">
      <div class="max-w-5xl mx-auto px-4 py-12 md:py-16">
        <div class="grid grid-cols-3 gap-4 md:gap-6">
          <div class="text-center">
            <div class="inline-flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary mb-3">
              <Icon name="book" class="h-6 w-6" />
            </div>
            <div class="font-serif text-3xl md:text-5xl text-ink tabular-nums">{{ stats.books }}+</div>
            <div class="text-xs md:text-sm uppercase tracking-wider text-ink-tertiary mt-1">{{ t("about.stat_books") }}</div>
          </div>
          <div class="text-center">
            <div class="inline-flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary mb-3">
              <Icon name="pencil" class="h-6 w-6" />
            </div>
            <div class="font-serif text-3xl md:text-5xl text-ink tabular-nums">{{ stats.authors }}+</div>
            <div class="text-xs md:text-sm uppercase tracking-wider text-ink-tertiary mt-1">{{ t("about.stat_authors") }}</div>
          </div>
          <div class="text-center">
            <div class="inline-flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary mb-3">
              <Icon name="folder" class="h-6 w-6" />
            </div>
            <div class="font-serif text-3xl md:text-5xl text-ink tabular-nums">{{ stats.categories }}+</div>
            <div class="text-xs md:text-sm uppercase tracking-wider text-ink-tertiary mt-1">{{ t("about.stat_categories") }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- VALUES -->
    <section class="border-b border-border">
      <div class="max-w-6xl mx-auto px-4 py-16 md:py-20">
        <div class="text-center mb-10 space-y-2">
          <span class="text-[11px] uppercase tracking-wider text-primary font-medium">
            {{ t("about.values_tag") }}
          </span>
          <h2 class="font-serif text-3xl md:text-4xl text-ink leading-tight">
            {{ t("about.values_title") }}
          </h2>
          <p class="text-ink-secondary max-w-2xl mx-auto">{{ t("about.values_subtitle") }}</p>
        </div>
        <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div
            v-for="v in values"
            :key="v.key"
            class="rounded-md border border-border bg-bg-card p-5 space-y-3 hover:border-primary/40 transition-colors"
          >
            <div class="inline-flex h-10 w-10 items-center justify-center rounded-md bg-primary/10 text-primary">
              <Icon :name="v.icon" class="h-5 w-5" />
            </div>
            <h3 class="font-serif text-lg text-ink leading-snug">
              {{ t(`about.values.${v.key}.title`) }}
            </h3>
            <p class="text-sm text-ink-secondary leading-relaxed">
              {{ t(`about.values.${v.key}.body`) }}
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- HOW IT WORKS -->
    <section class="border-b border-border bg-bg-secondary">
      <div class="max-w-5xl mx-auto px-4 py-16 md:py-20">
        <div class="text-center mb-10 space-y-2">
          <span class="text-[11px] uppercase tracking-wider text-primary font-medium">
            {{ t("about.how_tag") }}
          </span>
          <h2 class="font-serif text-3xl md:text-4xl text-ink leading-tight">
            {{ t("about.how_title") }}
          </h2>
        </div>
        <ol class="grid md:grid-cols-3 gap-6 relative">
          <li
            v-for="(step, i) in steps"
            :key="step.key"
            class="relative rounded-md border border-border bg-bg-card p-6 space-y-3"
          >
            <div class="font-serif text-5xl text-primary/30 leading-none">{{ step.num }}</div>
            <h3 class="font-serif text-lg text-ink">
              {{ t(`about.how.${step.key}.title`) }}
            </h3>
            <p class="text-sm text-ink-secondary leading-relaxed">
              {{ t(`about.how.${step.key}.body`) }}
            </p>
            <Icon
              v-if="i < steps.length - 1"
              name="arrow-right"
              aria-hidden="true"
              class="hidden md:block absolute -right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-ink-tertiary"
            />
          </li>
        </ol>
      </div>
    </section>

    <!-- FOR AUTHORS / READERS -->
    <section class="border-b border-border">
      <div class="max-w-5xl mx-auto px-4 py-16 md:py-20 grid md:grid-cols-2 gap-6 md:gap-8">
        <div class="relative rounded-md border border-border bg-bg-card p-6 md:p-8 space-y-4 hover:border-primary/40 transition-colors">
          <div class="inline-flex h-12 w-12 items-center justify-center rounded-md bg-primary/10 text-primary">
            <Icon name="pencil" class="h-6 w-6" />
          </div>
          <h3 class="font-serif text-2xl text-ink leading-tight">{{ t("about.for_authors_title") }}</h3>
          <p class="text-sm text-ink-secondary leading-relaxed">
            {{ t("about.for_authors_body") }}
          </p>
          <ul class="space-y-2 text-sm text-ink-secondary">
            <li class="flex items-start gap-2">
              <Icon name="check" class="h-4 w-4 text-success mt-0.5 shrink-0" />
              <span>{{ t("about.for_authors_point1") }}</span>
            </li>
            <li class="flex items-start gap-2">
              <Icon name="check" class="h-4 w-4 text-success mt-0.5 shrink-0" />
              <span>{{ t("about.for_authors_point2") }}</span>
            </li>
            <li class="flex items-start gap-2">
              <Icon name="check" class="h-4 w-4 text-success mt-0.5 shrink-0" />
              <span>{{ t("about.for_authors_point3") }}</span>
            </li>
          </ul>
          <UiButton :to="localePath('/authors/me')" size="md">
            <Icon name="pencil" class="h-4 w-4" />
            {{ t("about.for_authors_cta") }}
          </UiButton>
        </div>

        <div class="relative rounded-md border border-border bg-bg-card p-6 md:p-8 space-y-4 hover:border-primary/40 transition-colors">
          <div class="inline-flex h-12 w-12 items-center justify-center rounded-md bg-primary/10 text-primary">
            <Icon name="book" class="h-6 w-6" />
          </div>
          <h3 class="font-serif text-2xl text-ink leading-tight">{{ t("about.for_readers_title") }}</h3>
          <p class="text-sm text-ink-secondary leading-relaxed">
            {{ t("about.for_readers_body") }}
          </p>
          <ul class="space-y-2 text-sm text-ink-secondary">
            <li class="flex items-start gap-2">
              <Icon name="check" class="h-4 w-4 text-success mt-0.5 shrink-0" />
              <span>{{ t("about.for_readers_point1") }}</span>
            </li>
            <li class="flex items-start gap-2">
              <Icon name="check" class="h-4 w-4 text-success mt-0.5 shrink-0" />
              <span>{{ t("about.for_readers_point2") }}</span>
            </li>
            <li class="flex items-start gap-2">
              <Icon name="check" class="h-4 w-4 text-success mt-0.5 shrink-0" />
              <span>{{ t("about.for_readers_point3") }}</span>
            </li>
          </ul>
          <UiButton variant="ghost" :to="localePath('/books')" size="md">
            <Icon name="book" class="h-4 w-4" />
            {{ t("about.for_readers_cta") }}
          </UiButton>
        </div>
      </div>
    </section>

    <!-- CONTACT -->
    <section>
      <div class="max-w-4xl mx-auto px-4 py-16 md:py-20">
        <div class="text-center mb-8 space-y-2">
          <span class="text-[11px] uppercase tracking-wider text-primary font-medium">
            {{ t("about.contact_tag") }}
          </span>
          <h2 class="font-serif text-3xl md:text-4xl text-ink leading-tight">
            {{ t("about.contact_title") }}
          </h2>
          <p class="text-ink-secondary">{{ t("about.contact_subtitle") }}</p>
        </div>

        <div class="grid sm:grid-cols-2 gap-3 max-w-2xl mx-auto">
          <a
            href="mailto:info@monografiya.com"
            class="group flex items-center gap-4 rounded-md border border-border bg-bg-card p-4 hover:border-primary transition-colors"
          >
            <span class="h-10 w-10 rounded-md bg-primary/10 text-primary flex items-center justify-center shrink-0 group-hover:bg-primary group-hover:text-ink-inverse transition-colors">
              <Icon name="envelope" class="h-5 w-5" />
            </span>
            <div class="min-w-0">
              <div class="text-xs text-ink-tertiary">{{ t("about.contact_email_label") }}</div>
              <div class="text-sm text-ink truncate">info@monografiya.com</div>
            </div>
          </a>

          <a
            href="https://t.me/monografiya"
            target="_blank"
            rel="noopener noreferrer"
            class="group flex items-center gap-4 rounded-md border border-border bg-bg-card p-4 hover:border-primary transition-colors"
          >
            <span class="h-10 w-10 rounded-md bg-primary/10 text-primary flex items-center justify-center shrink-0 group-hover:bg-primary group-hover:text-ink-inverse transition-colors">
              <Icon name="chat" class="h-5 w-5" />
            </span>
            <div class="min-w-0">
              <div class="text-xs text-ink-tertiary">{{ t("about.contact_telegram_label") }}</div>
              <div class="text-sm text-ink truncate">@monografiya</div>
            </div>
          </a>
        </div>

        <p class="text-center text-xs text-ink-tertiary mt-6">
          {{ t("about.contact_response") }}
        </p>
      </div>
    </section>
  </article>
</template>
