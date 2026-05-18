# Meta teglari, Sitemap va JSON-LD

Texnik SEO'ning amaliy qismi: har bir sahifaga qanday meta teglar qo'shiladi, sitemap.xml qanday generatsiya qilinadi, va Schema.org strukturalashtirilgan ma'lumotlari.

## Meta teglar — har sahifa uchun

### Asosiy shablon

`composables/useSeo.ts`:

```typescript
interface SeoOptions {
  title: string
  description: string
  image?: string
  type?: 'website' | 'article' | 'book'
  noindex?: boolean
}

export const useSeo = (options: SeoOptions) => {
  const route = useRoute()
  const config = useRuntimeConfig()
  const { locale, locales } = useI18n()

  const url = `${config.public.siteUrl}${route.fullPath}`
  const image = options.image || `${config.public.siteUrl}/og-default.jpg`

  useSeoMeta({
    title: options.title,
    description: options.description,
    ogTitle: options.title,
    ogDescription: options.description,
    ogImage: image,
    ogUrl: url,
    ogType: options.type || 'website',
    ogSiteName: 'Anjumanlar.com',
    ogLocale: locale.value === 'uz' ? 'uz_UZ' : locale.value === 'ru' ? 'ru_RU' : 'en_US',
    twitterCard: 'summary_large_image',
    twitterTitle: options.title,
    twitterDescription: options.description,
    twitterImage: image,
    robots: options.noindex ? 'noindex, nofollow' : 'index, follow',
  })

  // hreflang
  useHead({
    link: [
      { rel: 'canonical', href: url },
      ...(locales.value as any[]).map(l => ({
        rel: 'alternate',
        hreflang: l.code,
        href: `${config.public.siteUrl}/${l.code}${route.path.replace(/^\/[a-z]{2}/, '')}`,
      })),
      {
        rel: 'alternate',
        hreflang: 'x-default',
        href: `${config.public.siteUrl}/uz${route.path.replace(/^\/[a-z]{2}/, '')}`,
      },
    ],
  })
}
```

### Kitob sahifasida foydalanish

`pages/[locale]/books/[slug].vue`:

```typescript
const { data: book } = await useFetch(`/api/v1/books/${slug}`)

useSeo({
  title: `${book.value.title} — ${book.value.author_name} | Anjumanlar.com`,
  description: book.value.description.slice(0, 155),
  image: book.value.cover_url,
  type: 'book',
})

// JSON-LD
useSchemaOrgBook({
  name: book.value.title,
  author: book.value.author_name,
  isbn: book.value.isbn,
  bookFormat: 'EBook',
  inLanguage: book.value.language,
  offers: {
    price: book.value.price,
    priceCurrency: 'UZS',
    availability: 'InStock',
  },
})
```

## Open Graph va Twitter Card

### Standart OG rasm

- O'lcham: **1200x630px**
- Format: JPG yoki PNG
- O'lcham: 1 MB dan kam
- Brand logo + kontent

### Dinamik OG rasm

Har kitob uchun avtomatik generatsiya. Backend'da Pillow yoki Vercel OG'dan foydalanish mumkin.

```python
# Backend: backend/app/services/og_image.py
from PIL import Image, ImageDraw, ImageFont

def generate_book_og_image(book) -> bytes:
    img = Image.new('RGB', (1200, 630), color='#FAF7F2')
    draw = ImageDraw.Draw(img)

    # Cover paste
    cover = Image.open(book.cover_path).resize((280, 420))
    img.paste(cover, (80, 105))

    # Title
    title_font = ImageFont.truetype('Lora-Bold.ttf', 48)
    draw.text((420, 150), book.title, fill='#1A1410', font=title_font)

    # Author
    author_font = ImageFont.truetype('Inter-Regular.ttf', 32)
    draw.text((420, 230), book.author_name, fill='#4A3F35', font=author_font)

    # Price
    price_font = ImageFont.truetype('Inter-Bold.ttf', 40)
    draw.text((420, 320), f"{book.price:,.0f} so'm", fill='#8B4513', font=price_font)

    # Logo
    logo = Image.open('logo.png').resize((180, 40))
    img.paste(logo, (80, 550), logo)

    output = BytesIO()
    img.save(output, format='JPEG', quality=85, optimize=True)
    return output.getvalue()
```

### Tekshirish

- [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/)
- [Twitter Card Validator](https://cards-dev.twitter.com/validator)
- [LinkedIn Post Inspector](https://www.linkedin.com/post-inspector/)
- [Telegram bot @WebpageBot](https://t.me/webpagebot) — Telegram preview yangilash

## JSON-LD Strukturalashtirilgan ma'lumotlar

Schema.org markup Google'ga sayt mazmunini tushunishga yordam beradi va rich snippet'lar (reyting yulduzlari, narx, mavjudlik) ko'rinishini ta'minlaydi.

### 1. Organization (har sahifada — global)

`layouts/default.vue` yoki `app.vue`:

```typescript
useSchemaOrg([
  defineOrganization({
    name: 'Anjumanlar.com',
    url: 'https://anjumanlar.com',
    logo: 'https://anjumanlar.com/logo.png',
    sameAs: [
      'https://t.me/anjumanlar',
      'https://www.facebook.com/anjumanlar',
      'https://www.instagram.com/anjumanlar',
    ],
    contactPoint: {
      contactType: 'customer support',
      email: 'support@anjumanlar.com',
      areaServed: 'UZ',
      availableLanguage: ['uz', 'ru', 'en'],
    },
  }),
  defineWebSite({
    name: 'Anjumanlar.com',
    url: 'https://anjumanlar.com',
    potentialAction: defineSearchAction({
      target: 'https://anjumanlar.com/search?q={search_term_string}',
    }),
  }),
])
```

### 2. Book (kitob sahifasida)

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Book",
  "name": "Yashash falsafasi",
  "author": {
    "@type": "Person",
    "name": "Aziz Aliyev",
    "url": "https://anjumanlar.com/uz/authors/aziz-aliyev"
  },
  "isbn": "978-9943-00-000-0",
  "bookFormat": "https://schema.org/EBook",
  "inLanguage": "uz",
  "datePublished": "2024-03-15",
  "publisher": {
    "@type": "Organization",
    "name": "Anjumanlar.com"
  },
  "image": "https://anjumanlar.com/covers/yashash-falsafasi.jpg",
  "description": "Inson hayoti va uning ma'nosi haqida monografiya.",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.7",
    "reviewCount": "24",
    "bestRating": "5"
  },
  "offers": {
    "@type": "Offer",
    "price": "45000",
    "priceCurrency": "UZS",
    "availability": "https://schema.org/InStock",
    "url": "https://anjumanlar.com/uz/books/yashash-falsafasi",
    "seller": {
      "@type": "Organization",
      "name": "Anjumanlar.com"
    }
  }
}
</script>
```

### 3. Person — Muallif sahifasi

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "Aziz Aliyev",
  "url": "https://anjumanlar.com/uz/authors/aziz-aliyev",
  "image": "https://anjumanlar.com/avatars/aziz-aliyev.jpg",
  "jobTitle": "Filosof, professor",
  "affiliation": {
    "@type": "Organization",
    "name": "O'zbekiston Milliy Universiteti"
  },
  "description": "Falsafa fanlari doktori, 15+ monografiya muallifi.",
  "sameAs": [
    "https://orcid.org/0000-0000-0000-0000"
  ]
}
</script>
```

### 4. BreadcrumbList — Navigatsiya

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Bosh sahifa",
      "item": "https://anjumanlar.com/uz"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "Katalog",
      "item": "https://anjumanlar.com/uz/catalog"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "Falsafa",
      "item": "https://anjumanlar.com/uz/categories/falsafa"
    },
    {
      "@type": "ListItem",
      "position": 4,
      "name": "Yashash falsafasi"
    }
  ]
}
</script>
```

### 5. Article — Blog post

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Monografiya qanday yoziladi?",
  "image": "https://anjumanlar.com/blog/monografiya.jpg",
  "datePublished": "2026-05-10T10:00:00+05:00",
  "dateModified": "2026-05-12T15:30:00+05:00",
  "author": {
    "@type": "Person",
    "name": "Anjumanlar tahririyat"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Anjumanlar.com",
    "logo": {
      "@type": "ImageObject",
      "url": "https://anjumanlar.com/logo.png"
    }
  },
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://anjumanlar.com/uz/blog/monografiya-qanday-yoziladi"
  }
}
</script>
```

### 6. FAQPage — FAQ sahifasi uchun

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Anjumanlar.com'da qanday qilib kitob sotish mumkin?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Muallif sifatida ro'yxatdan o'tib, kabinetingizda kitob yuklang."
      }
    },
    {
      "@type": "Question",
      "name": "Komissiya qancha?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Standart komissiya 15%."
      }
    }
  ]
}
</script>
```

### Test qilish

- [Google Rich Results Test](https://search.google.com/test/rich-results)
- [Schema.org Validator](https://validator.schema.org/)
- [Yandex Structured Data Validator](https://webmaster.yandex.com/tools/microtest/)

## Sitemap.xml

### Avtomatik generatsiya (Nuxt module)

```bash
npm install @nuxtjs/sitemap
```

`nuxt.config.ts`:

```typescript
export default defineNuxtConfig({
  modules: ['@nuxtjs/sitemap'],

  site: {
    url: 'https://anjumanlar.com',
  },

  sitemap: {
    sources: [
      '/api/__sitemap__/urls',  // Dinamik URL'lar API'dan
    ],
    autoLastmod: true,
    defaults: {
      changefreq: 'weekly',
      priority: 0.7,
    },
  },
})
```

### Dinamik URL'lar API

`server/api/__sitemap__/urls.ts`:

```typescript
export default defineEventHandler(async () => {
  const config = useRuntimeConfig()

  const [books, authors, categories, blogPosts] = await Promise.all([
    $fetch(`${config.public.apiBase}/api/v1/sitemap/books`),
    $fetch(`${config.public.apiBase}/api/v1/sitemap/authors`),
    $fetch(`${config.public.apiBase}/api/v1/sitemap/categories`),
    $fetch(`${config.public.apiBase}/api/v1/sitemap/blog`),
  ])

  const urls: any[] = []

  for (const locale of ['uz', 'ru', 'en']) {
    // Bosh sahifalar
    urls.push(
      { loc: `/${locale}`, priority: 1.0, changefreq: 'daily' },
      { loc: `/${locale}/catalog`, priority: 0.9, changefreq: 'daily' },
      { loc: `/${locale}/authors`, priority: 0.8, changefreq: 'weekly' },
      { loc: `/${locale}/blog`, priority: 0.7, changefreq: 'weekly' },
    )

    // Kitoblar
    for (const book of books as any[]) {
      urls.push({
        loc: `/${locale}/books/${book.slug}`,
        lastmod: book.updated_at,
        priority: 0.8,
        changefreq: 'monthly',
      })
    }

    // Mualliflar
    for (const author of authors as any[]) {
      urls.push({
        loc: `/${locale}/authors/${author.slug}`,
        lastmod: author.updated_at,
        priority: 0.6,
        changefreq: 'monthly',
      })
    }

    // Kategoriyalar
    for (const cat of categories as any[]) {
      urls.push({
        loc: `/${locale}/categories/${cat.slug}`,
        priority: 0.7,
        changefreq: 'weekly',
      })
    }

    // Blog
    for (const post of blogPosts as any[]) {
      urls.push({
        loc: `/${locale}/blog/${post.slug}`,
        lastmod: post.updated_at,
        priority: 0.6,
        changefreq: 'monthly',
      })
    }
  }

  return urls
})
```

### Backend sitemap endpoint'lari

`backend/app/api/v1/endpoints/sitemap.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter()

@router.get("/books")
async def sitemap_books(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Book.slug, Book.updated_at)
        .where(Book.status == 'published')
    )
    return [
        {"slug": row.slug, "updated_at": row.updated_at.isoformat()}
        for row in result
    ]

@router.get("/authors")
async def sitemap_authors(db: AsyncSession = Depends(get_db)):
    # ...

@router.get("/categories")
async def sitemap_categories(db: AsyncSession = Depends(get_db)):
    # ...

@router.get("/blog")
async def sitemap_blog(db: AsyncSession = Depends(get_db)):
    # ...
```

### Sitemap index (juda katta saytlar uchun)

Agar URL'lar 50,000'dan ko'p bo'lsa, sitemap'larni bo'lib indekslash kerak:

```xml
<!-- sitemap_index.xml -->
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>https://anjumanlar.com/sitemap-books.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://anjumanlar.com/sitemap-authors.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://anjumanlar.com/sitemap-blog.xml</loc>
  </sitemap>
</sitemapindex>
```

## robots.txt

`public/robots.txt`:

```
User-agent: *
Allow: /
Disallow: /admin/
Disallow: /author/
Disallow: /api/
Disallow: /checkout/
Disallow: /profile/
Disallow: /*?utm_*
Disallow: /*?ref=*

# Yandex
User-agent: Yandex
Allow: /
Disallow: /admin/
Disallow: /author/
Disallow: /api/
Crawl-delay: 1

# Google
User-agent: Googlebot
Allow: /

# Sitemap
Sitemap: https://anjumanlar.com/sitemap.xml
```

## Sitemap'ni qidiruv tizimlariga yuborish

### Google
1. [Search Console](https://search.google.com/search-console)'ga kirish
2. Sitemaps → Add new sitemap
3. `sitemap.xml` qo'shish

### Yandex
1. [Yandex Webmaster](https://webmaster.yandex.com/)'ga kirish
2. Indexing → Sitemap files
3. URL qo'shish

### Avtomatik xabar berish (ping)

Yangi kontent qo'shilganda:

```python
# backend/app/tasks/sitemap.py
import requests

@celery_app.task
def ping_search_engines():
    """Sitemap yangilanganida search engine'larga xabar berish"""
    sitemap_url = "https://anjumanlar.com/sitemap.xml"

    requests.get(f"https://www.google.com/ping?sitemap={sitemap_url}")
    requests.get(f"https://webmaster.yandex.com/ping?sitemap={sitemap_url}")
```

Trigger: yangi kitob nashr qilingan, blog post yozilgan, va h.k.

## Indexlash strategiyasi

### Index qilinishi kerak
- ✓ Bosh sahifa (3 til)
- ✓ Katalog
- ✓ Kategoriya sahifalari
- ✓ Kitob sahifalari (nashr qilingan)
- ✓ Muallif profillari
- ✓ Blog
- ✓ Statik sahifalar (Biz haqimizda, FAQ)

### Index qilinmasligi kerak (noindex)
- ✗ Admin panel
- ✗ Muallif kabineti
- ✗ Foydalanuvchi profili
- ✗ Checkout / to'lov sahifalari
- ✗ Search natijalari (parametrlar bilan)
- ✗ Filter URL'lari (`?sort=...&category=...`)
- ✗ Pagination sahifalari (canonical first page)
- ✗ 404, 500 sahifalar

Buni belgilash:

```typescript
useSeoMeta({
  robots: 'noindex, nofollow'
})
```

## Tekshirish vositalari

| Vosita | Maqsad |
|--------|--------|
| [Google Rich Results](https://search.google.com/test/rich-results) | JSON-LD test |
| [Schema Markup Validator](https://validator.schema.org/) | Schema.org tekshirish |
| [PageSpeed Insights](https://pagespeed.web.dev/) | Tezlik va Core Web Vitals |
| [Mobile-Friendly Test](https://search.google.com/test/mobile-friendly) | Mobile UX |
| [Screaming Frog](https://www.screamingfrog.co.uk/) | Sayt audit (bepul 500 URL) |
| [GSC URL Inspection](https://search.google.com/search-console) | Aniq URL indexlanishini tekshirish |

---

**Keyingi qadam:** [Yo'l xaritasi (Roadmap)](../10-roadmap/01-development-phases.md)
