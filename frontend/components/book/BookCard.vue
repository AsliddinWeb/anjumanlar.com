<script setup lang="ts">
import type { BookPublic } from "~/types/api";

const props = defineProps<{ book: BookPublic }>();

const { localised } = useLocaleText();
const localePath = useLocalePath();

const title = computed(() => localised(props.book.title, props.book.slug));
const href = computed(() => localePath(`/books/${props.book.slug}`));
</script>

<template>
  <NuxtLink
    :to="href"
    class="tilt-card group block rounded-md border border-border bg-bg-card shadow-sm hover:border-primary/40"
  >
    <div class="relative">
      <BookCover :src="book.cover_url" :alt="title" />
      <UiBadge
        v-if="book.is_free"
        tone="success"
        class="absolute top-2 left-2"
      >
        {{ $t("book.free") }}
      </UiBadge>
      <UiBadge
        v-else-if="book.featured"
        tone="gold"
        class="absolute top-2 left-2 inline-flex items-center gap-1"
      >
        <Icon name="star-solid" class="h-3.5 w-3.5" />
        {{ $t("book.featured") }}
      </UiBadge>
      <div class="absolute top-2 right-2 flex flex-col gap-1.5">
        <WishlistButton :book-id="book.id" size="sm" />
        <CartButton v-if="!book.is_free" :book="book" size="sm" />
      </div>
    </div>

    <div class="p-3 space-y-1.5">
      <h3
        class="font-serif text-ink leading-snug line-clamp-2 group-hover:text-primary"
        :title="title"
      >
        {{ title }}
      </h3>
      <p class="text-xs text-ink-secondary truncate">
        {{ book.author.display_name }}
      </p>
      <div class="flex items-center justify-between pt-1">
        <BookPriceTag
          :price="book.price"
          :discount-price="book.discount_price"
          :is-free="book.is_free"
          size="sm"
        />
        <BookRating
          v-if="book.reviews_count > 0"
          :rating="book.average_rating"
          :reviews-count="book.reviews_count"
        />
      </div>
    </div>
  </NuxtLink>
</template>
