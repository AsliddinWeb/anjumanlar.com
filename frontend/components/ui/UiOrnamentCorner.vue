<script setup lang="ts">
/**
 * Decorative corner flourish — small Turkic/suzani-inspired SVG that
 * sits at a section's corner as background detail. Positioned
 * absolutely by the parent (the component itself doesn't pick a spot).
 *
 * Pair with `class="absolute top-0 left-0 opacity-25"` etc.
 */
withDefaults(
  defineProps<{
    /** flip: rotate 180deg so the same shape can decorate the opposite corner. */
    flip?: boolean;
    /** Tone (defaults to gold accent). */
    tone?: "gold" | "primary";
  }>(),
  { flip: false, tone: "gold" },
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
    <!-- arabesque-style curving lines -->
    <path d="M10 10 Q60 10 60 60 Q10 60 10 10 Z" opacity="0.55" />
    <path d="M10 10 Q40 30 60 60" opacity="0.45" />
    <path d="M10 10 Q30 40 60 60" opacity="0.45" />
    <!-- accent dots along the diagonal -->
    <circle cx="22" cy="22" r="2" fill="currentColor" stroke="none" opacity="0.7" />
    <circle cx="38" cy="38" r="1.6" fill="currentColor" stroke="none" opacity="0.55" />
    <circle cx="54" cy="54" r="1.2" fill="currentColor" stroke="none" opacity="0.45" />
    <!-- 8-point mini star at top-left -->
    <g transform="translate(85 25)" opacity="0.6">
      <rect x="-7" y="-7" width="14" height="14" />
      <rect x="-7" y="-7" width="14" height="14" transform="rotate(45)" />
    </g>
  </svg>
</template>
