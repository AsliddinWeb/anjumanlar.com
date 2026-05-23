<script setup lang="ts">
import type { BlogPostPublic } from "~/types/api";

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

const breadcrumbs = computed(() => [
  { label: t("nav.home"), to: localePath("/") },
  { label: t("blog.title"), to: localePath("/blog") },
  { label: title.value },
]);
</script>

<template>
  <article class="max-w-3xl mx-auto px-4 py-8 space-y-6">
    <UiBreadcrumbs :items="breadcrumbs" />

    <img
      v-if="post.cover_url"
      :src="post.cover_url"
      :alt="title"
      class="w-full rounded-md object-cover aspect-[2/1] border border-border"
    >

    <header class="space-y-2">
      <h1 class="font-serif text-3xl md:text-4xl text-ink leading-tight">{{ title }}</h1>
      <p class="text-sm text-ink-tertiary">
        {{ t("blog.published_on", { date: formatDate(post.published_at) }) }}
      </p>
    </header>

    <p v-if="excerpt" class="text-lg text-ink-secondary leading-relaxed">
      {{ excerpt }}
    </p>

    <!--
      Body is plain text / markdown source. Rendering full markdown
      needs a sanitiser to avoid XSS — for v1 we display the raw text
      with whitespace preserved; rich rendering lands in Phase 7.x
      polish once we pick a hardened parser.
    -->
    <div class="prose-anjuman whitespace-pre-line text-ink leading-relaxed">
      {{ body }}
    </div>

    <footer class="pt-4 border-t border-border">
      <NuxtLink :to="localePath('/blog')" class="inline-flex items-center gap-1 text-sm text-primary hover:underline">
        <Icon name="arrow-left" class="h-4 w-4" />
        {{ t("blog.back_to_list") }}
      </NuxtLink>
    </footer>
  </article>
</template>
