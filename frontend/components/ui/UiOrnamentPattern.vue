<script setup lang="ts">
/**
 * Tileable ornament background — drop into a `relative` parent with
 * `class="absolute inset-0 -z-10"` to use the active site motif as a
 * subtle watermark behind a section.
 *
 * The repeating tile is the registry's `pattern` body, rendered inside
 * an SVG <pattern> at the requested size.
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

const toneClass = computed(() => {
  if (props.tone === "gold") return "text-accent-gold";
  if (props.tone === "ink") return "text-ink";
  return "text-primary";
});

// Each instance needs a unique <pattern> id so multiple patterns on
// one page don't clobber each other.
const patternId = `om-${ornament.value.name}-${Math.random().toString(36).slice(2, 8)}`;
</script>

<template>
  <svg
    :class="['select-none pointer-events-none', toneClass]"
    width="100%"
    height="100%"
    aria-hidden="true"
    :style="{ opacity }"
  >
    <defs>
      <pattern
        :id="patternId"
        :width="tileSize"
        :height="tileSize"
        patternUnits="userSpaceOnUse"
      >
        <svg width="80" height="80" viewBox="0 0 80 80" :x="(tileSize - 80) / 2" :y="(tileSize - 80) / 2">
          <g fill="none" stroke="currentColor" stroke-width="1.1">
            <g v-html="ornament.pattern" />
          </g>
        </svg>
      </pattern>
    </defs>
    <rect width="100%" height="100%" :fill="`url(#${patternId})`" />
  </svg>
</template>
