<script setup lang="ts">
withDefaults(
  defineProps<{
    width?: string;
    height?: string;
    rounded?: string;
    block?: boolean;
  }>(),
  {
    width: "100%",
    height: "1rem",
    rounded: "rounded",
  },
);
</script>

<template>
  <span
    class="inline-block animate-pulse bg-bg-secondary"
    :class="[rounded, block ? 'block' : '']"
    :style="{ width, height }"
    aria-hidden="true"
  />
</template>
