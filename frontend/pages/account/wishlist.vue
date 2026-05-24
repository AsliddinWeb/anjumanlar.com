<script setup lang="ts">
import type { WishlistList } from "~/types/api";

definePageMeta({ middleware: "auth" });

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const api = useApi();

useSiteSeo({ title: t("nav.wishlist"), noindex: true });

const PAGE_SIZE = 12;
const currentPage = computed(() => Math.max(1, Number(route.query.page) || 1));

const { data: wishlistRaw, pending, refresh, error: wishlistError } = await useAsyncData(
  "account:wishlist",
  () =>
    api<WishlistList>("/users/me/wishlist", {
      query: { page: currentPage.value, page_size: PAGE_SIZE },
    }),
  { server: false, watch: [currentPage] },
);

const wishlist = computed(() => wishlistRaw.value as WishlistList | null);
const total = computed(() => wishlist.value?.total ?? 0);

function changePage(page: number) {
  router.push({ query: { ...route.query, page } });
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}

// Refresh the list when the wishlist store loses an entry (heart toggle
// from a card removed an item).
const wishlistStore = useWishlistStore();
watch(
  () => wishlistStore.ids.size,
  async (size, prev) => {
    if (size < prev) await refresh();
  },
);
</script>

<template>
  <AccountShell>
    <header class="space-y-2 mb-6">
      <div class="flex items-center gap-3">
        <span class="h-10 w-10 rounded-md bg-error/10 text-error inline-flex items-center justify-center shrink-0">
          <Icon name="heart-solid" class="h-5 w-5" />
        </span>
        <div>
          <h1 class="font-serif text-2xl md:text-3xl text-ink leading-tight">
            {{ t("nav.wishlist") }}
          </h1>
          <p class="text-sm text-ink-secondary">{{ t("wishlist.subtitle") }}</p>
        </div>
      </div>
    </header>

    <div v-if="total > 0" class="flex items-center justify-between gap-3 mb-4">
      <span class="text-sm text-ink-secondary inline-flex items-center gap-1.5 tabular-nums">
        <Icon name="heart" class="h-4 w-4 text-error" />
        {{ t("wishlist.results", { n: total }) }}
      </span>
    </div>

    <!-- Loading -->
    <div
      v-if="pending && !wishlist"
      class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4"
    >
      <div v-for="i in 4" :key="i" class="space-y-2">
        <UiSkeleton class="aspect-[2/3]" rounded="rounded-md" block />
        <UiSkeleton width="80%" height="0.9rem" block />
        <UiSkeleton width="50%" height="0.7rem" block />
      </div>
    </div>

    <!-- Error -->
    <div
      v-else-if="wishlistError"
      class="rounded-md border border-error/30 bg-error/5 p-6 flex items-start gap-4"
    >
      <Icon name="warning-solid" class="h-6 w-6 text-error shrink-0" />
      <div>
        <h3 class="font-serif text-lg text-ink mb-1">{{ t("wishlist.error_title") }}</h3>
        <p class="text-sm text-ink-secondary">{{ t("wishlist.error_body") }}</p>
      </div>
    </div>

    <!-- Empty -->
    <UiEmptyState
      v-else-if="total === 0"
      icon="heart"
      :title="t('wishlist.empty_title')"
      :description="t('wishlist.empty_body')"
    >
      <UiButton :to="localePath('/books')">
        <Icon name="book" class="h-4 w-4" />
        {{ t("wishlist.empty_cta") }}
      </UiButton>
    </UiEmptyState>

    <!-- Wishlist grid (BookCard already has a heart toggle that reflects state) -->
    <div
      v-else
      class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4"
    >
      <BookCard v-for="entry in wishlist!.items" :key="entry.id" :book="entry.book" />
    </div>

    <div v-if="total > PAGE_SIZE" class="mt-8">
      <UiPagination
        :page="currentPage"
        :page-size="PAGE_SIZE"
        :total="total"
        @change="changePage"
      />
    </div>
  </AccountShell>
</template>
