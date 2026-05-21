<script setup lang="ts">
import { formatPrice } from "~/composables/useLocaleText";

const props = defineProps<{
  price: number;
  discountPrice?: number | null;
  isFree?: boolean;
  size?: "sm" | "md" | "lg";
}>();

const { t } = useI18n();

const hasDiscount = computed(
  () =>
    props.discountPrice != null
    && props.discountPrice > 0
    && props.discountPrice < props.price,
);

const sizeClass = computed(() =>
  props.size === "lg"
    ? "text-2xl"
    : props.size === "sm"
      ? "text-sm"
      : "text-base",
);
</script>

<template>
  <span class="inline-flex items-baseline gap-2">
    <span v-if="isFree" class="font-semibold text-success" :class="sizeClass">
      {{ t("book.free") }}
    </span>
    <template v-else>
      <span
        v-if="hasDiscount"
        class="line-through text-ink-tertiary"
        :class="size === 'lg' ? 'text-base' : 'text-xs'"
      >
        {{ formatPrice(price) }}
      </span>
      <span class="font-semibold text-primary" :class="sizeClass">
        {{ formatPrice(hasDiscount ? (discountPrice as number) : price) }}
      </span>
    </template>
  </span>
</template>
