# SEO Strategiyasi — Anjumanlar.com

Saytni Google va Yandex'da yaxshi joylashtirish — bu uzoq muddatli, lekin eng arzon foydalanuvchi olish kanali.

## Maqsadlar

1. **6 oy ichida:** Brand so'rovlari uchun #1 ("anjumanlar", "anjumanlar.com")
2. **12 oy ichida:** Asosiy kalit so'rovlar top 10'da ("monografiya yuklab olish", "ilmiy kitob uz")
3. **18 oy ichida:** Long-tail so'rovlar bo'yicha 10K+ oylik organic visit

## Maqsadli auditoriya va kalit so'rovlar

### Asosiy auditoriya
1. **Talabalar** — bakalavr, magistr, PhD
2. **O'qituvchilar va olimlar** — universitet, ilmiy institut
3. **Mualliflar** — o'z kitobini sotishni xohlaydiganlar
4. **Mutaxassislar** — soha bo'yicha bilim olishni xohlaydiganlar

### Kalit so'rov toifalari

#### 1. Brand (oson)
- `anjumanlar`
- `anjumanlar.com`
- `anjumanlar uz`

#### 2. Asosiy tijorat so'rovlari (o'rta-qiyin)
- `monografiya yuklab olish`
- `ilmiy kitob uz`
- `darslik yuklab olish pdf`
- `monografiya sotib olish`
- `uzbek scientific books`
- `научная литература узбекистан`

#### 3. Long-tail (oson, ko'p)
- `[fan nomi] monografiyasi pdf`
- `[muallif nomi] kitoblari`
- `[universitet] darslik`
- `[mavzu] bo'yicha kitob`
- Misol: `iqtisodiyot nazariyasi monografiya`, `kompyuter ilmlari darslik pdf`

#### 4. Informatsion (blog)
- `monografiya qanday yoziladi`
- `ilmiy maqola yozish qoidalari`
- `dissertatsiya tayyorlash`
- `referat yozish`

## Texnik SEO

### Asosiy talablar

- [ ] **HTTPS** — barcha sahifalar shifrlangan
- [ ] **Mobile-friendly** — Google Mobile-Friendly Test'dan o'tish
- [ ] **Tezlik** — PageSpeed Insights 80+ mobile, 90+ desktop
- [ ] **Core Web Vitals** — LCP < 2.5s, FID < 100ms, CLS < 0.1
- [ ] **Crawlability** — `robots.txt` to'g'ri, `sitemap.xml` mavjud
- [ ] **No duplicate content** — canonical teglar
- [ ] **Strukturalashtirilgan ma'lumotlar** — JSON-LD
- [ ] **Internationalization** — `hreflang` teglar

### URL strukturasi

**Yaxshi:**
```
✓ /uz/books/yashash-falsafasi-by-aliyev
✓ /uz/authors/aziz-aliyev
✓ /uz/categories/iqtisodiyot
✓ /uz/blog/monografiya-yozish-qoidalari
```

**Yomon:**
```
✗ /uz/book.php?id=12345
✗ /uz/books/12345
✗ /UZ/Books/Yashash-Falsafasi
```

### Slug yaratish

- Faqat kichik harflar
- Bo'sh joy o'rniga `-`
- Lotin alifbosi (transliteratsiya: ў→o', қ→q, ғ→g')
- Uzunlik: 50-60 belgidan kam
- Stop so'zlar (`va`, `ham`, `bu`) olib tashlanishi mumkin

```python
# Backend'da slug generatsiya
from slugify import slugify

slug = slugify(
    "Yashash falsafasi va uning ahamiyati",
    replacements=[["ў", "o"], ["қ", "q"], ["ғ", "g"]],
    lowercase=True
)
# Natija: "yashash-falsafasi-va-uning-ahamiyati"
```

### Kanonik URL'lar

Har bir sahifada `<link rel="canonical">`:

```html
<link rel="canonical" href="https://anjumanlar.com/uz/books/yashash-falsafasi" />
```

### Sahifa tezligi

**Frontend (Nuxt):**
- [ ] SSR yoqilgan (kontentni SEO uchun)
- [ ] Image optimizatsiya (Nuxt Image)
- [ ] Critical CSS inline
- [ ] Lazy load (rasmlar, komponentlar)
- [ ] Code splitting (per-route)
- [ ] Brotli/gzip compression

**Backend:**
- [ ] Redis cache (kategoriya, kitoblar ro'yxati)
- [ ] CDN (Cloudflare static fayllar uchun)
- [ ] Database indexlar

## On-Page SEO

### Title teg

**Formula:** `{Asosiy kalit so'z} — {Brand}`

**Yaxshi misollar:**
- `Yashash falsafasi — Aziz Aliyev | Anjumanlar.com`
- `Iqtisodiyot bo'yicha monografiyalar | Anjumanlar`
- `Aziz Aliyev — Anjumanlar.com mualliflari`

**Qoidalar:**
- 50-60 belgi (Google 600px ko'rsatadi)
- Asosiy kalit so'z boshida
- Brand oxirida
- Har sahifa noyob title
- Emoji va keraksiz belgilar yo'q

### Meta description

**Formula:** Tavsif + CTA

**Yaxshi misol:**
```
Aziz Aliyev tomonidan yozilgan "Yashash falsafasi" monografiyasi.
Inson hayoti va uning ma'nosi haqida zamonaviy qarashlar.
PDF formatda yuklab oling — 45 000 so'm.
```

**Qoidalar:**
- 150-160 belgi
- Kalit so'z tabiiy joylashgan
- Harakat undaydi (CTA)
- Noyob har sahifa uchun

### Heading ierarxiyasi

- **H1:** Faqat bitta sahifada, kitob nomi yoki bo'lim nomi
- **H2:** Asosiy bo'limlar
- **H3:** Quyi bo'limlar
- **H4-H6:** Kam ishlatiladi

**Yaxshi:**
```html
<h1>Yashash falsafasi</h1>
  <h2>Kitob haqida</h2>
  <h2>Muallif haqida</h2>
  <h2>Sharhlar</h2>
    <h3>Sharhlar (24)</h3>
```

### Alt matn

Har bir rasm `alt` ga ega:

```html
<!-- Yaxshi -->
<img src="cover.jpg" alt="Yashash falsafasi - Aziz Aliyev kitobining muqovasi" />

<!-- Yomon -->
<img src="cover.jpg" alt="image" />
<img src="cover.jpg" alt="" />  <!-- Bezak rasmlar uchun OK -->
```

## Kontent strategiyasi

### Blog — kontent marketing

**Maqsad:** Long-tail so'rovlar uchun trafik olish.

**Mavzu kategoriyalari:**

1. **"Qanday yoziladi?" turkumi:**
   - Monografiya qanday yoziladi?
   - Ilmiy maqola yozish qoidalari
   - Dissertatsiya himoyasi tayyorlash
   - Referat namunalari

2. **"Tavsiyalar" turkumi:**
   - 2026 yilning eng yaxshi 10 monografiyasi
   - Iqtisodchilar uchun majburiy kitoblar
   - Tibbiyot talabalari uchun darsliklar

3. **"Mualliflar haqida":**
   - Tanilgan mualliflar bilan suhbat
   - Yangi mualliflarni tanishtirish

4. **"Akademik dunyo":**
   - Universitetlardagi yangiliklar
   - Ilmiy konferensiyalar
   - Grant va stipendiyalar

### Kontent reja (oylik)

- 4 blog post (haftaga 1 ta)
- 2 muallif interv'yusi
- 1 kategoriya tahlili
- 1 hafta yangiliklari to'plami

### Kontent uzunligi

- Blog post: 1000-2500 so'z
- Tavsif sahifalari: 500-800 so'z
- Kategoriya sahifalari: 300-500 so'z intro + ro'yxat

## Mahalliy SEO (Uzbekistan)

### Yandex (muhim — auditoriya bilan ishlash)

- [ ] [Yandex Webmaster](https://webmaster.yandex.com/)'da ro'yxatdan o'tish
- [ ] Sayt tasdiqlash
- [ ] Sitemap yuborish
- [ ] Yandex Metrika o'rnatish
- [ ] Original kontent atributsiyasi
- [ ] Mobile versiya tasdiqlash

### Google

- [ ] [Google Search Console](https://search.google.com/search-console)
- [ ] Sitemap yuborish
- [ ] Index'lash so'rashi
- [ ] Mobile usability tekshirish
- [ ] Schema markup test

### Mahalliy backlink'lar

- [ ] Universitet saytlarida ko'rsatma
- [ ] Ilmiy institut'lar bilan hamkorlik
- [ ] Akademik bloglarda mehmon postlar
- [ ] Uzbek wikipedia (agar mos kelsa)
- [ ] Telegram kanallarda e'lon

## Ko'p tilli SEO (i18n)

### hreflang teglar

Har sahifada:

```html
<link rel="alternate" hreflang="uz" href="https://anjumanlar.com/uz/books/yashash-falsafasi" />
<link rel="alternate" hreflang="ru" href="https://anjumanlar.com/ru/books/yashash-falsafasi" />
<link rel="alternate" hreflang="en" href="https://anjumanlar.com/en/books/yashash-falsafasi" />
<link rel="alternate" hreflang="x-default" href="https://anjumanlar.com/uz/books/yashash-falsafasi" />
```

### Tarjima sifati

- Avtomatik tarjima EMAS — sun'iy bo'lib chiqadi
- Kalit so'zlarni har til uchun alohida tadqiq qilish
- Kitob tavsifi har til uchun professional yozilishi kerak

### Til-spetsifik bo'limlar

- Uzbek: monografiya, darslik, ilmiy adabiyot
- Rus: монография, учебник, научная литература
- English: monograph, textbook, scientific literature

## Strukturalashtirilgan ma'lumotlar (Schema.org)

Bu — Google'da yulduzcha, rasm, narx ko'rinishi uchun zarur. Batafsil keyingi faylda: [Meta va Sitemap](./02-meta-sitemap.md)

## SEO Monitoring

### Kunlik
- Uptime monitoring (saytning ishlashi)

### Haftalik
- Google Search Console — yangi xatolar, sahifalar
- Yandex Webmaster — xatolar
- Top 20 kalit so'rov pozitsiyasi (Serpstat, Ahrefs, Keys.so)

### Oylik
- Organic trafik o'sishi (GA4)
- Backlink hisoboti (Ahrefs)
- Sahifa tezligi (PageSpeed)
- Top 100 kalit so'z monitoring

### Vositalar (asboblar)

**Bepul:**
- Google Search Console
- Yandex Webmaster
- Google Analytics 4
- Yandex Metrika
- PageSpeed Insights
- Schema.org validator

**Pullik (ixtiyoriy):**
- Ahrefs / Semrush ($99+/oy) — to'liq tadqiq
- Keys.so ($10/oy) — rus tilidagi auditoriya uchun
- Screaming Frog (bepul 500 URL gacha) — texnik audit

## SEO checkist (har sahifa uchun)

- [ ] Noyob title (50-60 belgi)
- [ ] Noyob meta description (150-160 belgi)
- [ ] Bitta H1
- [ ] H2-H3 mantiqiy ierarxiya
- [ ] Canonical URL
- [ ] Open Graph teglar
- [ ] Twitter Card teglar
- [ ] hreflang teglar (3 til)
- [ ] JSON-LD strukturalashtirilgan ma'lumot
- [ ] Alt matn rasmlarda
- [ ] Internal link'lar (3-5 ta)
- [ ] External link'lar (1-2 ta avtoritet manbalarga, ixtiyoriy)
- [ ] URL slug — qisqa va kalit so'z bilan
- [ ] Sahifa tezligi tekshirilgan
- [ ] Mobile'da yaxshi ko'rinadi

## Zararli amallar (qochish)

- ✗ **Keyword stuffing** — bir kalit so'zni 20 marta yozish
- ✗ **Pulli link sotib olish** — Google jazo
- ✗ **Cloaking** — botga va foydalanuvchiga turli kontent
- ✗ **Yashirin matn** — `display: none` ichida kalit so'zlar
- ✗ **Duplicate content** — bir matn ko'p sahifalarda
- ✗ **Sun'iy backlink** — link farm, PBN
- ✗ **Auto-generated content** — past sifatli AI matn

---

**Keyingi qadam:** [Meta teglari va Sitemap](./02-meta-sitemap.md)
