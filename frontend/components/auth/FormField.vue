<script setup lang="ts">
defineProps<{
  modelValue: string;
  label: string;
  type?: string;
  placeholder?: string;
  hint?: string;
  error?: string;
  required?: boolean;
  autocomplete?: string;
  inputmode?: "text" | "email" | "tel" | "url" | "numeric" | "decimal";
  autofocus?: boolean;
  minlength?: number;
  maxlength?: number;
}>();

defineEmits<{ "update:modelValue": [value: string] }>();
</script>

<template>
  <label class="block space-y-1.5">
    <span class="text-sm text-ink-secondary">
      {{ label }}<span v-if="required" class="text-error"> *</span>
    </span>
    <input
      :value="modelValue"
      :type="type || 'text'"
      :placeholder="placeholder"
      :required="required"
      :autocomplete="autocomplete"
      :inputmode="inputmode"
      :autofocus="autofocus"
      :minlength="minlength"
      :maxlength="maxlength"
      class="w-full px-3 py-2.5 rounded border bg-bg-card text-ink placeholder:text-ink-tertiary transition-colors focus:outline-none"
      :class="[
        error
          ? 'border-error focus:border-error'
          : 'border-border focus:border-primary',
      ]"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    >
    <span v-if="error" class="block text-xs text-error">{{ error }}</span>
    <span v-else-if="hint" class="block text-xs text-ink-tertiary">{{ hint }}</span>
  </label>
</template>
