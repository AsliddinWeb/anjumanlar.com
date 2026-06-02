<script setup lang="ts">
/**
 * Decorative corner — the SVG motif tracks the active site ornament so
 * divider + corner stay visually paired. Override with the `variant`
 * prop if a page wants something off-theme.
 */
import { getOrnament, type OrnamentDefinition } from "~/utils/ornaments";

const props = withDefaults(
  defineProps<{
    variant?: string;
    /** Rotate 180° so the same motif fits an opposite corner. */
    flip?: boolean;
    tone?: "gold" | "primary";
  }>(),
  { flip: false, tone: "gold" },
);

const theme = useTheme();

const ornament = computed<OrnamentDefinition>(() =>
  getOrnament(props.variant ?? theme.currentOrnament.value),
);
</script>

<template>
  <svg
    width="120"
    height="120"
    viewBox="0 0 120 120"
    fill="none"
    stroke="currentColor"
    stroke-width="1.1"
    aria-hidden="true"
    :class="[
      'select-none pointer-events-none',
      tone === 'primary' ? 'text-primary' : 'text-accent-gold',
      flip ? 'rotate-180' : '',
    ]"
  >
    <g v-html="ornament.corner" />
  </svg>
</template>
