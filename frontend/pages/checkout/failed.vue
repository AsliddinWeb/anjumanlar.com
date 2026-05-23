<script setup lang="ts">
const { t } = useI18n();
const localePath = useLocalePath();

useHead({ title: t("checkout.failed_title") });
</script>

<template>
  <section class="max-w-md mx-auto px-4 py-16 text-center space-y-4">
    <div class="inline-flex h-16 w-16 items-center justify-center rounded-full bg-error/10 text-error">
      <Icon name="warning-solid" class="h-8 w-8" />
    </div>
    <h1 class="font-serif text-2xl text-ink">{{ t("checkout.failed_title") }}</h1>
    <p class="text-ink-secondary">{{ t("checkout.failed_body") }}</p>
    <div class="flex flex-wrap justify-center gap-3 pt-2">
      <UiButton :to="localePath('/cart')">
        {{ t("checkout.try_again") }}
      </UiButton>
      <UiButton variant="ghost" :to="localePath('/account/orders')">
        {{ t("checkout.go_orders") }}
      </UiButton>
    </div>
  </section>
</template>
