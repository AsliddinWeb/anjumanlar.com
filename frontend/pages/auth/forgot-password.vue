<script setup lang="ts">
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({ layout: "auth", middleware: "guest" });

const { t } = useI18n();
const localePath = useLocalePath();
const api = useApi();

useHead({ title: t("auth.forgot.title") });

const email = ref("");
const submitting = ref(false);
const error = ref<string | null>(null);
const success = ref(false);

async function onSubmit() {
  submitting.value = true;
  error.value = null;
  try {
    await api("/auth/forgot-password", {
      method: "POST",
      body: { email: email.value },
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
    <h1 class="text-2xl font-serif text-ink mb-1">{{ t("auth.forgot.title") }}</h1>
    <p class="text-sm text-ink-secondary mb-6">{{ t("auth.forgot.subtitle") }}</p>

    <p
      v-if="success"
      class="text-sm text-ink-secondary p-3 rounded border border-border bg-bg-secondary"
    >
      {{ t("auth.forgot.success") }}
    </p>

    <form v-else class="space-y-4" @submit.prevent="onSubmit">
      <label class="block">
        <span class="block text-sm text-ink-secondary mb-1">
          {{ t("auth.forgot.email") }}
        </span>
        <input
          v-model="email"
          type="email"
          required
          autocomplete="email"
          class="w-full px-3 py-2 rounded border border-border bg-bg-card text-ink focus:outline-none focus:border-primary"
        >
      </label>

      <p v-if="error" class="text-sm text-error">{{ error }}</p>

      <button
        type="submit"
        :disabled="submitting"
        class="w-full px-4 py-2.5 rounded bg-primary text-ink-inverse hover:bg-primary-hover disabled:opacity-60 transition-colors shadow-sm"
      >
        {{ submitting ? t("auth.forgot.submitting") : t("auth.forgot.submit") }}
      </button>
    </form>

    <p class="mt-6 text-sm text-center">
      <NuxtLink :to="localePath('/auth/login')" class="text-primary hover:underline">
        {{ t("auth.forgot.back_to_login") }}
      </NuxtLink>
    </p>
  </div>
</template>
