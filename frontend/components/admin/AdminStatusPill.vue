<script setup lang="ts">
import type { IconName } from "~/components/ui/Icon.vue";

type Tone = "success" | "warning" | "error" | "info" | "neutral";

const props = withDefaults(
  defineProps<{
    tone?: Tone;
    icon?: IconName;
    label: string;
    /** When true, the dot pulses (e.g. for "processing" state). */
    pulse?: boolean;
  }>(),
  { tone: "neutral" },
);

const toneClass: Record<Tone, string> = {
  success: "bg-success/10 text-success border-success/20",
  warning: "bg-warning/10 text-warning border-warning/20",
  error: "bg-error/10 text-error border-error/20",
  info: "bg-info/10 text-info border-info/20",
  neutral: "bg-bg-secondary text-ink-secondary border-border",
};

const dotClass: Record<Tone, string> = {
  success: "bg-success",
  warning: "bg-warning",
  error: "bg-error",
  info: "bg-info",
  neutral: "bg-ink-tertiary",
};
</script>

<template>
  <span
    class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-xs font-medium"
    :class="toneClass[tone]"
  >
    <Icon v-if="icon" :name="icon" class="h-3 w-3" />
    <span v-else class="relative inline-flex h-1.5 w-1.5 rounded-full" :class="dotClass[tone]">
      <span
        v-if="pulse"
        class="absolute inset-0 rounded-full opacity-75 animate-ping"
        :class="dotClass[tone]"
      />
    </span>
    {{ label }}
  </span>
</template>
