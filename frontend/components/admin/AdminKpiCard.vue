<script setup lang="ts">
import type { IconName } from "~/utils/icons";

defineProps<{
  label: string;
  value: string | number;
  /** Optional secondary line under the value. */
  hint?: string;
  icon?: IconName;
  /** Color theme for icon/value. */
  tone?: "default" | "success" | "warning" | "info";
  /** When provided, the card becomes a link. */
  to?: string;
}>();

const toneClass = {
  default: { icon: "bg-bg-secondary text-ink-secondary", value: "text-ink" },
  success: { icon: "bg-success/10 text-success", value: "text-success" },
  warning: { icon: "bg-warning/10 text-warning", value: "text-warning" },
  info: { icon: "bg-info/10 text-info", value: "text-info" },
};
</script>

<template>
  <component
    :is="to ? 'NuxtLink' : 'div'"
    :to="to"
    class="rounded-md border border-border bg-bg-card p-4 flex items-start gap-3 transition-colors"
    :class="to ? 'hover:border-primary hover:bg-bg-secondary/40 cursor-pointer' : ''"
  >
    <div
      v-if="icon"
      class="h-10 w-10 rounded flex items-center justify-center shrink-0"
      :class="toneClass[tone ?? 'default'].icon"
    >
      <Icon :name="icon" class="h-5 w-5" />
    </div>
    <div class="min-w-0 flex-1">
      <div class="text-xs uppercase tracking-wider text-ink-tertiary">{{ label }}</div>
      <div class="font-serif text-2xl mt-1" :class="toneClass[tone ?? 'default'].value">
        {{ value }}
      </div>
      <div v-if="hint" class="text-xs text-ink-tertiary mt-0.5">{{ hint }}</div>
    </div>
  </component>
</template>
