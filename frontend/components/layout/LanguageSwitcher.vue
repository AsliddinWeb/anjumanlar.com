<script setup lang="ts">
const { locale, locales, setLocale } = useI18n();
const switchLocalePath = useSwitchLocalePath();

const available = computed(() =>
  (locales.value as { code: string; name?: string }[]).map((l) => ({
    code: l.code,
    name: l.name ?? l.code.toUpperCase(),
  })),
);

const open = ref(false);
const current = computed(() => available.value.find((l) => l.code === locale.value));
</script>

<template>
  <div class="relative">
    <button
      type="button"
      class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded border border-border hover:border-border-hover text-sm text-ink-secondary uppercase"
      :aria-expanded="open"
      :aria-label="$t('language.label')"
      @click="open = !open"
    >
      <span>{{ locale }}</span>
      <span aria-hidden="true">▾</span>
    </button>

    <ul
      v-if="open"
      class="absolute right-0 mt-1 min-w-32 rounded border border-border bg-bg-elevated shadow-md py-1 text-sm"
      role="menu"
      @click="open = false"
    >
      <li v-for="l in available" :key="l.code">
        <NuxtLink
          :to="switchLocalePath(l.code) || '/'"
          class="block px-3 py-1.5 text-ink-secondary hover:bg-bg-secondary hover:text-primary"
          :class="{ 'font-semibold text-primary': l.code === locale }"
          @click="setLocale(l.code)"
        >
          {{ l.name }}
        </NuxtLink>
      </li>
    </ul>
  </div>
</template>
