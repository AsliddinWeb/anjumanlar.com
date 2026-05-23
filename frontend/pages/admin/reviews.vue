<script setup lang="ts">
import type { ReviewAdminView } from "~/types/api";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin"],
});

const { t, locale } = useI18n();
const localePath = useLocalePath();
const api = useApi();

useHead({ title: t("admin.reviews.title") });

// Backend returns a raw array here, not the paginated wrapper.
const { data: pendingRaw, pending: loading, refresh } = await useAsyncData(
  "admin:reviews:pending",
  () => api<ReviewAdminView[]>("/admin/reviews", { query: { page: 1, page_size: 100 } }),
);

const items = computed<ReviewAdminView[]>(
  () => (pendingRaw.value as ReviewAdminView[] | null) ?? [],
);

const busy = ref<Set<string>>(new Set());

async function act(id: string, action: "approve" | "reject", confirmKey: string) {
  if (!confirm(t(confirmKey))) return;
  if (busy.value.has(id)) return;
  busy.value.add(id);
  try {
    const opts: { method: "POST"; body?: Record<string, unknown> } = { method: "POST" };
    if (action === "reject") opts.body = {};
    await api(`/admin/reviews/${id}/${action}`, opts);
    await refresh();
  }
  catch {
    // Phase 5.9 polish — surface via toast.
  }
  finally {
    busy.value.delete(id);
  }
}

const formatDate = (iso: string) =>
  new Intl.DateTimeFormat(locale.value, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));

const breadcrumbs = computed(() => [
  { label: t("admin.title"), to: localePath("/admin") },
  { label: t("admin.reviews.title") },
]);
</script>

<template>
  <section class="space-y-6">
    <UiBreadcrumbs :items="breadcrumbs" />

    <header class="space-y-1">
      <h1 class="font-serif text-2xl text-ink">{{ t("admin.reviews.title") }}</h1>
      <p class="text-sm text-ink-secondary">{{ t("admin.reviews.subtitle") }}</p>
    </header>

    <div v-if="loading && items.length === 0" class="space-y-3">
      <UiSkeleton v-for="i in 3" :key="i" :height="'6rem'" :block="true" />
    </div>

    <UiEmptyState
      v-else-if="items.length === 0"
      icon="💬"
      :title="t('admin.reviews.empty_title')"
      :description="t('admin.reviews.empty_body')"
    />

    <ul v-else class="space-y-3">
      <li
        v-for="r in items"
        :key="r.id"
        class="rounded border border-border bg-bg-card p-4 space-y-3"
      >
        <header class="flex items-start justify-between gap-3">
          <div class="flex items-center gap-3 min-w-0">
            <div
              class="h-9 w-9 rounded-full bg-bg-secondary flex items-center justify-center text-sm text-ink-secondary shrink-0"
            >
              {{ (r.user.full_name || "?").trim().charAt(0).toUpperCase() }}
            </div>
            <div class="min-w-0">
              <div class="text-sm font-medium text-ink truncate">
                {{ r.user.full_name }}
              </div>
              <div class="text-xs text-ink-tertiary">{{ formatDate(r.created_at) }}</div>
            </div>
          </div>
          <StarRating :value="r.rating" size="sm" />
        </header>

        <h3 v-if="r.title" class="font-medium text-ink">{{ r.title }}</h3>
        <p class="text-sm text-ink-secondary whitespace-pre-line">{{ r.body }}</p>

        <footer class="flex flex-wrap items-center gap-2 pt-2 border-t border-border">
          <span class="text-xs text-ink-tertiary">
            {{ t("admin.reviews.book_label") }}:
            <code class="font-mono text-[11px]">{{ r.book_id }}</code>
          </span>
          <span class="flex-1" />
          <UiButton
            size="sm"
            variant="ghost"
            :disabled="busy.has(r.id)"
            @click="act(r.id, 'reject', 'admin.reviews.reject_confirm')"
          >
            {{ t("admin.reviews.reject") }}
          </UiButton>
          <UiButton
            size="sm"
            :loading="busy.has(r.id)"
            :disabled="busy.has(r.id)"
            @click="act(r.id, 'approve', 'admin.reviews.approve_confirm')"
          >
            ✓ {{ t("admin.reviews.approve") }}
          </UiButton>
        </footer>
      </li>
    </ul>
  </section>
</template>
