<script setup lang="ts">
import type { AuthorPublic, BookList } from "~/types/api";

const { t, locale } = useI18n();
const route = useRoute();
const router = useRouter();
const localePath = useLocalePath();
const { localised } = useLocaleText();
const { formatDate } = useFormatDate();
const api = useApi();

const slug = computed(() => route.params.slug as string);

const PAGE_SIZE = 12;

const currentPage = computed(() => Math.max(1, Number(route.query.page) || 1));
const sortValue = computed(() => (route.query.sort as string) || "-published_at");

const { data: authorRaw, error: authorErr } = await useAsyncData(
  `author:${slug.value}`,
  () => api<AuthorPublic>(`/authors/${slug.value}`),
  { watch: [slug] },
);

if (authorErr.value || !authorRaw.value) {
  throw createError({
    statusCode: 404,
    statusMessage: t("authors.profile_not_found"),
    fatal: true,
  });
}

const author = computed(() => authorRaw.value as AuthorPublic);

const { data: booksRaw, pending: booksPending, error: booksError } = await useAsyncData(
  `author:${slug.value}:books`,
  () =>
    api<BookList>("/books", {
      query: {
        author: slug.value,
        page: currentPage.value,
        page_size: PAGE_SIZE,
        sort: sortValue.value,
      },
    }),
  { watch: [slug, currentPage, sortValue] },
);

const books = computed(() => booksRaw.value as BookList | null);
const total = computed(() => books.value?.total ?? 0);

const bio = computed(() => localised(author.value.bio));

useSiteSeo({
  title: author.value.display_name,
  description: bio.value.slice(0, 160) || t("site.tagline"),
  ogType: "profile",
});

const runtime = useRuntimeConfig();
const siteUrl = runtime.public.siteUrl as string;
useStructuredData([
  buildPersonSchema({
    name: author.value.display_name,
    url: `${siteUrl}/${locale.value}/authors/${author.value.slug}`,
    description: bio.value || undefined,
    worksFor: author.value.institution,
    jobTitle: author.value.academic_title,
    sameAs: author.value.website ? [author.value.website] : undefined,
  }),
  buildBreadcrumbList([
    { name: t("nav.home"), url: `${siteUrl}/${locale.value}` },
    { name: t("authors.title"), url: `${siteUrl}/${locale.value}/authors` },
    { name: author.value.display_name, url: `${siteUrl}/${locale.value}/authors/${author.value.slug}` },
  ]),
]);

const breadcrumbs = computed(() => [
  { label: t("nav.home"), to: localePath("/") },
  { label: t("authors.title"), to: localePath("/authors") },
  { label: author.value.display_name },
]);

const initials = computed(() =>
  author.value.display_name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((p) => p.charAt(0).toUpperCase())
    .join(""),
);

const joinedAt = computed(() => formatDate(author.value.created_at, { withTime: false }));

const socialEntries = computed(() => Object.entries(author.value.social_links ?? {}));

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
  { value: "-sales_count", label: t("catalog.sort.sales") },
  { value: "-average_rating", label: t("catalog.sort.rating") },
]);
</script>

<template>
  <article v-if="author" class="bg-bg">
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
      <div class="max-w-6xl mx-auto px-4 py-10 md:py-14 grid md:grid-cols-[auto_1fr] gap-6 md:gap-8 items-start">
        <div class="relative">
          <div
            aria-hidden="true"
            class="absolute -inset-3 rounded-full opacity-50 blur-2xl"
            style="background-image: radial-gradient(circle, color-mix(in oklab, var(--color-primary) 18%, transparent), transparent 70%);"
          />
          <div
            class="relative h-24 w-24 md:h-28 md:w-28 rounded-full bg-primary text-ink-inverse flex items-center justify-center text-3xl md:text-4xl font-semibold shadow-lg ring-4 ring-bg"
          >
            {{ initials || "?" }}
          </div>
        </div>

        <div class="space-y-3 min-w-0">
          <div class="flex flex-wrap items-center gap-2">
            <h1 class="font-serif text-3xl md:text-4xl text-ink leading-tight tracking-tight">
              {{ author.display_name }}
            </h1>
            <UiBadge v-if="author.verified" tone="success" size="sm" class="inline-flex items-center gap-1">
              <Icon name="check-circle-solid" class="h-3.5 w-3.5" />
              {{ t("authors.verified") }}
            </UiBadge>
            <UiBadge v-if="author.featured" tone="gold" size="sm" class="inline-flex items-center gap-1">
              <Icon name="star-solid" class="h-3.5 w-3.5" />
              {{ t("authors.featured") }}
            </UiBadge>
          </div>

          <p v-if="author.academic_title" class="text-ink-secondary text-base">
            {{ author.academic_title }}
          </p>

          <dl class="flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-ink-secondary">
            <div v-if="author.institution" class="inline-flex items-center gap-1.5">
              <Icon name="institution" class="h-4 w-4 text-ink-tertiary" />
              <span>{{ author.institution }}</span>
            </div>
            <div v-if="author.website" class="inline-flex items-center gap-1.5">
              <Icon name="external" class="h-4 w-4 text-ink-tertiary" />
              <a
                :href="author.website"
                target="_blank"
                rel="noopener noreferrer"
                class="text-primary hover:underline truncate max-w-[18ch]"
              >
                {{ author.website.replace(/^https?:\/\//, "") }}
              </a>
            </div>
            <div class="inline-flex items-center gap-1.5">
              <Icon name="sparkles" class="h-4 w-4 text-ink-tertiary" />
              <span>{{ t("authors.joined_at", { date: joinedAt }) }}</span>
            </div>
          </dl>

          <div v-if="socialEntries.length" class="flex flex-wrap gap-1.5 pt-1">
            <a
              v-for="[label, href] in socialEntries"
              :key="label"
              :href="href"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full border border-border bg-bg-card text-xs text-ink-secondary hover:border-primary hover:text-primary transition-colors"
            >
              <Icon name="external" class="h-3 w-3" />
              {{ label }}
            </a>
          </div>
        </div>
      </div>
    </header>

    <!-- Stats strip -->
    <section class="border-b border-border bg-bg-secondary/40">
      <div class="max-w-6xl mx-auto px-4 py-5 grid grid-cols-3 gap-4">
        <div class="text-center sm:text-left">
          <div class="text-xs uppercase tracking-wider text-ink-tertiary">
            {{ t("authors.stat_books") }}
          </div>
          <div class="font-serif text-2xl text-ink mt-0.5 tabular-nums">{{ total }}</div>
        </div>
        <div class="text-center sm:text-left">
          <div class="text-xs uppercase tracking-wider text-ink-tertiary">
            {{ t("authors.stat_sales") }}
          </div>
          <div class="font-serif text-2xl text-ink mt-0.5 tabular-nums">
            {{ author.total_sales }}
          </div>
        </div>
        <div class="text-center sm:text-left">
          <div class="text-xs uppercase tracking-wider text-ink-tertiary">
            {{ t("authors.stat_joined") }}
          </div>
          <div class="font-serif text-2xl text-ink mt-0.5">{{ joinedAt }}</div>
        </div>
      </div>
    </section>

    <div class="max-w-6xl mx-auto px-4 py-8 md:py-10 space-y-10">
      <!-- Bio -->
      <section v-if="bio" class="prose-anjuman max-w-3xl">
        <h2 class="font-serif text-2xl text-ink leading-tight mb-4">
          {{ t("authors.about_heading") }}
        </h2>
        <p class="text-ink leading-relaxed whitespace-pre-line">{{ bio }}</p>
      </section>

      <!-- Books -->
      <section class="space-y-4">
        <div class="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 class="font-serif text-2xl text-ink leading-tight">
              {{ t("authors.books_by", { name: author.display_name }) }}
            </h2>
            <p class="text-sm text-ink-secondary mt-1 tabular-nums">
              {{ t("catalog.results", { n: total }) }}
            </p>
          </div>

          <div v-if="total > 1" class="relative">
            <Icon
              name="chart"
              class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-tertiary pointer-events-none"
            />
            <select
              :value="sortValue"
              class="appearance-none pl-9 pr-9 py-2 rounded-md border border-border bg-bg-card text-sm text-ink focus:outline-none focus:border-primary cursor-pointer"
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
          v-if="booksPending && !books"
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
            <h3 class="font-serif text-lg text-ink mb-1">{{ t("authors.error_books_title") }}</h3>
            <p class="text-sm text-ink-secondary">{{ t("authors.error_books_body") }}</p>
          </div>
        </div>

        <!-- Empty -->
        <UiEmptyState
          v-else-if="(books?.items.length ?? 0) === 0"
          icon="inbox"
          :title="t('authors.no_books_by')"
          :description="t('authors.no_books_by_body')"
        />

        <div v-else>
          <div
            class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-5 transition-opacity"
            :class="booksPending ? 'opacity-50 pointer-events-none' : ''"
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
    </div>
  </article>
</template>
