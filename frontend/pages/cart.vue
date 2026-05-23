<script setup lang="ts">
import type { OrderCheckout } from "~/types/api";
import { formatPrice } from "~/composables/useLocaleText";
import { apiErrorMessage } from "~/composables/useAuth";

const { t } = useI18n();
const localePath = useLocalePath();
const { localised } = useLocaleText();
const { isAuthenticated } = useAuth();
const api = useApi();
const cart = useCartStore();

useHead({ title: t("cart.title") });

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

    // Free order or Payme not configured — order is already pending,
    // route the user to the success page (the post-purchase flow will
    // run from the webhook side once real Payme is wired up).
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
</script>

<template>
  <section class="max-w-4xl mx-auto px-4 py-8 space-y-6">
    <header class="flex items-end justify-between gap-3">
      <div>
        <h1 class="font-serif text-3xl text-ink">{{ t("cart.title") }}</h1>
        <p class="text-sm text-ink-secondary">{{ t("cart.subtitle") }}</p>
      </div>
      <button
        v-if="cart.count > 0"
        type="button"
        class="text-xs text-ink-tertiary hover:text-error"
        @click="cart.clear()"
      >
        {{ t("cart.clear") }}
      </button>
    </header>

    <UiEmptyState
      v-if="cart.count === 0"
      icon="cart"
      :title="t('cart.empty_title')"
      :description="t('cart.empty_body')"
    >
      <UiButton :to="localePath('/books')">
        {{ t("home.hero.cta_browse") }}
      </UiButton>
    </UiEmptyState>

    <template v-else>
      <ul class="space-y-3">
        <li
          v-for="book in cart.items"
          :key="book.id"
          class="flex gap-3 rounded border border-border bg-bg-card p-3"
        >
          <NuxtLink
            :to="localePath(`/books/${book.slug}`)"
            class="w-16 shrink-0"
          >
            <BookCover :src="book.cover_url" :alt="localised(book.title, book.slug)" />
          </NuxtLink>
          <div class="min-w-0 flex-1">
            <NuxtLink
              :to="localePath(`/books/${book.slug}`)"
              class="font-medium text-ink hover:text-primary line-clamp-2"
            >
              {{ localised(book.title, book.slug) }}
            </NuxtLink>
            <p class="text-xs text-ink-secondary truncate mt-0.5">
              {{ book.author.display_name }}
            </p>
            <div class="mt-2 flex items-center justify-between gap-2">
              <BookPriceTag
                :price="book.price"
                :discount-price="book.discount_price"
                :is-free="book.is_free"
                size="sm"
              />
              <button
                type="button"
                class="inline-flex items-center gap-1 text-xs text-ink-tertiary hover:text-error"
                :aria-label="t('cart.remove')"
                @click="cart.remove(book.id)"
              >
                <Icon name="trash" class="h-3.5 w-3.5" />
                {{ t("cart.remove") }}
              </button>
            </div>
          </div>
        </li>
      </ul>

      <div class="rounded border border-border bg-bg-card p-4 space-y-3">
        <div class="flex items-center justify-between text-sm">
          <span class="text-ink-secondary">{{ t("cart.subtotal") }}</span>
          <span class="text-ink">{{ formatPrice(cart.subtotal) }}</span>
        </div>
        <div class="flex items-center justify-between text-base font-medium pt-2 border-t border-border">
          <span class="text-ink">{{ t("cart.total") }}</span>
          <span class="text-primary text-lg">{{ formatPrice(cart.subtotal) }}</span>
        </div>

        <p v-if="!isAuthenticated" class="text-sm text-warning">
          {{ t("cart.checkout_login_required") }}
        </p>
        <p v-if="checkoutError" class="text-sm text-error">{{ checkoutError }}</p>

        <UiButton
          size="lg"
          :block="true"
          :loading="checkoutPending"
          :disabled="checkoutPending"
          @click="onCheckout"
        >
          {{ checkoutPending ? t("checkout.redirecting") : t("cart.checkout") }}
        </UiButton>
      </div>
    </template>
  </section>
</template>
