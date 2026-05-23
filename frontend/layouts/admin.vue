<script setup lang="ts">
const { t } = useI18n();
const localePath = useLocalePath();
const { user, logout } = useAuth();

const drawerOpen = ref(false);
const route = useRoute();

// Close the mobile drawer whenever the route changes.
watch(
  () => route.fullPath,
  () => {
    drawerOpen.value = false;
  },
);

watch(drawerOpen, (open) => {
  if (import.meta.client) {
    document.body.style.overflow = open ? "hidden" : "";
  }
});

onBeforeUnmount(() => {
  if (import.meta.client) document.body.style.overflow = "";
});

async function onLogout() {
  await logout();
  await navigateTo(localePath("/"));
}
</script>

<template>
  <div class="min-h-screen flex bg-bg text-ink">
    <!-- Desktop sidebar -->
    <AdminSidebar class="hidden md:flex w-60 shrink-0 border-r border-border" />

    <!-- Mobile drawer -->
    <Teleport v-if="drawerOpen" to="body">
      <div
        class="fixed inset-0 z-40 bg-black/50 md:hidden"
        @click="drawerOpen = false"
      />
      <AdminSidebar
        class="fixed top-0 left-0 z-50 h-full w-72 max-w-[85vw] border-r border-border md:hidden shadow-xl"
      />
    </Teleport>

    <!-- Right side: header + main -->
    <div class="flex-1 flex flex-col min-w-0">
      <header class="sticky top-0 z-30 bg-bg/90 backdrop-blur border-b border-border">
        <div class="px-4 h-14 flex items-center gap-3">
          <button
            type="button"
            class="md:hidden h-9 w-9 inline-flex items-center justify-center rounded border border-border text-ink-secondary hover:border-primary hover:text-primary"
            :aria-label="t('admin.nav.toggle')"
            :aria-expanded="drawerOpen"
            @click="drawerOpen = !drawerOpen"
          >
            <span aria-hidden="true">{{ drawerOpen ? "✕" : "☰" }}</span>
          </button>

          <h1 class="font-serif text-lg text-ink truncate">
            {{ t("admin.title") }}
          </h1>

          <div class="flex-1" />

          <NuxtLink
            :to="localePath('/')"
            class="hidden sm:inline-flex items-center px-3 py-1 rounded border border-border text-sm text-ink-secondary hover:border-primary hover:text-primary"
          >
            ← {{ t("admin.back_to_site") }}
          </NuxtLink>

          <LanguageSwitcher />
          <ThemeToggle />

          <div v-if="user" class="hidden sm:flex items-center gap-2 text-sm">
            <span class="h-7 w-7 rounded-full bg-primary text-ink-inverse flex items-center justify-center text-xs font-semibold">
              {{ user.full_name.charAt(0).toUpperCase() }}
            </span>
            <span class="truncate max-w-[140px] text-ink-secondary">{{ user.full_name }}</span>
          </div>

          <button
            type="button"
            class="text-xs text-ink-tertiary hover:text-error px-2"
            @click="onLogout"
          >
            {{ t("auth.logout") }}
          </button>
        </div>
      </header>

      <main class="flex-1 px-4 py-6 md:px-6 md:py-8 max-w-6xl w-full mx-auto">
        <slot />
      </main>
    </div>
  </div>
</template>
