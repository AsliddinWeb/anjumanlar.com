<script setup lang="ts">
import type { OrderList, UserLibraryList, WishlistList } from "~/types/api";
import type { IconName } from "~/components/ui/Icon.vue";

definePageMeta({ middleware: "auth" });

const { t, locale } = useI18n();
const localePath = useLocalePath();
const { user, isVerified, hasRole } = useAuth();
const api = useApi();
const cart = useCartStore();

useSiteSeo({ title: t("account.title"), noindex: true });

const isAuthor = computed(() => hasRole("author"));

// Pull a small slice of each dataset so the dashboard can show counts +
// recent items without hammering the backend. Each call is wrapped so a
// single failure doesn't break the whole dashboard.
const { data: stats } = await useAsyncData(
  "account:dashboard",
  async () => {
    const [library, orders, wishlist] = await Promise.allSettled([
      api<UserLibraryList>("/libraries/me", { query: { page_size: 4 } }),
      api<OrderList>("/orders/me", { query: { page_size: 1 } }),
      api<WishlistList>("/users/me/wishlist", { query: { page_size: 1 } }),
    ]);
    return {
      library: library.status === "fulfilled" ? library.value : null,
      orders_total: orders.status === "fulfilled" ? orders.value.total : 0,
      wishlist_total: wishlist.status === "fulfilled" ? wishlist.value.total : 0,
    };
  },
  { server: false },
);

const libraryCount = computed(() => stats.value?.library?.total ?? 0);
const recentLibrary = computed(() => stats.value?.library?.items ?? []);
const ordersCount = computed(() => stats.value?.orders_total ?? 0);
const wishlistCount = computed(() => stats.value?.wishlist_total ?? 0);

const greeting = computed(() => {
  const h = new Date().getHours();
  if (h < 12) return t("account.greeting_morning");
  if (h < 18) return t("account.greeting_afternoon");
  return t("account.greeting_evening");
});

type Tile = {
  to: string;
  icon: IconName;
  iconTone: string;
  label: string;
  value: string | number;
  hint?: string;
};

const tiles = computed<Tile[]>(() => {
  const list: Tile[] = [
    {
      to: "/account/library",
      icon: "library",
      iconTone: "bg-primary/10 text-primary",
      label: t("account.tile_library"),
      value: libraryCount.value,
      hint: t("account.tile_library_hint"),
    },
    {
      to: "/account/orders",
      icon: "clipboard-check",
      iconTone: "bg-info/10 text-info",
      label: t("account.tile_orders"),
      value: ordersCount.value,
      hint: t("account.tile_orders_hint"),
    },
    {
      to: "/account/wishlist",
      icon: "heart",
      iconTone: "bg-error/10 text-error",
      label: t("account.tile_wishlist"),
      value: wishlistCount.value,
      hint: t("account.tile_wishlist_hint"),
    },
    {
      to: "/cart",
      icon: "cart",
      iconTone: "bg-warning/10 text-warning",
      label: t("account.tile_cart"),
      value: cart.count,
      hint: t("account.tile_cart_hint"),
    },
  ];
  if (isAuthor.value) {
    list.push({
      to: "/account/balance",
      icon: "currency",
      iconTone: "bg-success/10 text-success",
      label: t("account.tile_balance"),
      value: "—",
      hint: t("account.tile_balance_hint"),
    });
  }
  return list;
});

function formatDate(iso: string) {
  return new Intl.DateTimeFormat(locale.value, {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(iso));
}

const roleLabel = computed(() => t(`account.roles.${user.value?.role ?? "reader"}`));
</script>

<template>
  <AccountShell>
    <!-- Welcome header -->
    <header class="space-y-1 mb-6">
      <p class="text-sm text-ink-tertiary">{{ greeting }}</p>
      <h1 class="font-serif text-3xl md:text-4xl text-ink leading-tight tracking-tight">
        {{ user!.full_name }}
      </h1>
      <div class="flex flex-wrap items-center gap-2 text-sm text-ink-secondary mt-1">
        <span>{{ user!.email }}</span>
        <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-primary/10 text-primary text-[11px] font-medium">
          <Icon name="user-circle" class="h-3 w-3" />
          {{ roleLabel }}
        </span>
        <span
          v-if="isVerified"
          class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-success/10 text-success text-[11px] font-medium"
        >
          <Icon name="check-circle-solid" class="h-3 w-3" />
          {{ t("account.verified") }}
        </span>
      </div>
    </header>

    <!-- Unverified email banner -->
    <div
      v-if="!isVerified"
      class="mb-6 flex items-start gap-3 p-4 rounded-md border border-warning/40 bg-warning/5"
    >
      <Icon name="warning-solid" class="h-5 w-5 mt-0.5 shrink-0 text-warning" />
      <div class="flex-1 min-w-0">
        <p class="text-sm font-medium text-ink">{{ t("account.email_unverified") }}</p>
        <p class="text-xs text-ink-secondary mt-0.5">{{ t("account.email_unverified_body") }}</p>
      </div>
    </div>

    <!-- Stat tiles -->
    <section class="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
      <NuxtLink
        v-for="tile in tiles"
        :key="tile.to"
        :to="localePath(tile.to)"
        class="group rounded-md border border-border bg-bg-card p-4 hover:border-primary hover:shadow-sm transition-all"
      >
        <div class="flex items-center justify-between mb-3">
          <span
            class="h-9 w-9 rounded-md flex items-center justify-center"
            :class="tile.iconTone"
          >
            <Icon :name="tile.icon" class="h-4 w-4" />
          </span>
          <Icon name="arrow-right" class="h-4 w-4 text-ink-tertiary opacity-0 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all" />
        </div>
        <div class="font-serif text-2xl text-ink tabular-nums">{{ tile.value }}</div>
        <div class="text-xs uppercase tracking-wider text-ink-tertiary mt-1">{{ tile.label }}</div>
        <div v-if="tile.hint" class="text-xs text-ink-tertiary mt-0.5 truncate">{{ tile.hint }}</div>
      </NuxtLink>
    </section>

    <!-- Recent library -->
    <section v-if="recentLibrary.length > 0" class="space-y-4 mb-8">
      <div class="flex items-end justify-between gap-3">
        <div>
          <h2 class="font-serif text-2xl text-ink leading-tight">
            {{ t("account.recent_library") }}
          </h2>
          <p class="text-sm text-ink-secondary mt-1">{{ t("account.recent_library_hint") }}</p>
        </div>
        <NuxtLink
          :to="localePath('/account/library')"
          class="hidden sm:inline-flex items-center gap-1 text-sm text-primary hover:underline"
        >
          {{ t("account.see_all") }}
          <Icon name="arrow-right" class="h-4 w-4" />
        </NuxtLink>
      </div>
      <ul class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        <li v-for="entry in recentLibrary" :key="entry.id">
          <NuxtLink
            :to="localePath(`/books/${entry.book.slug}`)"
            class="group block rounded-md border border-border bg-bg-card overflow-hidden hover:border-primary transition-colors"
          >
            <BookCover :src="entry.book.cover_url" :alt="entry.book.slug" />
            <div class="p-2.5 space-y-1">
              <h3 class="font-serif text-sm text-ink leading-snug line-clamp-2 group-hover:text-primary transition-colors">
                {{ entry.book.title?.uz ?? entry.book.slug }}
              </h3>
              <p class="text-[10px] text-ink-tertiary">
                {{ formatDate(entry.acquired_at) }}
              </p>
            </div>
          </NuxtLink>
        </li>
      </ul>
    </section>

    <!-- Empty library inline CTA -->
    <section v-else class="rounded-md border border-dashed border-border bg-bg-card/40 p-8 text-center space-y-3">
      <div class="inline-flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary mx-auto">
        <Icon name="library" class="h-6 w-6" />
      </div>
      <div>
        <h3 class="font-serif text-lg text-ink">{{ t("account.dashboard_empty_title") }}</h3>
        <p class="text-sm text-ink-secondary mt-1">{{ t("account.dashboard_empty_body") }}</p>
      </div>
      <UiButton :to="localePath('/books')" size="md">
        <Icon name="book" class="h-4 w-4" />
        {{ t("account.dashboard_empty_cta") }}
      </UiButton>
    </section>
  </AccountShell>
</template>
