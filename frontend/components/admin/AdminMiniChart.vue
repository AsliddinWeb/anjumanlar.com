<script setup lang="ts">
/**
 * Inline SVG sparkline / line chart — zero deps, SSR-safe.
 *
 * Pass an array of points; the chart auto-scales to the container. Used
 * across the finance dashboard for daily revenue/sales trends. For the
 * tiny size on author dashboards, set ``compact`` to drop the axis
 * labels.
 */

const props = withDefaults(
  defineProps<{
    points: { date: string; value: number }[];
    height?: number;
    color?: string;
    fill?: string;
    /** Drop axis labels + grid; use for sparkline contexts. */
    compact?: boolean;
    /** Optional formatter for the y-axis labels + hover tooltip. */
    format?: (n: number) => string;
  }>(),
  { height: 180, color: "var(--color-primary)", fill: "var(--color-primary)", compact: false },
);

const viewBoxWidth = 800;
const viewBoxHeight = computed(() => props.height);

const margin = computed(() => (props.compact ? { top: 4, right: 4, bottom: 4, left: 4 } : { top: 12, right: 12, bottom: 24, left: 56 }));

const innerWidth = computed(() => viewBoxWidth - margin.value.left - margin.value.right);
const innerHeight = computed(() => viewBoxHeight.value - margin.value.top - margin.value.bottom);

const maxValue = computed(() => {
  const max = Math.max(0, ...props.points.map((p) => p.value));
  // Add 10% headroom so the line never touches the top.
  return max === 0 ? 1 : max * 1.1;
});

const linePoints = computed(() => {
  const n = props.points.length;
  if (n === 0) return "";
  const step = n > 1 ? innerWidth.value / (n - 1) : 0;
  return props.points
    .map((p, i) => {
      const x = margin.value.left + i * step;
      const y = margin.value.top + innerHeight.value - (p.value / maxValue.value) * innerHeight.value;
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
});

const areaPath = computed(() => {
  if (!linePoints.value) return "";
  const last = props.points.length - 1;
  const lastX = margin.value.left + last * (props.points.length > 1 ? innerWidth.value / last : 0);
  const baseY = margin.value.top + innerHeight.value;
  return `${linePoints.value} L${lastX.toFixed(1)},${baseY.toFixed(1)} L${margin.value.left.toFixed(1)},${baseY.toFixed(1)} Z`;
});

const yTicks = computed(() => {
  if (props.compact) return [];
  const steps = 4;
  const ticks = [];
  for (let i = 0; i <= steps; i++) {
    const value = (maxValue.value / steps) * i;
    const y = margin.value.top + innerHeight.value - (value / maxValue.value) * innerHeight.value;
    ticks.push({ value, y });
  }
  return ticks;
});

const xLabels = computed(() => {
  if (props.compact) return [];
  const n = props.points.length;
  if (n === 0) return [];
  const want = Math.min(5, n);
  const stride = Math.max(1, Math.floor(n / want));
  const labels: { x: number; label: string }[] = [];
  for (let i = 0; i < n; i += stride) {
    const x = margin.value.left + i * (n > 1 ? innerWidth.value / (n - 1) : 0);
    const d = props.points[i].date;
    // Render "DD/MM" — minimal, locale-agnostic, fits the tick spacing.
    const parts = d.split("-");
    labels.push({ x, label: parts.length === 3 ? `${parts[2]}/${parts[1]}` : d });
  }
  return labels;
});

function fmtY(n: number) {
  return props.format ? props.format(n) : new Intl.NumberFormat("uz", { maximumFractionDigits: 0 }).format(n);
}
</script>

<template>
  <div class="w-full">
    <svg
      :viewBox="`0 0 ${viewBoxWidth} ${viewBoxHeight}`"
      preserveAspectRatio="none"
      class="w-full"
      :style="{ height: `${viewBoxHeight}px` }"
    >
      <!-- Y grid + ticks -->
      <g v-if="!compact">
        <g v-for="(t, i) in yTicks" :key="i">
          <line
            :x1="margin.left"
            :x2="viewBoxWidth - margin.right"
            :y1="t.y"
            :y2="t.y"
            stroke="currentColor"
            stroke-width="1"
            stroke-dasharray="2 4"
            class="text-border"
          />
          <text
            :x="margin.left - 6"
            :y="t.y"
            font-size="10"
            text-anchor="end"
            dominant-baseline="middle"
            fill="currentColor"
            class="text-ink-tertiary"
          >{{ fmtY(t.value) }}</text>
        </g>
      </g>

      <!-- Filled area -->
      <path :d="areaPath" :fill="fill" fill-opacity="0.1" />
      <!-- Line -->
      <path :d="linePoints" fill="none" :stroke="color" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />

      <!-- Dots (skip for very dense series) -->
      <g v-if="points.length <= 31">
        <circle
          v-for="(p, i) in points"
          :key="i"
          :cx="margin.left + i * (points.length > 1 ? innerWidth / (points.length - 1) : 0)"
          :cy="margin.top + innerHeight - (p.value / maxValue) * innerHeight"
          r="2"
          :fill="color"
        />
      </g>

      <!-- X labels -->
      <g v-if="!compact">
        <text
          v-for="(l, i) in xLabels"
          :key="`xl-${i}`"
          :x="l.x"
          :y="viewBoxHeight - 4"
          font-size="10"
          text-anchor="middle"
          fill="currentColor"
          class="text-ink-tertiary"
        >{{ l.label }}</text>
      </g>
    </svg>
  </div>
</template>
