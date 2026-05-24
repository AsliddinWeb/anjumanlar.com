<script setup lang="ts">
import type { IconName } from "~/utils/icons";

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

type Item = { to: string; icon: IconName; label: string; exact?: boolean };

const items = computed<Item[]>(() => [
  { to: "/admin", icon: "chart", label: t("admin.nav.dashboard"), exact: true },
  { to: "/admin/books", icon: "book", label: t("admin.nav.books") },
  { to: "/admin/reviews", icon: "chat", label: t("admin.nav.reviews") },
  { to: "/admin/blog", icon: "news", label: t("admin.nav.blog") },
  { to: "/admin/categories", icon: "folder", label: t("admin.nav.categories") },
  { to: "/admin/users", icon: "users", label: t("admin.nav.users") },
  { to: "/admin/withdrawals", icon: "money", label: t("admin.nav.withdrawals") },
  { to: "/admin/audit", icon: "clipboard-list", label: t("admin.nav.audit") },
]);

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
            <Icon :name="item.icon" class="h-5 w-5 shrink-0" />
            <span v-if="!isCollapsed" class="truncate">{{ item.label }}</span>
            <span
              v-if="isCollapsed"
              class="pointer-events-none absolute left-full ml-2 px-2 py-1 rounded bg-bg-elevated border border-border text-xs text-ink whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity z-30 shadow-md"
            >
              {{ item.label }}
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
