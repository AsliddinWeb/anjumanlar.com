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
  /** Backend sort key for this column (no `-` prefix — pair with `sort`/`@update:sort`). */
  sortKey?: string;
}

const props = withDefaults(
  defineProps<{
    columns: Column<T>[];
    rows: readonly T[];
    rowKey: (row: T) => string | number;
    loading?: boolean;
    empty?: { icon?: IconName; title: string; description?: string };
    /** Number of skeleton rows to show while loading. */
    skeletonRows?: number;
    /** Enables the checkbox column + select-all when set. */
    selectable?: boolean;
    /** Currently selected row keys — pair with `@update:selected`. */
    selected?: readonly (string | number)[];
    /** Rows failing this predicate render without a checkbox and can't be selected. */
    isSelectable?: (row: T) => boolean;
    /** Active backend sort value, e.g. `"price"` or `"-price"` — pair with `@update:sort`. */
    sort?: string;
  }>(),
  { skeletonRows: 5, selected: () => [] },
);

const emit = defineEmits<{
  "update:selected": [(string | number)[]];
  "update:sort": [string];
}>();

const { t } = useI18n();
const slots = useSlots();

function alignClass(a?: "left" | "right" | "center") {
  if (a === "right") return "text-right";
  if (a === "center") return "text-center";
  return "text-left";
}

function rowSelectable(row: T) {
  return props.isSelectable ? props.isSelectable(row) : true;
}

const selectableRows = computed(() => props.rows.filter(rowSelectable));
const selectedSet = computed(() => new Set(props.selected));
const allSelected = computed(
  () => selectableRows.value.length > 0 && selectableRows.value.every((r) => selectedSet.value.has(props.rowKey(r))),
);
const someSelected = computed(
  () => selectedSet.value.size > 0 && !allSelected.value,
);

function toggleAll() {
  if (allSelected.value) {
    emit("update:selected", []);
  }
  else {
    emit("update:selected", selectableRows.value.map((r) => props.rowKey(r)));
  }
}

function toggleRow(row: T) {
  const key = props.rowKey(row);
  const next = new Set(selectedSet.value);
  if (next.has(key)) next.delete(key);
  else next.add(key);
  emit("update:selected", Array.from(next));
}

function sortDirection(col: Column<T>): "asc" | "desc" | null {
  if (!col.sortKey || !props.sort) return null;
  if (props.sort === col.sortKey) return "asc";
  if (props.sort === `-${col.sortKey}`) return "desc";
  return null;
}

function toggleSort(col: Column<T>) {
  if (!col.sortKey) return;
  emit("update:sort", sortDirection(col) === "asc" ? `-${col.sortKey}` : col.sortKey);
}
</script>

<template>
  <!-- ====== Desktop / tablet — table ====== -->
  <div class="hidden md:block rounded-md border border-border bg-bg-card overflow-hidden">
    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-bg-secondary text-xs uppercase tracking-wider text-ink-tertiary">
          <tr>
            <th v-if="selectable" class="px-3 py-2.5 w-px">
              <input
                type="checkbox"
                class="h-4 w-4 rounded border-border accent-primary"
                :checked="allSelected"
                :indeterminate="someSelected"
                :aria-label="t('admin.bulk.select_all')"
                @change="toggleAll"
              />
            </th>
            <th
              v-for="col in columns"
              :key="col.key"
              class="px-3 py-2.5 font-medium"
              :class="[alignClass(col.align), col.width]"
            >
              <button
                v-if="col.sortKey"
                type="button"
                class="inline-flex items-center gap-1 hover:text-ink transition-colors"
                :class="col.align === 'right' ? 'flex-row-reverse' : ''"
                @click="toggleSort(col)"
              >
                {{ col.label }}
                <Icon
                  :name="sortDirection(col) === 'desc' ? 'chevron-down' : sortDirection(col) === 'asc' ? 'chevron-up' : 'chevron-up-down'"
                  class="h-3 w-3 shrink-0"
                  :class="sortDirection(col) ? 'text-primary' : 'text-ink-tertiary/60'"
                />
              </button>
              <template v-else>{{ col.label }}</template>
            </th>
            <th v-if="slots.actions" class="px-3 py-2.5 text-right font-medium w-px">
              <span class="sr-only">Actions</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading && rows.length === 0">
            <tr v-for="i in skeletonRows" :key="`sk-${i}`" class="border-t border-border">
              <td v-if="selectable" class="px-3 py-3">
                <UiSkeleton class="h-3 w-4" />
              </td>
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
              <td :colspan="columns.length + (slots.actions ? 1 : 0) + (selectable ? 1 : 0)" class="p-0">
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
              :class="{ 'bg-primary/5': selectable && selectedSet.has(rowKey(row)) }"
            >
              <td v-if="selectable" class="px-3 py-2.5">
                <input
                  v-if="rowSelectable(row)"
                  type="checkbox"
                  class="h-4 w-4 rounded border-border accent-primary"
                  :checked="selectedSet.has(rowKey(row))"
                  :aria-label="t('admin.bulk.select_row')"
                  @change="toggleRow(row)"
                />
              </td>
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
    <label
      v-if="selectable && rows.length > 0"
      class="flex items-center gap-2 text-xs text-ink-tertiary px-1"
    >
      <input
        type="checkbox"
        class="h-4 w-4 rounded border-border accent-primary"
        :checked="allSelected"
        :indeterminate="someSelected"
        @change="toggleAll"
      />
      {{ t("admin.bulk.select_all") }}
    </label>
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
        :class="{ 'border-primary/40 bg-primary/5': selectable && selectedSet.has(rowKey(row)) }"
      >
        <!-- Header: first column + actions in top-right -->
        <div class="flex items-start justify-between gap-3">
          <input
            v-if="selectable && rowSelectable(row)"
            type="checkbox"
            class="h-4 w-4 rounded border-border accent-primary mt-0.5 shrink-0"
            :checked="selectedSet.has(rowKey(row))"
            :aria-label="t('admin.bulk.select_row')"
            @change="toggleRow(row)"
          />
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
