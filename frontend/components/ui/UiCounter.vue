<script setup lang="ts">
/**
 * Number that animates from 0 to `target` once it scrolls into view.
 * Uses IntersectionObserver so the count starts only when the user
 * actually sees the digit — keeps the moment-of-arrival feel without
 * burning frames for offscreen widgets.
 *
 * `suffix` lets the call site append "+" or "K" without an extra span.
 */
const props = withDefaults(
  defineProps<{
    target: number;
    suffix?: string;
    /** Animation length in ms — defaults to 1400. */
    duration?: number;
  }>(),
  { suffix: "+", duration: 1400 },
);

const value = ref(0);
const root = ref<HTMLElement | null>(null);
let started = false;

function easeOutExpo(t: number): number {
  return t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
}

function animate() {
  if (started) return;
  started = true;
  const start = performance.now();
  const target = props.target;
  const duration = props.duration;
  function step(now: number) {
    const elapsed = now - start;
    const t = Math.min(1, elapsed / duration);
    value.value = Math.round(target * easeOutExpo(t));
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

onMounted(() => {
  if (!root.value || !import.meta.client) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    value.value = props.target;
    return;
  }
  const observer = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        if (e.isIntersecting) {
          animate();
          observer.disconnect();
          break;
        }
      }
    },
    { threshold: 0.4 },
  );
  observer.observe(root.value);
  onBeforeUnmount(() => observer.disconnect());
});
</script>

<template>
  <span ref="root" class="counter-num">{{ value }}{{ suffix }}</span>
</template>
