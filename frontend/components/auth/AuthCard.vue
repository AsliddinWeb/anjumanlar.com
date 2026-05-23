<script setup lang="ts">
defineProps<{
  title: string;
  subtitle?: string;
  /** Lucide-style emoji or small mark above the title — purely decorative. */
  badge?: string;
}>();
</script>

<template>
  <div class="space-y-6">
    <header class="text-center space-y-2">
      <div
        v-if="badge"
        class="inline-flex items-center justify-center h-12 w-12 rounded-full bg-primary/10 text-primary text-2xl mb-1"
        aria-hidden="true"
      >
        {{ badge }}
      </div>
      <h1 class="font-serif text-2xl md:text-3xl text-ink leading-tight">
        {{ title }}
      </h1>
      <p v-if="subtitle" class="text-sm text-ink-secondary">{{ subtitle }}</p>
    </header>

    <slot />

    <footer v-if="$slots.footer" class="pt-2 border-t border-border text-sm text-center text-ink-secondary">
      <slot name="footer" />
    </footer>
  </div>
</template>
