<script setup lang="ts">
// Default public layout — used by all routes that don't override.
</script>

<template>
  <div class="min-h-screen flex flex-col bg-bg text-ink">
    <AppHeader />
    <main class="flex-1">
      <slot />
    </main>
    <AppFooter />
  </div>
</template>
