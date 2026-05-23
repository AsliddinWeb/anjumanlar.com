<script setup lang="ts">
import type { UserList, UserPublic, UserRole, UserStatus } from "~/types/api";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin"],
});

const { t, locale } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const api = useApi();
const { user: me } = useAuth();

useHead({ title: t("admin.users.title") });

const PAGE_SIZE = 20;

const queryParams = computed(() => ({
  page: Math.max(1, Number(route.query.page) || 1),
  page_size: PAGE_SIZE,
  search: ((route.query.search as string) || "").trim() || undefined,
  role: ((route.query.role as string) || undefined) as UserRole | undefined,
  status: ((route.query.status as string) || undefined) as UserStatus | undefined,
}));

const { data: usersRaw, pending, refresh } = await useAsyncData(
  "admin:users",
  () => api<UserList>("/admin/users", { query: queryParams.value }),
  { watch: [queryParams] },
);

const users = computed(() => usersRaw.value as UserList | null);

const searchInput = ref((route.query.search as string) || "");

watch(
  () => route.query.search,
  (v) => {
    searchInput.value = (v as string) || "";
  },
);

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

function submitSearch() {
  setQuery({ search: searchInput.value.trim() || undefined });
}

function changePage(page: number) {
  setQuery({ page });
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}

// ---- Role + status actions ----
const busy = ref<Set<string>>(new Set());

const roleOptions: UserRole[] = ["reader", "author", "admin"];

async function changeRole(target: UserPublic, newRole: UserRole) {
  if (newRole === target.role) return;
  if (busy.value.has(target.id)) return;
  busy.value.add(target.id);
  try {
    await api(`/admin/users/${target.id}/role`, {
      method: "PATCH",
      body: { role: newRole },
    });
    await refresh();
  }
  catch {
    // toast in 5.9 polish
  }
  finally {
    busy.value.delete(target.id);
  }
}

async function toggleBlock(target: UserPublic) {
  const blocking = target.status !== "blocked";
  const confirmMsg = blocking
    ? t("admin.users.actions.block_confirm")
    : t("admin.users.actions.unblock_confirm");
  if (!confirm(confirmMsg)) return;
  if (busy.value.has(target.id)) return;
  busy.value.add(target.id);
  try {
    await api(`/admin/users/${target.id}/status`, {
      method: "PATCH",
      body: { status: blocking ? "blocked" : "active" },
    });
    await refresh();
  }
  catch {
    // toast in 5.9 polish
  }
  finally {
    busy.value.delete(target.id);
  }
}

function statusTone(status: UserStatus) {
  return (
    {
      active: "success",
      pending: "warning",
      blocked: "neutral",
      deleted: "neutral",
    } as const
  )[status];
}

const formatDate = (iso: string) =>
  new Intl.DateTimeFormat(locale.value, {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(iso));

const breadcrumbs = computed(() => [
  { label: t("admin.title"), to: localePath("/admin") },
  { label: t("admin.users.title") },
]);

function initials(name: string) {
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((p) => p.charAt(0).toUpperCase())
    .join("");
}

function isSelf(u: UserPublic) {
  return me.value?.id === u.id;
}

function isImmutableSuperadmin(u: UserPublic) {
  return u.role === "superadmin" && me.value?.role !== "superadmin";
}
</script>

<template>
  <section class="space-y-6">
    <UiBreadcrumbs :items="breadcrumbs" />

    <header class="space-y-1">
      <h1 class="font-serif text-2xl text-ink">{{ t("admin.users.title") }}</h1>
      <p class="text-sm text-ink-secondary">{{ t("admin.users.subtitle") }}</p>
    </header>

    <div class="flex flex-wrap items-end gap-3">
      <form class="flex-1 min-w-[240px] max-w-md" @submit.prevent="submitSearch">
        <UiInput
          v-model="searchInput"
          :placeholder="t('admin.users.search_placeholder')"
        />
      </form>

      <UiSelect
        :model-value="(route.query.role as string) || ''"
        :label="t('admin.users.filter_role')"
        :placeholder="t('admin.users.filter_role_any')"
        :options="[
          { value: 'reader', label: t('admin.users.roles.reader') },
          { value: 'author', label: t('admin.users.roles.author') },
          { value: 'admin', label: t('admin.users.roles.admin') },
          { value: 'superadmin', label: t('admin.users.roles.superadmin') },
        ]"
        @update:model-value="(v) => setQuery({ role: v })"
      />

      <UiSelect
        :model-value="(route.query.status as string) || ''"
        :label="t('admin.users.filter_status')"
        :placeholder="t('admin.users.filter_status_any')"
        :options="[
          { value: 'active', label: t('admin.users.statuses.active') },
          { value: 'pending', label: t('admin.users.statuses.pending') },
          { value: 'blocked', label: t('admin.users.statuses.blocked') },
          { value: 'deleted', label: t('admin.users.statuses.deleted') },
        ]"
        @update:model-value="(v) => setQuery({ status: v })"
      />

      <span class="text-sm text-ink-tertiary ml-auto">
        {{ t("admin.users.results", { n: users?.total ?? 0 }) }}
      </span>
    </div>

    <div v-if="pending && !users" class="space-y-2">
      <UiSkeleton v-for="i in 4" :key="i" :height="'3.5rem'" :block="true" />
    </div>

    <UiEmptyState
      v-else-if="(users?.items.length ?? 0) === 0"
      icon="users"
      :title="t('admin.users.empty_title')"
      :description="t('admin.users.empty_body')"
    />

    <div v-else class="overflow-x-auto rounded border border-border">
      <table class="w-full text-sm">
        <thead class="bg-bg-secondary text-left text-xs text-ink-tertiary">
          <tr>
            <th class="px-3 py-2">{{ t("admin.users.table.user") }}</th>
            <th class="px-3 py-2">{{ t("admin.users.table.role") }}</th>
            <th class="px-3 py-2">{{ t("admin.users.table.status") }}</th>
            <th class="px-3 py-2">{{ t("admin.users.table.created_at") }}</th>
            <th class="px-3 py-2 text-right">{{ t("admin.users.table.actions") }}</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="u in users!.items"
            :key="u.id"
            class="border-t border-border hover:bg-bg-secondary/40"
          >
            <td class="px-3 py-2">
              <div class="flex items-center gap-3">
                <div class="h-8 w-8 rounded-full bg-bg-secondary flex items-center justify-center text-xs text-ink-secondary shrink-0">
                  {{ initials(u.full_name) || "?" }}
                </div>
                <div class="min-w-0">
                  <div class="text-ink truncate">{{ u.full_name }}</div>
                  <div class="text-xs text-ink-tertiary truncate">{{ u.email }}</div>
                </div>
              </div>
            </td>
            <td class="px-3 py-2">
              <UiBadge
                size="sm"
                :tone="u.role === 'admin' || u.role === 'superadmin' ? 'primary' : 'neutral'"
              >
                {{ t(`admin.users.roles.${u.role}`) }}
              </UiBadge>
            </td>
            <td class="px-3 py-2">
              <UiBadge size="sm" :tone="statusTone(u.status)">
                {{ t(`admin.users.statuses.${u.status}`) }}
              </UiBadge>
            </td>
            <td class="px-3 py-2 text-xs text-ink-tertiary">
              {{ formatDate(u.created_at) }}
            </td>
            <td class="px-3 py-2 text-right">
              <div class="inline-flex items-center gap-1.5">
                <UiSelect
                  v-if="!isSelf(u) && !isImmutableSuperadmin(u)"
                  :model-value="u.role"
                  :label="undefined"
                  :options="roleOptions.map((r) => ({ value: r, label: t(`admin.users.roles.${r}`) }))"
                  @update:model-value="(v) => changeRole(u, v as UserRole)"
                />
                <UiButton
                  v-if="!isSelf(u) && !isImmutableSuperadmin(u) && u.status !== 'deleted'"
                  size="sm"
                  :variant="u.status === 'blocked' ? 'ghost' : 'danger'"
                  :disabled="busy.has(u.id)"
                  @click="toggleBlock(u)"
                >
                  {{
                    u.status === "blocked"
                      ? t("admin.users.actions.unblock")
                      : t("admin.users.actions.block")
                  }}
                </UiButton>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="pt-4">
      <UiPagination
        :page="queryParams.page"
        :page-size="PAGE_SIZE"
        :total="users?.total ?? 0"
        @change="changePage"
      />
    </div>
  </section>
</template>
