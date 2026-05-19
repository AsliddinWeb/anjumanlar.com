<script setup lang="ts">
definePageMeta({ middleware: "auth" });

const { t } = useI18n();
const localePath = useLocalePath();
const { user, isVerified, logout } = useAuth();

useHead({ title: t("account.title") });

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
      class="mb-6 p-3 rounded border border-warning/40 bg-warning/10 text-sm text-ink"
    >
      ⚠ {{ t("account.email_unverified") }}
    </div>

    <dl class="grid grid-cols-2 gap-3 text-sm mb-8">
      <dt class="text-ink-tertiary">{{ t("account.role") }}</dt>
      <dd class="text-ink">{{ user.role }}</dd>
    </dl>

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
