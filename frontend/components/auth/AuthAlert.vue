<script setup lang="ts">
import type { IconName } from "~/utils/icons";

withDefaults(
  defineProps<{
    tone?: "error" | "warning" | "success" | "info";
  }>(),
  { tone: "error" },
);

const toneClass = {
  error: "bg-error/10 text-error border-error/30",
  warning: "bg-warning/10 text-warning border-warning/30",
  success: "bg-success/10 text-success border-success/30",
  info: "bg-info/10 text-info border-info/30",
};

const toneIcon: Record<"error" | "warning" | "success" | "info", IconName> = {
  error: "warning-solid",
  warning: "warning-solid",
  success: "check-circle-solid",
  info: "sparkles",
};
</script>

<template>
  <div
    class="flex items-start gap-2 px-3 py-2.5 rounded border text-sm"
    :class="toneClass[tone]"
    role="alert"
  >
    <Icon :name="toneIcon[tone]" class="h-4 w-4 mt-0.5 shrink-0" />
    <div class="flex-1 min-w-0">
      <slot />
    </div>
  </div>
</template>
