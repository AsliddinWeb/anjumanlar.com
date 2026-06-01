<script setup lang="ts">
import type { AdminUserDetail } from "~/types/api";
import type { UserFormValue } from "~/components/admin/UserForm.vue";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin"],
});

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const api = useApi();
const toast = useToast();

const userId = computed(() => route.params.id as string);

const { data: userRaw, refresh } = await useAsyncData(
  `admin:users:edit:${userId.value}`,
  () => api<AdminUserDetail>(`/admin/users/${userId.value}`),
  { server: false },
);
const user = computed(() => userRaw.value as AdminUserDetail | null);

useHead({
  title: computed(() => user.value
    ? `${user.value.full_name} — ${t("admin.users.edit_page_title")}`
    : t("admin.users.edit_page_title"),
  ),
});

function modelFromUser(u: AdminUserDetail): UserFormValue {
  return {
    email: u.email,
    full_name: u.full_name,
    role: u.role,
    status: u.status,
    password: "",
    display_name: u.author_display_name ?? "",
    academic_title: u.author_academic_title ?? "",
    institution: u.author_institution ?? "",
    bio: u.author_bio ?? "",
  };
}

const form = ref<UserFormValue | null>(null);
watch(user, (u) => { if (u && !form.value) form.value = modelFromUser(u); }, { immediate: true });

const submitting = ref(false);
const deleting = ref(false);
const error = ref<string | null>(null);

async function save() {
  if (!form.value || !user.value) return;
  error.value = null;

  if (!form.value.email.trim() || !form.value.full_name.trim()) {
    error.value = t("admin.users.errors.missing_required");
    return;
  }

  submitting.value = true;
  try {
    const isAuthorRole = ["author", "admin", "superadmin"].includes(form.value.role);
    const body: Record<string, unknown> = {
      email: form.value.email.trim(),
      full_name: form.value.full_name.trim(),
      role: form.value.role,
      status: form.value.status,
    };
    if (form.value.password) body.password = form.value.password;
    if (isAuthorRole) {
      body.display_name = form.value.display_name.trim() || form.value.full_name.trim();
      body.academic_title = form.value.academic_title.trim() || null;
      body.institution = form.value.institution.trim() || null;
      body.bio = form.value.bio.trim() || null;
    }

    await api(`/admin/users/${user.value.id}`, { method: "PATCH", body });
    toast.success(t("admin.users.update_success"));
    form.value.password = "";
    await refresh();
  }
  catch (err) {
    error.value = apiErrorMessage(err, t("common.error"));
    toast.error(error.value);
  }
  finally {
    submitting.value = false;
  }
}

const deleteOpen = ref(false);
async function confirmDelete() {
  if (!user.value || deleting.value) return;
  deleting.value = true;
  try {
    await api(`/admin/users/${user.value.id}`, { method: "DELETE" });
    toast.success(t("admin.users.delete_success"));
    deleteOpen.value = false;
    await router.push(localePath("/admin/users"));
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    deleting.value = false;
  }
}
</script>

<template>
  <section v-if="user" class="space-y-5">
    <AdminPageHeader
      :title="t('admin.users.edit_page_title')"
      :description="user.full_name + ' — ' + user.email"
      icon="user-circle"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('admin.users.title'), to: localePath('/admin/users') },
        { label: user.full_name },
      ]"
    >
      <template #actions>
        <UiButton
          variant="ghost"
          class="text-error hover:text-error"
          @click="deleteOpen = true"
        >
          <Icon name="trash" class="h-4 w-4" />
          {{ t('admin.users.delete_button') }}
        </UiButton>
      </template>
    </AdminPageHeader>

    <UserForm
      v-if="form"
      v-model="form"
      password-optional
      :loading="submitting"
      :error="error"
      :submit-label="t('admin.actions.save')"
      :cancel-to="localePath('/admin/users')"
      @submit="save"
    />

    <AdminConfirmDialog
      :open="deleteOpen"
      tone="danger"
      icon="trash"
      :title="t('admin.users.delete_modal_title')"
      :description="t('admin.users.delete_modal_body', { name: user.full_name })"
      :confirm-label="t('admin.users.delete_button')"
      :cancel-label="t('admin.actions.cancel')"
      :loading="deleting"
      @update:open="(v) => (deleteOpen = v)"
      @confirm="confirmDelete"
    />
  </section>
  <section v-else class="space-y-3">
    <UiSkeleton height="3rem" block />
    <UiSkeleton height="16rem" block />
  </section>
</template>
