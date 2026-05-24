import { defineStore } from "pinia";
import type { BookPublic } from "~/types/api";

/**
 * Cart store — basket of books the user intends to buy.
 *
 * Persists to localStorage so the cart survives page reloads + tab
 * close-and-reopens. We only store the BookPublic snapshot (id, slug,
 * title, price, ...) since the backend is the source of truth for
 * prices at checkout time — anything stale gets re-resolved when the
 * user hits "Pay".
 *
 * SSR-safe: localStorage access happens behind `import.meta.client`,
 * so hydration starts from the empty default and the saved cart
 * arrives on the client tick.
 */

const STORAGE_KEY = "monografiya:cart:v1";

interface SerializedCart {
  items: BookPublic[];
}

function readStorage(): BookPublic[] {
  if (!import.meta.client) return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as SerializedCart;
    if (!Array.isArray(parsed?.items)) return [];
    return parsed.items.filter((b) => b && typeof b.id === "string");
  }
  catch {
    return [];
  }
}

function writeStorage(items: BookPublic[]) {
  if (!import.meta.client) return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ items }));
  }
  catch {
    // Quota or private-mode failures are non-fatal — the in-memory
    // store still works for the lifetime of the page.
  }
}

export const useCartStore = defineStore("cart", () => {
  const items = ref<BookPublic[]>([]);
  const hydrated = ref(false);

  /** Sync from localStorage. Called from the plugin on app boot. */
  function hydrate() {
    if (hydrated.value) return;
    items.value = readStorage();
    hydrated.value = true;
  }

  const count = computed(() => items.value.length);

  const subtotal = computed(() =>
    items.value.reduce((sum, b) => {
      const price = b.is_free
        ? 0
        : b.discount_price != null && b.discount_price > 0 && b.discount_price < b.price
          ? b.discount_price
          : b.price;
      return sum + price;
    }, 0),
  );

  function has(bookId: string): boolean {
    return items.value.some((b) => b.id === bookId);
  }

  function add(book: BookPublic) {
    if (has(book.id)) return;
    items.value = [...items.value, book];
    writeStorage(items.value);
  }

  function remove(bookId: string) {
    items.value = items.value.filter((b) => b.id !== bookId);
    writeStorage(items.value);
  }

  function toggle(book: BookPublic) {
    if (has(book.id)) remove(book.id);
    else add(book);
  }

  function clear() {
    items.value = [];
    writeStorage(items.value);
  }

  return {
    items,
    hydrated,
    count,
    subtotal,
    hydrate,
    has,
    add,
    remove,
    toggle,
    clear,
  };
});
