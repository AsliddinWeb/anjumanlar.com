/**
 * Inject a JSON-LD ``<script type="application/ld+json">`` block via
 * useHead. Pages call this with a fully-formed schema.org payload —
 * the helpers below build the common shapes.
 *
 * Multiple calls per page are fine; each becomes its own script tag.
 */
export function useStructuredData(payload: Record<string, unknown> | Record<string, unknown>[]) {
  useHead({
    script: [
      {
        type: "application/ld+json",
        innerHTML: JSON.stringify(payload),
      },
    ],
  });
}

interface BreadcrumbItem {
  name: string;
  url: string;
}

export function buildBreadcrumbList(items: BreadcrumbItem[]) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": items.map((item, idx) => ({
      "@type": "ListItem",
      "position": idx + 1,
      "name": item.name,
      "item": item.url,
    })),
  };
}

interface BookSchemaInput {
  name: string;
  description: string;
  url: string;
  image?: string | null;
  isbn?: string | null;
  inLanguage: string;
  datePublished?: string | null;
  authorName: string;
  authorUrl: string;
  publisher?: string | null;
  priceUzs?: number | null;
  isFree?: boolean;
  ratingValue?: number | null;
  ratingCount?: number | null;
}

export function buildBookSchema(b: BookSchemaInput) {
  const payload: Record<string, unknown> = {
    "@context": "https://schema.org",
    "@type": "Book",
    "name": b.name,
    "description": b.description,
    "url": b.url,
    "inLanguage": b.inLanguage,
    "author": {
      "@type": "Person",
      "name": b.authorName,
      "url": b.authorUrl,
    },
  };
  if (b.image) payload.image = b.image;
  if (b.isbn) payload.isbn = b.isbn;
  if (b.datePublished) payload.datePublished = b.datePublished;
  if (b.publisher) {
    payload.publisher = { "@type": "Organization", "name": b.publisher };
  }
  if (b.priceUzs != null) {
    payload.offers = {
      "@type": "Offer",
      "price": b.isFree ? 0 : b.priceUzs,
      "priceCurrency": "UZS",
      "availability": "https://schema.org/InStock",
      "url": b.url,
    };
  }
  if (b.ratingValue != null && b.ratingCount && b.ratingCount > 0) {
    payload.aggregateRating = {
      "@type": "AggregateRating",
      "ratingValue": b.ratingValue,
      "ratingCount": b.ratingCount,
      "bestRating": 5,
      "worstRating": 1,
    };
  }
  return payload;
}

export function buildOrganizationSchema(opts: { siteUrl: string; siteName: string }) {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": opts.siteName,
    "url": opts.siteUrl,
    "logo": `${opts.siteUrl}/favicon.ico`,
    "sameAs": [
      "https://t.me/anjumanlar",
    ],
  };
}

interface PersonSchemaInput {
  name: string;
  url: string;
  description?: string;
  worksFor?: string | null;
  jobTitle?: string | null;
  sameAs?: string[];
}

export function buildPersonSchema(p: PersonSchemaInput) {
  const payload: Record<string, unknown> = {
    "@context": "https://schema.org",
    "@type": "Person",
    "name": p.name,
    "url": p.url,
  };
  if (p.description) payload.description = p.description;
  if (p.worksFor) {
    payload.worksFor = { "@type": "Organization", "name": p.worksFor };
  }
  if (p.jobTitle) payload.jobTitle = p.jobTitle;
  if (p.sameAs && p.sameAs.length > 0) payload.sameAs = p.sameAs;
  return payload;
}

/**
 * Wire alternate-locale links for the current path. The site uses
 * ``/uz``, ``/ru``, ``/en`` prefixes; we swap the current locale
 * segment for each variant.
 */
export function useHreflangAlternates(pathWithoutLocale: string) {
  const runtime = useRuntimeConfig();
  const siteUrl = (runtime.public.siteUrl as string) || "";
  const cleanPath = pathWithoutLocale.startsWith("/") ? pathWithoutLocale : `/${pathWithoutLocale}`;

  useHead({
    link: [
      { rel: "alternate", hreflang: "uz", href: `${siteUrl}/uz${cleanPath}` },
      { rel: "alternate", hreflang: "ru", href: `${siteUrl}/ru${cleanPath}` },
      { rel: "alternate", hreflang: "en", href: `${siteUrl}/en${cleanPath}` },
      { rel: "alternate", hreflang: "x-default", href: `${siteUrl}/uz${cleanPath}` },
    ],
  });
}
