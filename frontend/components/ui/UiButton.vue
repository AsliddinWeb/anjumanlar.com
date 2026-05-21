<script setup lang="ts">
type Variant = "primary" | "ghost" | "danger" | "subtle";
type Size = "sm" | "md" | "lg";

const props = withDefaults(
  defineProps<{
    variant?: Variant;
    size?: Size;
    block?: boolean;
    disabled?: boolean;
    loading?: boolean;
    type?: "button" | "submit" | "reset";
    to?: string; // when set, renders as NuxtLink instead of button
  }>(),
  {
    variant: "primary",
    size: "md",
    type: "button",
  },
);

defineEmits<{ click: [event: MouseEvent] }>();

const variantClass: Record<Variant, string> = {
  primary:
    "bg-primary text-ink-inverse hover:bg-primary-hover disabled:bg-primary/50",
  ghost:
    "border border-border text-ink-secondary hover:border-primary hover:text-primary",
  danger: "bg-error text-ink-inverse hover:opacity-90",
  subtle: "text-ink-secondary hover:bg-bg-secondary hover:text-primary",
};

const sizeClass: Record<Size, string> = {
  sm: "px-2.5 py-1 text-xs",
  md: "px-4 py-2 text-sm",
  lg: "px-5 py-2.5 text-base",
};

const classes = computed(() =>
  [
    "inline-flex items-center justify-center gap-1.5 rounded font-medium",
    "transition-colors shadow-sm",
    "disabled:cursor-not-allowed disabled:opacity-60",
    variantClass[props.variant],
    sizeClass[props.size],
    props.block ? "w-full" : "",
  ].join(" "),
);
</script>

<template>
  <NuxtLink v-if="to" :to="to" :class="classes">
    <UiSpinner v-if="loading" class="h-4 w-4" />
    <slot />
  </NuxtLink>
  <button
    v-else
    :type="type"
    :disabled="disabled || loading"
    :class="classes"
    @click="$emit('click', $event)"
  >
    <UiSpinner v-if="loading" class="h-4 w-4" />
    <slot />
  </button>
</template>
