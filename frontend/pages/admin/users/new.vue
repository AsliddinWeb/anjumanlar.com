<script setup lang="ts">
import type { UserPublic } from "~/types/api";
import type { UserFormValue } from "~/components/admin/UserForm.vue";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin"],
});

const { t } = useI18n();
const localePath = useLocalePath();
const router = useRouter();
const api = useApi();
const toast = useToast();

useHead({ title: t("admin.users.new_page_title") });

const form = ref<UserFormValue>({
  email: "",
  full_name: "",
  role: "reader",
  status: "active",
  password: "",
});

const submitting = ref(false);
const error = ref<string | null>(null);

async function submit() {
  error.value = null;
  if (!form.value.email.trim() || !form.value.full_name.trim() || !form.value.password) {
    error.value = t("admin.users.errors.missing_required");
    return;
  }

  submitting.value = true;
  try {
    const created = await api<UserPublic>("/admin/users", {
      method: "POST",
      body: {
        email: form.value.email.trim(),
        full_name: form.value.full_name.trim(),
        role: form.value.role,
        status: form.value.status,
        password: form.value.password,
      },
    });
    toast.success(t("admin.users.create_success", { name: created.full_name }));
    await router.push(localePath("/admin/users"));
  }
  catch (err) {
    error.value = apiErrorMessage(err, t("common.error"));
    toast.error(error.value);
  }
  finally {
    submitting.value = false;
  }
}
</script>

<template>
  <section>
    <AdminPageHeader
      :title="t('admin.users.new_page_title')"
      :description="t('admin.users.new_page_subtitle')"
      icon="user-plus"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('admin.users.title'), to: localePath('/admin/users') },
        { label: t('admin.users.new_page_title') },
      ]"
    />

    <UserForm
      v-model="form"
      :loading="submitting"
      :error="error"
      :submit-label="t('admin.actions.create')"
      :cancel-to="localePath('/admin/users')"
      @submit="submit"
    />
  </section>
</template>
