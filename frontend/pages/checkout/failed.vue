<script setup lang="ts">
const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();

useSiteSeo({ title: t("checkout.failed_title"), noindex: true });

const reason = computed(() => (route.query.reason as string) || "");

const reasonText = computed(() => {
  // Backend may pass a Payme/Click error code as `?reason=...`.
  // Show it verbatim if we don't recognise it.
  if (!reason.value) return null;
  const key = `checkout.failure_reasons.${reason.value}`;
  const translated = t(key);
  return translated === key ? reason.value : translated;
});
</script>

<template>
  <section class="bg-bg">
    <div class="max-w-2xl mx-auto px-4 py-12 md:py-16">
      <!-- Hero -->
      <div class="text-center space-y-5 mb-8">
        <div class="inline-flex h-20 w-20 items-center justify-center rounded-full bg-error/10">
          <Icon name="warning-solid" class="h-10 w-10 text-error" />
        </div>
        <div class="space-y-2">
          <h1 class="font-serif text-3xl md:text-4xl text-ink leading-tight tracking-tight">
            {{ t("checkout.failed_title") }}
          </h1>
          <p class="text-ink-secondary leading-relaxed max-w-lg mx-auto">
            {{ t("checkout.failed_body") }}
          </p>
        </div>
      </div>

      <!-- Concrete reason -->
      <div
        v-if="reasonText"
        class="rounded-md border border-error/30 bg-error/5 p-4 flex items-start gap-3 mb-6"
      >
        <Icon name="warning-solid" class="h-5 w-5 text-error shrink-0 mt-0.5" />
        <div class="text-sm">
          <p class="text-ink font-medium">{{ t("checkout.failure_label") }}</p>
          <p class="text-ink-secondary mt-0.5">{{ reasonText }}</p>
        </div>
      </div>

      <!-- Common reasons -->
      <section class="rounded-md border border-border bg-bg-card p-5 space-y-3 mb-6">
        <h2 class="text-sm uppercase tracking-wider text-ink-tertiary">
          {{ t("checkout.common_reasons") }}
        </h2>
        <ul class="space-y-2 text-sm">
          <li class="flex items-start gap-2.5">
            <Icon name="warning" class="h-4 w-4 text-warning shrink-0 mt-0.5" />
            <span class="text-ink-secondary">{{ t("checkout.reason_insufficient") }}</span>
          </li>
          <li class="flex items-start gap-2.5">
            <Icon name="warning" class="h-4 w-4 text-warning shrink-0 mt-0.5" />
            <span class="text-ink-secondary">{{ t("checkout.reason_3ds") }}</span>
          </li>
          <li class="flex items-start gap-2.5">
            <Icon name="warning" class="h-4 w-4 text-warning shrink-0 mt-0.5" />
            <span class="text-ink-secondary">{{ t("checkout.reason_blocked") }}</span>
          </li>
          <li class="flex items-start gap-2.5">
            <Icon name="warning" class="h-4 w-4 text-warning shrink-0 mt-0.5" />
            <span class="text-ink-secondary">{{ t("checkout.reason_network") }}</span>
          </li>
        </ul>
      </section>

      <!-- CTAs -->
      <div class="flex flex-wrap justify-center gap-2">
        <UiButton :to="localePath('/cart')" size="lg">
          <Icon name="arrow-path" class="h-4 w-4" />
          {{ t("checkout.try_again") }}
        </UiButton>
        <UiButton variant="ghost" :to="localePath('/account/orders')" size="lg">
          <Icon name="clipboard-check" class="h-4 w-4" />
          {{ t("checkout.go_orders") }}
        </UiButton>
      </div>

      <!-- Help -->
      <p class="text-center text-xs text-ink-tertiary mt-6">
        {{ t("checkout.need_help") }}
        <a
          href="mailto:info@monografiya.com"
          class="text-primary hover:underline"
        >info@monografiya.com</a>
      </p>
    </div>
  </section>
</template>
