<script setup lang="ts">
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({ layout: "auth", middleware: "guest" });

const { t, locale } = useI18n();
const localePath = useLocalePath();
const auth = useAuthStore();

useHead({ title: t("auth.register.title") });

const full_name = ref("");
const email = ref("");
const password = ref("");
const submitting = ref(false);
const error = ref<string | null>(null);
const success = ref(false);

async function onSubmit() {
  submitting.value = true;
  error.value = null;
  try {
    await auth.register({
      email: email.value,
      password: password.value,
      full_name: full_name.value,
      preferred_locale: locale.value,
    });
    success.value = true;
  } catch (err) {
    error.value = apiErrorMessage(err, t("common.error"));
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <div>
    <template v-if="success">
      <h1 class="text-2xl font-serif text-ink mb-3">
        {{ t("auth.register.success_title") }}
      </h1>
      <p class="text-sm text-ink-secondary mb-6">
        {{ t("auth.register.success_body", { email }) }}
      </p>
      <NuxtLink
        :to="localePath('/auth/login')"
        class="inline-block px-4 py-2 rounded border border-border text-ink-secondary hover:border-primary hover:text-primary"
      >
        {{ t("auth.login.title") }}
      </NuxtLink>
    </template>

    <template v-else>
      <h1 class="text-2xl font-serif text-ink mb-1">
        {{ t("auth.register.title") }}
      </h1>
      <p class="text-sm text-ink-secondary mb-6">
        {{ t("auth.register.subtitle") }}
      </p>

      <form class="space-y-4" @submit.prevent="onSubmit">
        <label class="block">
          <span class="block text-sm text-ink-secondary mb-1">
            {{ t("auth.register.full_name") }}
          </span>
          <input
            v-model="full_name"
            type="text"
            required
            autocomplete="name"
            class="w-full px-3 py-2 rounded border border-border bg-bg-card text-ink focus:outline-none focus:border-primary"
          >
        </label>

        <label class="block">
          <span class="block text-sm text-ink-secondary mb-1">
            {{ t("auth.register.email") }}
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
            {{ t("auth.register.password") }}
          </span>
          <input
            v-model="password"
            type="password"
            required
            autocomplete="new-password"
            minlength="8"
            class="w-full px-3 py-2 rounded border border-border bg-bg-card text-ink focus:outline-none focus:border-primary"
          >
          <span class="block text-xs text-ink-tertiary mt-1">
            {{ t("auth.register.password_hint") }}
          </span>
        </label>

        <p v-if="error" class="text-sm text-error">{{ error }}</p>

        <button
          type="submit"
          :disabled="submitting"
          class="w-full px-4 py-2.5 rounded bg-primary text-ink-inverse hover:bg-primary-hover disabled:opacity-60 disabled:cursor-not-allowed transition-colors shadow-sm"
        >
          {{ submitting ? t("auth.register.submitting") : t("auth.register.submit") }}
        </button>
      </form>

      <p class="mt-6 text-sm text-ink-secondary text-center">
        {{ t("auth.register.have_account") }}
        <NuxtLink :to="localePath('/auth/login')" class="text-primary hover:underline">
          {{ t("auth.register.login_link") }}
        </NuxtLink>
      </p>
    </template>
  </div>
</template>
