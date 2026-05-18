<script setup lang="ts">
const { t } = useI18n();
const localePath = useLocalePath();

useHead({
  title: t("nav.home"),
  meta: [{ name: "description", content: t("site.tagline") }],
});
</script>

<template>
  <section class="max-w-6xl mx-auto px-4 py-16">
    <div class="max-w-2xl">
      <h1 class="font-serif text-4xl md:text-5xl text-ink leading-tight mb-4">
        {{ t("home.hero.title") }}
      </h1>
      <p class="text-lg text-ink-secondary mb-8">{{ t("home.hero.subtitle") }}</p>

      <div class="flex flex-wrap gap-3">
        <NuxtLink
          :to="localePath('/books')"
          class="px-5 py-2.5 rounded bg-primary text-ink-inverse hover:bg-primary-hover transition-colors shadow-md"
        >
          {{ t("home.hero.cta_browse") }}
        </NuxtLink>
        <NuxtLink
          :to="localePath('/about')"
          class="px-5 py-2.5 rounded border border-border text-ink-secondary hover:border-primary hover:text-primary transition-colors"
        >
          {{ t("home.hero.cta_become_author") }}
        </NuxtLink>
      </div>
    </div>

    <div
      class="mt-12 p-4 rounded border border-border bg-bg-card text-sm text-ink-tertiary"
    >
      ⓘ {{ t("home.skeleton_note") }}
    </div>
  </section>
</template>
