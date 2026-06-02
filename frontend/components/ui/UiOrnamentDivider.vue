<script setup lang="ts">
/**
 * Decorative horizontal divider — the active SVG motif is picked from
 * the ornament registry, either via the `variant` prop or, when
 * omitted, the site-wide setting controlled by the admin theme picker.
 */
import { getOrnament, type OrnamentDefinition } from "~/utils/ornaments";

const props = withDefaults(
  defineProps<{
    /** Override the site-wide ornament. Usually left unset. */
    variant?: string;
    /** Colour tone for the motif. */
    tone?: "primary" | "gold";
  }>(),
  { tone: "primary" },
);

const theme = useTheme();

const ornament = computed<OrnamentDefinition>(() =>
  getOrnament(props.variant ?? theme.currentOrnament.value),
);
</script>

<template>
  <div
    class="inline-flex items-center gap-3 select-none pointer-events-none"
    :class="tone === 'gold' ? 'text-accent-gold' : 'text-primary'"
    aria-hidden="true"
  >
    <span
      class="block h-px w-12 sm:w-24"
      style="background: linear-gradient(to right, transparent, currentColor 70%, currentColor);"
    />
    <svg
      width="42"
      height="42"
      viewBox="0 0 42 42"
      fill="none"
      stroke="currentColor"
      stroke-width="1.2"
      class="opacity-70"
    >
      <g v-html="ornament.divider" />
    </svg>
    <span
      class="block h-px w-12 sm:w-24"
      style="background: linear-gradient(to right, currentColor, currentColor 30%, transparent);"
    />
  </div>
</template>
