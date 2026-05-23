<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    bookId: string;
    /** "icon" — heart-only, absolute on a card. "button" — full pill button. */
    variant?: "icon" | "button";
    size?: "sm" | "md" | "lg";
  }>(),
  { variant: "icon", size: "md" },
);

const { t } = useI18n();
const localePath = useLocalePath();
const { isAuthenticated } = useAuth();
const wishlist = useWishlistStore();

const isWishlisted = computed(() => wishlist.isWishlisted(props.bookId));
const isPending = computed(() => wishlist.isPending(props.bookId));

async function onClick(event: MouseEvent) {
  // Stop the surrounding NuxtLink from navigating when this lives on a card.
  event.preventDefault();
  event.stopPropagation();

  if (!isAuthenticated.value) {
    await navigateTo(localePath("/auth/login"));
    return;
  }
  try {
    await wishlist.toggle(props.bookId);
  }
  catch {
    // Store already rolled back; nothing more to surface here.
  }
}

const label = computed(() =>
  isWishlisted.value
    ? t("book.remove_from_wishlist")
    : t("book.add_to_wishlist"),
);

const sizeClass = computed(() => {
  if (props.variant === "icon") {
    return { sm: "h-7 w-7", md: "h-9 w-9", lg: "h-10 w-10" }[props.size];
  }
  return { sm: "px-2.5 py-1 text-xs", md: "px-4 py-2 text-sm", lg: "px-5 py-2.5 text-base" }[props.size];
});

const heartSize = computed(() => {
  return { sm: "h-4 w-4", md: "h-5 w-5", lg: "h-5 w-5" }[props.size];
});
</script>

<template>
  <button
    v-if="variant === 'icon'"
    type="button"
    :aria-label="label"
    :aria-pressed="isWishlisted"
    :disabled="isPending"
    class="inline-flex items-center justify-center rounded-full border bg-bg-card/90 backdrop-blur shadow-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
    :class="[
      sizeClass,
      isWishlisted
        ? 'border-error/40 text-error hover:bg-error/10'
        : 'border-border text-ink-tertiary hover:border-error hover:text-error',
    ]"
    @click="onClick"
  >
    <Icon :name="isWishlisted ? 'heart-solid' : 'heart'" :class="heartSize" />
  </button>

  <button
    v-else
    type="button"
    :aria-pressed="isWishlisted"
    :disabled="isPending"
    class="inline-flex items-center justify-center gap-1.5 rounded font-medium transition-colors disabled:opacity-60 disabled:cursor-not-allowed border"
    :class="[
      sizeClass,
      isWishlisted
        ? 'border-error/40 text-error bg-error/5 hover:bg-error/10'
        : 'border-border text-ink-secondary hover:border-primary hover:text-primary',
    ]"
    @click="onClick"
  >
    <Icon :name="isWishlisted ? 'heart-solid' : 'heart'" :class="heartSize" />
    <span>{{ label }}</span>
  </button>
</template>
