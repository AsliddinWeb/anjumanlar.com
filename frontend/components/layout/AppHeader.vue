<script setup lang="ts">
const { t } = useI18n();
const localePath = useLocalePath();
const { user, isAuthenticated, logout } = useAuth();

const nav = computed(() => [
  { to: "/", label: t("nav.home") },
  { to: "/books", label: t("nav.books") },
  { to: "/authors", label: t("nav.authors") },
  { to: "/blog", label: t("nav.blog") },
  { to: "/about", label: t("nav.about") },
]);

const userMenuOpen = ref(false);

async function onLogout() {
  userMenuOpen.value = false;
  await logout();
  await navigateTo(localePath("/"));
}
</script>

<template>
  <header class="sticky top-0 z-30 bg-bg/90 backdrop-blur border-b border-border">
    <div class="max-w-6xl mx-auto px-4 h-14 flex items-center gap-6">
      <NuxtLink :to="localePath('/')" class="font-serif font-bold text-lg text-primary">
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

      <div class="flex-1" />

      <LanguageSwitcher />
      <ThemeToggle />

      <!-- Authenticated: avatar dropdown -->
      <div v-if="isAuthenticated && user" class="relative">
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
      <div v-else class="flex items-center gap-2 text-sm">
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
    </div>
  </header>
</template>
