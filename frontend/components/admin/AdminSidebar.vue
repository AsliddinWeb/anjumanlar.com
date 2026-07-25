<script setup lang="ts">
import type { IconName } from "~/utils/icons";
import type { AdminScope } from "~/types/api";

const props = withDefaults(
  defineProps<{
    collapsed?: boolean;
    /** When true, never collapses (used in the mobile drawer). */
    forceExpanded?: boolean;
  }>(),
  { collapsed: false, forceExpanded: false },
);

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const api = useApi();
const { hasAdminScope } = useAuth();

interface StatsSnapshot {
  books: { pending: number };
  reviews: { pending: number };
  review_requests: { pending: number };
  withdrawals: { open: number };
}

// Same key the dashboard page (`admin/index.vue`) fetches under — Nuxt
// dedupes/shares `useAsyncData` calls by key, so this doesn't double the
// request when both are mounted (sidebar + dashboard content).
const { data: statsRaw } = useAsyncData(
  "admin:stats",
  () => api<StatsSnapshot>("/admin/stats"),
  { server: false, lazy: true },
);
const stats = computed(() => statsRaw.value as StatsSnapshot | null);

type Item = {
  to: string;
  icon: IconName;
  label: string;
  exact?: boolean;
  scope?: AdminScope;
  badge?: () => number;
};

const allItems = computed<Item[]>(() => [
  { to: "/admin", icon: "chart", label: t("admin.nav.dashboard"), exact: true },
  { to: "/admin/books", icon: "book", label: t("admin.nav.books"), scope: "books", badge: () => stats.value?.books.pending ?? 0 },
  { to: "/admin/reviews", icon: "chat", label: t("admin.nav.reviews"), scope: "reviews", badge: () => stats.value?.reviews.pending ?? 0 },
  { to: "/admin/review-requests", icon: "inbox", label: t("admin.nav.review_requests"), scope: "review_requests", badge: () => stats.value?.review_requests.pending ?? 0 },
  { to: "/admin/review-categories", icon: "folder", label: t("admin.nav.review_categories"), scope: "review_categories" },
  { to: "/admin/blog", icon: "news", label: t("admin.nav.blog"), scope: "blog" },
  { to: "/admin/categories", icon: "folder", label: t("admin.nav.categories"), scope: "categories" },
  { to: "/admin/users", icon: "users", label: t("admin.nav.users"), scope: "users" },
  { to: "/admin/withdrawals", icon: "money", label: t("admin.nav.withdrawals"), scope: "withdrawals", badge: () => stats.value?.withdrawals.open ?? 0 },
  { to: "/admin/finance", icon: "chart", label: t("admin.nav.finance"), scope: "finance" },
  { to: "/admin/audit", icon: "clipboard-list", label: t("admin.nav.audit"), scope: "audit" },
  { to: "/admin/settings", icon: "settings", label: t("admin.nav.settings"), scope: "settings" },
]);

// `hasAdminScope` reads the auth store, which is only ever populated
// client-side (session bootstrap is a `.client` plugin). Filtering
// straight away would render fewer <li>s during SSR than the client
// settles on once the store resolves, tripping a hydration mismatch —
// so show everything until this component has actually mounted, then
// narrow to what the signed-in admin can see. Mirrors the `<ClientOnly>`
// fallback pattern used for the dashboard greeting for the same reason.
const mounted = ref(false);
onMounted(() => { mounted.value = true; });

const items = computed(() => {
  if (!mounted.value) return allItems.value;
  return allItems.value.filter((item) => !item.scope || hasAdminScope(item.scope));
});

function isActive(target: string, exact = false): boolean {
  const localised = localePath(target);
  if (exact) return route.path === localised;
  return route.path === localised || route.path.startsWith(localised + "/");
}

const isCollapsed = computed(() => !props.forceExpanded && props.collapsed);
</script>

<template>
  <aside
    class="bg-bg-secondary flex flex-col transition-[width] duration-200 ease-out"
    :class="isCollapsed ? 'w-16' : 'w-60'"
    :data-collapsed="isCollapsed ? 'true' : 'false'"
  >
    <NuxtLink
      :to="localePath('/admin')"
      class="flex items-center gap-2 px-4 h-14 border-b border-border shrink-0"
    >
      <span class="h-8 w-8 rounded bg-primary text-ink-inverse flex items-center justify-center shrink-0">
        <Icon name="academic" class="h-4 w-4" />
      </span>
      <span v-if="!isCollapsed" class="min-w-0">
        <span class="block font-serif font-bold text-primary leading-tight truncate">
          {{ $t("site.title") }}
        </span>
        <span class="block text-[10px] uppercase tracking-wider text-ink-tertiary">
          {{ $t("admin.title") }}
        </span>
      </span>
    </NuxtLink>

    <nav class="flex-1 overflow-y-auto overflow-x-hidden py-3">
      <ul class="space-y-1 px-2 text-sm">
        <li v-for="item in items" :key="item.to">
          <NuxtLink
            :to="localePath(item.to)"
            class="group relative flex items-center gap-3 rounded transition-colors"
            :class="[
              isCollapsed ? 'px-2 py-2 justify-center' : 'px-3 py-2',
              isActive(item.to, item.exact)
                ? 'bg-primary/10 text-primary font-medium'
                : 'text-ink-secondary hover:bg-bg-card hover:text-ink',
            ]"
            :title="isCollapsed ? item.label : undefined"
          >
            <span class="relative shrink-0">
              <Icon :name="item.icon" class="h-5 w-5" />
              <span
                v-if="isCollapsed && item.badge?.()"
                class="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-warning"
              />
            </span>
            <span v-if="!isCollapsed" class="truncate flex-1">{{ item.label }}</span>
            <span
              v-if="!isCollapsed && item.badge?.()"
              class="inline-flex items-center justify-center min-w-[1.25rem] h-5 px-1 rounded-full bg-warning/15 text-warning text-[11px] font-medium tabular-nums"
            >
              {{ item.badge() }}
            </span>
            <span
              v-if="isCollapsed"
              class="pointer-events-none absolute left-full ml-2 px-2 py-1 rounded bg-bg-elevated border border-border text-xs text-ink whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity z-30 shadow-md"
            >
              {{ item.label }}<template v-if="item.badge?.()"> ({{ item.badge() }})</template>
            </span>
          </NuxtLink>
        </li>
      </ul>
    </nav>

    <div class="border-t border-border p-2">
      <NuxtLink
        :to="localePath('/')"
        class="group relative flex items-center gap-2 rounded px-3 py-2 text-sm text-ink-secondary hover:bg-bg-card hover:text-ink"
        :class="isCollapsed ? 'justify-center px-2' : ''"
        :title="isCollapsed ? $t('admin.back_to_site') : undefined"
      >
        <Icon name="arrow-left" class="h-4 w-4 shrink-0" />
        <span v-if="!isCollapsed">{{ $t("admin.back_to_site") }}</span>
        <span
          v-if="isCollapsed"
          class="pointer-events-none absolute left-full ml-2 px-2 py-1 rounded bg-bg-elevated border border-border text-xs text-ink whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity z-30 shadow-md"
        >
          {{ $t("admin.back_to_site") }}
        </span>
      </NuxtLink>
    </div>
  </aside>
</template>
