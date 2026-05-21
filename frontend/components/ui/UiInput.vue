<script setup lang="ts">
defineProps<{
  modelValue: string | number | null | undefined;
  label?: string;
  hint?: string;
  error?: string;
  type?: string;
  placeholder?: string;
  required?: boolean;
  autocomplete?: string;
  minlength?: number;
  maxlength?: number;
}>();

defineEmits<{ "update:modelValue": [value: string] }>();
</script>

<template>
  <label class="block">
    <span v-if="label" class="block text-sm text-ink-secondary mb-1">
      {{ label }}<span v-if="required" class="text-error"> *</span>
    </span>
    <input
      :type="type || 'text'"
      :value="modelValue"
      :placeholder="placeholder"
      :required="required"
      :autocomplete="autocomplete"
      :minlength="minlength"
      :maxlength="maxlength"
      class="w-full px-3 py-2 rounded border border-border bg-bg-card text-ink placeholder:text-ink-tertiary focus:outline-none focus:border-primary"
      :class="error ? 'border-error focus:border-error' : ''"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    >
    <span v-if="hint && !error" class="block text-xs text-ink-tertiary mt-1">
      {{ hint }}
    </span>
    <span v-if="error" class="block text-xs text-error mt-1">{{ error }}</span>
  </label>
</template>
