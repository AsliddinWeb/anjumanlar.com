<script setup lang="ts">
const { t } = useI18n();
const localePath = useLocalePath();

useSiteSeo({
  title: t("blog.title"),
  description: t("blog.subtitle"),
});
</script>

<template>
  <section class="max-w-3xl mx-auto px-4 py-12 space-y-6">
    <header class="space-y-1">
      <h1 class="font-serif text-3xl text-ink">{{ t("blog.title") }}</h1>
      <p class="text-sm text-ink-secondary">{{ t("blog.subtitle") }}</p>
    </header>

    <UiEmptyState
      icon="📝"
      :title="t('blog.coming_soon_title')"
      :description="t('blog.coming_soon_body')"
    >
      <UiButton :to="localePath('/books')">
        {{ t("home.hero.cta_browse") }}
      </UiButton>
    </UiEmptyState>
  </section>
</template>
