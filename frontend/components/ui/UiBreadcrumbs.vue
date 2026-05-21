<script setup lang="ts">
defineProps<{
  items: { label: string; to?: string }[];
}>();
</script>

<template>
  <nav class="text-sm text-ink-tertiary" aria-label="Breadcrumbs">
    <ol class="flex flex-wrap items-center gap-1.5">
      <li
        v-for="(item, i) in items"
        :key="i"
        class="flex items-center gap-1.5"
      >
        <NuxtLink
          v-if="item.to && i < items.length - 1"
          :to="item.to"
          class="hover:text-primary"
        >
          {{ item.label }}
        </NuxtLink>
        <span v-else class="text-ink-secondary">{{ item.label }}</span>
        <span v-if="i < items.length - 1" aria-hidden="true">/</span>
      </li>
    </ol>
  </nav>
</template>
