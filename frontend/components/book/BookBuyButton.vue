<script setup lang="ts">
import type { BookPublic, OrderCheckout } from "~/types/api";
import { apiErrorMessage } from "~/composables/useAuth";

const props = withDefaults(
  defineProps<{
    book: BookPublic;
    size?: "sm" | "md" | "lg";
    block?: boolean;
  }>(),
  { size: "lg", block: true },
);

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const api = useApi();
const toast = useToast();
const { isAuthenticated } = useAuth();

const pending = ref(false);

async function onBuy() {
  if (pending.value) return;

  if (!isAuthenticated.value) {
    const redirect = encodeURIComponent(route.fullPath);
    await navigateTo(localePath(`/auth/login?redirect=${redirect}`));
    return;
  }

  pending.value = true;
  try {
    const response = await api<OrderCheckout>("/orders", {
      method: "POST",
      body: {
        book_ids: [props.book.id],
        payment_method: "payme",
      },
    });
    if (response.payment_url) {
      window.location.href = response.payment_url;
      return;
    }
    // payment_url is null for free books or when Payme keys are missing.
    // Free books → land in the library directly. Paid orders → keep the
    // order in pending state and surface a clear error, then send the
    // user to /orders where they can retry once payment is configured.
    if (props.book.is_free || Number(response.order.total) === 0) {
      await navigateTo(localePath(`/checkout/success?order=${response.order.id}`));
      return;
    }
    toast.error(t("book.errors.payment_unavailable"));
    await navigateTo(localePath("/account/orders"));
  }
  catch (err: unknown) {
    const code = (err as { data?: { details?: { code?: string } } })?.data?.details?.code;
    if (code === "already_owned") {
      toast.info(t("book.errors.already_owned"));
      await navigateTo(localePath("/account/library"));
      return;
    }
    toast.error(apiErrorMessage(err, t("book.errors.buy_failed")));
  }
  finally {
    pending.value = false;
  }
}
</script>

<template>
  <UiButton
    :size="size"
    :block="block"
    :loading="pending"
    :disabled="pending"
    @click="onBuy"
  >
    <Icon name="lock" class="h-4 w-4" />
    {{ pending ? t("checkout.redirecting") : t("book.cta.buy_now") }}
  </UiButton>
</template>
