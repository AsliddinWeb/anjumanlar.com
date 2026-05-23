<script setup lang="ts">
const { t, locale } = useI18n();
const localePath = useLocalePath();

useSiteSeo({
  title: t("footer.terms"),
  description: t("legal.draft_body"),
});

const breadcrumbs = computed(() => [
  { label: t("nav.home"), to: localePath("/") },
  { label: t("footer.legal") },
  { label: t("footer.terms") },
]);

const lastUpdated = new Intl.DateTimeFormat(locale.value, {
  year: "numeric",
  month: "long",
  day: "numeric",
}).format(new Date("2026-05-21"));
</script>

<template>
  <section class="max-w-3xl mx-auto px-4 py-8 space-y-6">
    <UiBreadcrumbs :items="breadcrumbs" />

    <header class="space-y-1">
      <h1 class="font-serif text-3xl text-ink">{{ t("footer.terms") }}</h1>
      <p class="text-xs text-ink-tertiary">{{ t("legal.last_updated", { date: lastUpdated }) }}</p>
    </header>

    <UiEmptyState
      icon="📄"
      :title="t('legal.draft_title')"
      :description="t('legal.draft_body')"
    />
  </section>
</template>
