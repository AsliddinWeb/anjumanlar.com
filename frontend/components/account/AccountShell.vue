<script setup lang="ts">
import type { IconName } from "~/utils/icons";

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const { user, hasRole, logout } = useAuth();
const cart = useCartStore();

const isAuthor = computed(() => hasRole("author"));

type NavItem = {
  to: string;
  icon: IconName;
  label: string;
  badge?: number;
  exact?: boolean;
};

const navItems = computed<NavItem[]>(() => {
  const items: NavItem[] = [
    { to: "/account", icon: "home", label: t("account.nav.dashboard"), exact: true },
    { to: "/account/library", icon: "library", label: t("account.nav.library") },
    { to: "/account/orders", icon: "clipboard-check", label: t("account.nav.orders") },
    { to: "/account/wishlist", icon: "heart", label: t("account.nav.wishlist") },
    { to: "/cart", icon: "cart", label: t("account.nav.cart"), badge: cart.count },
  ];
  if (isAuthor.value) {
    items.push(
      { to: "/account/balance", icon: "currency", label: t("account.nav.balance") },
      { to: "/account/withdrawals", icon: "money", label: t("account.nav.withdrawals") },
    );
  }
  return items;
});

function isActive(target: string, exact = false): boolean {
  const localised = localePath(target);
  if (exact) return route.path === localised;
  return route.path === localised || route.path.startsWith(localised + "/");
}

const initial = computed(() =>
  user.value?.full_name.charAt(0).toUpperCase() ?? "?",
);

const drawerOpen = ref(false);
watch(() => route.fullPath, () => { drawerOpen.value = false; });
watch(drawerOpen, (open) => {
  if (import.meta.client) document.body.style.overflow = open ? "hidden" : "";
});
onBeforeUnmount(() => {
  if (import.meta.client) document.body.style.overflow = "";
});
useEscape(() => { drawerOpen.value = false; }, { enabled: drawerOpen });

async function onLogout() {
  await logout();
  await navigateTo(localePath("/"));
}
</script>

<template>
  <ClientOnly>
    <template #fallback>
      <div class="bg-bg">
        <div class="max-w-6xl mx-auto px-4 py-6 md:py-8">
          <div class="grid md:grid-cols-[260px_1fr] gap-6 md:gap-8">
            <div class="hidden md:block space-y-3">
              <UiSkeleton height="4rem" block rounded="rounded-md" />
              <UiSkeleton height="18rem" block rounded="rounded-md" />
            </div>
            <div class="space-y-3">
              <UiSkeleton height="2.5rem" width="60%" block rounded="rounded-md" />
              <UiSkeleton height="20rem" block rounded="rounded-md" />
            </div>
          </div>
        </div>
      </div>
    </template>

  <div v-if="user" class="bg-bg">
    <div class="max-w-6xl mx-auto px-4 py-6 md:py-8">
      <!-- Mobile trigger -->
      <button
        type="button"
        class="md:hidden inline-flex items-center gap-2 px-3 py-2 mb-4 rounded-md border border-border bg-bg-card text-sm text-ink-secondary hover:border-primary hover:text-primary w-full justify-between"
        @click="drawerOpen = true"
      >
        <span class="inline-flex items-center gap-2">
          <Icon name="menu" class="h-4 w-4" />
          {{ t("account.nav.menu") }}
        </span>
        <Icon name="chevron-down" class="h-4 w-4 -rotate-90" />
      </button>

      <div class="grid md:grid-cols-[260px_1fr] gap-6 md:gap-8">
        <!-- Desktop sidebar -->
        <aside class="hidden md:block">
          <div class="sticky top-20 space-y-3">
            <!-- Profile card -->
            <NuxtLink
              :to="localePath('/account')"
              class="block rounded-md border border-border bg-bg-card p-4"
            >
              <div class="flex items-center gap-3">
                <span class="h-10 w-10 rounded-full bg-primary text-ink-inverse flex items-center justify-center text-sm font-semibold shrink-0">
                  {{ initial }}
                </span>
                <div class="min-w-0">
                  <div class="text-sm font-medium text-ink truncate">{{ user.full_name }}</div>
                  <div class="text-xs text-ink-tertiary truncate">{{ user.email }}</div>
                </div>
              </div>
            </NuxtLink>

            <!-- Nav -->
            <nav class="rounded-md border border-border bg-bg-card overflow-hidden">
              <ul class="text-sm">
                <li v-for="item in navItems" :key="item.to">
                  <NuxtLink
                    :to="localePath(item.to)"
                    class="flex items-center gap-3 px-3 py-2.5 transition-colors border-l-2"
                    :class="isActive(item.to, item.exact)
                      ? 'bg-primary/5 text-primary font-medium border-primary'
                      : 'text-ink-secondary hover:bg-bg-secondary hover:text-ink border-transparent'"
                  >
                    <Icon :name="item.icon" class="h-4 w-4 shrink-0" />
                    <span class="flex-1 truncate">{{ item.label }}</span>
                    <span
                      v-if="item.badge && item.badge > 0"
                      class="inline-flex items-center justify-center min-w-[20px] h-5 px-1.5 rounded-full bg-primary/10 text-primary text-[11px] font-semibold tabular-nums"
                    >
                      {{ item.badge }}
                    </span>
                  </NuxtLink>
                </li>
              </ul>
              <div class="border-t border-border">
                <button
                  type="button"
                  class="flex items-center gap-3 px-3 py-2.5 w-full text-left text-sm text-ink-secondary hover:bg-error/5 hover:text-error transition-colors"
                  @click="onLogout"
                >
                  <Icon name="arrow-right" class="h-4 w-4 rotate-180" />
                  {{ t("account.logout") }}
                </button>
              </div>
            </nav>
          </div>
        </aside>

        <!-- Content -->
        <div class="min-w-0">
          <slot />
        </div>
      </div>
    </div>

    <!-- Mobile drawer -->
    <Teleport v-if="drawerOpen" to="body">
      <Transition
        appear
        enter-active-class="transition duration-150"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
      >
        <div
          class="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden"
          @click="drawerOpen = false"
        />
      </Transition>
      <Transition
        appear
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="-translate-x-full"
        enter-to-class="translate-x-0"
      >
        <aside
          class="fixed top-0 left-0 z-50 h-full w-72 max-w-[85vw] bg-bg-elevated border-r border-border shadow-2xl md:hidden flex flex-col"
          role="dialog"
          aria-modal="true"
        >
          <header class="flex items-center justify-between p-4 border-b border-border">
            <div class="flex items-center gap-3 min-w-0">
              <span class="h-10 w-10 rounded-full bg-primary text-ink-inverse flex items-center justify-center text-sm font-semibold shrink-0">
                {{ initial }}
              </span>
              <div class="min-w-0">
                <div class="text-sm font-medium text-ink truncate">{{ user.full_name }}</div>
                <div class="text-xs text-ink-tertiary truncate">{{ user.email }}</div>
              </div>
            </div>
            <button
              type="button"
              class="h-8 w-8 inline-flex items-center justify-center rounded text-ink-secondary hover:bg-bg-secondary hover:text-ink shrink-0"
              :aria-label="t('common.cancel')"
              @click="drawerOpen = false"
            >
              <Icon name="close" class="h-5 w-5" />
            </button>
          </header>
          <nav class="flex-1 overflow-y-auto p-2">
            <ul class="space-y-1 text-sm">
              <li v-for="item in navItems" :key="item.to">
                <NuxtLink
                  :to="localePath(item.to)"
                  class="flex items-center gap-3 px-3 py-2.5 rounded transition-colors"
                  :class="isActive(item.to, item.exact)
                    ? 'bg-primary/10 text-primary font-medium'
                    : 'text-ink-secondary hover:bg-bg-secondary hover:text-ink'"
                >
                  <Icon :name="item.icon" class="h-5 w-5 shrink-0" />
                  <span class="flex-1 truncate">{{ item.label }}</span>
                  <span
                    v-if="item.badge && item.badge > 0"
                    class="inline-flex items-center justify-center min-w-[20px] h-5 px-1.5 rounded-full bg-primary/10 text-primary text-[11px] font-semibold tabular-nums"
                  >
                    {{ item.badge }}
                  </span>
                </NuxtLink>
              </li>
            </ul>
          </nav>
          <div class="border-t border-border p-2">
            <button
              type="button"
              class="flex items-center gap-3 px-3 py-2.5 w-full text-left text-sm text-ink-secondary hover:bg-error/5 hover:text-error rounded transition-colors"
              @click="onLogout"
            >
              <Icon name="arrow-right" class="h-5 w-5 rotate-180" />
              {{ t("account.logout") }}
            </button>
          </div>
        </aside>
      </Transition>
    </Teleport>
  </div>
  </ClientOnly>
</template>
