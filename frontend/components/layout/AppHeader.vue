<script setup lang="ts">
const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const { user, isAuthenticated, hasRole, logout } = useAuth();

const isAdmin = computed(() => hasRole("admin"));
const cart = useCartStore();

const nav = computed(() => [
  { to: "/", label: t("nav.home") },
  { to: "/books", label: t("nav.books") },
  { to: "/authors", label: t("nav.authors") },
  { to: "/blog", label: t("nav.blog") },
  { to: "/about", label: t("nav.about") },
]);

const userMenuOpen = ref(false);
const authMenuOpen = ref(false);
const searchOpen = ref(false);
const mobileMenuOpen = ref(false);

const userRoot = ref<HTMLElement | null>(null);
const authRoot = ref<HTMLElement | null>(null);
const searchRoot = ref<HTMLElement | null>(null);
const searchInputEl = ref<HTMLInputElement | null>(null);

const searchInput = ref((route.query.q as string) || "");

watch(
  () => route.query.q,
  (v) => {
    searchInput.value = (v as string) || "";
  },
);

watch(
  () => route.fullPath,
  () => {
    mobileMenuOpen.value = false;
    userMenuOpen.value = false;
    authMenuOpen.value = false;
    searchOpen.value = false;
  },
);

watch(mobileMenuOpen, (open) => {
  if (import.meta.client) {
    document.body.style.overflow = open ? "hidden" : "";
  }
});

watch(searchOpen, async (open) => {
  if (open) {
    await nextTick();
    searchInputEl.value?.focus();
  }
});

function onDocumentClick(event: MouseEvent) {
  const target = event.target as Node;
  if (userMenuOpen.value && userRoot.value && !userRoot.value.contains(target)) {
    userMenuOpen.value = false;
  }
  if (authMenuOpen.value && authRoot.value && !authRoot.value.contains(target)) {
    authMenuOpen.value = false;
  }
  if (searchOpen.value && searchRoot.value && !searchRoot.value.contains(target)) {
    searchOpen.value = false;
  }
}

onMounted(() => {
  if (import.meta.client) document.addEventListener("mousedown", onDocumentClick);
});
onBeforeUnmount(() => {
  if (import.meta.client) {
    document.removeEventListener("mousedown", onDocumentClick);
    document.body.style.overflow = "";
  }
});

useEscape(() => {
  mobileMenuOpen.value = false;
  userMenuOpen.value = false;
  authMenuOpen.value = false;
  searchOpen.value = false;
});

async function onSearch() {
  const q = searchInput.value.trim();
  if (!q) return;
  mobileMenuOpen.value = false;
  searchOpen.value = false;
  await navigateTo({ path: localePath("/search"), query: { q } });
}

async function onLogout() {
  userMenuOpen.value = false;
  mobileMenuOpen.value = false;
  await logout();
  await navigateTo(localePath("/"));
}
</script>

<template>
  <header class="sticky top-0 z-30 bg-bg/90 backdrop-blur border-b border-border">
    <div class="max-w-7xl mx-auto px-4 lg:px-6 h-14 flex items-center gap-3 md:gap-5">
      <NuxtLink :to="localePath('/')" class="font-serif font-bold text-lg text-primary shrink-0">
        {{ t("site.title") }}
      </NuxtLink>

      <div class="flex-1" />

      <nav class="hidden md:flex items-center gap-6 text-sm">
        <NuxtLink
          v-for="item in nav"
          :key="item.to"
          :to="localePath(item.to)"
          class="text-ink-secondary hover:text-primary transition-colors"
        >
          {{ item.label }}
        </NuxtLink>
      </nav>

      <div class="flex-1" />

      <!-- Search icon + dropdown -->
      <div ref="searchRoot" class="relative hidden md:block">
        <button
          type="button"
          class="inline-flex items-center justify-center h-9 w-9 rounded-md border border-border text-ink-secondary hover:border-primary hover:text-primary transition-colors"
          :aria-label="t('search.title')"
          :aria-expanded="searchOpen"
          @click="searchOpen = !searchOpen"
        >
          <Icon :name="searchOpen ? 'close' : 'search'" class="h-4 w-4" />
        </button>

        <Transition
          enter-active-class="transition duration-150 ease-out"
          enter-from-class="opacity-0 -translate-y-1"
          enter-to-class="opacity-100 translate-y-0"
          leave-active-class="transition duration-100 ease-in"
          leave-from-class="opacity-100"
          leave-to-class="opacity-0"
        >
          <div
            v-if="searchOpen"
            class="absolute right-0 mt-2 w-[min(420px,calc(100vw-2rem))] rounded-md border border-border bg-bg-elevated shadow-lg p-3 z-30"
          >
            <form role="search" @submit.prevent="onSearch">
              <div class="relative">
                <Icon
                  name="search"
                  class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-tertiary pointer-events-none"
                />
                <input
                  ref="searchInputEl"
                  v-model="searchInput"
                  type="search"
                  :placeholder="t('search.placeholder')"
                  :aria-label="t('search.title')"
                  class="w-full pl-9 pr-3 py-2 rounded-md border border-border bg-bg text-sm text-ink placeholder:text-ink-tertiary focus:outline-none focus:border-primary"
                >
              </div>
              <div class="flex items-center justify-between mt-2.5">
                <NuxtLink
                  :to="localePath('/search')"
                  class="text-xs text-ink-tertiary hover:text-primary"
                  @click="searchOpen = false"
                >
                  {{ t("search.advanced") }}
                </NuxtLink>
                <button
                  type="submit"
                  class="inline-flex items-center gap-1 px-3 py-1.5 rounded-md bg-primary text-ink-inverse text-xs font-medium hover:bg-primary-hover transition-colors"
                >
                  {{ t("search.submit") }}
                  <Icon name="arrow-right" class="h-3.5 w-3.5" />
                </button>
              </div>
            </form>
          </div>
        </Transition>
      </div>

      <NuxtLink
        :to="localePath('/cart')"
        class="relative hidden md:inline-flex items-center justify-center h-9 w-9 rounded-md border border-border text-ink-secondary hover:border-primary hover:text-primary transition-colors"
        :aria-label="t('cart.title')"
      >
        <Icon name="cart" class="h-4 w-4" />
        <span
          v-if="cart.count > 0"
          class="absolute -top-1.5 -right-1.5 min-w-[18px] h-[18px] inline-flex items-center justify-center px-1 rounded-full bg-primary text-ink-inverse text-[10px] font-semibold tabular-nums"
        >
          {{ cart.count }}
        </span>
      </NuxtLink>

      <LanguageSwitcher class="hidden md:block" />
      <ThemeToggle class="hidden md:inline-flex" />

      <!-- Authenticated: avatar dropdown -->
      <div v-if="isAuthenticated && user" ref="userRoot" class="relative hidden md:block">
        <button
          type="button"
          class="inline-flex items-center gap-2 h-9 pl-1 pr-2 rounded-full border border-border text-ink-secondary hover:border-primary transition-colors"
          :aria-expanded="userMenuOpen"
          @click="userMenuOpen = !userMenuOpen"
        >
          <span class="h-7 w-7 rounded-full bg-primary text-ink-inverse flex items-center justify-center text-xs font-semibold shrink-0">
            {{ user.full_name.charAt(0).toUpperCase() }}
          </span>
          <Icon name="chevron-down" class="h-3.5 w-3.5 transition-transform" :class="userMenuOpen ? 'rotate-180' : ''" />
        </button>

        <Transition
          enter-active-class="transition duration-150 ease-out"
          enter-from-class="opacity-0 -translate-y-1"
          enter-to-class="opacity-100 translate-y-0"
          leave-active-class="transition duration-100 ease-in"
          leave-from-class="opacity-100"
          leave-to-class="opacity-0"
        >
          <div
            v-if="userMenuOpen"
            class="absolute right-0 mt-2 w-60 rounded-md border border-border bg-bg-elevated shadow-lg overflow-hidden z-30"
            role="menu"
          >
            <div class="px-4 py-3 border-b border-border bg-bg-secondary/60">
              <p class="text-sm font-medium text-ink truncate">{{ user.full_name }}</p>
              <p class="text-xs text-ink-tertiary truncate">{{ user.email }}</p>
            </div>
            <ul class="py-1 text-sm">
              <li>
                <NuxtLink
                  :to="localePath('/account')"
                  class="flex items-center gap-2.5 px-4 py-2 text-ink-secondary hover:bg-bg-secondary hover:text-ink"
                  @click="userMenuOpen = false"
                >
                  <Icon name="user-circle" class="h-4 w-4" />
                  {{ t("nav.account") }}
                </NuxtLink>
              </li>
              <li>
                <NuxtLink
                  :to="localePath('/account/library')"
                  class="flex items-center gap-2.5 px-4 py-2 text-ink-secondary hover:bg-bg-secondary hover:text-ink"
                  @click="userMenuOpen = false"
                >
                  <Icon name="library" class="h-4 w-4" />
                  {{ t("library.title") }}
                </NuxtLink>
              </li>
              <li v-if="isAdmin">
                <NuxtLink
                  :to="localePath('/admin')"
                  class="flex items-center gap-2.5 px-4 py-2 text-primary hover:bg-bg-secondary"
                  @click="userMenuOpen = false"
                >
                  <Icon name="settings" class="h-4 w-4" />
                  {{ t("admin.title") }}
                </NuxtLink>
              </li>
            </ul>
            <div class="border-t border-border py-1">
              <button
                type="button"
                class="flex items-center gap-2.5 w-full text-left px-4 py-2 text-sm text-ink-secondary hover:bg-error/5 hover:text-error"
                @click="onLogout"
              >
                <Icon name="arrow-right" class="h-4 w-4 rotate-180" />
                {{ t("auth.logout") }}
              </button>
            </div>
          </div>
        </Transition>
      </div>

      <!-- Anonymous: single CTA with dropdown -->
      <div v-else ref="authRoot" class="relative hidden md:block">
        <button
          type="button"
          class="inline-flex items-center gap-1.5 h-9 px-3 rounded-md bg-primary text-ink-inverse text-sm font-medium hover:bg-primary-hover transition-colors"
          :aria-expanded="authMenuOpen"
          @click="authMenuOpen = !authMenuOpen"
        >
          <Icon name="user-circle" class="h-4 w-4" />
          {{ t("nav.login") }}
          <Icon name="chevron-down" class="h-3.5 w-3.5 transition-transform" :class="authMenuOpen ? 'rotate-180' : ''" />
        </button>

        <Transition
          enter-active-class="transition duration-150 ease-out"
          enter-from-class="opacity-0 -translate-y-1"
          enter-to-class="opacity-100 translate-y-0"
          leave-active-class="transition duration-100 ease-in"
          leave-from-class="opacity-100"
          leave-to-class="opacity-0"
        >
          <div
            v-if="authMenuOpen"
            class="absolute right-0 mt-2 w-64 rounded-md border border-border bg-bg-elevated shadow-lg overflow-hidden z-30"
            role="menu"
          >
            <NuxtLink
              :to="localePath('/auth/login')"
              class="flex items-center gap-3 px-4 py-3 hover:bg-bg-secondary transition-colors"
              @click="authMenuOpen = false"
            >
              <span class="h-9 w-9 rounded-md bg-primary/10 text-primary flex items-center justify-center shrink-0">
                <Icon name="user-circle" class="h-4 w-4" />
              </span>
              <div class="min-w-0">
                <div class="text-sm font-medium text-ink">{{ t("nav.login") }}</div>
                <div class="text-xs text-ink-tertiary">{{ t("auth.login.subtitle") }}</div>
              </div>
            </NuxtLink>
            <div class="border-t border-border">
              <NuxtLink
                :to="localePath('/auth/register')"
                class="flex items-center gap-3 px-4 py-3 hover:bg-bg-secondary transition-colors"
                @click="authMenuOpen = false"
              >
                <span class="h-9 w-9 rounded-md bg-success/10 text-success flex items-center justify-center shrink-0">
                  <Icon name="user-plus" class="h-4 w-4" />
                </span>
                <div class="min-w-0">
                  <div class="text-sm font-medium text-ink">{{ t("nav.register") }}</div>
                  <div class="text-xs text-ink-tertiary">{{ t("auth.register.subtitle") }}</div>
                </div>
              </NuxtLink>
            </div>
          </div>
        </Transition>
      </div>

      <!-- Mobile hamburger -->
      <button
        type="button"
        class="md:hidden inline-flex items-center justify-center h-9 w-9 rounded-md border border-border text-ink-secondary hover:border-primary hover:text-primary"
        :aria-label="t('nav.account')"
        :aria-expanded="mobileMenuOpen"
        @click="mobileMenuOpen = !mobileMenuOpen"
      >
        <Icon :name="mobileMenuOpen ? 'close' : 'menu'" class="h-5 w-5" />
      </button>
    </div>

    <!-- Mobile drawer -->
    <Teleport v-if="mobileMenuOpen" to="body">
      <div
        class="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden"
        @click="mobileMenuOpen = false"
      />
      <aside
        class="fixed top-0 right-0 z-50 h-full w-80 max-w-[85vw] bg-bg-elevated border-l border-border shadow-xl flex flex-col md:hidden"
        role="dialog"
        aria-modal="true"
      >
        <header class="flex items-center justify-between p-4 border-b border-border">
          <span class="font-serif font-bold text-primary">{{ t("site.title") }}</span>
          <button
            type="button"
            class="h-8 w-8 inline-flex items-center justify-center rounded text-ink-secondary hover:bg-bg-secondary hover:text-ink"
            :aria-label="t('common.cancel')"
            @click="mobileMenuOpen = false"
          >
            <Icon name="close" class="h-5 w-5" />
          </button>
        </header>

        <form class="p-4 border-b border-border" role="search" @submit.prevent="onSearch">
          <div class="relative">
            <Icon
              name="search"
              class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-tertiary pointer-events-none"
            />
            <input
              v-model="searchInput"
              type="search"
              :placeholder="t('search.placeholder')"
              :aria-label="t('search.title')"
              class="w-full pl-9 pr-3 py-2 rounded-md border border-border bg-bg-card text-sm text-ink placeholder:text-ink-tertiary focus:outline-none focus:border-primary"
            >
          </div>
        </form>

        <nav class="flex-1 overflow-y-auto p-2 text-base">
          <ul class="space-y-1">
            <li v-for="item in nav" :key="item.to">
              <NuxtLink
                :to="localePath(item.to)"
                class="block px-3 py-2 rounded text-ink-secondary hover:bg-bg-secondary hover:text-primary"
              >
                {{ item.label }}
              </NuxtLink>
            </li>
          </ul>

          <div class="flex items-center gap-2 px-3 py-3 mt-3 border-t border-border">
            <NuxtLink
              :to="localePath('/cart')"
              class="relative inline-flex items-center justify-center h-9 w-9 rounded-md border border-border text-ink-secondary"
            >
              <Icon name="cart" class="h-4 w-4" />
              <span
                v-if="cart.count > 0"
                class="absolute -top-1.5 -right-1.5 min-w-[18px] h-[18px] inline-flex items-center justify-center px-1 rounded-full bg-primary text-ink-inverse text-[10px] font-semibold tabular-nums"
              >
                {{ cart.count }}
              </span>
            </NuxtLink>
            <LanguageSwitcher />
            <ThemeToggle />
          </div>
        </nav>

        <div class="p-4 border-t border-border space-y-2">
          <template v-if="isAuthenticated && user">
            <NuxtLink
              :to="localePath('/account')"
              class="block w-full text-center px-3 py-2 rounded border border-border text-ink-secondary hover:border-primary hover:text-primary"
            >
              {{ t("nav.account") }}
            </NuxtLink>
            <NuxtLink
              v-if="isAdmin"
              :to="localePath('/admin')"
              class="flex items-center justify-center gap-2 w-full text-center px-3 py-2 rounded border border-primary text-primary hover:bg-primary/10"
            >
              <Icon name="settings" class="h-4 w-4" />
              {{ t("admin.title") }}
            </NuxtLink>
            <button
              type="button"
              class="block w-full text-center px-3 py-2 rounded bg-bg-secondary text-ink-secondary hover:text-error"
              @click="onLogout"
            >
              {{ t("auth.logout") }}
            </button>
          </template>
          <template v-else>
            <NuxtLink
              :to="localePath('/auth/login')"
              class="block w-full text-center px-3 py-2 rounded border border-border text-ink-secondary hover:border-primary hover:text-primary"
            >
              {{ t("nav.login") }}
            </NuxtLink>
            <NuxtLink
              :to="localePath('/auth/register')"
              class="block w-full text-center px-3 py-2 rounded bg-primary text-ink-inverse hover:bg-primary-hover"
            >
              {{ t("nav.register") }}
            </NuxtLink>
          </template>
        </div>
      </aside>
    </Teleport>
  </header>
</template>
