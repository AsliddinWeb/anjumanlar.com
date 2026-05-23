<script setup lang="ts">
const { t } = useI18n();

const props = withDefaults(
  defineProps<{
    searchPlaceholder?: string;
    /** v-model for the search input. Set to undefined to hide the search box. */
    search?: string;
    /** Whether any filter is active (controls visibility of the Reset button). */
    dirty?: boolean;
  }>(),
  {},
);

defineEmits<{
  "update:search": [value: string];
  "reset": [];
}>();

const localSearch = ref(props.search ?? "");

watch(
  () => props.search,
  (v) => {
    if (v !== undefined && v !== localSearch.value) {
      localSearch.value = v;
    }
  },
);
</script>

<template>
  <div class="rounded-md border border-border bg-bg-card p-3 mb-4 flex flex-wrap items-center gap-2">
    <div v-if="search !== undefined" class="relative flex-1 min-w-[200px]">
      <Icon
        name="search"
        class="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-tertiary pointer-events-none"
      />
      <input
        v-model="localSearch"
        type="search"
        :placeholder="searchPlaceholder ?? t('admin.filters.search_placeholder')"
        class="w-full pl-8 pr-3 py-1.5 rounded border border-border bg-bg text-sm text-ink placeholder:text-ink-tertiary focus:outline-none focus:border-primary"
        @input="$emit('update:search', ($event.target as HTMLInputElement).value)"
      >
    </div>

    <slot />

    <div class="flex-1" />

    <button
      v-if="dirty"
      type="button"
      class="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs text-ink-secondary hover:text-error transition-colors"
      @click="$emit('reset')"
    >
      <Icon name="close" class="h-3.5 w-3.5" />
      {{ t("admin.filters.reset") }}
    </button>
  </div>
</template>
