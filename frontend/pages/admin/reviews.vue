<script setup lang="ts">
import type { ReviewAdminView } from "~/types/api";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin"],
});

const { t, locale } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const api = useApi();
const toast = useToast();

useHead({ title: t("admin.reviews.title") });

const { data: pendingRaw, pending: loading, refresh } = await useAsyncData(
  "admin:reviews:pending",
  () => api<ReviewAdminView[]>("/admin/reviews", { query: { page: 1, page_size: 100 } }),
  { server: false },
);

const allItems = computed<ReviewAdminView[]>(
  () => (pendingRaw.value as ReviewAdminView[] | null) ?? [],
);

const searchQuery = computed(() => (route.query.q as string) || "");
const ratingFilter = computed(() => (route.query.rating as string) || "");

const items = computed<ReviewAdminView[]>(() => {
  const q = searchQuery.value.trim().toLowerCase();
  const r = ratingFilter.value ? Number(ratingFilter.value) : 0;
  return allItems.value.filter((rev) => {
    if (r && rev.rating !== r) return false;
    if (!q) return true;
    return rev.user.full_name.toLowerCase().includes(q)
      || (rev.title ?? "").toLowerCase().includes(q)
      || rev.body.toLowerCase().includes(q);
  });
});

const filtersDirty = computed(() => Boolean(searchQuery.value || ratingFilter.value));

function setQuery(updates: Record<string, string | number | undefined>) {
  const next: Record<string, string> = {};
  for (const [k, v] of Object.entries(route.query)) {
    if (typeof v === "string") next[k] = v;
  }
  for (const [k, v] of Object.entries(updates)) {
    if (v === undefined || v === null || v === "") delete next[k];
    else next[k] = String(v);
  }
  router.push({ query: next });
}

function resetFilters() {
  router.replace({ query: {} });
}

const actionTarget = ref<{ review: ReviewAdminView; action: "approve" | "reject" } | null>(null);
const busy = ref(false);

async function confirmAction() {
  if (!actionTarget.value || busy.value) return;
  const { review, action } = actionTarget.value;
  busy.value = true;
  try {
    const opts: { method: "POST"; body?: Record<string, unknown> } = { method: "POST" };
    if (action === "reject") opts.body = {};
    await api(`/admin/reviews/${review.id}/${action}`, opts);
    if (action === "approve") {
      toast.success(t("admin.reviews.approve_success"));
    }
    else {
      toast.warning(t("admin.reviews.reject_success"));
    }
    actionTarget.value = null;
    await refresh();
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    busy.value = false;
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
</script>

<template>
  <section>
    <AdminPageHeader
      :title="t('admin.reviews.title')"
      :description="t('admin.reviews.subtitle')"
      icon="chat"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('admin.reviews.title') },
      ]"
    >
      <template #actions>
        <AdminStatusPill
          tone="warning"
          icon="clipboard-list"
          :label="t('admin.reviews.queue_count', { n: allItems.length })"
        />
      </template>
    </AdminPageHeader>

    <AdminFilterBar
      :search="searchQuery"
      :search-placeholder="t('admin.reviews.search_placeholder')"
      :dirty="filtersDirty"
      @update:search="(v) => setQuery({ q: v })"
      @reset="resetFilters"
    >
      <UiSelect
        :model-value="ratingFilter"
        size="sm"
        :options="[
          { value: '', label: t('admin.reviews.rating_any') },
          { value: '5', label: '★★★★★' },
          { value: '4', label: '★★★★' },
          { value: '3', label: '★★★' },
          { value: '2', label: '★★' },
          { value: '1', label: '★' },
        ]"
        @update:model-value="(v) => setQuery({ rating: v })"
      />
    </AdminFilterBar>

    <div v-if="loading && allItems.length === 0" class="space-y-3">
      <UiSkeleton v-for="i in 3" :key="i" height="7rem" block />
    </div>

    <UiEmptyState
      v-else-if="items.length === 0 && !filtersDirty"
      icon="chat"
      :title="t('admin.reviews.empty_title')"
      :description="t('admin.reviews.empty_body')"
    />

    <UiEmptyState
      v-else-if="items.length === 0"
      icon="search"
      :title="t('admin.filters.no_results')"
      :description="t('admin.filters.no_results_desc')"
    />

    <ul v-else class="space-y-3">
      <li
        v-for="r in items"
        :key="r.id"
        class="rounded-md border border-border bg-bg-card overflow-hidden hover:border-primary/40 transition-colors"
      >
        <div class="p-4 space-y-3">
          <header class="flex items-start justify-between gap-3">
            <div class="flex items-center gap-3 min-w-0">
              <div
                class="h-9 w-9 rounded-full bg-primary/10 text-primary flex items-center justify-center text-sm font-semibold shrink-0"
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
            <div class="flex items-center gap-2">
              <StarRating :value="r.rating" size="sm" />
              <AdminStatusPill tone="warning" :label="t('admin.reviews.status_pending')" />
            </div>
          </header>

          <h3 v-if="r.title" class="font-medium text-ink">{{ r.title }}</h3>
          <p class="text-sm text-ink-secondary whitespace-pre-line leading-relaxed">{{ r.body }}</p>
        </div>

        <footer class="flex flex-wrap items-center gap-2 px-4 py-2.5 bg-bg-secondary/50 border-t border-border">
          <span class="inline-flex items-center gap-1.5 text-xs text-ink-tertiary">
            <Icon name="book" class="h-3.5 w-3.5" />
            <code class="font-mono text-[11px]">{{ r.book_id.slice(0, 8) }}…</code>
          </span>
          <span class="flex-1" />
          <UiButton
            size="sm"
            variant="ghost"
            :disabled="busy"
            @click="actionTarget = { review: r, action: 'reject' }"
          >
            <Icon name="close" class="h-4 w-4" />
            {{ t("admin.reviews.reject") }}
          </UiButton>
          <UiButton
            size="sm"
            :disabled="busy"
            @click="actionTarget = { review: r, action: 'approve' }"
          >
            <Icon name="check" class="h-4 w-4" />
            {{ t("admin.reviews.approve") }}
          </UiButton>
        </footer>
      </li>
    </ul>

    <AdminConfirmDialog
      :open="!!actionTarget"
      :tone="actionTarget?.action === 'approve' ? 'primary' : 'danger'"
      :icon="actionTarget?.action === 'approve' ? 'check-circle-solid' : 'close'"
      :title="actionTarget?.action === 'approve'
        ? t('admin.reviews.approve_modal_title')
        : t('admin.reviews.reject_modal_title')"
      :description="actionTarget?.action === 'approve'
        ? t('admin.reviews.approve_modal_body')
        : t('admin.reviews.reject_modal_body')"
      :confirm-label="actionTarget?.action === 'approve' ? t('admin.reviews.approve') : t('admin.reviews.reject')"
      :cancel-label="t('admin.actions.cancel')"
      :loading="busy"
      @update:open="(v) => !v && (actionTarget = null)"
      @confirm="confirmAction"
    />
  </section>
</template>
