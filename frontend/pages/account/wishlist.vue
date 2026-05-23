<script setup lang="ts">
import type { WishlistList } from "~/types/api";

definePageMeta({ middleware: "auth" });

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const api = useApi();

const PAGE_SIZE = 20;

const currentPage = computed(() => Math.max(1, Number(route.query.page) || 1));

const { data: wishlistRaw, pending, refresh } = await useAsyncData(
  "account:wishlist",
  () =>
    api<WishlistList>("/users/me/wishlist", {
      query: { page: currentPage.value, page_size: PAGE_SIZE },
    }),
  { watch: [currentPage] },
);

const wishlist = computed(() => wishlistRaw.value as WishlistList | null);

useHead({ title: t("nav.wishlist") });

const breadcrumbs = computed(() => [
  { label: t("nav.home"), to: localePath("/") },
  { label: t("account.title"), to: localePath("/account") },
  { label: t("nav.wishlist") },
]);

function changePage(page: number) {
  router.push({ query: { ...route.query, page } });
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}

// Refresh when the store toggles an entry from a card-level heart click.
const wishlistStore = useWishlistStore();
watch(
  () => wishlistStore.ids.size,
  async (size, prev) => {
    if (size < prev) await refresh();
  },
);
</script>

<template>
  <section class="max-w-6xl mx-auto px-4 py-8 space-y-6">
    <UiBreadcrumbs :items="breadcrumbs" />

    <header class="space-y-1">
      <h1 class="font-serif text-3xl text-ink">{{ t("nav.wishlist") }}</h1>
      <p class="text-sm text-ink-secondary">
        {{ t("wishlist.subtitle") }}
      </p>
    </header>

    <div
      v-if="pending && !wishlist"
      class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4"
    >
      <div v-for="i in 4" :key="i" class="space-y-2">
        <UiSkeleton class="aspect-[2/3] !block" :rounded="'rounded'" />
        <UiSkeleton :width="'80%'" :height="'1rem'" :block="true" />
      </div>
    </div>

    <UiEmptyState
      v-else-if="(wishlist?.items.length ?? 0) === 0"
      icon="heart"
      :title="t('wishlist.empty_title')"
      :description="t('wishlist.empty_body')"
    >
      <UiButton :to="localePath('/books')">
        {{ t("home.hero.cta_browse") }}
      </UiButton>
    </UiEmptyState>

    <div
      v-else
      class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4"
    >
      <BookCard v-for="entry in wishlist!.items" :key="entry.id" :book="entry.book" />
    </div>

    <div class="pt-4">
      <UiPagination
        :page="currentPage"
        :page-size="PAGE_SIZE"
        :total="wishlist?.total ?? 0"
        @change="changePage"
      />
    </div>
  </section>
</template>
