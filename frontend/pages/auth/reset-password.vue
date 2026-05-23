<script setup lang="ts">
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({ layout: "auth", middleware: "guest" });

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const api = useApi();

useSiteSeo({
  title: t("auth.reset.title"),
  description: t("auth.reset.subtitle"),
  noindex: true,
});

const token = computed(() => (route.query.token as string | undefined) || "");
const newPassword = ref("");
const submitting = ref(false);
const error = ref<string | null>(null);
const success = ref(false);

const passwordError = ref<string | null>(null);

function validatePassword() {
  if (!newPassword.value) {
    passwordError.value = null;
    return;
  }
  if (newPassword.value.length < 8) {
    passwordError.value = t("auth.validation.password_too_short");
    return;
  }
  if (
    !/[A-Z]/.test(newPassword.value)
    || !/[a-z]/.test(newPassword.value)
    || !/\d/.test(newPassword.value)
  ) {
    passwordError.value = t("auth.validation.password_weak");
    return;
  }
  passwordError.value = null;
}

const canSubmit = computed(
  () =>
    token.value
    && newPassword.value
    && !passwordError.value
    && !submitting.value,
);

async function onSubmit() {
  validatePassword();
  if (passwordError.value) return;
  if (!token.value) {
    error.value = t("auth.reset.invalid_token");
    return;
  }
  submitting.value = true;
  error.value = null;
  try {
    await api("/auth/reset-password", {
      method: "POST",
      body: { token: token.value, new_password: newPassword.value },
    });
    success.value = true;
  }
  catch (err) {
    error.value = apiErrorMessage(err, t("auth.reset.invalid_token"));
  }
  finally {
    submitting.value = false;
  }
}
</script>

<template>
  <AuthCard
    v-if="success"
    icon="check-circle-solid"
    :title="t('auth.reset.title')"
    :subtitle="t('auth.reset.success')"
  >
    <NuxtLink
      :to="localePath('/auth/login')"
      class="block w-full text-center px-4 py-2.5 rounded bg-primary text-ink-inverse hover:bg-primary-hover transition-colors shadow-sm"
    >
      {{ t("auth.reset.go_to_login") }}
    </NuxtLink>
  </AuthCard>

  <AuthCard
    v-else
    icon="lock"
    :title="t('auth.reset.title')"
    :subtitle="t('auth.reset.subtitle')"
  >
    <AuthAlert v-if="!token" tone="warning">
      {{ t("auth.reset.invalid_token") }}
    </AuthAlert>

    <form v-else class="space-y-4" novalidate @submit.prevent="onSubmit">
      <AuthAlert v-if="error">
        {{ error }}
      </AuthAlert>

      <PasswordField
        v-model="newPassword"
        :label="t('auth.reset.new_password')"
        :hint="t('auth.register.password_hint')"
        :error="passwordError ?? undefined"
        autocomplete="new-password"
        :minlength="8"
        show-strength
        required
        autofocus
        @update:model-value="validatePassword"
      />

      <AuthSubmit
        :loading="submitting"
        :disabled="!canSubmit"
        :label="t('auth.reset.submit')"
        :loading-label="t('auth.reset.submitting')"
      />
    </form>

    <template #footer>
      <NuxtLink
        :to="localePath('/auth/login')"
        class="inline-flex items-center gap-1 text-primary hover:underline"
      >
        <Icon name="arrow-left" class="h-4 w-4" />
        {{ t("auth.forgot.back_to_login") }}
      </NuxtLink>
    </template>
  </AuthCard>
</template>
