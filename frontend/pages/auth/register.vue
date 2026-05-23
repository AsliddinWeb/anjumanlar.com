<script setup lang="ts">
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({ layout: "auth", middleware: "guest" });

const { t, locale } = useI18n();
const localePath = useLocalePath();
const auth = useAuthStore();

useSiteSeo({
  title: t("auth.register.title"),
  description: t("auth.register.subtitle"),
  noindex: true,
});

const fullName = ref("");
const email = ref("");
const password = ref("");
const submitting = ref(false);
const error = ref<string | null>(null);
const success = ref(false);

const nameError = ref<string | null>(null);
const emailError = ref<string | null>(null);
const passwordError = ref<string | null>(null);

function validateName() {
  if (!fullName.value) {
    nameError.value = null;
    return;
  }
  nameError.value =
    fullName.value.trim().length >= 2 ? null : t("auth.validation.name_too_short");
}

function validateEmail() {
  if (!email.value) {
    emailError.value = null;
    return;
  }
  emailError.value =
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value) ? null : t("auth.validation.email_invalid");
}

function validatePassword() {
  if (!password.value) {
    passwordError.value = null;
    return;
  }
  if (password.value.length < 8) {
    passwordError.value = t("auth.validation.password_too_short");
    return;
  }
  // Backend rule: upper + lower + digit.
  if (!/[A-Z]/.test(password.value) || !/[a-z]/.test(password.value) || !/\d/.test(password.value)) {
    passwordError.value = t("auth.validation.password_weak");
    return;
  }
  passwordError.value = null;
}

const canSubmit = computed(
  () =>
    fullName.value
    && email.value
    && password.value
    && !nameError.value
    && !emailError.value
    && !passwordError.value
    && !submitting.value,
);

async function onSubmit() {
  validateName();
  validateEmail();
  validatePassword();
  if (nameError.value || emailError.value || passwordError.value) return;

  submitting.value = true;
  error.value = null;
  try {
    await auth.register({
      email: email.value,
      password: password.value,
      full_name: fullName.value,
      preferred_locale: locale.value,
    });
    success.value = true;
  }
  catch (err) {
    error.value = apiErrorMessage(err, t("common.error"));
  }
  finally {
    submitting.value = false;
  }
}
</script>

<template>
  <AuthCard
    v-if="success"
    icon="envelope-open"
    :title="t('auth.register.success_title')"
    :subtitle="t('auth.register.success_body', { email })"
  >
    <NuxtLink
      :to="localePath('/auth/login')"
      class="block w-full text-center px-4 py-2.5 rounded border border-border text-ink-secondary hover:border-primary hover:text-primary"
    >
      {{ t("auth.login.title") }}
    </NuxtLink>
  </AuthCard>

  <AuthCard
    v-else
    icon="sparkles"
    :title="t('auth.register.title')"
    :subtitle="t('auth.register.subtitle')"
  >
    <form class="space-y-4" novalidate @submit.prevent="onSubmit">
      <AuthAlert v-if="error">
        {{ error }}
      </AuthAlert>

      <FormField
        v-model="fullName"
        :label="t('auth.register.full_name')"
        autocomplete="name"
        :error="nameError ?? undefined"
        :placeholder="t('auth.register.full_name')"
        required
        autofocus
        @update:model-value="validateName"
      />

      <FormField
        v-model="email"
        :label="t('auth.register.email')"
        type="email"
        inputmode="email"
        autocomplete="email"
        :error="emailError ?? undefined"
        placeholder="name@example.com"
        required
        @update:model-value="validateEmail"
      />

      <PasswordField
        v-model="password"
        :label="t('auth.register.password')"
        :hint="t('auth.register.password_hint')"
        :error="passwordError ?? undefined"
        autocomplete="new-password"
        :minlength="8"
        show-strength
        required
        @update:model-value="validatePassword"
      />

      <AuthSubmit
        :loading="submitting"
        :disabled="!canSubmit"
        :label="t('auth.register.submit')"
        :loading-label="t('auth.register.submitting')"
      />
    </form>

    <template #footer>
      {{ t("auth.register.have_account") }}
      <NuxtLink
        :to="localePath('/auth/login')"
        class="text-primary hover:underline font-medium"
      >
        {{ t("auth.register.login_link") }}
      </NuxtLink>
    </template>
  </AuthCard>
</template>
