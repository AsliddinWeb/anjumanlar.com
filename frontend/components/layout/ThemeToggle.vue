<script setup lang="ts">
const colorMode = useColorMode();
const { t } = useI18n();

const order = ["light", "dark", "system"] as const;
type Pref = (typeof order)[number];

function cycle() {
  const i = order.indexOf(colorMode.preference as Pref);
  colorMode.preference = order[(i + 1) % order.length];
}

const label = computed(() => t(`theme.${colorMode.preference || "system"}`));
const icon = computed(() => {
  if (colorMode.preference === "dark") return "🌙";
  if (colorMode.preference === "light") return "☀";
  return "🖥";
});
</script>

<template>
  <button
    type="button"
    class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded border border-border hover:border-border-hover text-sm text-ink-secondary"
    :aria-label="t('theme.label')"
    :title="`${t('theme.label')}: ${label}`"
    @click="cycle"
  >
    <span aria-hidden="true">{{ icon }}</span>
    <span class="hidden sm:inline">{{ label }}</span>
  </button>
</template>
