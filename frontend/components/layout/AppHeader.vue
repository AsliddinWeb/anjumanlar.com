<script setup lang="ts">
const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const { user, isAuthenticated, logout } = useAuth();

const nav = computed(() => [
  { to: "/", label: t("nav.home") },
  { to: "/books", label: t("nav.books") },
  { to: "/authors", label: t("nav.authors") },
  { to: "/blog", label: t("nav.blog") },
  { to: "/about", label: t("nav.about") },
]);

const userMenuOpen = ref(false);
const mobileMenuOpen = ref(false);

const searchInput = ref((route.query.q as string) || "");

watch(
  () => route.query.q,
  (v) => {
    searchInput.value = (v as string) || "";
  },
);

// Close mobile menu when route changes.
watch(
  () => route.fullPath,
  () => {
    mobileMenuOpen.value = false;
    userMenuOpen.value = false;
  },
);

watch(mobileMenuOpen, (open) => {
  if (import.meta.client) {
    document.body.style.overflow = open ? "hidden" : "";
  }
});

onBeforeUnmount(() => {
  if (import.meta.client) document.body.style.overflow = "";
});

async function onSearch() {
  const q = searchInput.value.trim();
  if (!q) return;
  mobileMenuOpen.value = false;
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
    <div class="max-w-6xl mx-auto px-4 h-14 flex items-center gap-3 md:gap-6">
      <NuxtLink :to="localePath('/')" class="font-serif font-bold text-lg text-primary shrink-0">
        {{ t("site.title") }}
      </NuxtLink>

      <nav class="hidden md:flex items-center gap-4 text-sm">
        <NuxtLink
          v-for="item in nav"
          :key="item.to"
          :to="localePath(item.to)"
          class="text-ink-secondary hover:text-primary transition-colors"
        >
          {{ item.label }}
        </NuxtLink>
      </nav>

      <form
        class="flex-1 max-w-md hidden md:flex items-center"
        role="search"
        @submit.prevent="onSearch"
      >
        <div class="relative w-full">
          <input
            v-model="searchInput"
            type="search"
            :placeholder="t('search.placeholder')"
            :aria-label="t('search.title')"
            class="w-full pl-8 pr-3 py-1.5 rounded border border-border bg-bg-card text-sm text-ink placeholder:text-ink-tertiary focus:outline-none focus:border-primary"
          >
          <span
            class="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-tertiary text-sm pointer-events-none"
            aria-hidden="true"
          >
            🔎
          </span>
        </div>
      </form>

      <div class="flex-1 md:hidden" />

      <LanguageSwitcher />
      <ThemeToggle />

      <!-- Authenticated: avatar dropdown -->
      <div v-if="isAuthenticated && user" class="relative hidden md:block">
        <button
          type="button"
          class="inline-flex items-center gap-2 px-2.5 py-1 rounded border border-border hover:border-border-hover text-sm text-ink-secondary"
          :aria-expanded="userMenuOpen"
          @click="userMenuOpen = !userMenuOpen"
        >
          <span class="h-6 w-6 rounded-full bg-primary text-ink-inverse flex items-center justify-center text-xs font-semibold">
            {{ user.full_name.charAt(0).toUpperCase() }}
          </span>
          <span class="hidden sm:inline truncate max-w-[140px]">
            {{ user.full_name }}
          </span>
          <span aria-hidden="true">▾</span>
        </button>

        <ul
          v-if="userMenuOpen"
          class="absolute right-0 mt-1 min-w-44 rounded border border-border bg-bg-elevated shadow-md py-1 text-sm"
          role="menu"
          @click="userMenuOpen = false"
        >
          <li>
            <NuxtLink
              :to="localePath('/account')"
              class="block px-3 py-1.5 text-ink-secondary hover:bg-bg-secondary hover:text-primary"
            >
              {{ t("nav.account") }}
            </NuxtLink>
          </li>
          <li>
            <button
              type="button"
              class="w-full text-left block px-3 py-1.5 text-ink-secondary hover:bg-bg-secondary hover:text-primary"
              @click="onLogout"
            >
              {{ t("auth.logout") }}
            </button>
          </li>
        </ul>
      </div>

      <!-- Anonymous: login + register CTAs -->
      <div v-else class="hidden md:flex items-center gap-2 text-sm">
        <NuxtLink
          :to="localePath('/auth/login')"
          class="px-3 py-1 rounded border border-border text-ink-secondary hover:border-primary hover:text-primary"
        >
          {{ t("nav.login") }}
        </NuxtLink>
        <NuxtLink
          :to="localePath('/auth/register')"
          class="hidden sm:inline-block px-3 py-1 rounded bg-primary text-ink-inverse hover:bg-primary-hover"
        >
          {{ t("nav.register") }}
        </NuxtLink>
      </div>

      <!-- Mobile hamburger -->
      <button
        type="button"
        class="md:hidden h-9 w-9 inline-flex items-center justify-center rounded border border-border text-ink-secondary hover:border-primary hover:text-primary"
        :aria-label="t('nav.account')"
        :aria-expanded="mobileMenuOpen"
        @click="mobileMenuOpen = !mobileMenuOpen"
      >
        <span v-if="!mobileMenuOpen" aria-hidden="true">☰</span>
        <span v-else aria-hidden="true">✕</span>
      </button>
    </div>

    <!-- Mobile drawer -->
    <Teleport v-if="mobileMenuOpen" to="body">
      <div
        class="fixed inset-0 z-40 bg-black/50 md:hidden"
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
            ✕
          </button>
        </header>

        <form class="p-4 border-b border-border" role="search" @submit.prevent="onSearch">
          <div class="relative">
            <input
              v-model="searchInput"
              type="search"
              :placeholder="t('search.placeholder')"
              :aria-label="t('search.title')"
              class="w-full pl-8 pr-3 py-2 rounded border border-border bg-bg-card text-sm text-ink placeholder:text-ink-tertiary focus:outline-none focus:border-primary"
            >
            <span
              class="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-tertiary text-sm pointer-events-none"
              aria-hidden="true"
            >
              🔎
            </span>
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
        </nav>

        <div class="p-4 border-t border-border space-y-2">
          <template v-if="isAuthenticated && user">
            <NuxtLink
              :to="localePath('/account')"
              class="block w-full text-center px-3 py-2 rounded border border-border text-ink-secondary hover:border-primary hover:text-primary"
            >
              {{ t("nav.account") }}
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
