<script setup lang="ts" generic="T">
import type { IconName } from "~/utils/icons";

export interface Column<R> {
  key: string;
  label: string;
  /** Tailwind width class, e.g. "w-32". */
  width?: string;
  align?: "left" | "right" | "center";
  /** Custom cell renderer via slot `cell-{key}`. If absent, falls back to `row[key]`. */
  field?: keyof R;
  truncate?: boolean;
  /** Hide this column from the mobile card layout (it's already shown in the header column). */
  mobileHidden?: boolean;
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
  <!-- ====== Desktop / tablet — table ====== -->
  <div class="hidden md:block rounded-md border border-border bg-bg-card overflow-hidden">
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

  <!-- ====== Mobile — cards ====== -->
  <div class="md:hidden space-y-3">
    <template v-if="loading && rows.length === 0">
      <div
        v-for="i in skeletonRows"
        :key="`sk-${i}`"
        class="rounded-md border border-border bg-bg-card p-3 space-y-2"
      >
        <UiSkeleton class="h-4 w-2/3" />
        <UiSkeleton class="h-3 w-1/2" />
        <UiSkeleton class="h-3 w-1/3" />
      </div>
    </template>
    <template v-else-if="rows.length === 0">
      <div class="rounded-md border border-border bg-bg-card">
        <UiEmptyState
          :icon="empty?.icon"
          :title="empty?.title"
          :description="empty?.description"
        />
      </div>
    </template>
    <template v-else>
      <article
        v-for="row in rows"
        :key="rowKey(row)"
        class="rounded-md border border-border bg-bg-card p-3 space-y-2"
      >
        <!-- Header: first column + actions in top-right -->
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0 flex-1">
            <slot
              :name="`cell-${columns[0].key}`"
              :row="row"
              :value="columns[0].field ? row[columns[0].field] : undefined"
            >
              {{ columns[0].field ? row[columns[0].field] : "" }}
            </slot>
          </div>
          <div v-if="slots.actions" class="shrink-0 -mr-1 -mt-1">
            <slot name="actions" :row="row" />
          </div>
        </div>

        <!-- Remaining columns as label/value pairs -->
        <dl
          v-if="columns.length > 1"
          class="space-y-1.5 pt-2 border-t border-border"
        >
          <div
            v-for="col in columns.slice(1).filter((c) => !c.mobileHidden)"
            :key="col.key"
            class="flex items-baseline justify-between gap-3 text-sm"
          >
            <dt class="text-xs uppercase tracking-wider text-ink-tertiary shrink-0">
              {{ col.label }}
            </dt>
            <dd class="text-ink text-right min-w-0">
              <slot
                :name="`cell-${col.key}`"
                :row="row"
                :value="col.field ? row[col.field] : undefined"
              >
                {{ col.field ? row[col.field] : "" }}
              </slot>
            </dd>
          </div>
        </dl>
      </article>
    </template>
  </div>
</template>
