<script setup lang="ts">
/**
 * Single-select combobox with a filter-as-you-type text box — the
 * plain `UiSelect` native <select> is unusable once the option list
 * grows past a couple dozen entries (authors, languages, ...).
 */
export interface UiSearchSelectOption {
  value: string;
  label: string;
}

const props = withDefaults(
  defineProps<{
    modelValue: string | null | undefined;
    options: UiSearchSelectOption[];
    label?: string;
    hint?: string;
    placeholder?: string;
    searchPlaceholder?: string;
    /** Text shown when no option matches the typed query. */
    noResultsLabel?: string;
    /**
     * When true, `options` is assumed to already be filtered by the
     * caller (e.g. a debounced `/authors?search=` call) — the
     * component skips its own local filtering and just emits `search`
     * on every keystroke instead.
     */
    remote?: boolean;
    loading?: boolean;
  }>(),
  { placeholder: "", searchPlaceholder: "" },
);

const emit = defineEmits<{
  "update:modelValue": [value: string];
  "search": [query: string];
}>();

const root = ref<HTMLElement | null>(null);
const inputEl = ref<HTMLInputElement | null>(null);
const open = ref(false);
const query = ref("");
const highlighted = ref(0);

const selectedOption = computed(() =>
  props.options.find((o) => o.value === props.modelValue) ?? null,
);

const filtered = computed(() => {
  if (props.remote) return props.options;
  const q = query.value.trim().toLowerCase();
  if (!q) return props.options;
  return props.options.filter((o) => o.label.toLowerCase().includes(q));
});

function openList() {
  open.value = true;
  query.value = "";
  highlighted.value = Math.max(0, props.options.findIndex((o) => o.value === props.modelValue));
  nextTick(() => inputEl.value?.select());
}

function closeList() {
  open.value = false;
  query.value = "";
}

function choose(option: UiSearchSelectOption) {
  emit("update:modelValue", option.value);
  closeList();
}

function onDocumentClick(event: MouseEvent) {
  if (!open.value || !root.value) return;
  if (!root.value.contains(event.target as Node)) closeList();
}

onMounted(() => {
  if (import.meta.client) document.addEventListener("mousedown", onDocumentClick);
});
onBeforeUnmount(() => {
  if (import.meta.client) document.removeEventListener("mousedown", onDocumentClick);
});

function onKeydown(e: KeyboardEvent) {
  if (!open.value) {
    if (e.key === "ArrowDown" || e.key === "Enter") {
      e.preventDefault();
      openList();
    }
    return;
  }
  if (e.key === "ArrowDown") {
    e.preventDefault();
    highlighted.value = Math.min(highlighted.value + 1, filtered.value.length - 1);
  }
  else if (e.key === "ArrowUp") {
    e.preventDefault();
    highlighted.value = Math.max(highlighted.value - 1, 0);
  }
  else if (e.key === "Enter") {
    e.preventDefault();
    const opt = filtered.value[highlighted.value];
    if (opt) choose(opt);
  }
  else if (e.key === "Escape") {
    e.preventDefault();
    closeList();
  }
}

function onInput(e: Event) {
  query.value = (e.target as HTMLInputElement).value;
  if (props.remote) emit("search", query.value);
}

watch(query, () => { highlighted.value = 0; });
</script>

<template>
  <div ref="root" class="relative">
    <label class="block">
      <span v-if="label" class="block text-sm font-medium text-ink-secondary mb-1.5">
        {{ label }}
      </span>
      <div class="relative">
        <input
          ref="inputEl"
          :value="open ? query : (selectedOption?.label ?? '')"
          type="text"
          :placeholder="open ? (searchPlaceholder || placeholder) : placeholder"
          class="w-full px-3.5 py-2.5 pr-9 rounded-md border border-border bg-bg-card text-ink placeholder:text-ink-tertiary focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors cursor-pointer"
          autocomplete="off"
          @focus="openList"
          @click="openList"
          @input="onInput"
          @keydown="onKeydown"
        >
        <Icon
          name="chevron-down"
          class="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-tertiary pointer-events-none transition-transform"
          :class="open ? 'rotate-180' : ''"
        />
      </div>
    </label>

    <span v-if="hint" class="block text-xs text-ink-tertiary mt-1.5">{{ hint }}</span>

    <Transition
      enter-active-class="transition duration-100 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
    >
      <ul
        v-if="open"
        class="absolute left-0 right-0 mt-1 max-h-64 overflow-y-auto rounded-md border border-border bg-bg-elevated shadow-lg py-1 text-sm z-30"
        role="listbox"
      >
        <li v-if="loading" class="px-3 py-2 text-ink-tertiary text-sm">
          {{ $t("common.loading") }}
        </li>
        <li v-else-if="filtered.length === 0" class="px-3 py-2 text-ink-tertiary text-sm">
          {{ noResultsLabel }}
        </li>
        <li
          v-for="(opt, i) in filtered"
          :key="opt.value"
          role="option"
          :aria-selected="opt.value === modelValue"
          class="px-3 py-1.5 cursor-pointer flex items-center justify-between gap-2"
          :class="i === highlighted
            ? 'bg-primary/10 text-primary'
            : 'text-ink-secondary hover:bg-bg-secondary hover:text-ink'"
          @mouseenter="highlighted = i"
          @mousedown.prevent="choose(opt)"
        >
          <span class="truncate">{{ opt.label }}</span>
          <Icon v-if="opt.value === modelValue" name="check" class="h-3.5 w-3.5 shrink-0" />
        </li>
      </ul>
    </Transition>
  </div>
</template>
