import type { LocalisedText } from "~/types/api";

/**
 * Pick the active-locale string out of a JSONB ``{uz, ru, en}`` payload.
 *
 * Fallback chain: requested locale → uz → en → ru → fallback param. The
 * backend allows authors to leave non-default locales blank, so we have
 * to be defensive.
 */
export function useLocaleText() {
  const { locale } = useI18n();

  function localised(text: LocalisedText | null | undefined, fallback = ""): string {
    if (!text) return fallback;
    const order = [locale.value, "uz", "en", "ru"];
    for (const key of order) {
      const value = text[key];
      if (value && value.trim()) return value;
    }
    return fallback;
  }

  return { localised };
}

/**
 * Format an integer price in UZS with thousands separators, e.g. ``50 000 so'm``.
 * Negative amounts (refunds etc.) get a leading minus.
 */
export function formatPrice(price: number, currency = "UZS"): string {
  const abs = Math.abs(price);
  const formatted = new Intl.NumberFormat("uz-UZ", {
    maximumFractionDigits: 0,
  }).format(abs);
  const sign = price < 0 ? "-" : "";
  if (currency === "UZS") return `${sign}${formatted} so'm`;
  return `${sign}${formatted} ${currency}`;
}
