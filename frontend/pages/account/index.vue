<script setup lang="ts">
definePageMeta({ middleware: "auth" });

const { t } = useI18n();
const localePath = useLocalePath();
const { user, isVerified, hasRole, logout } = useAuth();

useHead({ title: t("account.title") });

const isAuthor = computed(() => hasRole("author"));

async function onLogout() {
  await logout();
  await navigateTo(localePath("/"));
}
</script>

<template>
  <section v-if="user" class="max-w-2xl mx-auto px-4 py-12">
    <h1 class="text-2xl font-serif text-ink mb-2">
      {{ t("account.welcome", { name: user.full_name }) }}
    </h1>
    <p class="text-ink-secondary mb-6">{{ user.email }}</p>

    <div
      v-if="!isVerified"
      class="mb-6 flex items-start gap-2 p-3 rounded border border-warning/40 bg-warning/10 text-sm text-ink"
    >
      <Icon name="warning-solid" class="h-4 w-4 mt-0.5 shrink-0 text-warning" />
      <span>{{ t("account.email_unverified") }}</span>
    </div>

    <dl class="grid grid-cols-2 gap-3 text-sm mb-8">
      <dt class="text-ink-tertiary">{{ t("account.role") }}</dt>
      <dd class="text-ink">{{ user.role }}</dd>
    </dl>

    <nav class="grid sm:grid-cols-2 gap-3 mb-8">
      <NuxtLink
        :to="localePath('/account/library')"
        class="rounded border border-border bg-bg-card p-4 hover:border-primary hover:shadow-sm flex items-center gap-3"
      >
        <Icon name="library" class="h-7 w-7 text-primary shrink-0" />
        <div>
          <div class="font-medium text-ink">{{ t("library.title") }}</div>
          <div class="text-xs text-ink-tertiary">{{ t("library.subtitle") }}</div>
        </div>
      </NuxtLink>
      <NuxtLink
        :to="localePath('/account/orders')"
        class="rounded border border-border bg-bg-card p-4 hover:border-primary hover:shadow-sm flex items-center gap-3"
      >
        <Icon name="clipboard-check" class="h-7 w-7 text-primary shrink-0" />
        <div>
          <div class="font-medium text-ink">{{ t("orders.title") }}</div>
          <div class="text-xs text-ink-tertiary">{{ t("orders.subtitle") }}</div>
        </div>
      </NuxtLink>
      <NuxtLink
        :to="localePath('/account/wishlist')"
        class="rounded border border-border bg-bg-card p-4 hover:border-primary hover:shadow-sm flex items-center gap-3"
      >
        <Icon name="heart-solid" class="h-7 w-7 text-error shrink-0" />
        <div>
          <div class="font-medium text-ink">{{ t("nav.wishlist") }}</div>
          <div class="text-xs text-ink-tertiary">{{ t("wishlist.subtitle") }}</div>
        </div>
      </NuxtLink>
      <NuxtLink
        :to="localePath('/cart')"
        class="rounded border border-border bg-bg-card p-4 hover:border-primary hover:shadow-sm flex items-center gap-3"
      >
        <Icon name="cart" class="h-7 w-7 text-primary shrink-0" />
        <div>
          <div class="font-medium text-ink">{{ t("cart.title") }}</div>
          <div class="text-xs text-ink-tertiary">{{ t("cart.subtitle") }}</div>
        </div>
      </NuxtLink>
      <template v-if="isAuthor">
        <NuxtLink
          :to="localePath('/account/balance')"
          class="rounded border border-border bg-bg-card p-4 hover:border-primary hover:shadow-sm flex items-center gap-3"
        >
          <Icon name="currency" class="h-7 w-7 text-success shrink-0" />
          <div>
            <div class="font-medium text-ink">{{ t("balance.title") }}</div>
            <div class="text-xs text-ink-tertiary">{{ t("balance.subtitle") }}</div>
          </div>
        </NuxtLink>
        <NuxtLink
          :to="localePath('/account/withdrawals')"
          class="rounded border border-border bg-bg-card p-4 hover:border-primary hover:shadow-sm flex items-center gap-3"
        >
          <Icon name="money" class="h-7 w-7 text-warning shrink-0" />
          <div>
            <div class="font-medium text-ink">{{ t("withdrawals.title") }}</div>
            <div class="text-xs text-ink-tertiary">{{ t("withdrawals.subtitle") }}</div>
          </div>
        </NuxtLink>
      </template>
    </nav>

    <div class="flex gap-3">
      <button
        type="button"
        class="px-4 py-2 rounded border border-border text-ink-secondary hover:border-primary hover:text-primary"
        @click="onLogout"
      >
        {{ t("account.logout") }}
      </button>
    </div>
  </section>
</template>
