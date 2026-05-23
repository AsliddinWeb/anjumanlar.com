<script setup lang="ts" generic="T">
import type { IconName } from "~/components/ui/Icon.vue";

export interface Column<R> {
  key: string;
  label: string;
  /** Tailwind width class, e.g. "w-32". */
  width?: string;
  align?: "left" | "right" | "center";
  /** Custom cell renderer via slot `cell-{key}`. If absent, falls back to `row[key]`. */
  field?: keyof R;
  truncate?: boolean;
}

withDefaults(
  defineProps<{
    columns: Column<T>[];
    rows: readonly T[];
    rowKey: (row: T) => string | number;
    loading?: boolean;
    empty?: { icon?: IconName; title: string; description?: string };
    /** Number of skeleton rows to show while loading. */
    skeletonRows?: number;
  }>(),
  { skeletonRows: 5 },
);

const slots = useSlots();

function alignClass(a?: "left" | "right" | "center") {
  if (a === "right") return "text-right";
  if (a === "center") return "text-center";
  return "text-left";
}
</script>

<template>
  <div class="rounded-md border border-border bg-bg-card overflow-hidden">
    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-bg-secondary text-xs uppercase tracking-wider text-ink-tertiary">
          <tr>
            <th
              v-for="col in columns"
              :key="col.key"
              class="px-3 py-2.5 font-medium"
              :class="[alignClass(col.align), col.width]"
            >
              {{ col.label }}
            </th>
            <th v-if="slots.actions" class="px-3 py-2.5 text-right font-medium w-px">
              <span class="sr-only">Actions</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading && rows.length === 0">
            <tr v-for="i in skeletonRows" :key="`sk-${i}`" class="border-t border-border">
              <td v-for="col in columns" :key="col.key" class="px-3 py-3">
                <UiSkeleton class="h-3 w-24" />
              </td>
              <td v-if="slots.actions" class="px-3 py-3">
                <UiSkeleton class="h-3 w-16" />
              </td>
            </tr>
          </template>
          <template v-else-if="rows.length === 0">
            <tr>
              <td :colspan="columns.length + (slots.actions ? 1 : 0)" class="p-0">
                <UiEmptyState
                  :icon="empty?.icon"
                  :title="empty?.title"
                  :description="empty?.description"
                />
              </td>
            </tr>
          </template>
          <template v-else>
            <tr
              v-for="row in rows"
              :key="rowKey(row)"
              class="border-t border-border hover:bg-bg-secondary/50 transition-colors"
            >
              <td
                v-for="col in columns"
                :key="col.key"
                class="px-3 py-2.5 text-ink"
                :class="[alignClass(col.align), col.truncate ? 'truncate max-w-[28ch]' : '']"
              >
                <slot
                  :name="`cell-${col.key}`"
                  :row="row"
                  :value="col.field ? row[col.field] : undefined"
                >
                  {{ col.field ? row[col.field] : "" }}
                </slot>
              </td>
              <td v-if="slots.actions" class="px-3 py-2.5 text-right whitespace-nowrap">
                <slot name="actions" :row="row" />
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>
