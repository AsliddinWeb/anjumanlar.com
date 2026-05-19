<script setup lang="ts">
// Minimal layout for the unauthenticated flow — no nav, just brand + card.
const { t } = useI18n();
const localePath = useLocalePath();
</script>

<template>
  <div class="min-h-screen flex flex-col bg-bg">
    <header class="border-b border-border bg-bg-card">
      <div class="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <NuxtLink :to="localePath('/')" class="font-serif font-bold text-lg text-primary">
          {{ t("site.title") }}
        </NuxtLink>
        <div class="flex items-center gap-2">
          <LanguageSwitcher />
          <ThemeToggle />
        </div>
      </div>
    </header>

    <main class="flex-1 flex items-center justify-center px-4 py-8">
      <div
        class="w-full max-w-md bg-bg-card border border-border rounded-md shadow-md p-6 md:p-8"
      >
        <slot />
      </div>
    </main>

    <footer class="border-t border-border">
      <div
        class="max-w-6xl mx-auto px-4 py-4 text-xs text-ink-tertiary text-center"
      >
        © {{ new Date().getFullYear() }} {{ t("site.title") }}
      </div>
    </footer>
  </div>
</template>
