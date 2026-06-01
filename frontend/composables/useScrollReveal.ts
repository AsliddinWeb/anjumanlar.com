/**
 * Toggle `.in-view` on elements with class `.reveal` once they enter
 * the viewport. Combined with the CSS in main.css, this gives every
 * marked section a fade-in/slide-up entrance the first time the user
 * scrolls past it.
 *
 * Usage in a page/component:
 *
 *   <script setup>
 *     useScrollReveal();
 *   </script>
 *
 *   <template>
 *     <section class="reveal">…</section>
 *     <div class="reveal reveal-delay-1">…</div>
 *   </template>
 *
 * Idempotent: re-running on the same DOM is a no-op. Respects
 * prefers-reduced-motion by skipping the observer entirely (the CSS
 * media query already keeps elements visible in that case).
 */
export function useScrollReveal() {
  if (!import.meta.client) return;

  onMounted(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      // Make everything visible immediately, no animation
      document.querySelectorAll<HTMLElement>(".reveal").forEach((el) => {
        el.classList.add("in-view");
      });
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add("in-view");
            observer.unobserve(entry.target);
          }
        }
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" },
    );

    document.querySelectorAll<HTMLElement>(".reveal:not(.in-view)").forEach((el) => {
      observer.observe(el);
    });

    onBeforeUnmount(() => observer.disconnect());
  });
}
