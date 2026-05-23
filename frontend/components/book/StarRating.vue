<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    /** Current rating, 0-5, fractional values OK. */
    value: number;
    /** When ``true``, clicking a star emits ``update:value``. */
    interactive?: boolean;
    size?: "sm" | "md" | "lg";
  }>(),
  { interactive: false, size: "md" },
);

const emit = defineEmits<{ "update:value": [n: number] }>();

const sizeClass = computed(() => {
  return { sm: "h-4 w-4", md: "h-5 w-5", lg: "h-7 w-7" }[props.size];
});

const hovered = ref(0);
const display = computed(() => (hovered.value || props.value));

function setRating(n: number) {
  if (!props.interactive) return;
  emit("update:value", n);
}
</script>

<template>
  <div
    class="inline-flex items-center gap-0.5"
    role="img"
    :aria-label="`Rating ${value} / 5`"
  >
    <button
      v-for="n in 5"
      :key="n"
      type="button"
      class="inline-flex items-center transition-colors"
      :class="[
        interactive ? 'cursor-pointer' : 'cursor-default',
        n <= display ? 'text-accent-gold' : 'text-ink-tertiary',
      ]"
      :disabled="!interactive"
      @click="setRating(n)"
      @mouseenter="interactive && (hovered = n)"
      @mouseleave="interactive && (hovered = 0)"
    >
      <Icon :name="n <= display ? 'star-solid' : 'star'" :class="sizeClass" />
    </button>
  </div>
</template>
