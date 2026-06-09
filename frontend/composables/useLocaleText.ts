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
 *
 * Hand-rolled rather than `Intl.NumberFormat("uz-UZ")` because the Node
 * runtime that does SSR ships different ICU locale data from the
 * browser — Node emits a narrow no-break space, the browser emits an
 * ASCII comma, and the mismatch trips Vue's hydration check on every
 * price tag. A regex group is deterministic across both environments.
 */
export function formatPrice(price: number, currency = "UZS"): string {
  const abs = Math.floor(Math.abs(price));
  const formatted = abs.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  const sign = price < 0 ? "-" : "";
  if (currency === "UZS") return `${sign}${formatted} so'm`;
  return `${sign}${formatted} ${currency}`;
}

// Manual Uzbek month tables. Node and Chrome both emit "M06" style strings
// for the uz locale because the ICU data only ships the numeric form for
// short month — full month names land just fine. We keep both forms hand-
// rolled so the output is identical across SSR + browser regardless of
// whichever locale-data subset the runtime happens to bundle.
const UZ_MONTHS = [
  "yanvar", "fevral", "mart", "aprel", "may", "iyun",
  "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr",
];
const RU_MONTHS = [
  "января", "февраля", "марта", "апреля", "мая", "июня",
  "июля", "августа", "сентября", "октября", "ноября", "декабря",
];
const EN_MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

function pad2(n: number): string {
  return n < 10 ? `0${n}` : String(n);
}

/**
 * Render a date in a locale-appropriate, hydration-safe form.
 *
 * Examples (locale = uz):
 *   formatDate("2026-06-09T15:32:00Z")            // "9 iyun 2026, 15:32"
 *   formatDate(iso, "uz", { withTime: false })    // "9 iyun 2026"
 *   formatDate(iso, "uz", { short: true })        // "9-iyun"
 *
 * The reason this exists rather than calling `Intl.DateTimeFormat`
 * directly: the `uz` ICU locale emits "M06" for short months which is
 * meaningless to users. Hand-rolled month tables also keep the output
 * byte-identical across Node SSR and the browser, dodging hydration
 * mismatches that Intl-based formatting routinely produces.
 */
export function formatDate(
  iso: string | Date | null | undefined,
  locale: string = "uz",
  opts: { withTime?: boolean; short?: boolean } = {},
): string {
  if (!iso) return "";
  const d = typeof iso === "string" ? new Date(iso) : iso;
  if (Number.isNaN(d.getTime())) return "";

  const day = d.getDate();
  const monthIdx = d.getMonth();
  const year = d.getFullYear();
  const hours = pad2(d.getHours());
  const minutes = pad2(d.getMinutes());

  const months = locale === "ru" ? RU_MONTHS : locale === "en" ? EN_MONTHS : UZ_MONTHS;
  const month = months[monthIdx] ?? "";

  if (opts.short) {
    // "9-iyun" / "9 июня" / "Jun 9" — drop the year.
    if (locale === "en") return `${month.slice(0, 3)} ${day}`;
    return locale === "uz" ? `${day}-${month}` : `${day} ${month}`;
  }

  let base: string;
  if (locale === "en") base = `${month} ${day}, ${year}`;
  else base = `${day} ${month} ${year}`;

  if (opts.withTime === false) return base;
  return `${base}, ${hours}:${minutes}`;
}

/**
 * Composable wrapper that pulls the active locale from i18n so call
 * sites don't have to repeat ``locale.value``.
 */
export function useFormatDate() {
  const { locale } = useI18n();

  return {
    formatDate: (iso: string | Date | null | undefined, opts?: { withTime?: boolean; short?: boolean }) =>
      formatDate(iso, locale.value, opts),
  };
}
