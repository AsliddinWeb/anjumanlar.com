<script setup lang="ts">
import type { BookPublic } from "~/types/api";

const props = withDefaults(
  defineProps<{
    book: BookPublic;
    /** "icon" — compact pill on a card. "button" — full button on book detail. */
    variant?: "icon" | "button";
    size?: "sm" | "md" | "lg";
  }>(),
  { variant: "icon", size: "md" },
);

const { t } = useI18n();
const cart = useCartStore();

const inCart = computed(() => cart.has(props.book.id));

function onClick(event: MouseEvent) {
  event.preventDefault();
  event.stopPropagation();
  cart.toggle(props.book);
}

const label = computed(() => (inCart.value ? t("cart.added") : t("cart.add")));

const sizeClass = computed(() => {
  if (props.variant === "icon") {
    return { sm: "h-7 w-7", md: "h-9 w-9", lg: "h-10 w-10" }[props.size];
  }
  return { sm: "px-2.5 py-1 text-xs", md: "px-4 py-2 text-sm", lg: "px-5 py-2.5 text-base" }[props.size];
});

const iconSize = computed(() => {
  return { sm: "h-4 w-4", md: "h-5 w-5", lg: "h-5 w-5" }[props.size];
});
</script>

<template>
  <button
    v-if="variant === 'icon'"
    type="button"
    :aria-label="label"
    :aria-pressed="inCart"
    class="inline-flex items-center justify-center rounded-full border bg-bg-card/90 backdrop-blur shadow-sm transition-colors"
    :class="[
      sizeClass,
      inCart
        ? 'border-primary text-primary hover:bg-primary/10'
        : 'border-border text-ink-tertiary hover:border-primary hover:text-primary',
    ]"
    @click="onClick"
  >
    <Icon :name="inCart ? 'check' : 'plus'" :class="iconSize" />
  </button>

  <button
    v-else
    type="button"
    :aria-pressed="inCart"
    class="inline-flex items-center justify-center gap-1.5 rounded font-medium transition-colors border"
    :class="[
      sizeClass,
      inCart
        ? 'border-primary text-primary bg-primary/5 hover:bg-primary/10'
        : 'border-primary bg-primary text-ink-inverse hover:bg-primary-hover',
    ]"
    @click="onClick"
  >
    <Icon :name="inCart ? 'check' : 'plus'" :class="iconSize" />
    <span>{{ label }}</span>
  </button>
</template>
