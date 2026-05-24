<script setup lang="ts">
import { ICON_NAMES, type IconName } from "~/utils/icons";

const props = defineProps<{
  modelValue: string;
  label?: string;
  hint?: string;
  /** Allow clearing the selection. */
  clearable?: boolean;
}>();

const emit = defineEmits<{ "update:modelValue": [value: string] }>();

const { t } = useI18n();
const open = ref(false);
const search = ref("");
const root = ref<HTMLElement | null>(null);

const filtered = computed<IconName[]>(() => {
  const q = search.value.trim().toLowerCase();
  if (!q) return ICON_NAMES;
  return ICON_NAMES.filter((n) => n.includes(q));
});

const selected = computed<IconName | null>(() => {
  const v = props.modelValue?.trim();
  if (!v) return null;
  return (ICON_NAMES as readonly string[]).includes(v) ? (v as IconName) : null;
});

function pick(name: IconName) {
  emit("update:modelValue", name);
  open.value = false;
  search.value = "";
}

function clear() {
  emit("update:modelValue", "");
  open.value = false;
}

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
  <div ref="root" class="block">
    <span v-if="label" class="block text-sm text-ink-secondary mb-1">
      {{ label }}
    </span>

    <button
      type="button"
      class="w-full flex items-center gap-2 px-3 py-2 rounded border border-border bg-bg-card text-sm text-ink hover:border-primary focus:outline-none focus:border-primary transition-colors"
      :aria-expanded="open"
      @click="open = !open"
    >
      <span
        v-if="selected"
        class="h-8 w-8 rounded-md bg-primary/10 text-primary flex items-center justify-center shrink-0"
      >
        <Icon :name="selected" class="h-4 w-4" />
      </span>
      <span
        v-else
        class="h-8 w-8 rounded-md border border-dashed border-border text-ink-tertiary flex items-center justify-center shrink-0"
      >
        <Icon name="search" class="h-4 w-4" />
      </span>
      <span class="flex-1 text-left truncate" :class="selected ? '' : 'text-ink-tertiary'">
        {{ selected ?? t("admin.icon_picker.placeholder") }}
      </span>
      <Icon name="chevron-down" class="h-4 w-4 text-ink-tertiary transition-transform" :class="open ? 'rotate-180' : ''" />
    </button>

    <p v-if="hint && !open" class="text-xs text-ink-tertiary mt-1">{{ hint }}</p>

    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="opacity-0 -translate-y-1"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition duration-100 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="open"
        class="mt-2 rounded-md border border-border bg-bg-elevated shadow-lg overflow-hidden"
      >
        <div class="p-2 border-b border-border flex items-center gap-2">
          <div class="relative flex-1">
            <Icon
              name="search"
              class="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-ink-tertiary pointer-events-none"
            />
            <input
              v-model="search"
              type="search"
              :placeholder="t('admin.icon_picker.search')"
              class="w-full pl-8 pr-3 py-1.5 rounded border border-border bg-bg text-sm text-ink placeholder:text-ink-tertiary focus:outline-none focus:border-primary"
              autofocus
            >
          </div>
          <button
            v-if="clearable && selected"
            type="button"
            class="inline-flex items-center gap-1 px-2 py-1.5 rounded text-xs text-ink-tertiary hover:text-error transition-colors"
            @click="clear"
          >
            <Icon name="close" class="h-3.5 w-3.5" />
            {{ t("admin.icon_picker.clear") }}
          </button>
        </div>

        <div class="max-h-[260px] overflow-y-auto p-2">
          <div
            v-if="filtered.length === 0"
            class="text-center text-xs text-ink-tertiary py-8"
          >
            {{ t("admin.icon_picker.no_match") }}
          </div>
          <div
            v-else
            class="grid grid-cols-6 sm:grid-cols-8 gap-1"
          >
            <button
              v-for="name in filtered"
              :key="name"
              type="button"
              :title="name"
              class="aspect-square inline-flex flex-col items-center justify-center rounded text-ink-secondary hover:bg-bg-secondary hover:text-primary transition-colors"
              :class="selected === name ? 'bg-primary/10 text-primary ring-1 ring-primary' : ''"
              @click="pick(name)"
            >
              <Icon :name="name" class="h-5 w-5" />
            </button>
          </div>
        </div>

        <footer class="px-3 py-2 border-t border-border text-[11px] text-ink-tertiary flex items-center justify-between">
          <span>{{ t("admin.icon_picker.count", { n: filtered.length }) }}</span>
          <span v-if="selected" class="font-mono">{{ selected }}</span>
        </footer>
      </div>
    </Transition>
  </div>
</template>
