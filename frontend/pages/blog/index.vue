<script setup lang="ts">
import type { BlogPostList } from "~/types/api";

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

const { data: postsRaw, pending } = await useAsyncData(
  "blog:list",
  () =>
    api<BlogPostList>("/blog", {
      query: { page: currentPage.value, page_size: PAGE_SIZE },
    }),
  { watch: [currentPage] },
);

const posts = computed(() => postsRaw.value as BlogPostList | null);

function formatDate(iso: string | null) {
  if (!iso) return "";
  return new Intl.DateTimeFormat(locale.value, {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(iso));
}

function changePage(page: number) {
  router.push({ query: { ...route.query, page } });
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}
</script>

<template>
  <section class="max-w-4xl mx-auto px-4 py-8 space-y-6">
    <header class="space-y-1">
      <h1 class="font-serif text-3xl text-ink">{{ t("blog.title") }}</h1>
      <p class="text-sm text-ink-secondary">{{ t("blog.subtitle") }}</p>
    </header>

    <div v-if="pending && !posts" class="space-y-4">
      <UiSkeleton v-for="i in 3" :key="i" :height="'9rem'" :block="true" />
    </div>

    <UiEmptyState
      v-else-if="(posts?.items.length ?? 0) === 0"
      icon="📝"
      :title="t('blog.empty_title')"
      :description="t('blog.empty_body')"
    />

    <ul v-else class="space-y-6">
      <li
        v-for="post in posts!.items"
        :key="post.id"
        class="rounded border border-border bg-bg-card overflow-hidden grid md:grid-cols-[180px_1fr]"
      >
        <NuxtLink
          :to="localePath(`/blog/${post.slug}`)"
          class="h-40 md:h-full bg-bg-secondary"
        >
          <img
            v-if="post.cover_url"
            :src="post.cover_url"
            :alt="localised(post.title, post.slug)"
            class="w-full h-full object-cover"
          >
          <div
            v-else
            class="w-full h-full flex items-center justify-center text-4xl font-serif text-primary/40"
            aria-hidden="true"
          >
            📰
          </div>
        </NuxtLink>
        <div class="p-4 space-y-2">
          <NuxtLink
            :to="localePath(`/blog/${post.slug}`)"
            class="block font-serif text-xl text-ink hover:text-primary leading-snug"
          >
            {{ localised(post.title, post.slug) }}
          </NuxtLink>
          <p class="text-xs text-ink-tertiary">
            {{ t("blog.published_on", { date: formatDate(post.published_at) }) }}
          </p>
          <p v-if="localised(post.excerpt)" class="text-sm text-ink-secondary line-clamp-3">
            {{ localised(post.excerpt) }}
          </p>
          <NuxtLink
            :to="localePath(`/blog/${post.slug}`)"
            class="inline-block text-sm text-primary hover:underline"
          >
            {{ t("blog.read_more") }} →
          </NuxtLink>
        </div>
      </li>
    </ul>

    <div class="pt-2">
      <UiPagination
        :page="currentPage"
        :page-size="PAGE_SIZE"
        :total="posts?.total ?? 0"
        @change="changePage"
      />
    </div>
  </section>
</template>
