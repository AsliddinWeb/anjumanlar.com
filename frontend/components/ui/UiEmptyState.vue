<script setup lang="ts">
defineProps<{
  title?: string;
  description?: string;
  icon?: string;
}>();
</script>

<template>
  <div class="text-center py-12 px-4">
    <div
      v-if="icon"
      class="text-4xl mb-3 text-ink-tertiary"
      aria-hidden="true"
    >
      {{ icon }}
    </div>
    <h3 v-if="title" class="font-serif text-lg text-ink mb-1">{{ title }}</h3>
    <p v-if="description" class="text-sm text-ink-secondary mb-4">
      {{ description }}
    </p>
    <slot />
  </div>
</template>
