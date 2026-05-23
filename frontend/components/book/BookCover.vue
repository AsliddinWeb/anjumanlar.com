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
    <div
      v-else
      class="relative h-full w-full flex flex-col items-center justify-center gap-2 bg-gradient-to-br from-primary/15 to-accent-burgundy/15 text-primary"
    >
      <Icon name="book" class="h-10 w-10 opacity-70" />
      <span class="text-3xl font-serif">{{ alt.charAt(0).toUpperCase() }}</span>
    </div>
  </div>
</template>
