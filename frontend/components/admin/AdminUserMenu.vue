<script setup lang="ts">
const { t } = useI18n();
const localePath = useLocalePath();
const { user, logout } = useAuth();
const route = useRoute();

const open = ref(false);
const root = ref<HTMLElement | null>(null);

watch(
  () => route.fullPath,
  () => {
    open.value = false;
  },
);

function onDocumentClick(event: MouseEvent) {
  if (!open.value || !root.value) return;
  if (!root.value.contains(event.target as Node)) {
    open.value = false;
  }
}

onMounted(() => {
  if (import.meta.client) document.addEventListener("mousedown", onDocumentClick);
});

onBeforeUnmount(() => {
  if (import.meta.client) document.removeEventListener("mousedown", onDocumentClick);
});

useEscape(() => {
  open.value = false;
}, { enabled: open });

const initial = computed(() => user.value?.full_name.charAt(0).toUpperCase() ?? "?");

async function onLogout() {
  open.value = false;
  await logout();
  await navigateTo(localePath("/"));
}
</script>

<template>
  <div v-if="user" ref="root" class="relative">
    <button
      type="button"
      class="inline-flex items-center gap-2 pl-1 pr-2 py-1 rounded-full border border-border hover:border-primary hover:bg-bg-secondary transition-colors"
      :aria-expanded="open"
      :aria-label="user.full_name"
      @click="open = !open"
    >
      <span class="h-7 w-7 rounded-full bg-primary text-ink-inverse flex items-center justify-center text-xs font-semibold shrink-0">
        {{ initial }}
      </span>
      <span class="hidden sm:inline text-sm text-ink truncate max-w-[140px]">
        {{ user.full_name }}
      </span>
      <Icon name="chevron-down" class="h-4 w-4 text-ink-tertiary transition-transform" :class="open ? 'rotate-180' : ''" />
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
        v-if="open"
        class="absolute right-0 mt-2 w-64 rounded-md border border-border bg-bg-elevated shadow-lg overflow-hidden z-30"
        role="menu"
      >
        <div class="px-4 py-3 border-b border-border bg-bg-secondary/60">
          <p class="text-sm font-medium text-ink truncate">{{ user.full_name }}</p>
          <p class="text-xs text-ink-tertiary truncate">{{ user.email }}</p>
          <span class="inline-block mt-1.5 text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-primary/10 text-primary">
            {{ user.role }}
          </span>
        </div>

        <ul class="py-1 text-sm">
          <li>
            <NuxtLink
              :to="localePath('/account')"
              class="flex items-center gap-2.5 px-4 py-2 text-ink-secondary hover:bg-bg-secondary hover:text-ink"
              role="menuitem"
              @click="open = false"
            >
              <Icon name="user-circle" class="h-4 w-4" />
              {{ t("nav.account") }}
            </NuxtLink>
          </li>
          <li>
            <NuxtLink
              :to="localePath('/')"
              class="flex items-center gap-2.5 px-4 py-2 text-ink-secondary hover:bg-bg-secondary hover:text-ink"
              role="menuitem"
              @click="open = false"
            >
              <Icon name="home" class="h-4 w-4" />
              {{ t("admin.back_to_site") }}
            </NuxtLink>
          </li>
        </ul>

        <div class="border-t border-border py-1">
          <button
            type="button"
            class="flex items-center gap-2.5 w-full text-left px-4 py-2 text-sm text-ink-secondary hover:bg-error/5 hover:text-error"
            role="menuitem"
            @click="onLogout"
          >
            <Icon name="arrow-right" class="h-4 w-4 rotate-180" />
            {{ t("auth.logout") }}
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>
