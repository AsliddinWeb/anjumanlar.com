<script setup lang="ts">
withDefaults(
  defineProps<{
    modelValue: string | null | undefined;
    options: { value: string; label: string }[];
    label?: string;
    placeholder?: string;
    /** `sm` = auto-width inline select sized to match h-9 toolbar inputs.
     *  `md` (default) = block-level form select that fills the parent. */
    size?: "sm" | "md";
  }>(),
  { size: "md" },
);

defineEmits<{ "update:modelValue": [value: string] }>();
</script>

<template>
  <label class="block">
    <span v-if="label" class="block text-sm text-ink-secondary mb-1">
      {{ label }}
    </span>
    <select
      :value="modelValue ?? ''"
      class="rounded-md border border-border bg-bg-card text-ink focus:outline-none focus:border-primary transition-colors cursor-pointer"
      :class="[
        size === 'sm' ? 'h-9 px-3 pr-8 text-sm' : 'px-3 py-2 w-full',
      ]"
      @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
    >
      <option v-if="placeholder" value="">{{ placeholder }}</option>
      <option v-for="opt in options" :key="opt.value" :value="opt.value">
        {{ opt.label }}
      </option>
    </select>
  </label>
</template>
