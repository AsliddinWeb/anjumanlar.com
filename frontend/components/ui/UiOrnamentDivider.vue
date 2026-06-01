<script setup lang="ts">
/**
 * Decorative horizontal divider with a central Turkic/Uzbek-inspired
 * motif (8-point star + diamond pattern). Used to separate marketing
 * sections on the homepage without resorting to a flat <hr>.
 *
 * Renders as inline-flex so the surrounding section can center it
 * with `class="flex justify-center"`.
 */
withDefaults(
  defineProps<{
    /** Tone — default uses --color-primary at low opacity. */
    tone?: "primary" | "gold";
  }>(),
  { tone: "primary" },
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
      width="42" height="42" viewBox="0 0 42 42"
      fill="none" stroke="currentColor" stroke-width="1.2"
      class="opacity-70"
    >
      <!-- 8-point star (rotated square + axis-aligned square) -->
      <rect x="11" y="11" width="20" height="20" />
      <rect x="11" y="11" width="20" height="20" transform="rotate(45 21 21)" />
      <!-- inner diamond -->
      <path d="M21 8 L34 21 L21 34 L8 21 Z" />
      <!-- center dot -->
      <circle cx="21" cy="21" r="2" fill="currentColor" stroke="none" />
    </svg>
    <span
      class="block h-px w-12 sm:w-24"
      style="background: linear-gradient(to right, currentColor, currentColor 30%, transparent);"
    />
  </div>
</template>
