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
    await navigateTo(localePath(`/checkout/success?order=${response.order.id}`));
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
