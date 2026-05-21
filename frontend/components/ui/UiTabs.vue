<script setup lang="ts">
const props = defineProps<{
  tabs: { id: string; label: string; badge?: string | number }[];
  modelValue: string;
}>();

const emit = defineEmits<{ "update:modelValue": [id: string] }>();

function select(id: string) {
  if (id !== props.modelValue) emit("update:modelValue", id);
}
</script>

<template>
  <div>
    <div class="border-b border-border" role="tablist">
      <div class="flex gap-1 -mb-px">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          type="button"
          role="tab"
          :aria-selected="tab.id === modelValue"
          class="px-4 py-2 text-sm font-medium border-b-2 transition-colors"
          :class="
            tab.id === modelValue
              ? 'border-primary text-primary'
              : 'border-transparent text-ink-secondary hover:text-ink hover:border-border-hover'
          "
          @click="select(tab.id)"
        >
          {{ tab.label }}
          <UiBadge v-if="tab.badge !== undefined" tone="neutral" size="sm" class="ml-1">
            {{ tab.badge }}
          </UiBadge>
        </button>
      </div>
    </div>
    <div class="pt-6">
      <slot :active="modelValue" />
    </div>
  </div>
</template>
