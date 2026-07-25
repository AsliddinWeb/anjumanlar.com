<script setup lang="ts">
import type { AuditAction, AuditLogList, AuditLogPublic } from "~/types/api";
import type { Column } from "~/components/admin/AdminDataTable.vue";
import type { IconName } from "~/utils/icons";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin", "admin-scope"],
  adminScope: "audit",
});

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const api = useApi();
const toast = useToast();
const { formatDate } = useFormatDate();

useHead({ title: t("admin.audit.title") });

const PAGE_SIZE = 50;
const currentPage = computed(() => Math.max(1, Number(route.query.page) || 1));
const actionFilter = computed(() => (route.query.action as string) || "");
const searchQuery = computed(() => (route.query.q as string) || "");
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const userIdFilter = computed(() => {
  const raw = (route.query.user_id as string) || "";
  return UUID_RE.test(raw) ? raw : "";
});

const sort = computed(() => (route.query.sort as string) || "-created_at");

const queryParams = computed(() => {
  const p: Record<string, string | number> = {
    page: currentPage.value,
    page_size: PAGE_SIZE,
    sort: sort.value,
  };
  if (actionFilter.value) p.action = actionFilter.value;
  if (userIdFilter.value) p.user_id = userIdFilter.value;
  return p;
});

const { data: rawList, pending } = await useAsyncData(
  "admin:audit",
  () => api<AuditLogList>("/admin/audit", { query: queryParams.value }),
  { server: false, watch: [queryParams] },
);

const list = computed(() => rawList.value as AuditLogList | null);

// Server already scopes results to `userIdFilter`. The free-text box only
// narrows the current page further by action label / IP — it isn't a
// substitute for the user filter above, which is the only thing that
// searches across the full audit history.
const filtered = computed<AuditLogPublic[]>(() => {
  const items = list.value?.items ?? [];
  const q = searchQuery.value.trim().toLowerCase();
  if (!q) return items;
  return items.filter((r) =>
    (r.ip_address ?? "").toLowerCase().includes(q)
    || t(`admin.audit.actions.${r.action}`).toLowerCase().includes(q),
  );
});

function filterByUser(userId: string | null) {
  setQuery({ user_id: userId ?? undefined });
}

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

function resetFilters() {
  router.replace({ query: {} });
}

const filtersDirty = computed(() => Boolean(actionFilter.value || searchQuery.value || userIdFilter.value));

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

const ACTION_META: Record<string, { tone: "success" | "warning" | "error" | "neutral" | "info"; icon: IconName }> = {
  register: { tone: "info", icon: "user-plus" },
  email_verified: { tone: "success", icon: "check-circle" },
  resend_verification: { tone: "info", icon: "envelope" },
  login_success: { tone: "success", icon: "check" },
  login_failed: { tone: "warning", icon: "warning" },
  logout: { tone: "neutral", icon: "arrow-right" },
  logout_all: { tone: "warning", icon: "arrow-right" },
  password_changed: { tone: "info", icon: "key" },
  password_reset_requested: { tone: "info", icon: "key" },
  password_reset_completed: { tone: "success", icon: "check" },
  profile_updated: { tone: "neutral", icon: "pencil" },
  avatar_uploaded: { tone: "neutral", icon: "pencil" },
  account_deleted: { tone: "error", icon: "trash" },
};

function meta(action: string) {
  return ACTION_META[action] ?? { tone: "neutral" as const, icon: "clipboard-list" as IconName };
}

const expanded = ref<Set<string>>(new Set());
function toggleExpand(id: string) {
  if (expanded.value.has(id)) expanded.value.delete(id);
  else expanded.value.add(id);
}

// ---- Excel export (walks every page of the current filter) ----
const exporting = ref(false);

async function exportExcel() {
  if (exporting.value) return;
  exporting.value = true;
  try {
    const all = await fetchAllPages<AuditLogPublic>(
      (page, page_size) => api<AuditLogList>("/admin/audit", { query: { ...queryParams.value, page, page_size } }),
      200,
    );
    const rows = all.map((r) => ({
      [t("admin.audit.col_action")]: t(`admin.audit.actions.${r.action}`),
      [t("admin.audit.col_user")]: r.user_id ?? t("admin.audit.anonymous"),
      [t("admin.audit.col_ip")]: r.ip_address ?? "",
      [t("admin.audit.col_when")]: formatDate(r.created_at),
    }));
    await exportToExcel(`monografiya-audit-${new Date().toISOString().slice(0, 10)}`, "Audit log", rows);
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    exporting.value = false;
  }
}

const columns: Column<AuditLogPublic>[] = [
  { key: "action", label: t("admin.audit.col_action"), width: "w-56" },
  { key: "user", label: t("admin.audit.col_user") },
  { key: "ip", label: t("admin.audit.col_ip"), width: "w-32", mobileHidden: true },
  { key: "when", label: t("admin.audit.col_when"), width: "w-44", sortKey: "created_at" },
];
</script>

<template>
  <section>
    <AdminPageHeader
      :title="t('admin.audit.title')"
      :description="t('admin.audit.subtitle')"
      icon="clipboard-list"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('admin.audit.title') },
      ]"
    >
      <template #actions>
        <AdminStatusPill
          v-if="list"
          tone="info"
          icon="document"
          :label="t('admin.audit.total', { n: list.total })"
        />
        <UiButton variant="ghost" size="sm" :loading="exporting" @click="exportExcel">
          <Icon name="document" class="h-3.5 w-3.5" />
          {{ t('admin.finance.export_excel') }}
        </UiButton>
      </template>
    </AdminPageHeader>

    <AdminFilterBar
      :search="searchQuery"
      :search-placeholder="t('admin.audit.search_placeholder')"
      :dirty="filtersDirty"
      @update:search="(v) => setQuery({ q: v })"
      @reset="resetFilters"
    >
      <UiSelect
        :model-value="actionFilter"
        size="sm"
        :options="[
          { value: '', label: t('admin.audit.filter_action_any') },
          ...actionOptions.map((a) => ({ value: a, label: t(`admin.audit.actions.${a}`) })),
        ]"
        @update:model-value="(v) => setQuery({ action: v })"
      />
    </AdminFilterBar>

    <div
      v-if="userIdFilter"
      class="flex items-center gap-2 mb-3 px-3 py-2 rounded-md border border-primary/30 bg-primary/5 text-sm"
    >
      <Icon name="user-circle" class="h-4 w-4 text-primary shrink-0" />
      <span class="text-ink">{{ t('admin.audit.filtering_user') }}</span>
      <code class="font-mono text-xs text-ink-secondary">{{ userIdFilter }}</code>
      <span class="flex-1" />
      <UiButton size="sm" variant="ghost" @click="filterByUser(null)">
        {{ t('admin.audit.clear_user_filter') }}
      </UiButton>
    </div>

    <AdminDataTable
      :columns="columns"
      :rows="filtered"
      :row-key="(r) => r.id"
      :loading="pending"
      :empty="{
        icon: 'clipboard-list',
        title: filtersDirty ? t('admin.filters.no_results') : t('admin.audit.empty_title'),
        description: filtersDirty ? t('admin.filters.no_results_desc') : t('admin.audit.empty_body'),
      }"
      :sort="sort"
      @update:sort="(v) => setQuery({ sort: v })"
    >
      <template #cell-action="{ row }">
        <button
          type="button"
          class="inline-flex items-center gap-2 group"
          @click="toggleExpand(row.id)"
        >
          <AdminStatusPill
            :tone="meta(row.action).tone"
            :icon="meta(row.action).icon"
            :label="t(`admin.audit.actions.${row.action}`)"
          />
          <Icon
            v-if="row.meta && Object.keys(row.meta).length"
            name="chevron-down"
            class="h-3 w-3 text-ink-tertiary transition-transform"
            :class="expanded.has(row.id) ? 'rotate-180' : ''"
          />
        </button>
      </template>
      <template #cell-user="{ row }">
        <button
          v-if="row.user_id"
          type="button"
          class="font-mono text-xs text-ink-secondary hover:text-primary underline decoration-dotted underline-offset-2"
          :title="t('admin.audit.filter_by_user')"
          @click="filterByUser(row.user_id)"
        >
          {{ row.user_id.slice(0, 8) }}…
        </button>
        <span v-else class="text-xs text-ink-tertiary italic">
          {{ t("admin.audit.anonymous") }}
        </span>
      </template>
      <template #cell-ip="{ row }">
        <code class="font-mono text-xs text-ink-tertiary">{{ row.ip_address ?? "—" }}</code>
      </template>
      <template #cell-when="{ row }">
        <span class="text-xs text-ink-tertiary whitespace-nowrap">{{ formatDate(row.created_at) }}</span>
      </template>
    </AdminDataTable>

    <div v-if="list && list.total > PAGE_SIZE" class="pt-4">
      <UiPagination
        :page="currentPage"
        :page-size="PAGE_SIZE"
        :total="list.total"
        @change="changePage"
      />
    </div>
  </section>
</template>
