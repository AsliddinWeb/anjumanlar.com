<script setup lang="ts">
/**
 * Project-wide icon wrapper. The registry of available icons lives in
 * ~/utils/icons.ts so pickers and other non-component code can import it
 * without going through the Vue SFC compiler — `<script setup>` doesn't
 * allow named exports.
 *
 * Usage:
 *  <Icon name="heart" class="h-5 w-5" />
 *  <Icon name="heart-solid" class="h-5 w-5 text-error" />
 */
import { ICONS, type IconName } from "~/utils/icons";

const props = defineProps<{
  /** Accepts any string at runtime to tolerate user-supplied category icons. */
  name: IconName | string | null | undefined;
  /** Tailwind size class — h-5 w-5 default. Pass empty string to opt out. */
  class?: string;
  /** Fallback icon when ``name`` doesn't match a known entry. */
  fallback?: IconName;
}>();

const component = computed(() => {
  const key = props.name as IconName;
  if (key && key in ICONS) return ICONS[key];
  return props.fallback ? ICONS[props.fallback] : null;
});
const sizeClass = computed(() => (props.class === undefined ? "h-5 w-5" : props.class));
</script>

<template>
  <component :is="component" v-if="component" :class="sizeClass" aria-hidden="true" />
</template>
