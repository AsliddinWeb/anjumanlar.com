<script setup lang="ts">
const { t } = useI18n();
const route = useRoute();
const { collapsed, mobileDrawerOpen, toggleCollapsed } = useAdminLayout();

watch(
  () => route.fullPath,
  () => {
    mobileDrawerOpen.value = false;
  },
);

watch(mobileDrawerOpen, (open) => {
  if (import.meta.client) {
    document.body.style.overflow = open ? "hidden" : "";
  }
});

onBeforeUnmount(() => {
  if (import.meta.client) document.body.style.overflow = "";
});

useEscape(() => {
  mobileDrawerOpen.value = false;
});
</script>

<template>
  <div class="min-h-screen flex bg-bg text-ink">
    <AdminSidebar
      :collapsed="collapsed"
      class="hidden md:flex shrink-0 border-r border-border sticky top-0 h-screen"
    />

    <Teleport v-if="mobileDrawerOpen" to="body">
      <Transition
        appear
        enter-active-class="transition duration-150"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
      >
        <div
          class="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden"
          @click="mobileDrawerOpen = false"
        />
      </Transition>
      <Transition
        appear
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="-translate-x-full"
        enter-to-class="translate-x-0"
      >
        <AdminSidebar
          force-expanded
          class="fixed top-0 left-0 z-50 h-full w-72 max-w-[85vw] border-r border-border md:hidden shadow-xl"
        />
      </Transition>
    </Teleport>

    <div class="flex-1 flex flex-col min-w-0">
      <header class="sticky top-0 z-30 bg-bg/90 backdrop-blur border-b border-border">
        <div class="px-4 h-14 flex items-center gap-3">
          <button
            type="button"
            class="md:hidden h-9 w-9 inline-flex items-center justify-center rounded border border-border text-ink-secondary hover:border-primary hover:text-primary"
            :aria-label="t('admin.sidebar.toggle_mobile')"
            :aria-expanded="mobileDrawerOpen"
            @click="mobileDrawerOpen = !mobileDrawerOpen"
          >
            <Icon :name="mobileDrawerOpen ? 'close' : 'menu'" class="h-5 w-5" />
          </button>

          <button
            type="button"
            class="hidden md:inline-flex h-9 w-9 items-center justify-center rounded text-ink-tertiary hover:bg-bg-secondary hover:text-ink transition-colors"
            :aria-label="collapsed ? t('admin.sidebar.expand') : t('admin.sidebar.collapse')"
            :title="collapsed ? t('admin.sidebar.expand') : t('admin.sidebar.collapse')"
            @click="toggleCollapsed"
          >
            <Icon
              name="menu"
              class="h-4 w-4 transition-transform"
              :class="collapsed ? 'rotate-180' : ''"
            />
          </button>

          <div class="flex-1" />

          <LanguageSwitcher />
          <ThemeToggle />
          <AdminUserMenu />
        </div>
      </header>

      <main class="flex-1 px-4 py-6 md:px-6 md:py-8 max-w-7xl w-full mx-auto">
        <slot />
      </main>
    </div>

    <UiToaster />
  </div>
</template>
