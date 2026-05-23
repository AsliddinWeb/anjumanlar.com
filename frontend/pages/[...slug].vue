<script setup lang="ts">
// Catch-all 404 page. Lives in pages/ so it inherits the default layout
// (header, footer, i18n) — unlike root error.vue, which renders outside
// the plugin context.
const { t } = useI18n();
const localePath = useLocalePath();

definePageMeta({
  // Match anything that didn't hit a real route.
});

setResponseStatus(404);

useSiteSeo({
  title: t("error.404_title"),
  description: t("error.404_body"),
  noindex: true,
});
</script>

<template>
  <section class="max-w-md mx-auto px-4 py-20 text-center space-y-4">
    <div class="font-serif text-6xl md:text-7xl text-primary">404</div>
    <h1 class="font-serif text-2xl text-ink">{{ t("error.404_title") }}</h1>
    <p class="text-ink-secondary">{{ t("error.404_body") }}</p>
    <UiButton size="lg" :to="localePath('/')">
      {{ t("error.go_home") }}
    </UiButton>
  </section>
</template>
