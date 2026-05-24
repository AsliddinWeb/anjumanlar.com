<script setup lang="ts">
import type { IconName } from "~/utils/icons";

defineProps<{
  title: string;
  description?: string;
  icon?: IconName;
  /** Breadcrumb segments. Last one is rendered as plain text. */
  breadcrumbs?: { label: string; to?: string }[];
}>();
</script>

<template>
  <header class="flex flex-col gap-4 pb-6 mb-6 border-b border-border md:flex-row md:items-end md:justify-between">
    <div class="space-y-2 min-w-0">
      <nav
        v-if="breadcrumbs && breadcrumbs.length"
        class="flex items-center gap-1.5 text-xs text-ink-tertiary"
        aria-label="Breadcrumb"
      >
        <template v-for="(crumb, i) in breadcrumbs" :key="i">
          <NuxtLink
            v-if="crumb.to && i < breadcrumbs.length - 1"
            :to="crumb.to"
            class="hover:text-primary truncate max-w-[14ch]"
          >
            {{ crumb.label }}
          </NuxtLink>
          <span v-else class="text-ink-secondary truncate max-w-[20ch]">
            {{ crumb.label }}
          </span>
          <Icon
            v-if="i < breadcrumbs.length - 1"
            name="chevron-down"
            class="h-3 w-3 -rotate-90 shrink-0"
          />
        </template>
      </nav>

      <div class="flex items-center gap-3">
        <div
          v-if="icon"
          class="hidden sm:inline-flex h-10 w-10 items-center justify-center rounded-md bg-primary/10 text-primary shrink-0"
        >
          <Icon :name="icon" class="h-5 w-5" />
        </div>
        <div class="min-w-0">
          <h1 class="font-serif text-2xl text-ink leading-tight truncate">
            {{ title }}
          </h1>
          <p v-if="description" class="text-sm text-ink-secondary mt-0.5">
            {{ description }}
          </p>
        </div>
      </div>
    </div>

    <div v-if="$slots.actions" class="flex flex-wrap items-center gap-2">
      <slot name="actions" />
    </div>
  </header>
</template>
