<script setup lang="ts">
import type { ReviewRequestList, ReviewRequestStatus } from "~/types/api";
import { formatPrice } from "~/composables/useLocaleText";

definePageMeta({ middleware: "auth" });

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const api = useApi();
const { formatDate } = useFormatDate();

useHead({ title: t("review_requests.my_requests_title") });

const PAGE_SIZE = 20;
const queryParams = computed(() => ({
  page: Math.max(1, Number(route.query.page) || 1),
  page_size: PAGE_SIZE,
  status: ((route.query.status as string) || undefined) as ReviewRequestStatus | undefined,
}));

const { data: listRaw, pending } = await useAsyncData(
  "account:review-requests",
  () => api<ReviewRequestList>("/review-requests/me", { query: queryParams.value }),
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
  <AccountShell>
    <section class="space-y-5">
      <header class="flex items-end justify-between gap-3 flex-wrap">
        <div>
          <h1 class="font-serif text-2xl md:text-3xl text-ink leading-tight">
            {{ t("review_requests.my_requests_title") }}
          </h1>
          <p class="text-sm text-ink-secondary mt-1">{{ t("review_requests.my_requests_subtitle") }}</p>
        </div>
        <UiButton :to="localePath('/review-request/new')">
          <Icon name="plus" class="h-4 w-4" />
          {{ t("review_requests.new_title") }}
        </UiButton>
      </header>

      <div class="rounded-md border border-border bg-bg-card p-3 flex flex-wrap items-center gap-2">
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
      </div>

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
          <NuxtLink :to="localePath(`/account/review-requests/${r.id}`)" class="block space-y-2">
            <header class="flex items-start justify-between gap-3 flex-wrap">
              <div class="min-w-0">
                <div class="text-sm font-medium text-ink">
                  {{ r.author.display_name }}
                </div>
                <div class="text-xs text-ink-tertiary">{{ formatDate(r.created_at, { withTime: false }) }}</div>
              </div>
              <span
                class="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium"
                :class="STATUS_TONE[r.status]"
              >
                {{ t(`review_requests.statuses.${r.status}`) }}
              </span>
            </header>
            <p v-if="r.notes" class="text-sm text-ink-secondary line-clamp-2">{{ r.notes }}</p>
            <div class="flex items-center justify-between text-xs text-ink-tertiary pt-1">
              <span>
                <Icon name="document" class="inline h-3.5 w-3.5 align-text-bottom mr-0.5" />
                {{ r.manuscript_filename || (r.manuscript_url ? "PDF" : "—") }}
              </span>
              <span v-if="r.final_price != null" class="tabular-nums text-primary">
                {{ formatPrice(r.final_price) }}
              </span>
            </div>
          </NuxtLink>
        </li>
      </ul>
    </section>
  </AccountShell>
</template>
