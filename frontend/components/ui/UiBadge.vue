<script setup lang="ts">
type Tone = "neutral" | "primary" | "success" | "warning" | "info" | "gold";

const props = withDefaults(
  defineProps<{ tone?: Tone; size?: "sm" | "md" }>(),
  { tone: "neutral", size: "sm" },
);

const toneClass: Record<Tone, string> = {
  neutral: "bg-bg-secondary text-ink-secondary border-border",
  primary: "bg-primary/10 text-primary border-primary/30",
  success: "bg-success/10 text-success border-success/30",
  warning: "bg-warning/10 text-warning border-warning/30",
  info: "bg-info/10 text-info border-info/30",
  gold: "bg-accent-gold/15 text-accent-gold border-accent-gold/40",
};

const sizeClass = { sm: "text-xs px-1.5 py-0.5", md: "text-sm px-2 py-1" }[props.size];
</script>

<template>
  <span
    class="inline-flex items-center gap-1 rounded border font-medium"
    :class="[toneClass[tone], sizeClass]"
  >
    <slot />
  </span>
</template>
