<script setup lang="ts">
defineProps<{
  rating: number;
  reviewsCount: number;
  size?: "sm" | "md" | "lg";
}>();

const { t } = useI18n();
</script>

<template>
  <div class="inline-flex items-center gap-1.5">
    <StarRating :value="rating" :size="size || 'sm'" />
    <span v-if="reviewsCount > 0" class="text-xs text-ink-secondary">
      {{ rating.toFixed(1) }}
      <span class="text-ink-tertiary">
        ({{ reviewsCount }})
      </span>
    </span>
    <span v-else class="text-xs text-ink-tertiary">
      {{ t("book.no_reviews") }}
    </span>
  </div>
</template>
