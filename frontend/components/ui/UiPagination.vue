<script setup lang="ts">
const props = defineProps<{
  page: number;
  pageSize: number;
  total: number;
}>();

const emit = defineEmits<{ change: [page: number] }>();

const totalPages = computed(() =>
  Math.max(1, Math.ceil(props.total / props.pageSize)),
);

const isFirst = computed(() => props.page <= 1);
const isLast = computed(() => props.page >= totalPages.value);

/** Compact page-number window — current ±2, plus first/last with ellipsis. */
const pageNumbers = computed<(number | "…")[]>(() => {
  const total = totalPages.value;
  const current = props.page;
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);

  const out: (number | "…")[] = [1];
  if (current - 2 > 2) out.push("…");
  for (let p = Math.max(2, current - 2); p <= Math.min(total - 1, current + 2); p++) {
    out.push(p);
  }
  if (current + 2 < total - 1) out.push("…");
  out.push(total);
  return out;
});

function go(page: number) {
  if (page < 1 || page > totalPages.value || page === props.page) return;
  emit("change", page);
}
</script>

<template>
  <nav
    v-if="totalPages > 1"
    class="flex items-center justify-center gap-1 text-sm"
    aria-label="Pagination"
  >
    <button
      type="button"
      class="px-2 py-1 rounded border border-border text-ink-secondary hover:border-primary hover:text-primary disabled:opacity-50 disabled:cursor-not-allowed"
      :disabled="isFirst"
      @click="go(page - 1)"
    >
      ‹
    </button>

    <template v-for="(p, i) in pageNumbers" :key="i">
      <span
        v-if="p === '…'"
        class="px-2 py-1 text-ink-tertiary select-none"
      >
        …
      </span>
      <button
        v-else
        type="button"
        class="min-w-[2rem] px-2 py-1 rounded border text-center"
        :class="
          p === page
            ? 'border-primary bg-primary text-ink-inverse'
            : 'border-border text-ink-secondary hover:border-primary hover:text-primary'
        "
        @click="go(p as number)"
      >
        {{ p }}
      </button>
    </template>

    <button
      type="button"
      class="px-2 py-1 rounded border border-border text-ink-secondary hover:border-primary hover:text-primary disabled:opacity-50 disabled:cursor-not-allowed"
      :disabled="isLast"
      @click="go(page + 1)"
    >
      ›
    </button>
  </nav>
</template>
