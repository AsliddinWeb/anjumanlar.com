<script setup lang="ts">
// Placeholder until the author dashboard ships in Phase 4. Redirect
// authenticated users to /account, unauthenticated ones to the login page.
const { isAuthenticated } = useAuth();
const localePath = useLocalePath();

if (import.meta.server || import.meta.client) {
  await navigateTo(
    localePath(isAuthenticated.value ? "/account" : "/auth/login"),
    { redirectCode: 302 },
  );
}
</script>

<template>
  <div />
</template>
