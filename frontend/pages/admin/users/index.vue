<script setup lang="ts">
import type { UserList, UserPublic, UserRole, UserStatus } from "~/types/api";
import type { Column } from "~/components/admin/AdminDataTable.vue";
import type { IconName } from "~/utils/icons";
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
const { user: me } = useAuth();

useHead({ title: t("admin.users.title") });

const PAGE_SIZE = 20;

const queryParams = computed(() => ({
  page: Math.max(1, Number(route.query.page) || 1),
  page_size: PAGE_SIZE,
  search: ((route.query.q as string) || "").trim() || undefined,
  role: ((route.query.role as string) || undefined) as UserRole | undefined,
  status: ((route.query.status as string) || undefined) as UserStatus | undefined,
}));

const { data: usersRaw, pending, refresh } = await useAsyncData(
  "admin:users",
  () => api<UserList>("/admin/users", { query: queryParams.value }),
  { server: false, watch: [queryParams] },
);

const users = computed(() => usersRaw.value as UserList | null);

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

const filtersDirty = computed(() =>
  Boolean(route.query.q || route.query.role || route.query.status),
);

// ---- Role + status + delete actions ----
const busy = ref<Set<string>>(new Set());
const roleTarget = ref<{ user: UserPublic; newRole: UserRole } | null>(null);
const blockTarget = ref<UserPublic | null>(null);
const deleteTarget = ref<UserPublic | null>(null);

const roleOptions: UserRole[] = ["reader", "author", "admin"];

async function confirmRoleChange() {
  if (!roleTarget.value) return;
  const { user: target, newRole } = roleTarget.value;
  if (busy.value.has(target.id)) return;
  busy.value.add(target.id);
  try {
    await api(`/admin/users/${target.id}/role`, {
      method: "PATCH",
      body: { role: newRole },
    });
    toast.success(t("admin.users.role_success", {
      name: target.full_name,
      role: t(`admin.users.roles.${newRole}`),
    }));
    roleTarget.value = null;
    await refresh();
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    busy.value.delete(target.id);
  }
}

async function confirmBlock() {
  if (!blockTarget.value) return;
  const target = blockTarget.value;
  const blocking = target.status !== "blocked";
  if (busy.value.has(target.id)) return;
  busy.value.add(target.id);
  try {
    await api(`/admin/users/${target.id}/status`, {
      method: "PATCH",
      body: { status: blocking ? "blocked" : "active" },
    });
    blocking ? toast.warning(t("admin.users.block_success")) : toast.success(t("admin.users.unblock_success"));
    blockTarget.value = null;
    await refresh();
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    busy.value.delete(target.id);
  }
}

async function confirmDelete() {
  if (!deleteTarget.value) return;
  const target = deleteTarget.value;
  if (busy.value.has(target.id)) return;
  busy.value.add(target.id);
  try {
    await api(`/admin/users/${target.id}`, { method: "DELETE" });
    toast.success(t("admin.users.delete_success"));
    deleteTarget.value = null;
    await refresh();
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    busy.value.delete(target.id);
  }
}

const STATUS_TONE: Record<UserStatus, "success" | "warning" | "neutral" | "error"> = {
  active: "success",
  pending: "warning",
  blocked: "error",
};

const ROLE_ICON: Record<UserRole, IconName> = {
  reader: "user-circle",
  author: "pencil",
  admin: "settings",
  superadmin: "key",
};

const formatDate = (iso: string) =>
  new Intl.DateTimeFormat(locale.value, {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(iso));

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

function canAct(u: UserPublic) {
  return !isSelf(u) && !isImmutableSuperadmin(u);
}

const columns: Column<UserPublic>[] = [
  { key: "user", label: t("admin.users.table.user") },
  { key: "role", label: t("admin.users.table.role"), width: "w-28" },
  { key: "status", label: t("admin.users.table.status"), align: "center", width: "w-28" },
  { key: "created_at", label: t("admin.users.table.created_at"), width: "w-32" },
];
</script>

<template>
  <section>
    <AdminPageHeader
      :title="t('admin.users.title')"
      :description="t('admin.users.subtitle')"
      icon="users"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('admin.users.title') },
      ]"
    >
      <template #actions>
        <AdminStatusPill
          v-if="users"
          tone="info"
          icon="users"
          :label="t('admin.users.results', { n: users.total })"
        />
        <UiButton :to="localePath('/admin/users/new')">
          <Icon name="plus" class="h-4 w-4" />
          {{ t('admin.users.new_button') }}
        </UiButton>
      </template>
    </AdminPageHeader>

    <AdminFilterBar
      :search="(route.query.q as string) || ''"
      :search-placeholder="t('admin.users.search_placeholder')"
      :dirty="filtersDirty"
      @update:search="(v) => setQuery({ q: v })"
      @reset="resetFilters"
    >
      <UiSelect
        :model-value="(route.query.role as string) || ''"
        size="sm"
        :options="[
          { value: '', label: t('admin.users.filter_role_any') },
          { value: 'reader', label: t('admin.users.roles.reader') },
          { value: 'author', label: t('admin.users.roles.author') },
          { value: 'admin', label: t('admin.users.roles.admin') },
          { value: 'superadmin', label: t('admin.users.roles.superadmin') },
        ]"
        @update:model-value="(v) => setQuery({ role: v })"
      />
      <UiSelect
        :model-value="(route.query.status as string) || ''"
        size="sm"
        :options="[
          { value: '', label: t('admin.users.filter_status_any') },
          { value: 'active', label: t('admin.users.statuses.active') },
          { value: 'pending', label: t('admin.users.statuses.pending') },
          { value: 'blocked', label: t('admin.users.statuses.blocked') },
        ]"
        @update:model-value="(v) => setQuery({ status: v })"
      />
    </AdminFilterBar>

    <AdminDataTable
      :columns="columns"
      :rows="users?.items ?? []"
      :row-key="(r) => r.id"
      :loading="pending"
      :empty="{
        icon: 'users',
        title: filtersDirty ? t('admin.filters.no_results') : t('admin.users.empty_title'),
        description: filtersDirty ? t('admin.filters.no_results_desc') : t('admin.users.empty_body'),
      }"
    >
      <template #cell-user="{ row }">
        <div class="flex items-center gap-3">
          <div
            class="h-9 w-9 rounded-full bg-primary/10 text-primary flex items-center justify-center text-sm font-semibold shrink-0"
          >
            {{ initials(row.full_name) || "?" }}
          </div>
          <div class="min-w-0">
            <NuxtLink
              :to="localePath(`/admin/users/${row.id}/edit`)"
              class="text-ink truncate font-medium hover:text-primary block"
            >
              {{ row.full_name }}
              <span v-if="isSelf(row)" class="text-xs text-ink-tertiary ml-1">
                ({{ t("admin.users.you") }})
              </span>
            </NuxtLink>
            <div class="text-xs text-ink-tertiary truncate">{{ row.email }}</div>
          </div>
        </div>
      </template>
      <template #cell-role="{ row }">
        <span class="inline-flex items-center gap-1.5 text-xs">
          <Icon :name="ROLE_ICON[row.role]" class="h-3.5 w-3.5 text-ink-tertiary" />
          {{ t(`admin.users.roles.${row.role}`) }}
        </span>
      </template>
      <template #cell-status="{ row }">
        <AdminStatusPill
          :tone="STATUS_TONE[row.status]"
          :label="t(`admin.users.statuses.${row.status}`)"
        />
      </template>
      <template #cell-created_at="{ row }">
        <span class="text-xs text-ink-tertiary">{{ formatDate(row.created_at) }}</span>
      </template>
      <template #actions="{ row }">
        <AdminActionMenu
          :items="[
            {
              key: 'edit',
              label: t('admin.actions.edit'),
              icon: 'pencil' as const,
              to: localePath(`/admin/users/${row.id}/edit`),
            },
            ...(canAct(row)
              ? roleOptions
                .filter((r) => r !== row.role)
                .map((r) => ({
                  key: `role:${r}`,
                  label: t('admin.users.set_role', { role: t(`admin.users.roles.${r}`) }),
                  icon: ROLE_ICON[r],
                  divider: r === roleOptions.filter((rx) => rx !== row.role)[0],
                }))
              : []),
            ...(canAct(row)
              ? [row.status === 'blocked'
                ? { key: 'unblock', label: t('admin.users.actions.unblock'), icon: 'check-circle' as const, divider: true }
                : { key: 'block', label: t('admin.users.actions.block'), icon: 'lock' as const, danger: true, divider: true }]
              : []),
            ...(canAct(row)
              ? [{ key: 'delete', label: t('admin.users.actions.delete'), icon: 'trash' as const, danger: true }]
              : []),
          ]"
          @action="(k) => {
            if (k.startsWith('role:')) roleTarget = { user: row, newRole: k.slice(5) as UserRole };
            else if (k === 'block' || k === 'unblock') blockTarget = row;
            else if (k === 'delete') deleteTarget = row;
          }"
        />
      </template>
    </AdminDataTable>

    <div v-if="users && users.total > PAGE_SIZE" class="pt-4">
      <UiPagination
        :page="queryParams.page"
        :page-size="PAGE_SIZE"
        :total="users.total"
        @change="changePage"
      />
    </div>

    <AdminConfirmDialog
      :open="!!roleTarget"
      tone="primary"
      icon="key"
      :title="t('admin.users.role_modal_title')"
      :description="roleTarget ? t('admin.users.role_modal_body', { name: roleTarget.user.full_name, role: t(`admin.users.roles.${roleTarget.newRole}`) }) : ''"
      :confirm-label="t('admin.actions.save')"
      :cancel-label="t('admin.actions.cancel')"
      :loading="roleTarget ? busy.has(roleTarget.user.id) : false"
      @update:open="(v) => !v && (roleTarget = null)"
      @confirm="confirmRoleChange"
    />

    <AdminConfirmDialog
      :open="!!blockTarget"
      :tone="blockTarget?.status === 'blocked' ? 'primary' : 'danger'"
      :icon="blockTarget?.status === 'blocked' ? 'check-circle' : 'lock'"
      :title="blockTarget?.status === 'blocked' ? t('admin.users.unblock_modal_title') : t('admin.users.block_modal_title')"
      :description="blockTarget?.status === 'blocked'
        ? t('admin.users.unblock_modal_body', { name: blockTarget.full_name })
        : (blockTarget ? t('admin.users.block_modal_body', { name: blockTarget.full_name }) : '')"
      :confirm-label="blockTarget?.status === 'blocked' ? t('admin.users.actions.unblock') : t('admin.users.actions.block')"
      :cancel-label="t('admin.actions.cancel')"
      :loading="blockTarget ? busy.has(blockTarget.id) : false"
      @update:open="(v) => !v && (blockTarget = null)"
      @confirm="confirmBlock"
    />

    <AdminConfirmDialog
      :open="!!deleteTarget"
      tone="danger"
      icon="trash"
      :title="t('admin.users.delete_modal_title')"
      :description="deleteTarget ? t('admin.users.delete_modal_body', { name: deleteTarget.full_name }) : ''"
      :confirm-label="t('admin.users.actions.delete')"
      :cancel-label="t('admin.actions.cancel')"
      :loading="deleteTarget ? busy.has(deleteTarget.id) : false"
      @update:open="(v) => !v && (deleteTarget = null)"
      @confirm="confirmDelete"
    />
  </section>
</template>
