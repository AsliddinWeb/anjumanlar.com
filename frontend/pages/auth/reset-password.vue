<script setup lang="ts">
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({ layout: "auth", middleware: "guest" });

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const api = useApi();

useHead({ title: t("auth.reset.title") });

const token = computed(() => (route.query.token as string | undefined) || "");
const new_password = ref("");
const submitting = ref(false);
const error = ref<string | null>(null);
const success = ref(false);

async function onSubmit() {
  if (!token.value) {
    error.value = t("auth.reset.invalid_token");
    return;
  }
  submitting.value = true;
  error.value = null;
  try {
    await api("/auth/reset-password", {
      method: "POST",
      body: { token: token.value, new_password: new_password.value },
    });
    success.value = true;
  } catch (err) {
    error.value = apiErrorMessage(err, t("auth.reset.invalid_token"));
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-serif text-ink mb-1">{{ t("auth.reset.title") }}</h1>
    <p class="text-sm text-ink-secondary mb-6">{{ t("auth.reset.subtitle") }}</p>

    <template v-if="success">
      <p
        class="text-sm text-ink-secondary p-3 rounded border border-border bg-bg-secondary mb-4"
      >
        {{ t("auth.reset.success") }}
      </p>
      <NuxtLink
        :to="localePath('/auth/login')"
        class="inline-block px-4 py-2 rounded bg-primary text-ink-inverse hover:bg-primary-hover"
      >
        {{ t("auth.reset.go_to_login") }}
      </NuxtLink>
    </template>

    <form v-else class="space-y-4" @submit.prevent="onSubmit">
      <label class="block">
        <span class="block text-sm text-ink-secondary mb-1">
          {{ t("auth.reset.new_password") }}
        </span>
        <input
          v-model="new_password"
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
        :disabled="submitting || !token"
        class="w-full px-4 py-2.5 rounded bg-primary text-ink-inverse hover:bg-primary-hover disabled:opacity-60 transition-colors shadow-sm"
      >
        {{ submitting ? t("auth.reset.submitting") : t("auth.reset.submit") }}
      </button>
    </form>
  </div>
</template>
