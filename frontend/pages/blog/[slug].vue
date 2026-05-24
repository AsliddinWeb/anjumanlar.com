<script setup lang="ts">
import type { BlogPostList, BlogPostPublic } from "~/types/api";

const { t, locale } = useI18n();
const localePath = useLocalePath();
const { localised } = useLocaleText();
const route = useRoute();
const api = useApi();

const slug = computed(() => route.params.slug as string);

const { data: postRaw, error } = await useAsyncData(
  `blog:${slug.value}`,
  () => api<BlogPostPublic>(`/blog/${slug.value}`),
  { watch: [slug] },
);

if (error.value || !postRaw.value) {
  throw createError({
    statusCode: 404,
    statusMessage: t("blog.not_found"),
    fatal: true,
  });
}

const post = computed(() => postRaw.value as BlogPostPublic);
const title = computed(() => localised(post.value.title, post.value.slug));
const body = computed(() => localised(post.value.body));
const excerpt = computed(() => localised(post.value.excerpt));

useSiteSeo({
  title: title.value,
  description: excerpt.value || body.value.slice(0, 160) || t("blog.subtitle"),
  image: post.value.cover_url ?? undefined,
  ogType: "article",
});

const runtime = useRuntimeConfig();
const siteUrl = runtime.public.siteUrl as string;
useStructuredData([
  {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    "headline": title.value,
    "description": excerpt.value || body.value.slice(0, 160),
    "image": post.value.cover_url ?? undefined,
    "datePublished": post.value.published_at,
    "dateModified": post.value.published_at,
    "inLanguage": locale.value,
    "url": `${siteUrl}/${locale.value}/blog/${post.value.slug}`,
  },
  buildBreadcrumbList([
    { name: t("nav.home"), url: `${siteUrl}/${locale.value}` },
    { name: t("blog.title"), url: `${siteUrl}/${locale.value}/blog` },
    { name: title.value, url: `${siteUrl}/${locale.value}/blog/${post.value.slug}` },
  ]),
]);

function formatDate(iso: string | null) {
  if (!iso) return "";
  return new Intl.DateTimeFormat(locale.value, {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(iso));
}

const readingMinutes = computed(() => {
  const text = body.value + " " + excerpt.value;
  const words = text.trim().split(/\s+/).filter(Boolean).length;
  return Math.max(1, Math.round(words / 200));
});

const breadcrumbs = computed(() => [
  { label: t("nav.home"), to: localePath("/") },
  { label: t("blog.title"), to: localePath("/blog") },
  { label: title.value },
]);

// Related posts — exclude current, take latest 3.
const { data: relatedRaw } = await useAsyncData(
  `blog:${slug.value}:related`,
  () => api<BlogPostList>("/blog", { query: { page: 1, page_size: 4 } }).catch(() => null),
);
const related = computed<BlogPostPublic[]>(() => {
  const items = ((relatedRaw.value as BlogPostList | null)?.items ?? []) as BlogPostPublic[];
  return items.filter((p) => p.id !== post.value.id).slice(0, 3);
});

// --- Copy URL to clipboard
const copied = ref(false);
async function copyLink() {
  if (!import.meta.client) return;
  try {
    await navigator.clipboard.writeText(window.location.href);
    copied.value = true;
    setTimeout(() => { copied.value = false; }, 2000);
  }
  catch { /* ignore */ }
}
</script>

<template>
  <article v-if="post" class="bg-bg">
    <!-- Breadcrumbs strip -->
    <div class="border-b border-border bg-bg-secondary/40">
      <div class="max-w-3xl mx-auto px-4 py-3">
        <UiBreadcrumbs :items="breadcrumbs" />
      </div>
    </div>

    <!-- Article header -->
    <header class="max-w-3xl mx-auto px-4 pt-10 md:pt-14 space-y-5">
      <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-primary/10 text-primary text-xs font-medium">
        <Icon name="news" class="h-3.5 w-3.5" />
        {{ t("blog.label") }}
      </span>
      <h1 class="font-serif text-3xl md:text-5xl text-ink leading-[1.1] tracking-tight">
        {{ title }}
      </h1>
      <div class="flex flex-wrap items-center gap-4 text-sm text-ink-tertiary">
        <span class="inline-flex items-center gap-1.5">
          <Icon name="sparkles" class="h-4 w-4" />
          {{ formatDate(post.published_at) }}
        </span>
        <span>·</span>
        <span class="inline-flex items-center gap-1.5">
          <Icon name="document" class="h-4 w-4" />
          {{ t("blog.reading_minutes", { n: readingMinutes }) }}
        </span>
      </div>
    </header>

    <!-- Cover -->
    <figure v-if="post.cover_url" class="max-w-4xl mx-auto px-4 mt-8">
      <img
        :src="post.cover_url"
        :alt="title"
        class="w-full rounded-lg aspect-[2/1] object-cover border border-border shadow-sm"
      >
    </figure>

    <!-- Body -->
    <div class="max-w-3xl mx-auto px-4 py-10 md:py-12 space-y-6">
      <p v-if="excerpt" class="text-lg md:text-xl text-ink-secondary leading-relaxed font-serif italic border-l-2 border-primary pl-4">
        {{ excerpt }}
      </p>

      <!--
        Body is plain text / markdown source. Rendering full markdown
        needs a sanitiser to avoid XSS — for v1 we display the raw text
        with whitespace preserved.
      -->
      <div class="prose-anjuman whitespace-pre-line text-ink text-base md:text-lg leading-[1.75]">
        {{ body }}
      </div>

      <!-- Share + back -->
      <footer class="pt-6 border-t border-border space-y-4">
        <div class="flex flex-wrap items-center gap-2">
          <span class="text-xs uppercase tracking-wider text-ink-tertiary mr-1">
            {{ t("blog.share") }}
          </span>
          <button
            type="button"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-border bg-bg-card text-xs text-ink-secondary hover:border-primary hover:text-primary transition-colors"
            @click="copyLink"
          >
            <Icon :name="copied ? 'check' : 'document'" class="h-3.5 w-3.5" />
            {{ copied ? t("blog.copied") : t("blog.copy_link") }}
          </button>
          <a
            :href="`https://t.me/share/url?url=${encodeURIComponent(`${siteUrl}/${locale}/blog/${post.slug}`)}&text=${encodeURIComponent(title)}`"
            target="_blank"
            rel="noopener noreferrer"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-border bg-bg-card text-xs text-ink-secondary hover:border-primary hover:text-primary transition-colors"
          >
            <Icon name="external" class="h-3.5 w-3.5" />
            Telegram
          </a>
        </div>

        <NuxtLink
          :to="localePath('/blog')"
          class="inline-flex items-center gap-1 text-sm text-primary hover:underline"
        >
          <Icon name="arrow-left" class="h-4 w-4" />
          {{ t("blog.back_to_list") }}
        </NuxtLink>
      </footer>
    </div>

    <!-- Related posts -->
    <section v-if="related.length > 0" class="border-t border-border bg-bg-secondary/40">
      <div class="max-w-5xl mx-auto px-4 py-10 md:py-12 space-y-5">
        <div class="flex items-end justify-between gap-3">
          <h2 class="font-serif text-2xl text-ink leading-tight">
            {{ t("blog.related") }}
          </h2>
          <NuxtLink
            :to="localePath('/blog')"
            class="hidden sm:inline-flex items-center gap-1 text-sm text-primary hover:underline"
          >
            {{ t("blog.see_all") }}
            <Icon name="arrow-right" class="h-4 w-4" />
          </NuxtLink>
        </div>
        <ul class="grid sm:grid-cols-3 gap-4">
          <li v-for="p in related" :key="p.id">
            <NuxtLink
              :to="localePath(`/blog/${p.slug}`)"
              class="group block rounded-md border border-border bg-bg-card overflow-hidden hover:border-primary transition-colors h-full"
            >
              <div class="aspect-[16/10] bg-bg-secondary overflow-hidden">
                <img
                  v-if="p.cover_url"
                  :src="p.cover_url"
                  :alt="localised(p.title, p.slug)"
                  class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                >
                <div v-else class="w-full h-full flex items-center justify-center text-primary/30">
                  <Icon name="news" class="h-10 w-10" />
                </div>
              </div>
              <div class="p-3 space-y-1">
                <h3 class="font-serif text-base text-ink leading-snug line-clamp-2 group-hover:text-primary transition-colors">
                  {{ localised(p.title, p.slug) }}
                </h3>
                <p class="text-xs text-ink-tertiary">{{ formatDate(p.published_at) }}</p>
              </div>
            </NuxtLink>
          </li>
        </ul>
      </div>
    </section>
  </article>
</template>
