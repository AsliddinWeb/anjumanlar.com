<script setup lang="ts">
import type { IconName } from "~/utils/icons";

const colorMode = useColorMode();
const { t } = useI18n();

const order = ["light", "dark", "system"] as const;
type Pref = (typeof order)[number];

function cycle() {
  const i = order.indexOf(colorMode.preference as Pref);
  colorMode.preference = order[(i + 1) % order.length];
}

const label = computed(() => t(`theme.${colorMode.preference || "system"}`));
const icon = computed<IconName>(() => {
  if (colorMode.preference === "dark") return "moon";
  if (colorMode.preference === "light") return "sun";
  return "desktop";
});
</script>

<template>
  <button
    type="button"
    class="inline-flex items-center justify-center h-9 w-9 rounded-md border border-border text-ink-secondary hover:border-primary hover:text-primary transition-colors"
    :aria-label="t('theme.label')"
    :title="`${t('theme.label')}: ${label}`"
    @click="cycle"
  >
    <Icon :name="icon" class="h-4 w-4" />
  </button>
</template>
