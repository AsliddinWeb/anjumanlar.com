/**
 * Single source of truth for the `BookLanguage` enum's display options —
 * mirrors `app.models.book.BookLanguage` on the backend. Add a language
 * in both places together; the label comes from the `home.languages.*`
 * i18n namespace (shared with the homepage's language cloud).
 */
export const BOOK_LANGUAGE_CODES = [
  "uz",
  "ru",
  "en",
  "kk",
  "tr",
  "ky",
  "tg",
  "tk",
  "kaa",
  "az",
  "ar",
  "fa",
  "zh",
  "de",
  "fr",
  "es",
  "mixed",
] as const;

export type BookLanguageCode = (typeof BOOK_LANGUAGE_CODES)[number];

export function useBookLanguageOptions() {
  const { t } = useI18n();
  return computed(() =>
    BOOK_LANGUAGE_CODES.map((code) => ({ value: code, label: t(`home.languages.${code}`) })),
  );
}
