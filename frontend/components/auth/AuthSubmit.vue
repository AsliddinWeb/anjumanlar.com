<script setup lang="ts">
withDefaults(
  defineProps<{
    loading?: boolean;
    disabled?: boolean;
    label: string;
    loadingLabel?: string;
  }>(),
  { loading: false, disabled: false },
);
</script>

<template>
  <button
    type="submit"
    :disabled="disabled || loading"
    class="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded font-medium bg-primary text-ink-inverse hover:bg-primary-hover disabled:opacity-60 disabled:cursor-not-allowed transition-colors shadow-sm"
  >
    <UiSpinner v-if="loading" class="h-4 w-4" />
    <span>{{ loading && loadingLabel ? loadingLabel : label }}</span>
  </button>
</template>
