<script setup lang="ts">
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({ layout: "auth" });

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const api = useApi();

useHead({ title: t("auth.verify.title") });

type State = "verifying" | "success" | "error";
const state = ref<State>("verifying");
const error = ref<string | null>(null);

onMounted(async () => {
  const token = route.query.token as string | undefined;
  if (!token) {
    state.value = "error";
    error.value = t("auth.verify.error");
    return;
  }
  try {
    await api("/auth/verify-email", {
      method: "POST",
      body: { token },
    });
    state.value = "success";
  } catch (err) {
    error.value = apiErrorMessage(err, t("auth.verify.error"));
    state.value = "error";
  }
});
</script>

<template>
  <div class="text-center">
    <h1 class="text-2xl font-serif text-ink mb-4">{{ t("auth.verify.title") }}</h1>

    <p v-if="state === 'verifying'" class="text-ink-secondary">
      {{ t("auth.verify.in_progress") }}
    </p>

    <template v-else-if="state === 'success'">
      <p class="text-success mb-6">{{ t("auth.verify.success") }}</p>
      <NuxtLink
        :to="localePath('/auth/login')"
        class="inline-block px-4 py-2 rounded bg-primary text-ink-inverse hover:bg-primary-hover"
      >
        {{ t("auth.verify.go_to_login") }}
      </NuxtLink>
    </template>

    <template v-else>
      <p class="text-error mb-6">{{ error || t("auth.verify.error") }}</p>
      <NuxtLink
        :to="localePath('/auth/login')"
        class="inline-block px-4 py-2 rounded border border-border text-ink-secondary hover:border-primary hover:text-primary"
      >
        {{ t("auth.verify.go_to_login") }}
      </NuxtLink>
    </template>
  </div>
</template>
