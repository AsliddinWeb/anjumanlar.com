<script setup lang="ts">
const { t, locale, locales } = useI18n();
const switchLocalePath = useSwitchLocalePath();

interface LocaleEntry {
  code: string;
  name: string;
  flag: string;
}

const FLAGS: Record<string, string> = {
  uz: "🇺🇿",
  ru: "🇷🇺",
  en: "🇬🇧",
};

const available = computed<LocaleEntry[]>(() =>
  (locales.value as { code: string; name?: string }[]).map((l) => ({
    code: l.code,
    name: l.name ?? l.code.toUpperCase(),
    flag: FLAGS[l.code] ?? "🌐",
  })),
);

const current = computed(() =>
  available.value.find((l) => l.code === locale.value),
);

const open = ref(false);
const root = ref<HTMLElement | null>(null);

function onDocumentClick(event: MouseEvent) {
  if (!open.value || !root.value) return;
  if (!root.value.contains(event.target as Node)) open.value = false;
}

onMounted(() => {
  if (import.meta.client) document.addEventListener("mousedown", onDocumentClick);
});
onBeforeUnmount(() => {
  if (import.meta.client) document.removeEventListener("mousedown", onDocumentClick);
});
useEscape(() => { open.value = false; }, { enabled: open });
</script>

<template>
  <div ref="root" class="relative">
    <button
      type="button"
      class="inline-flex items-center gap-1.5 h-9 px-2 rounded-md border border-border text-ink-secondary hover:border-primary hover:text-primary transition-colors"
      :aria-expanded="open"
      :aria-label="t('language.label')"
      @click="open = !open"
    >
      <span class="text-base leading-none" aria-hidden="true">{{ current?.flag ?? "🌐" }}</span>
      <Icon
        name="chevron-down"
        class="h-3.5 w-3.5 transition-transform"
        :class="open ? 'rotate-180' : ''"
      />
    </button>

    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="opacity-0 -translate-y-1"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition duration-100 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <ul
        v-if="open"
        class="absolute right-0 mt-2 min-w-40 rounded-md border border-border bg-bg-elevated shadow-lg py-1 text-sm z-30"
        role="menu"
        @click="open = false"
      >
        <li v-for="l in available" :key="l.code">
          <NuxtLink
            :to="switchLocalePath(l.code) || '/'"
            class="flex items-center gap-2.5 px-3 py-2 transition-colors"
            :class="l.code === locale
              ? 'bg-primary/5 text-primary font-medium'
              : 'text-ink-secondary hover:bg-bg-secondary hover:text-ink'"
          >
            <span class="text-base leading-none" aria-hidden="true">{{ l.flag }}</span>
            <span class="flex-1">{{ l.name }}</span>
            <Icon
              v-if="l.code === locale"
              name="check"
              class="h-3.5 w-3.5"
            />
          </NuxtLink>
        </li>
      </ul>
    </Transition>
  </div>
</template>
