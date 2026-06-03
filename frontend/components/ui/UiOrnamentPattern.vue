<script setup lang="ts">
/**
 * Tileable ornament background — drop into a `relative` parent with
 * `class="absolute inset-0 -z-10"` to use the active site motif as a
 * subtle watermark behind a section.
 *
 * Uses Vue's `useId()` for an SSR-stable pattern id so the
 * server-rendered <rect fill="url(#…)"> and the hydrated DOM agree
 * (random ids generated at setup were causing the pattern to vanish
 * after hydration).
 *
 * The repeating tile is the registry's `pattern` body, rendered inside
 * a `<pattern>` element whose viewBox 0..80 maps to the requested
 * pixel tile size.
 */
import { getOrnament, type OrnamentDefinition } from "~/utils/ornaments";

const props = withDefaults(
  defineProps<{
    /** Override the site-wide ornament. */
    variant?: string;
    /** Tile size in CSS pixels. Bigger = sparser motifs. */
    tileSize?: number;
    /** Opacity 0..1 — keep low so the pattern stays a watermark. */
    opacity?: number;
    /** primary / gold / ink colour tone. */
    tone?: "primary" | "gold" | "ink";
  }>(),
  { tileSize: 120, opacity: 0.06, tone: "primary" },
);

const theme = useTheme();

const ornament = computed<OrnamentDefinition>(() =>
  getOrnament(props.variant ?? theme.currentOrnament.value),
);

// Vue 3.5+ — SSR-stable unique id. Falls back to a deterministic
// combo if useId is unavailable.
const uid = typeof useId === "function" ? useId() : "om-pattern-static";
const patternId = computed(() => `om-${ornament.value.name}-${uid}`);

const toneClass = computed(() => {
  if (props.tone === "gold") return "text-accent-gold";
  if (props.tone === "ink") return "text-ink";
  return "text-primary";
});
</script>

<template>
  <svg
    :class="['select-none pointer-events-none w-full h-full', toneClass]"
    aria-hidden="true"
    :style="{ opacity }"
    xmlns="http://www.w3.org/2000/svg"
  >
    <defs>
      <pattern
        :id="patternId"
        :width="tileSize"
        :height="tileSize"
        patternUnits="userSpaceOnUse"
        viewBox="0 0 80 80"
      >
        <g fill="none" stroke="currentColor" stroke-width="1.1" v-html="ornament.pattern" />
      </pattern>
    </defs>
    <rect width="100%" height="100%" :fill="`url(#${patternId})`" />
  </svg>
</template>
