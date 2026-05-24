/**
 * Centralised wrapper around ``useSeoMeta`` that fills in the site-wide
 * defaults (siteName, default cover, locale code) so individual pages
 * only have to declare title + description (+ optional cover URL).
 *
 * Call it instead of ``useHead`` whenever a page needs Open Graph /
 * Twitter / canonical metadata — i.e. every public page. Admin /
 * /account pages don't need SEO (they're noindexed via robots.txt).
 */
export interface SiteSeoInput {
  title?: string;
  description?: string;
  /** Absolute URL (or path under siteUrl) to a cover image (1200x630 ideal). */
  image?: string;
  /** ``article`` for book / blog pages, ``website`` everywhere else. */
  ogType?: "website" | "article" | "profile" | "book";
  /** When set, search engines won't index this page (e.g. /search). */
  noindex?: boolean;
  /** Canonical URL — defaults to current path under siteUrl. */
  canonical?: string;
}

export function useSiteSeo(input: SiteSeoInput) {
  const route = useRoute();
  const { locale } = useI18n();
  const runtime = useRuntimeConfig();

  const siteUrl = (runtime.public.siteUrl as string) || "";
  const siteName = (runtime.public.siteName as string) || "Monografiya.com";

  const fullUrl = computed(() => {
    if (input.canonical) {
      return input.canonical.startsWith("http")
        ? input.canonical
        : `${siteUrl}${input.canonical}`;
    }
    return `${siteUrl}${route.path}`;
  });

  const fullImage = computed(() => {
    if (!input.image) return undefined;
    return input.image.startsWith("http") ? input.image : `${siteUrl}${input.image}`;
  });

  const localeMap: Record<string, string> = {
    uz: "uz_UZ",
    ru: "ru_RU",
    en: "en_US",
  };

  useSeoMeta({
    title: input.title,
    description: input.description,
    ogSiteName: siteName,
    ogTitle: input.title,
    ogDescription: input.description,
    ogImage: fullImage,
    ogUrl: fullUrl,
    ogType: input.ogType ?? "website",
    ogLocale: localeMap[locale.value] ?? "uz_UZ",
    twitterCard: input.image ? "summary_large_image" : "summary",
    twitterTitle: input.title,
    twitterDescription: input.description,
    twitterImage: fullImage,
    robots: input.noindex ? "noindex, nofollow" : "index, follow",
  });

  // hreflang variants — strip the current locale prefix from the path
  // so each entry points at the same logical page in a different locale.
  const localeFreePath = computed(() => {
    const segs = route.path.split("/").filter(Boolean);
    if (segs[0] === locale.value) segs.shift();
    return "/" + segs.join("/");
  });

  useHead({
    link: [
      { rel: "canonical", href: fullUrl.value },
      { rel: "alternate", hreflang: "uz", href: `${siteUrl}/uz${localeFreePath.value}` },
      { rel: "alternate", hreflang: "ru", href: `${siteUrl}/ru${localeFreePath.value}` },
      { rel: "alternate", hreflang: "en", href: `${siteUrl}/en${localeFreePath.value}` },
      { rel: "alternate", hreflang: "x-default", href: `${siteUrl}/uz${localeFreePath.value}` },
    ],
  });
}
