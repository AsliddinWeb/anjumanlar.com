<script setup lang="ts">
import type { IconName } from "~/utils/icons";

defineProps<{
  icon: IconName;
  title: string;
  lastUpdated: string;
  sections: { id: string; label: string }[];
}>();

const activeSection = ref<string | null>(null);

onMounted(() => {
  if (!import.meta.client) return;
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) activeSection.value = entry.target.id;
      });
    },
    { rootMargin: "-30% 0px -60% 0px" },
  );
  document.querySelectorAll("section[id]").forEach((el) => observer.observe(el));
  onBeforeUnmount(() => observer.disconnect());
});

function scrollTo(id: string) {
  if (!import.meta.client) return;
  const el = document.getElementById(id);
  if (!el) return;
  const top = el.getBoundingClientRect().top + window.scrollY - 80;
  window.scrollTo({ top, behavior: "smooth" });
  // Update URL hash without triggering Vue Router navigation.
  history.replaceState(null, "", `#${id}`);
  activeSection.value = id;
}
</script>

<template>
  <section class="bg-bg">
    <!-- Hero -->
    <header class="relative overflow-hidden border-b border-border">
      <div
        aria-hidden="true"
        class="absolute inset-0 -z-10"
        style="background-image:
          radial-gradient(ellipse 50% 50% at 50% 0%, color-mix(in oklab, var(--color-primary) 8%, transparent), transparent 65%);"
      />
      <div class="max-w-4xl mx-auto px-4 py-12 md:py-16 text-center space-y-3">
        <div class="inline-flex h-12 w-12 items-center justify-center rounded-md bg-primary/10 text-primary">
          <Icon :name="icon" class="h-6 w-6" />
        </div>
        <h1 class="font-serif text-3xl md:text-5xl text-ink leading-tight tracking-tight">
          {{ title }}
        </h1>
        <p class="text-xs text-ink-tertiary">
          {{ lastUpdated }}
        </p>
      </div>
    </header>

    <div class="max-w-6xl mx-auto px-4 py-10 md:py-12 grid md:grid-cols-[220px_1fr] gap-8 md:gap-12">
      <!-- TOC sidebar -->
      <aside class="hidden md:block">
        <nav class="sticky top-20 space-y-1 text-sm">
          <p class="text-xs uppercase tracking-wider text-ink-tertiary px-3 mb-2">
            {{ $t("legal.toc") }}
          </p>
          <button
            v-for="s in sections"
            :key="s.id"
            type="button"
            class="block w-full text-left px-3 py-1.5 rounded transition-colors border-l-2"
            :class="activeSection === s.id
              ? 'bg-primary/5 text-primary font-medium border-primary'
              : 'text-ink-secondary hover:bg-bg-secondary hover:text-ink border-transparent'"
            @click="scrollTo(s.id)"
          >
            {{ s.label }}
          </button>
        </nav>
      </aside>

      <!-- Content -->
      <article class="prose-anjuman min-w-0 max-w-none">
        <slot />
      </article>
    </div>
  </section>
</template>

<style scoped>
:deep(h2) {
  font-family: var(--font-serif, ui-serif, Georgia, serif);
  font-size: 1.5rem;
  line-height: 1.3;
  color: var(--color-ink);
  margin-top: 2rem;
  margin-bottom: 0.75rem;
  scroll-margin-top: 5rem;
}
:deep(h2:first-child) {
  margin-top: 0;
}
:deep(p) {
  color: var(--color-ink);
  line-height: 1.75;
  margin-bottom: 1rem;
}
:deep(ul) {
  margin-bottom: 1rem;
  padding-left: 1.25rem;
  list-style: disc;
}
:deep(li) {
  color: var(--color-ink);
  margin-bottom: 0.5rem;
  line-height: 1.65;
}
:deep(strong) {
  color: var(--color-ink);
  font-weight: 600;
}
:deep(a) {
  color: var(--color-primary);
  text-decoration: underline;
}
</style>
