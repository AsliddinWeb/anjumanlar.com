<script setup lang="ts">
import type { BookList, OrderCheckout } from "~/types/api";
import { formatPrice } from "~/composables/useLocaleText";
import { apiErrorMessage } from "~/composables/useAuth";

const { t } = useI18n();
const localePath = useLocalePath();
const { localised } = useLocaleText();
const { isAuthenticated } = useAuth();
const api = useApi();
const cart = useCartStore();

useSiteSeo({ title: t("cart.title"), noindex: true });

// Discount sum is the difference between list and effective price across
// items. We compute it explicitly so the summary can display "you save X".
const grossSubtotal = computed(() =>
  cart.items.reduce((sum, b) => (b.is_free ? sum : sum + b.price), 0),
);
const discountTotal = computed(() => grossSubtotal.value - cart.subtotal);
const freeCount = computed(() => cart.items.filter((b) => b.is_free).length);
const paidCount = computed(() => cart.items.length - freeCount.value);

const checkoutPending = ref(false);
const checkoutError = ref<string | null>(null);

async function onCheckout() {
  if (cart.count === 0 || checkoutPending.value) return;
  if (!isAuthenticated.value) {
    await navigateTo(localePath("/auth/login?redirect=/cart"));
    return;
  }

  checkoutPending.value = true;
  checkoutError.value = null;
  try {
    const response = await api<OrderCheckout>("/orders", {
      method: "POST",
      body: {
        book_ids: cart.items.map((b) => b.id),
        payment_method: "payme",
      },
    });
    const orderId = response.order.id;
    if (response.payment_url) {
      cart.clear();
      window.location.href = response.payment_url;
      return;
    }
    cart.clear();
    await navigateTo(localePath(`/checkout/success?order=${orderId}`));
  }
  catch (err) {
    checkoutError.value = apiErrorMessage(err, t("cart.error_generic"));
  }
  finally {
    checkoutPending.value = false;
  }
}

// Recommended books — shown ONLY when cart is empty so the page feels
// alive instead of dead-end. Skipped (and silently swallowed) when the
// backend can't be reached, to avoid breaking the empty-cart layout.
const { data: recommendedRaw } = await useAsyncData("cart:recommended", () =>
  api<BookList>("/books", {
    query: { sort: "-sales_count", page_size: 4 },
  }).catch(() => null),
);
const recommended = computed(() =>
  ((recommendedRaw.value as BookList | null)?.items ?? []).slice(0, 4),
);
</script>

<template>
  <section class="bg-bg">
    <!-- Page header -->
    <header class="border-b border-border">
      <div class="max-w-6xl mx-auto px-4 py-6 md:py-8 flex items-end justify-between gap-3 flex-wrap">
        <div class="flex items-center gap-3">
          <span class="h-10 w-10 rounded-md bg-primary/10 text-primary inline-flex items-center justify-center shrink-0">
            <Icon name="cart" class="h-5 w-5" />
          </span>
          <div>
            <h1 class="font-serif text-2xl md:text-3xl text-ink leading-tight">
              {{ t("cart.title") }}
            </h1>
            <p class="text-sm text-ink-secondary">
              {{ cart.count === 0 ? t("cart.subtitle") : t("cart.items_count", { n: cart.count }) }}
            </p>
          </div>
        </div>
        <button
          v-if="cart.count > 0"
          type="button"
          class="inline-flex items-center gap-1 text-xs text-ink-tertiary hover:text-error transition-colors"
          @click="cart.clear()"
        >
          <Icon name="trash" class="h-3.5 w-3.5" />
          {{ t("cart.clear") }}
        </button>
      </div>
    </header>

    <div class="max-w-6xl mx-auto px-4 py-8 md:py-10">
      <!-- EMPTY -->
      <template v-if="cart.count === 0">
        <div class="max-w-2xl mx-auto">
          <UiEmptyState
            icon="cart"
            :title="t('cart.empty_title')"
            :description="t('cart.empty_body')"
          >
            <div class="flex flex-wrap items-center justify-center gap-2">
              <UiButton :to="localePath('/books')">
                <Icon name="book" class="h-4 w-4" />
                {{ t("cart.empty_cta_browse") }}
              </UiButton>
              <UiButton variant="ghost" :to="localePath('/account/wishlist')">
                <Icon name="heart" class="h-4 w-4" />
                {{ t("cart.empty_cta_wishlist") }}
              </UiButton>
            </div>
          </UiEmptyState>
        </div>

        <!-- Recommended -->
        <section v-if="recommended.length > 0" class="mt-12 space-y-5">
          <div class="flex items-end justify-between gap-3">
            <div>
              <h2 class="font-serif text-2xl text-ink leading-tight">
                {{ t("cart.recommended_title") }}
              </h2>
              <p class="text-sm text-ink-secondary mt-1">{{ t("cart.recommended_subtitle") }}</p>
            </div>
            <NuxtLink
              :to="localePath('/books')"
              class="hidden sm:inline-flex items-center gap-1 text-sm text-primary hover:underline"
            >
              {{ t("cart.see_all") }}
              <Icon name="arrow-right" class="h-4 w-4" />
            </NuxtLink>
          </div>
          <div class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-5">
            <BookCard v-for="b in recommended" :key="b.id" :book="b" />
          </div>
        </section>
      </template>

      <!-- HAS ITEMS -->
      <div v-else class="grid lg:grid-cols-[1fr_360px] gap-6 lg:gap-8">
        <!-- Items list -->
        <ul class="space-y-3">
          <li
            v-for="book in cart.items"
            :key="book.id"
            class="group relative flex gap-4 rounded-md border border-border bg-bg-card p-3 md:p-4 hover:border-primary/40 transition-colors"
          >
            <NuxtLink
              :to="localePath(`/books/${book.slug}`)"
              class="w-20 md:w-24 shrink-0 rounded overflow-hidden ring-1 ring-border"
            >
              <BookCover :src="book.cover_url" :alt="localised(book.title, book.slug)" />
            </NuxtLink>

            <div class="min-w-0 flex-1 flex flex-col">
              <div class="min-w-0 pr-8">
                <NuxtLink
                  :to="localePath(`/books/${book.slug}`)"
                  class="block font-serif text-base md:text-lg text-ink hover:text-primary leading-snug line-clamp-2"
                >
                  {{ localised(book.title, book.slug) }}
                </NuxtLink>
                <NuxtLink
                  :to="localePath(`/authors/${book.author.slug}`)"
                  class="inline-flex items-center gap-1 text-xs text-ink-secondary hover:text-primary mt-1"
                >
                  <Icon name="user-circle" class="h-3 w-3" />
                  {{ book.author.display_name }}
                </NuxtLink>
              </div>

              <div class="mt-auto pt-2 flex items-end justify-between gap-2">
                <BookPriceTag
                  :price="book.price"
                  :discount-price="book.discount_price"
                  :is-free="book.is_free"
                  size="md"
                />
              </div>
            </div>

            <button
              type="button"
              class="absolute top-2 right-2 h-8 w-8 inline-flex items-center justify-center rounded-md text-ink-tertiary hover:bg-error/10 hover:text-error transition-colors"
              :aria-label="t('cart.remove')"
              @click="cart.remove(book.id)"
            >
              <Icon name="close" class="h-4 w-4" />
            </button>
          </li>
        </ul>

        <!-- Summary (sticky on desktop) -->
        <aside>
          <div class="lg:sticky lg:top-20 rounded-lg border border-border bg-bg-card shadow-sm overflow-hidden">
            <div class="p-5 space-y-4">
              <h2 class="font-serif text-lg text-ink">{{ t("cart.summary_title") }}</h2>

              <dl class="space-y-2.5 text-sm">
                <div class="flex items-center justify-between">
                  <dt class="text-ink-secondary inline-flex items-center gap-1.5">
                    <Icon name="book" class="h-3.5 w-3.5 text-ink-tertiary" />
                    {{ t("cart.items_in_cart") }}
                  </dt>
                  <dd class="text-ink tabular-nums">{{ cart.count }}</dd>
                </div>
                <div v-if="freeCount > 0" class="flex items-center justify-between">
                  <dt class="text-ink-secondary inline-flex items-center gap-1.5">
                    <Icon name="gift" class="h-3.5 w-3.5 text-success" />
                    {{ t("cart.free_items") }}
                  </dt>
                  <dd class="text-success tabular-nums">{{ freeCount }}</dd>
                </div>
                <div class="flex items-center justify-between">
                  <dt class="text-ink-secondary">{{ t("cart.subtotal") }}</dt>
                  <dd class="text-ink tabular-nums">{{ formatPrice(grossSubtotal) }}</dd>
                </div>
                <div v-if="discountTotal > 0" class="flex items-center justify-between">
                  <dt class="text-success inline-flex items-center gap-1.5">
                    <Icon name="sparkles" class="h-3.5 w-3.5" />
                    {{ t("cart.discount") }}
                  </dt>
                  <dd class="text-success tabular-nums">−{{ formatPrice(discountTotal) }}</dd>
                </div>
              </dl>

              <div class="pt-3 border-t border-border flex items-baseline justify-between gap-3">
                <span class="text-ink font-medium">{{ t("cart.total") }}</span>
                <span class="font-serif text-2xl text-primary tabular-nums">
                  {{ formatPrice(cart.subtotal) }}
                </span>
              </div>

              <div
                v-if="!isAuthenticated"
                class="flex items-start gap-2 p-3 rounded-md bg-warning/10 border border-warning/30 text-xs text-warning"
              >
                <Icon name="warning" class="h-4 w-4 shrink-0 mt-0.5" />
                <span>{{ t("cart.checkout_login_required") }}</span>
              </div>

              <p v-if="checkoutError" class="flex items-start gap-1.5 text-sm text-error">
                <Icon name="warning-solid" class="h-4 w-4 mt-0.5 shrink-0" />
                <span>{{ checkoutError }}</span>
              </p>

              <UiButton
                size="lg"
                block
                :loading="checkoutPending"
                :disabled="checkoutPending"
                @click="onCheckout"
              >
                <Icon name="lock" class="h-4 w-4" />
                {{ checkoutPending ? t("checkout.redirecting") : (paidCount > 0 ? t("cart.checkout") : t("cart.checkout_free")) }}
              </UiButton>

              <NuxtLink
                :to="localePath('/books')"
                class="inline-flex items-center justify-center gap-1 text-sm text-ink-secondary hover:text-primary w-full"
              >
                <Icon name="arrow-left" class="h-4 w-4" />
                {{ t("cart.continue_shopping") }}
              </NuxtLink>
            </div>

            <!-- Trust footer -->
            <div class="border-t border-border bg-bg-secondary/40 px-5 py-3 space-y-1.5 text-xs text-ink-tertiary">
              <div class="flex items-center gap-1.5">
                <Icon name="check-circle" class="h-3.5 w-3.5 text-success shrink-0" />
                <span>{{ t("cart.trust.instant") }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <Icon name="check-circle" class="h-3.5 w-3.5 text-success shrink-0" />
                <span>{{ t("cart.trust.secure") }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <Icon name="check-circle" class="h-3.5 w-3.5 text-success shrink-0" />
                <span>{{ t("cart.trust.forever") }}</span>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  </section>
</template>
