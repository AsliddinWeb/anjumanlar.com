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
    class="group flex flex-col rounded-md border border-border bg-bg-card p-4 transition-all hover:border-primary hover:shadow-sm"
  >
    <div class="flex items-start gap-3">
      <div
        class="h-12 w-12 shrink-0 rounded-full bg-primary text-ink-inverse flex items-center justify-center font-semibold text-sm"
      >
        {{ initials(author.display_name) || "?" }}
      </div>
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-1.5 flex-wrap">
          <h3 class="font-medium text-ink truncate group-hover:text-primary transition-colors">
            {{ author.display_name }}
          </h3>
          <Icon
            v-if="author.verified"
            name="check-circle-solid"
            class="h-3.5 w-3.5 text-success shrink-0"
            :title="t('authors.verified')"
          />
          <Icon
            v-if="author.featured"
            name="star-solid"
            class="h-3.5 w-3.5 text-accent-gold shrink-0"
            :title="t('authors.featured')"
          />
        </div>
        <p v-if="author.academic_title" class="text-xs text-ink-secondary truncate mt-0.5">
          {{ author.academic_title }}
        </p>
        <p v-if="author.institution" class="inline-flex items-center gap-1 text-xs text-ink-tertiary truncate mt-0.5">
          <Icon name="institution" class="h-3 w-3 shrink-0" />
          <span class="truncate">{{ author.institution }}</span>
        </p>
      </div>
    </div>
  </NuxtLink>
</template>
