<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    src: string | null | undefined;
    alt: string;
    aspect?: "book" | "square";
    rounded?: boolean;
    eager?: boolean;
  }>(),
  {
    aspect: "book", // 2:3
    rounded: true,
  },
);

const aspectClass = computed(() =>
  props.aspect === "square" ? "aspect-square" : "aspect-[2/3]",
);
</script>

<template>
  <div
    class="overflow-hidden bg-bg-secondary"
    :class="[aspectClass, rounded ? 'rounded' : '']"
  >
    <img
      v-if="src"
      :src="src"
      :alt="alt"
      :loading="eager ? 'eager' : 'lazy'"
      decoding="async"
      class="h-full w-full object-cover transition-transform group-hover:scale-105"
    >
    <!-- Fallback: subtle gradient with the first letter of the title -->
    <div
      v-else
      class="h-full w-full flex items-center justify-center bg-gradient-to-br from-primary/20 to-accent-burgundy/20 text-primary text-4xl font-serif"
    >
      {{ alt.charAt(0).toUpperCase() }}
    </div>
  </div>
</template>
