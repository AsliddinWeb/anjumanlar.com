<script setup lang="ts">
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

const icon = {
  error: "⚠",
  warning: "⚠",
  success: "✓",
  info: "ℹ",
};
</script>

<template>
  <div
    class="flex items-start gap-2 px-3 py-2.5 rounded border text-sm"
    :class="toneClass[tone]"
    role="alert"
  >
    <span class="text-base leading-none mt-0.5" aria-hidden="true">{{ icon[tone] }}</span>
    <div class="flex-1 min-w-0">
      <slot />
    </div>
  </div>
</template>
