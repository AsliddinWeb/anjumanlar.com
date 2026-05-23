<script setup lang="ts">
// Default public layout — used by all routes that don't override.
const { t } = useI18n();
</script>

<template>
  <div class="min-h-screen flex flex-col bg-bg text-ink">
    <a href="#main-content" class="skip-to-content">
      {{ t("nav.skip_to_content") }}
    </a>
    <AppHeader />
    <main id="main-content" class="flex-1" tabindex="-1">
      <slot />
    </main>
    <AppFooter />
  </div>
</template>
