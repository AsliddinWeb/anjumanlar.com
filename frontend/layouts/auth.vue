<script setup lang="ts">
// Minimal layout for the unauthenticated flow — header strip, centred
// card on a softly-tinted background, footer pinned to the bottom.
const { t } = useI18n();
const localePath = useLocalePath();
</script>

<template>
  <div class="min-h-screen flex flex-col bg-bg auth-shell">
    <header class="border-b border-border/60 bg-bg/80 backdrop-blur sticky top-0 z-10">
      <div class="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <NuxtLink
          :to="localePath('/')"
          class="font-serif font-bold text-lg text-primary"
        >
          {{ t("site.title") }}
        </NuxtLink>
        <div class="flex items-center gap-2">
          <NuxtLink
            :to="localePath('/')"
            class="hidden sm:inline-flex text-sm text-ink-secondary hover:text-primary mr-2"
          >
            ← {{ t("nav.home") }}
          </NuxtLink>
          <LanguageSwitcher />
          <ThemeToggle />
        </div>
      </div>
    </header>

    <main class="flex-1 flex items-center justify-center px-4 py-10">
      <div
        class="w-full max-w-md bg-bg-card border border-border rounded-lg shadow-lg shadow-primary/5 p-6 md:p-8"
      >
        <slot />
      </div>
    </main>

    <footer class="border-t border-border/60">
      <div
        class="max-w-6xl mx-auto px-4 py-4 text-xs text-ink-tertiary flex flex-wrap items-center justify-between gap-2"
      >
        <span>© {{ new Date().getFullYear() }} {{ t("site.title") }}</span>
        <div class="flex items-center gap-3">
          <NuxtLink :to="localePath('/legal/terms')" class="hover:text-primary">
            {{ t("footer.terms") }}
          </NuxtLink>
          <NuxtLink :to="localePath('/legal/privacy')" class="hover:text-primary">
            {{ t("footer.privacy") }}
          </NuxtLink>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
/* Soft brand-coloured glow behind the card — pure CSS, no extra DOM. */
.auth-shell {
  background-image:
    radial-gradient(
      ellipse 80% 50% at 50% 0%,
      color-mix(in oklab, var(--color-primary) 8%, transparent),
      transparent 60%
    ),
    radial-gradient(
      ellipse 60% 40% at 50% 100%,
      color-mix(in oklab, var(--color-primary) 4%, transparent),
      transparent 60%
    );
}
</style>
