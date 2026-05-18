<script setup lang="ts">
const { t } = useI18n();
const localePath = useLocalePath();

const nav = computed(() => [
  { to: "/", label: t("nav.home") },
  { to: "/books", label: t("nav.books") },
  { to: "/authors", label: t("nav.authors") },
  { to: "/blog", label: t("nav.blog") },
  { to: "/about", label: t("nav.about") },
]);
</script>

<template>
  <header class="sticky top-0 z-30 bg-bg/90 backdrop-blur border-b border-border">
    <div class="max-w-6xl mx-auto px-4 h-14 flex items-center gap-6">
      <NuxtLink :to="localePath('/')" class="font-serif font-bold text-lg text-primary">
        {{ t("site.title") }}
      </NuxtLink>

      <nav class="hidden md:flex items-center gap-4 text-sm">
        <NuxtLink
          v-for="item in nav"
          :key="item.to"
          :to="localePath(item.to)"
          class="text-ink-secondary hover:text-primary transition-colors"
        >
          {{ item.label }}
        </NuxtLink>
      </nav>

      <div class="flex-1" />

      <LanguageSwitcher />
      <ThemeToggle />
    </div>
  </header>
</template>
