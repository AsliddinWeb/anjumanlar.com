<script setup lang="ts">
import type { IconName } from "~/utils/icons";

defineProps<{
  title?: string;
  description?: string;
  icon?: IconName;
}>();
</script>

<template>
  <div class="text-center py-12 px-4">
    <div
      v-if="icon"
      class="inline-flex items-center justify-center h-14 w-14 rounded-full bg-bg-secondary text-ink-tertiary mb-3"
    >
      <Icon :name="icon" class="h-7 w-7" />
    </div>
    <h3 v-if="title" class="font-serif text-lg text-ink mb-1">{{ title }}</h3>
    <p v-if="description" class="text-sm text-ink-secondary mb-4">
      {{ description }}
    </p>
    <slot />
  </div>
</template>
