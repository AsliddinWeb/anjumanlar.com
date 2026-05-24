<script setup lang="ts">
import type { BlogPostList, BlogPostPublic } from "~/types/api";

const { t, locale } = useI18n();
const localePath = useLocalePath();
const { localised } = useLocaleText();
const route = useRoute();
const router = useRouter();
const api = useApi();

useSiteSeo({
  title: t("blog.title"),
  description: t("blog.subtitle"),
});

const PAGE_SIZE = 12;
const currentPage = computed(() => Math.max(1, Number(route.query.page) || 1));

const { data: postsRaw, pending, error: blogError } = await useAsyncData(
  "blog:list",
  () =>
    api<BlogPostList>("/blog", {
      query: { page: currentPage.value, page_size: PAGE_SIZE },
    }),
  { watch: [currentPage] },
);

const posts = computed(() => (postsRaw.value as BlogPostList | null)?.items ?? []);
const total = computed(() => (postsRaw.value as BlogPostList | null)?.total ?? 0);

// First post on page 1 becomes the hero; rest are the grid.
const heroPost = computed<BlogPostPublic | null>(() =>
  currentPage.value === 1 && posts.value.length > 0 ? posts.value[0] : null,
);
const gridPosts = computed<BlogPostPublic[]>(() =>
  heroPost.value ? posts.value.slice(1) : posts.value,
);

function formatDate(iso: string | null) {
  if (!iso) return "";
  return new Intl.DateTimeFormat(locale.value, {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(iso));
}

// Rough reading time (200 wpm) — empty body → 1 min.
function readingMinutes(post: BlogPostPublic): number {
  const text = localised(post.body) + " " + localised(post.excerpt);
  const words = text.trim().split(/\s+/).filter(Boolean).length;
  return Math.max(1, Math.round(words / 200));
}

function changePage(page: number) {
  router.push({ query: { ...route.query, page } });
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}
</script>

<template>
  <section class="bg-bg">
    <!-- Hero strip -->
    <header class="relative overflow-hidden border-b border-border">
      <div
        aria-hidden="true"
        class="absolute inset-0 -z-10"
        style="background-image:
          radial-gradient(ellipse 60% 50% at 50% 0%, color-mix(in oklab, var(--color-primary) 10%, transparent), transparent 65%);"
      />
      <div class="max-w-4xl mx-auto px-4 py-12 md:py-16 text-center space-y-4">
        <span class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-bg-card/80 backdrop-blur text-xs text-ink-secondary">
          <Icon name="news" class="h-3.5 w-3.5 text-primary" />
          {{ t("blog.tag") }}
        </span>
        <h1 class="font-serif text-3xl md:text-5xl text-ink leading-tight tracking-tight">
          {{ t("blog.title") }}
        </h1>
        <p class="text-ink-secondary max-w-2xl mx-auto">{{ t("blog.subtitle") }}</p>
      </div>
    </header>

    <div class="max-w-6xl mx-auto px-4 py-10 md:py-12 space-y-10">
      <!-- Loading -->
      <div v-if="pending && posts.length === 0" class="space-y-8">
        <UiSkeleton class="aspect-[16/9]" rounded="rounded-md" block />
        <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          <div v-for="i in 6" :key="i" class="space-y-2">
            <UiSkeleton class="aspect-[16/10]" rounded="rounded-md" block />
            <UiSkeleton width="80%" height="1rem" block />
            <UiSkeleton width="50%" height="0.7rem" block />
          </div>
        </div>
      </div>

      <!-- Error -->
      <div
        v-else-if="blogError"
        class="rounded-md border border-error/30 bg-error/5 p-6 flex items-start gap-4"
      >
        <Icon name="warning-solid" class="h-6 w-6 text-error shrink-0" />
        <div>
          <h2 class="font-serif text-lg text-ink mb-1">{{ t("blog.error_title") }}</h2>
          <p class="text-sm text-ink-secondary">{{ t("blog.error_body") }}</p>
        </div>
      </div>

      <!-- Empty -->
      <UiEmptyState
        v-else-if="posts.length === 0"
        icon="news"
        :title="t('blog.empty_title')"
        :description="t('blog.empty_body')"
      >
        <UiButton variant="ghost" :to="localePath('/books')">
          <Icon name="book" class="h-4 w-4" />
          {{ t("blog.empty_cta") }}
        </UiButton>
      </UiEmptyState>

      <template v-else>
        <!-- Hero post -->
        <NuxtLink
          v-if="heroPost"
          :to="localePath(`/blog/${heroPost.slug}`)"
          class="group block rounded-lg border border-border bg-bg-card overflow-hidden grid md:grid-cols-[1.4fr_1fr] hover:border-primary transition-colors"
        >
          <div class="aspect-[16/10] md:aspect-auto bg-bg-secondary overflow-hidden">
            <img
              v-if="heroPost.cover_url"
              :src="heroPost.cover_url"
              :alt="localised(heroPost.title, heroPost.slug)"
              class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
            >
            <div v-else class="w-full h-full flex items-center justify-center text-primary/30">
              <Icon name="news" class="h-20 w-20" />
            </div>
          </div>
          <div class="p-6 md:p-8 flex flex-col justify-center space-y-3">
            <span class="inline-flex items-center gap-1.5 self-start px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs font-medium">
              <Icon name="sparkles" class="h-3 w-3" />
              {{ t("blog.latest") }}
            </span>
            <h2 class="font-serif text-2xl md:text-3xl text-ink leading-tight group-hover:text-primary transition-colors">
              {{ localised(heroPost.title, heroPost.slug) }}
            </h2>
            <p v-if="localised(heroPost.excerpt)" class="text-ink-secondary leading-relaxed line-clamp-3">
              {{ localised(heroPost.excerpt) }}
            </p>
            <div class="flex items-center gap-3 pt-1 text-xs text-ink-tertiary">
              <span class="inline-flex items-center gap-1">
                <Icon name="sparkles" class="h-3.5 w-3.5" />
                {{ formatDate(heroPost.published_at) }}
              </span>
              <span>·</span>
              <span class="inline-flex items-center gap-1">
                <Icon name="document" class="h-3.5 w-3.5" />
                {{ t("blog.reading_minutes", { n: readingMinutes(heroPost) }) }}
              </span>
            </div>
            <span class="inline-flex items-center gap-1 text-sm text-primary group-hover:underline pt-2">
              {{ t("blog.read_more") }}
              <Icon name="arrow-right" class="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </span>
          </div>
        </NuxtLink>

        <!-- Grid of remaining posts -->
        <section v-if="gridPosts.length > 0" class="space-y-5">
          <div class="flex items-end justify-between gap-3">
            <h2 v-if="heroPost" class="font-serif text-2xl text-ink leading-tight">
              {{ t("blog.more_posts") }}
            </h2>
            <span class="text-sm text-ink-tertiary tabular-nums">
              {{ t("blog.total", { n: total }) }}
            </span>
          </div>
          <ul class="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            <li v-for="post in gridPosts" :key="post.id">
              <NuxtLink
                :to="localePath(`/blog/${post.slug}`)"
                class="group block rounded-md border border-border bg-bg-card overflow-hidden hover:border-primary transition-colors h-full"
              >
                <div class="aspect-[16/10] bg-bg-secondary overflow-hidden">
                  <img
                    v-if="post.cover_url"
                    :src="post.cover_url"
                    :alt="localised(post.title, post.slug)"
                    class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                  >
                  <div v-else class="w-full h-full flex items-center justify-center text-primary/30">
                    <Icon name="news" class="h-12 w-12" />
                  </div>
                </div>
                <div class="p-4 space-y-2">
                  <h3 class="font-serif text-lg text-ink leading-snug line-clamp-2 group-hover:text-primary transition-colors">
                    {{ localised(post.title, post.slug) }}
                  </h3>
                  <p v-if="localised(post.excerpt)" class="text-sm text-ink-secondary line-clamp-2">
                    {{ localised(post.excerpt) }}
                  </p>
                  <div class="flex items-center gap-2 pt-1 text-xs text-ink-tertiary">
                    <span>{{ formatDate(post.published_at) }}</span>
                    <span>·</span>
                    <span>{{ t("blog.reading_minutes", { n: readingMinutes(post) }) }}</span>
                  </div>
                </div>
              </NuxtLink>
            </li>
          </ul>
        </section>

        <div v-if="total > PAGE_SIZE" class="pt-2">
          <UiPagination
            :page="currentPage"
            :page-size="PAGE_SIZE"
            :total="total"
            @change="changePage"
          />
        </div>
      </template>
    </div>
  </section>
</template>
