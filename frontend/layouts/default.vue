<script setup lang="ts">
// Default public layout — used by all routes that don't override.
</script>

<template>
  <div class="min-h-screen flex flex-col bg-bg text-ink">
    <AppHeader />
    <main class="flex-1">
      <slot />
    </main>
    <footer class="border-t border-border mt-12">
      <div class="max-w-6xl mx-auto px-4 py-6 text-sm text-ink-tertiary">
        © {{ new Date().getFullYear() }} Anjumanlar.com
      </div>
    </footer>
  </div>
</template>
