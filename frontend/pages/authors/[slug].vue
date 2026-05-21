<script setup lang="ts">
import type { AuthorPublic, BookList } from "~/types/api";

const { t, locale } = useI18n();
const route = useRoute();
const router = useRouter();
const localePath = useLocalePath();
const { localised } = useLocaleText();
const api = useApi();

const slug = computed(() => route.params.slug as string);

const PAGE_SIZE = 12;

const currentPage = computed(() =>
  Math.max(1, Number(route.query.page) || 1),
);

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

const { data: booksRaw, pending: booksPending } = await useAsyncData(
  `author:${slug.value}:books`,
  () =>
    api<BookList>("/books", {
      query: {
        author: slug.value,
        page: currentPage.value,
        page_size: PAGE_SIZE,
        sort: "-published_at",
      },
    }),
  { watch: [slug, currentPage] },
);

const books = computed(() => booksRaw.value as BookList | null);

const bio = computed(() => localised(author.value.bio));

useHead({
  title: author.value.display_name,
  meta: [
    { name: "description", content: bio.value.slice(0, 160) || t("site.tagline") },
  ],
});

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

const joinedAt = computed(() =>
  new Intl.DateTimeFormat(locale.value, { year: "numeric", month: "long" })
    .format(new Date(author.value.created_at)),
);

const socialEntries = computed(() => Object.entries(author.value.social_links ?? {}));

function changePage(page: number) {
  router.push({ query: { ...route.query, page } });
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}
</script>

<template>
  <article class="max-w-6xl mx-auto px-4 py-8 space-y-8">
    <UiBreadcrumbs :items="breadcrumbs" />

    <header class="grid md:grid-cols-[120px_1fr] gap-6 items-start">
      <div
        class="h-24 w-24 md:h-28 md:w-28 rounded-full bg-bg-secondary flex items-center justify-center text-3xl font-medium text-ink-secondary"
      >
        {{ initials || "?" }}
      </div>

      <div class="space-y-3">
        <div class="flex flex-wrap items-center gap-2">
          <h1 class="font-serif text-3xl text-ink">{{ author.display_name }}</h1>
          <UiBadge v-if="author.verified" tone="success" size="sm">
            ✓ {{ t("authors.verified") }}
          </UiBadge>
          <UiBadge v-if="author.featured" tone="gold" size="sm">
            ★ {{ t("authors.featured") }}
          </UiBadge>
        </div>

        <p v-if="author.academic_title" class="text-ink-secondary">
          {{ author.academic_title }}
        </p>

        <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1 text-sm">
          <div v-if="author.institution" class="flex gap-2">
            <dt class="text-ink-tertiary">{{ t("authors.institution") }}:</dt>
            <dd class="text-ink">{{ author.institution }}</dd>
          </div>
          <div v-if="author.website" class="flex gap-2">
            <dt class="text-ink-tertiary">{{ t("authors.website") }}:</dt>
            <dd class="text-ink truncate">
              <a
                :href="author.website"
                target="_blank"
                rel="noopener noreferrer"
                class="text-primary hover:underline"
              >
                {{ author.website }}
              </a>
            </dd>
          </div>
          <div class="flex gap-2">
            <dt class="text-ink-tertiary">{{ t("authors.joined_at", { date: joinedAt }) }}</dt>
          </div>
          <div class="flex gap-2">
            <dt class="text-ink-tertiary">
              {{ t("authors.total_sales", { n: author.total_sales }) }}
            </dt>
          </div>
        </dl>

        <div v-if="socialEntries.length" class="flex flex-wrap gap-2 pt-1">
          <a
            v-for="[label, href] in socialEntries"
            :key="label"
            :href="href"
            target="_blank"
            rel="noopener noreferrer"
            class="text-xs text-primary hover:underline"
          >
            {{ label }}
          </a>
        </div>

        <p v-if="bio" class="text-ink leading-relaxed whitespace-pre-line pt-3">{{ bio }}</p>
      </div>
    </header>

    <section class="space-y-4 pt-4 border-t border-border">
      <h2 class="font-serif text-2xl text-ink">
        {{ t("authors.books_by", { name: author.display_name }) }}
      </h2>

      <div
        v-if="booksPending && !books"
        class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4"
      >
        <div v-for="i in 4" :key="i" class="space-y-2">
          <UiSkeleton class="aspect-[2/3] !block" :rounded="'rounded'" />
          <UiSkeleton :width="'80%'" :height="'1rem'" :block="true" />
        </div>
      </div>

      <UiEmptyState
        v-else-if="(books?.items.length ?? 0) === 0"
        icon="📭"
        :title="t('authors.no_books_by')"
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
  </article>
</template>
