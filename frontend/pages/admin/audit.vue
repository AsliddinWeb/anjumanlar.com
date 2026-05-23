<script setup lang="ts">
import type { AuditAction, AuditLogList } from "~/types/api";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin"],
});

const { t, locale } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const api = useApi();

useHead({ title: t("admin.audit.title") });

const PAGE_SIZE = 50;
const currentPage = computed(() => Math.max(1, Number(route.query.page) || 1));
const actionFilter = computed(() => (route.query.action as string) || "");

const queryParams = computed(() => {
  const p: Record<string, string | number> = {
    page: currentPage.value,
    page_size: PAGE_SIZE,
  };
  if (actionFilter.value) p.action = actionFilter.value;
  return p;
});

const { data: rawList, pending } = await useAsyncData(
  "admin:audit",
  () => api<AuditLogList>("/admin/audit", { query: queryParams.value }),
  { watch: [queryParams] },
);

const list = computed(() => rawList.value as AuditLogList | null);

function setQuery(updates: Record<string, string | number | undefined>) {
  const next: Record<string, string> = {};
  for (const [k, v] of Object.entries(route.query)) {
    if (typeof v === "string") next[k] = v;
  }
  for (const [k, v] of Object.entries(updates)) {
    if (v === undefined || v === null || v === "") delete next[k];
    else next[k] = String(v);
  }
  if (!("page" in updates)) delete next.page;
  router.push({ query: next });
}

function changePage(page: number) {
  setQuery({ page });
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}

const formatDate = (iso: string) =>
  new Intl.DateTimeFormat(locale.value, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(iso));

const actionOptions: AuditAction[] = [
  "register",
  "email_verified",
  "resend_verification",
  "login_success",
  "login_failed",
  "logout",
  "logout_all",
  "password_changed",
  "password_reset_requested",
  "password_reset_completed",
  "profile_updated",
  "avatar_uploaded",
  "account_deleted",
];

function actionTone(action: AuditAction) {
  if (action === "login_failed") return "warning";
  if (action === "account_deleted") return "neutral";
  if (action.startsWith("login_") || action === "email_verified") return "success";
  return "neutral";
}

const breadcrumbs = computed(() => [
  { label: t("admin.title"), to: localePath("/admin") },
  { label: t("admin.audit.title") },
]);
</script>

<template>
  <section class="space-y-6">
    <UiBreadcrumbs :items="breadcrumbs" />

    <header class="space-y-1">
      <h1 class="font-serif text-2xl text-ink">{{ t("admin.audit.title") }}</h1>
      <p class="text-sm text-ink-secondary">{{ t("admin.audit.subtitle") }}</p>
    </header>

    <div class="flex flex-wrap items-end gap-3">
      <UiSelect
        :model-value="actionFilter"
        :label="t('admin.audit.filter_action')"
        :placeholder="t('admin.audit.filter_action_any')"
        :options="actionOptions.map((a) => ({ value: a, label: t(`admin.audit.actions.${a}`) }))"
        @update:model-value="(v) => setQuery({ action: v })"
      />
      <span class="text-sm text-ink-tertiary ml-auto">
        {{ list?.total ?? 0 }}
      </span>
    </div>

    <div v-if="pending && !list" class="space-y-2">
      <UiSkeleton v-for="i in 4" :key="i" :height="'3rem'" :block="true" />
    </div>

    <UiEmptyState
      v-else-if="(list?.items.length ?? 0) === 0"
      icon="📜"
      :title="t('admin.audit.empty_title')"
      :description="t('admin.audit.empty_body')"
    />

    <div v-else class="overflow-x-auto rounded border border-border">
      <table class="w-full text-sm">
        <thead class="bg-bg-secondary text-left text-xs text-ink-tertiary">
          <tr>
            <th class="px-3 py-2">{{ t("admin.audit.title") }}</th>
            <th class="px-3 py-2">User</th>
            <th class="px-3 py-2">IP</th>
            <th class="px-3 py-2">When</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in list!.items"
            :key="row.id"
            class="border-t border-border hover:bg-bg-secondary/40"
          >
            <td class="px-3 py-2">
              <UiBadge :tone="actionTone(row.action)" size="sm">
                {{ t(`admin.audit.actions.${row.action}`) }}
              </UiBadge>
            </td>
            <td class="px-3 py-2 font-mono text-xs text-ink-secondary">
              <span v-if="row.user_id">{{ row.user_id }}</span>
              <span v-else class="text-ink-tertiary italic">
                {{ t("admin.audit.anonymous") }}
              </span>
            </td>
            <td class="px-3 py-2 font-mono text-xs text-ink-tertiary">
              {{ row.ip_address ?? "—" }}
            </td>
            <td class="px-3 py-2 text-xs text-ink-tertiary whitespace-nowrap">
              {{ formatDate(row.created_at) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="pt-4">
      <UiPagination
        :page="currentPage"
        :page-size="PAGE_SIZE"
        :total="list?.total ?? 0"
        @change="changePage"
      />
    </div>
  </section>
</template>
