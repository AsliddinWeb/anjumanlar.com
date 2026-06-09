<script setup lang="ts">
import type { ReviewRequestList, ReviewRequestStatus } from "~/types/api";
import { formatPrice } from "~/composables/useLocaleText";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin"],
});

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const api = useApi();
const { formatDate } = useFormatDate();

useHead({ title: t("review_requests.title") });

const PAGE_SIZE = 20;

const queryParams = computed(() => ({
  page: Math.max(1, Number(route.query.page) || 1),
  page_size: PAGE_SIZE,
  status: ((route.query.status as string) || undefined) as ReviewRequestStatus | undefined,
}));

const { data: listRaw, pending } = await useAsyncData(
  "admin:review-requests",
  () => api<ReviewRequestList>("/admin/review-requests", { query: queryParams.value }),
  { server: false, watch: [queryParams] },
);
const list = computed(() => listRaw.value as ReviewRequestList | null);
const items = computed(() => list.value?.items ?? []);

const STATUS_TONE: Record<ReviewRequestStatus, string> = {
  pending: "bg-bg-secondary text-ink-tertiary",
  quoted: "bg-warning/10 text-warning",
  paid: "bg-info/10 text-info",
  completed: "bg-success/10 text-success",
  cancelled: "bg-error/10 text-error",
};

function setStatus(s: string) {
  const next: Record<string, string> = {};
  for (const [k, v] of Object.entries(route.query)) {
    if (typeof v === "string") next[k] = v;
  }
  if (s) next.status = s; else delete next.status;
  delete next.page;
  router.push({ query: next });
}
</script>

<template>
  <section>
    <AdminPageHeader
      :title="t('review_requests.title')"
      :description="t('review_requests.subtitle')"
      icon="chat"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('review_requests.title') },
      ]"
    >
      <template #actions>
        <AdminStatusPill
          v-if="list"
          tone="info"
          icon="chat"
          :label="t('account_books.results', { n: list.total })"
        />
      </template>
    </AdminPageHeader>

    <AdminFilterBar
      :search="undefined"
      :dirty="!!route.query.status"
      @reset="setStatus('')"
    >
      <UiSelect
        :model-value="(route.query.status as string) || ''"
        size="sm"
        :options="[
          { value: '', label: t('review_requests.filter_status_any') },
          { value: 'pending', label: t('review_requests.statuses.pending') },
          { value: 'quoted', label: t('review_requests.statuses.quoted') },
          { value: 'paid', label: t('review_requests.statuses.paid') },
          { value: 'completed', label: t('review_requests.statuses.completed') },
          { value: 'cancelled', label: t('review_requests.statuses.cancelled') },
        ]"
        @update:model-value="setStatus"
      />
    </AdminFilterBar>

    <div v-if="pending && !list" class="space-y-3">
      <UiSkeleton v-for="i in 3" :key="i" height="5rem" block />
    </div>

    <UiEmptyState
      v-else-if="items.length === 0"
      icon="chat"
      :title="t('review_requests.empty_title')"
      :description="t('review_requests.empty_body')"
    />

    <ul v-else class="space-y-3">
      <li
        v-for="r in items"
        :key="r.id"
        class="rounded-md border border-border bg-bg-card p-4 hover:border-primary/40 transition-colors"
      >
        <div class="grid sm:grid-cols-[1fr_auto] gap-3 items-start">
          <div class="space-y-2 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-sm text-ink-secondary">{{ r.requester.full_name }}</span>
              <Icon name="arrow-right" class="h-3 w-3 text-ink-tertiary" />
              <span class="text-sm font-medium text-ink">{{ r.author.display_name }}</span>
              <span
                class="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium"
                :class="STATUS_TONE[r.status]"
              >
                {{ t(`review_requests.statuses.${r.status}`) }}
              </span>
            </div>
            <p v-if="r.notes" class="text-xs text-ink-secondary line-clamp-2 whitespace-pre-line">{{ r.notes }}</p>
            <div class="flex items-center gap-4 text-xs text-ink-tertiary">
              <span>{{ formatDate(r.created_at, { withTime: false }) }}</span>
              <span v-if="r.final_price != null" class="text-primary tabular-nums">
                {{ formatPrice(r.final_price) }}
              </span>
              <a
                v-if="r.manuscript_url"
                :href="r.manuscript_url"
                target="_blank"
                rel="noopener noreferrer"
                class="text-primary hover:underline inline-flex items-center gap-1"
              >
                <Icon name="document" class="h-3 w-3" />
                {{ t("review_requests.actions.download_manuscript") }}
              </a>
              <a
                v-if="r.review_file_url"
                :href="r.review_file_url"
                target="_blank"
                rel="noopener noreferrer"
                class="text-primary hover:underline inline-flex items-center gap-1"
              >
                <Icon name="document" class="h-3 w-3" />
                {{ t("review_requests.actions.download_review_file") }}
              </a>
            </div>
          </div>
          <UiButton
            variant="ghost"
            size="sm"
            :to="localePath(`/account/review-requests/${r.id}`)"
          >
            <Icon name="external" class="h-3.5 w-3.5" />
            {{ t("review_requests.actions.view") }}
          </UiButton>
        </div>
      </li>
    </ul>
  </section>
</template>
