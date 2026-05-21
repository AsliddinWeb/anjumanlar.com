<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    padded?: boolean;
    hoverable?: boolean;
    to?: string;
  }>(),
  { padded: true },
);

const classes = computed(() =>
  [
    "rounded-md border border-border bg-bg-card shadow-sm",
    props.padded ? "p-4" : "",
    props.hoverable
      ? "transition-shadow hover:shadow-book hover:border-border-hover"
      : "",
  ].join(" "),
);
</script>

<template>
  <NuxtLink v-if="to" :to="to" :class="classes">
    <slot />
  </NuxtLink>
  <div v-else :class="classes">
    <slot />
  </div>
</template>
