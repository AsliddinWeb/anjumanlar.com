<script setup lang="ts">
import type { IconName } from "~/components/ui/Icon.vue";

defineProps<{
  title: string;
  subtitle?: string;
  /** Heroicon name shown above the title in a rounded chip. */
  icon?: IconName;
}>();
</script>

<template>
  <div class="space-y-6">
    <header class="text-center space-y-2">
      <div
        v-if="icon"
        class="inline-flex items-center justify-center h-12 w-12 rounded-full bg-primary/10 text-primary mb-1"
      >
        <Icon :name="icon" class="h-6 w-6" />
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
