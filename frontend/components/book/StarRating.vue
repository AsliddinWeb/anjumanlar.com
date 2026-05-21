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

const sizePx = { sm: 16, md: 20, lg: 28 }[props.size];

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
      class="leading-none transition-colors"
      :class="[
        interactive ? 'cursor-pointer' : 'cursor-default',
        n <= display ? 'text-accent-gold' : 'text-ink-tertiary',
      ]"
      :style="{ fontSize: sizePx + 'px' }"
      :disabled="!interactive"
      @click="setRating(n)"
      @mouseenter="interactive && (hovered = n)"
      @mouseleave="interactive && (hovered = 0)"
    >
      ★
    </button>
  </div>
</template>
