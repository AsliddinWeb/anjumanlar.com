/**
 * Pull the cart back out of localStorage on the first client tick.
 * SSR starts from the empty default so the markup hydrates cleanly;
 * the saved cart appears once this plugin runs.
 */
export default defineNuxtPlugin(() => {
  const cart = useCartStore();
  cart.hydrate();
});
