<script setup lang="ts">
import type { IconName } from "~/components/ui/Icon.vue";

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
</script>

<template>
  <aside class="bg-bg-secondary flex-col">
    <NuxtLink
      :to="localePath('/admin')"
      class="block px-4 py-4 border-b border-border"
    >
      <span class="font-serif font-bold text-lg text-primary">
        {{ $t("site.title") }}
      </span>
      <span class="block text-xs text-ink-tertiary mt-0.5">
        {{ $t("admin.title") }}
      </span>
    </NuxtLink>

    <nav class="flex-1 overflow-y-auto py-3">
      <ul class="space-y-1 px-2 text-sm">
        <li v-for="item in items" :key="item.to">
          <NuxtLink
            :to="localePath(item.to)"
            class="flex items-center gap-3 px-3 py-2 rounded transition-colors"
            :class="
              isActive(item.to, item.exact)
                ? 'bg-primary/10 text-primary font-medium'
                : 'text-ink-secondary hover:bg-bg-card hover:text-ink'
            "
          >
            <Icon :name="item.icon" class="h-5 w-5 shrink-0" />
            <span class="truncate">{{ item.label }}</span>
          </NuxtLink>
        </li>
      </ul>
    </nav>

    <div class="border-t border-border p-3">
      <NuxtLink
        :to="localePath('/account')"
        class="flex items-center gap-2 px-3 py-2 rounded text-sm text-ink-secondary hover:bg-bg-card hover:text-ink"
      >
        <Icon name="arrow-left" class="h-4 w-4" />
        <span>{{ $t("admin.back_to_account") }}</span>
      </NuxtLink>
    </div>
  </aside>
</template>
