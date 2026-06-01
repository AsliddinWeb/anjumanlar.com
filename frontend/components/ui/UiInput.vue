<script setup lang="ts">
const props = defineProps<{
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

const showPassword = ref(false);
const isPassword = computed(() => props.type === "password");

const renderedType = computed(() => {
  if (isPassword.value) return showPassword.value ? "text" : "password";
  return props.type || "text";
});
</script>

<template>
  <label class="block">
    <span v-if="label" class="block text-sm font-medium text-ink-secondary mb-1.5">
      {{ label }}<span v-if="required" class="text-error ml-0.5">*</span>
    </span>
    <div class="relative">
      <input
        :type="renderedType"
        :value="modelValue"
        :placeholder="placeholder"
        :required="required"
        :autocomplete="autocomplete"
        :minlength="minlength"
        :maxlength="maxlength"
        class="w-full px-3.5 py-2.5 rounded-md border bg-bg-card text-ink placeholder:text-ink-tertiary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
        :class="[
          error
            ? 'border-error focus:border-error focus:ring-error/20'
            : 'border-border focus:border-primary',
          isPassword ? 'pr-11' : '',
        ]"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      >
      <button
        v-if="isPassword"
        type="button"
        class="absolute right-2 top-1/2 -translate-y-1/2 h-8 w-8 inline-flex items-center justify-center rounded text-ink-tertiary hover:text-ink hover:bg-bg-secondary transition-colors"
        :aria-label="showPassword ? 'Hide password' : 'Show password'"
        :title="showPassword ? 'Hide password' : 'Show password'"
        tabindex="-1"
        @click="showPassword = !showPassword"
      >
        <Icon :name="showPassword ? 'eye-slash' : 'eye'" class="h-4 w-4" />
      </button>
    </div>
    <span v-if="hint && !error" class="block text-xs text-ink-tertiary mt-1.5">
      {{ hint }}
    </span>
    <span v-if="error" class="block text-xs text-error mt-1.5">{{ error }}</span>
  </label>
</template>
