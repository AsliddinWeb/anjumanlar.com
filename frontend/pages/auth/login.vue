<script setup lang="ts">
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({ layout: "auth", middleware: "guest" });

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const auth = useAuthStore();

useHead({ title: t("auth.login.title") });

const email = ref("");
const password = ref("");
const submitting = ref(false);
const error = ref<string | null>(null);

async function onSubmit() {
  submitting.value = true;
  error.value = null;
  try {
    await auth.login(email.value, password.value);
    const redirect = (route.query.redirect as string) || localePath("/account");
    await navigateTo(redirect);
  } catch (err) {
    error.value = apiErrorMessage(err, t("auth.login.error_generic"));
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-serif text-ink mb-1">{{ t("auth.login.title") }}</h1>
    <p class="text-sm text-ink-secondary mb-6">{{ t("auth.login.subtitle") }}</p>

    <form class="space-y-4" @submit.prevent="onSubmit">
      <label class="block">
        <span class="block text-sm text-ink-secondary mb-1">
          {{ t("auth.login.email") }}
        </span>
        <input
          v-model="email"
          type="email"
          required
          autocomplete="email"
          class="w-full px-3 py-2 rounded border border-border bg-bg-card text-ink focus:outline-none focus:border-primary"
        >
      </label>

      <label class="block">
        <span class="block text-sm text-ink-secondary mb-1">
          {{ t("auth.login.password") }}
        </span>
        <input
          v-model="password"
          type="password"
          required
          autocomplete="current-password"
          minlength="1"
          class="w-full px-3 py-2 rounded border border-border bg-bg-card text-ink focus:outline-none focus:border-primary"
        >
      </label>

      <p v-if="error" class="text-sm text-error">{{ error }}</p>

      <button
        type="submit"
        :disabled="submitting"
        class="w-full px-4 py-2.5 rounded bg-primary text-ink-inverse hover:bg-primary-hover disabled:opacity-60 disabled:cursor-not-allowed transition-colors shadow-sm"
      >
        {{ submitting ? t("auth.login.submitting") : t("auth.login.submit") }}
      </button>
    </form>

    <div class="mt-6 flex items-center justify-between text-sm">
      <NuxtLink
        :to="localePath('/auth/forgot-password')"
        class="text-primary hover:underline"
      >
        {{ t("auth.login.forgot_link") }}
      </NuxtLink>
      <div class="text-ink-secondary">
        {{ t("auth.login.no_account") }}
        <NuxtLink :to="localePath('/auth/register')" class="text-primary hover:underline">
          {{ t("auth.login.register_link") }}
        </NuxtLink>
      </div>
    </div>
  </div>
</template>
