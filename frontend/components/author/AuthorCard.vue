<script setup lang="ts">
import type { AuthorPublic } from "~/types/api";

defineProps<{ author: AuthorPublic }>();

const { t } = useI18n();
const localePath = useLocalePath();

const initials = (name: string) =>
  name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((p) => p.charAt(0).toUpperCase())
    .join("");
</script>

<template>
  <NuxtLink
    :to="localePath(`/authors/${author.slug}`)"
    class="group block rounded-md border border-border bg-bg-card p-4 shadow-sm transition-shadow hover:shadow-book hover:border-border-hover"
  >
    <div class="flex items-start gap-3">
      <div
        class="h-12 w-12 shrink-0 rounded-full bg-bg-secondary flex items-center justify-center font-medium text-ink-secondary"
      >
        {{ initials(author.display_name) || "?" }}
      </div>
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-2">
          <h3 class="font-medium text-ink truncate group-hover:text-primary">
            {{ author.display_name }}
          </h3>
          <UiBadge v-if="author.verified" tone="success" size="sm">
            ✓ {{ t("authors.verified") }}
          </UiBadge>
        </div>
        <p v-if="author.academic_title" class="text-xs text-ink-tertiary truncate">
          {{ author.academic_title }}
        </p>
        <p v-if="author.institution" class="text-xs text-ink-tertiary truncate">
          {{ author.institution }}
        </p>
      </div>
    </div>
  </NuxtLink>
</template>
