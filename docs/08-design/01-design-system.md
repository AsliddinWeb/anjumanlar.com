# Design System — Anjumanlar.com

Saytning vizual tili. "Zamonaviy raqamli kutubxona" estetikasi: iliq, ishonarli, akademik lekin zerikarli emas.

## Dizayn falsafasi

**Asosiy g'oya:** Anjumanlar — bu raqamli kutubxona. Foydalanuvchi sahifaga kirganda kitob do'koniga kelgandek his qilishi kerak: tinch, tartibli, izlanishga undovchi.

**Tamoyillar:**
- **Iliq, qog'oz-siyoh palitra** — sovuq Material/Apple dizaynidan farqli
- **Tipografika asosiy** — kitoblar dunyosida shrift muhim
- **Kontent birinchi** — bezak ikkinchi darajada
- **Tezlik** — sahifalar 1 sekunddan tez ochilishi kerak
- **Konsistentlik** — bir xil element har joyda bir xil ko'rinadi

## Ranglar palitra

### Light mode (asosiy)

```css
:root {
  /* Brand — iliq qog'oz va siyoh */
  --color-primary: #8B4513;          /* Saddle Brown — asosiy aksent */
  --color-primary-hover: #6B3410;
  --color-primary-light: #D2691E;    /* Chocolate */

  /* Accent ranglar */
  --color-accent-gold: #C9A961;      /* Eski oltin — premium, mukofotlar */
  --color-accent-burgundy: #722F37;  /* Burgundy — CTA */
  --color-accent-forest: #2D5016;    /* Forest green — muvaffaqiyat, "Bepul" */

  /* Neytral — qog'oz tonalari */
  --color-bg: #FAF7F2;               /* Iliq qog'oz fon */
  --color-bg-secondary: #F5F0E8;     /* Sahifalar orasi */
  --color-bg-card: #FFFFFF;          /* Karta foni */
  --color-bg-elevated: #FFFFFF;      /* Modal, dropdown */

  /* Matn — siyoh tonalari */
  --color-text-primary: #1A1410;     /* Quyuq siyoh */
  --color-text-secondary: #4A3F35;   /* O'rta siyoh */
  --color-text-tertiary: #8B7E70;    /* Och, hint */
  --color-text-inverse: #FAF7F2;     /* Tugma ichidagi matn */

  /* Border */
  --color-border: #E8DFD0;
  --color-border-hover: #D4C5A9;

  /* Semantic */
  --color-success: #2D5016;
  --color-warning: #B8860B;
  --color-error: #8B0000;
  --color-info: #4682B4;

  /* Shadow */
  --shadow-sm: 0 1px 2px rgba(26, 20, 16, 0.06);
  --shadow-md: 0 4px 6px rgba(26, 20, 16, 0.08);
  --shadow-lg: 0 10px 25px rgba(26, 20, 16, 0.12);
  --shadow-book: 0 8px 20px rgba(139, 69, 19, 0.15);  /* Kitob uchun maxsus */
}
```

### Dark mode

```css
.dark {
  /* Brand — qora siyoh ustida och oltin */
  --color-primary: #D4A574;
  --color-primary-hover: #E0B584;
  --color-primary-light: #E8C99A;

  /* Accent */
  --color-accent-gold: #D4AF37;
  --color-accent-burgundy: #A04050;
  --color-accent-forest: #4A7C2A;

  /* Neytral — quyuq qog'oz */
  --color-bg: #1A1614;               /* Quyuq jigarrang-qora */
  --color-bg-secondary: #221E1A;
  --color-bg-card: #2A2520;
  --color-bg-elevated: #332E28;

  /* Matn */
  --color-text-primary: #F0E6D6;
  --color-text-secondary: #C8B89A;
  --color-text-tertiary: #8B7E6A;
  --color-text-inverse: #1A1614;

  /* Border */
  --color-border: #3D3530;
  --color-border-hover: #4D453E;

  /* Semantic */
  --color-success: #6B9E4A;
  --color-warning: #DAA520;
  --color-error: #CD5C5C;
  --color-info: #5F9EA0;

  /* Shadow */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.5);
  --shadow-book: 0 8px 20px rgba(212, 165, 116, 0.15);
}
```

### Rang foydalanish qoidalari

| Element | Light | Dark |
|---------|-------|------|
| Asosiy CTA tugma | `bg-primary` | `bg-primary` |
| Hover holati | `bg-primary-hover` | `bg-primary-hover` |
| Bepul kitob badge | `bg-accent-forest` | `bg-accent-forest` |
| Premium / Bestseller | `bg-accent-gold` | `bg-accent-gold` |
| Xato xabarlari | `text-error` | `text-error` |
| Kartochka foni | `bg-card` | `bg-card` |
| Sahifaning umumiy foni | `bg` | `bg` |

## Tipografika

### Shriftlar tanlovi

| Shrift | Maqsad | Sabab |
|--------|--------|-------|
| **Inter** | UI matn, tugmalar, formalar | Zamonaviy, o'qiluvchan, ko'p tilli (uz/ru) |
| **Lora** | Kitob nomlari, sarlavhalar | Serif — kitob, akademik tuyg'u |
| **Playfair Display** | Hero sarlavha, alohida ta'kid | Klassik kitob estetikasi |
| **JetBrains Mono** | Kod, ID raqamlar | Texnik elementlar uchun |

### Yuklash (`assets/css/main.css`)

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Lora:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Playfair+Display:wght@400;700;900&display=swap');

:root {
  --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
  --font-serif: 'Lora', Georgia, serif;
  --font-display: 'Playfair Display', 'Lora', Georgia, serif;
  --font-mono: 'JetBrains Mono', monospace;
}
```

### O'lcham shkalasi

```css
/* Tailwind config'da */
fontSize: {
  'xs':   ['0.75rem',  { lineHeight: '1rem' }],     /* 12px */
  'sm':   ['0.875rem', { lineHeight: '1.25rem' }],  /* 14px */
  'base': ['1rem',     { lineHeight: '1.5rem' }],   /* 16px — asosiy */
  'lg':   ['1.125rem', { lineHeight: '1.75rem' }],  /* 18px */
  'xl':   ['1.25rem',  { lineHeight: '1.75rem' }],  /* 20px */
  '2xl':  ['1.5rem',   { lineHeight: '2rem' }],     /* 24px */
  '3xl':  ['1.875rem', { lineHeight: '2.25rem' }],  /* 30px */
  '4xl':  ['2.25rem',  { lineHeight: '2.5rem' }],   /* 36px */
  '5xl':  ['3rem',     { lineHeight: '1' }],        /* 48px */
  '6xl':  ['3.75rem',  { lineHeight: '1' }],        /* 60px — hero */
}
```

### Tipografika namunalari

```html
<!-- Hero sarlavha -->
<h1 class="font-display text-5xl md:text-6xl font-bold tracking-tight">
  Bilim — kelajak kaliti
</h1>

<!-- Sahifa sarlavhasi -->
<h1 class="font-serif text-4xl font-semibold">
  Yangi monografiyalar
</h1>

<!-- Kitob nomi -->
<h2 class="font-serif text-2xl font-medium leading-snug">
  Sun'iy intellekt asoslari
</h2>

<!-- Bo'lim sarlavhasi -->
<h3 class="font-sans text-xl font-semibold">
  Mualliflar haqida
</h3>

<!-- Body matn -->
<p class="font-sans text-base leading-relaxed text-text-secondary">
  Asosiy matn shu yerda...
</p>

<!-- Sitata -->
<blockquote class="font-serif italic text-lg border-l-4 border-primary pl-4">
  "Kitob — eng yaxshi do'st"
</blockquote>
```

## Bo'shliq tizimi (Spacing)

Tailwind'ning standart `0.25rem` (4px) bazasi ishlatiladi.

| Token | Qiymat | Foydalanish |
|-------|--------|-------------|
| `p-1` | 4px | Juda kichik (badge ichidagi padding) |
| `p-2` | 8px | Kichik (icon button) |
| `p-3` | 12px | Form input |
| `p-4` | 16px | **Standart card padding** |
| `p-6` | 24px | Katta card |
| `p-8` | 32px | Section padding mobile |
| `p-12` | 48px | Section padding tablet |
| `p-16` | 64px | Section padding desktop |
| `gap-4` | 16px | **Standart grid gap** |
| `gap-8` | 32px | Katta section orasi |

**Qoida:** Vertikal ritm 4'ning karralari bilan (4, 8, 12, 16, 24, 32, 48, 64).

## Border radius

```css
borderRadius: {
  'none': '0',
  'sm':   '0.25rem',   /* 4px — kichik elementlar */
  'DEFAULT': '0.5rem', /* 8px — tugmalar, input */
  'md':   '0.75rem',   /* 12px — cards */
  'lg':   '1rem',      /* 16px — modallar */
  'xl':   '1.5rem',    /* 24px — katta featured cards */
  'full': '9999px',    /* avatar, pill badge */
}
```

**Kitob muqovasi uchun:** `rounded-sm` (kitob real ko'rinishi uchun deyarli to'g'ri burchak).

## Komponentlar — vizual qoidalar

### Tugmalar (Buttons)

```html
<!-- Primary -->
<button class="px-6 py-3 bg-primary text-white rounded-lg font-medium
               hover:bg-primary-hover transition-colors
               focus:outline-none focus:ring-2 focus:ring-primary/50">
  Sotib olish
</button>

<!-- Secondary -->
<button class="px-6 py-3 bg-bg-secondary text-text-primary border border-border
               rounded-lg font-medium hover:bg-bg-card transition-colors">
  Bekor qilish
</button>

<!-- Ghost -->
<button class="px-6 py-3 text-primary hover:bg-primary/10
               rounded-lg font-medium transition-colors">
  Batafsil
</button>

<!-- Destructive -->
<button class="px-6 py-3 bg-error text-white rounded-lg font-medium
               hover:bg-error/90 transition-colors">
  O'chirish
</button>
```

**O'lchamlar:**
- `sm`: `px-3 py-1.5 text-sm`
- `md` (default): `px-6 py-3 text-base`
- `lg`: `px-8 py-4 text-lg`

### Kartochkalar (Cards)

```html
<div class="bg-bg-card border border-border rounded-md p-6
            hover:shadow-md transition-shadow">
  <!-- content -->
</div>
```

**Kitob kartochkasi:** alohida — `shadow-book` ishlatiladi.

### Form elementlari

```html
<!-- Input -->
<input class="w-full px-4 py-3 bg-bg-card border border-border rounded-lg
              text-text-primary placeholder:text-text-tertiary
              focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20
              transition-colors" />

<!-- Label -->
<label class="block text-sm font-medium text-text-secondary mb-2">
  Email
</label>

<!-- Error -->
<p class="mt-1 text-sm text-error">
  Email noto'g'ri formatda
</p>
```

### Badge

```html
<!-- Bepul -->
<span class="px-2 py-1 bg-accent-forest/10 text-accent-forest text-xs font-medium rounded">
  Bepul
</span>

<!-- Yangi -->
<span class="px-2 py-1 bg-primary/10 text-primary text-xs font-medium rounded">
  Yangi
</span>

<!-- Bestseller -->
<span class="px-2 py-1 bg-accent-gold/15 text-accent-gold text-xs font-medium rounded">
  Bestseller
</span>
```

## Iconography

**Kutubxona:** [Lucide Icons](https://lucide.dev/) (`lucide-vue-next`)

**Sabab:** Stroke-based, zamonaviy, kichik bundle, ko'p icon (1000+).

**Standart o'lchamlar:**
- `size-4` (16px) — inline icon
- `size-5` (20px) — tugma ichida
- `size-6` (24px) — header
- `size-8` (32px) — feature card

```vue
<Icon name="lucide:book-open" class="size-5" />
<Icon name="lucide:shopping-cart" class="size-5" />
<Icon name="lucide:user" class="size-6" />
```

**Kitob mavzusiga oid asosiy ikonlar:** `book`, `book-open`, `library`, `bookmark`, `pen-tool`, `feather`, `scroll`, `user`, `users`, `shopping-cart`, `download`, `star`, `heart`.

## Animatsiya va o'tishlar

```css
/* Standart transitions */
.transition-fast { transition: all 150ms ease-in-out; }
.transition-base { transition: all 250ms ease-in-out; }
.transition-slow { transition: all 400ms ease-in-out; }
```

**Qoidalar:**
- Hover effektlar: 150-200ms
- Modal ochilishi: 250ms
- Sahifa o'tishlari: 300-400ms
- Hech qachon 500ms'dan ko'p emas (tezlikni his etish uchun)

**Easing:**
- UI elementlari: `ease-in-out`
- Modal kirishi: `ease-out`
- Modal chiqishi: `ease-in`

## Grid va Layout

```css
/* Container */
.container {
  max-width: 1280px;  /* 7xl */
  margin: 0 auto;
  padding: 0 1rem;     /* mobile */
}

@media (min-width: 768px) {
  .container { padding: 0 2rem; }
}
```

**Breakpoint'lar (Tailwind default):**
- `sm`: 640px — kichik telefonlar
- `md`: 768px — planshet
- `lg`: 1024px — laptop
- `xl`: 1280px — desktop
- `2xl`: 1536px — katta ekran

**Kitob katalogi grid:**
```html
<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 md:gap-6">
  <!-- BookCard'lar -->
</div>
```

## Dark mode'da maxsus holatlar

### PDF Viewer
PDF'ni dark mode'da invert qilish kerak emas (matn buziladi). O'rniga viewer foni:
```css
.dark .pdf-viewer { background: #2A2520; }
```

### Rasm chegaralari
Dark mode'da rasmlarning oq foni ko'zga uradi. Yumshatish:
```css
.dark img { filter: brightness(0.95); }
```

### Kod bloklari
Light: `bg-bg-secondary text-text-primary`
Dark: `bg-bg-card text-text-primary` (boshqacha kontrast)

## Misol: Kitob kartochkasining to'liq dizayni

```vue
<template>
  <article class="group">
    <NuxtLink :to="`/books/${book.slug}`">
      <!-- Cover -->
      <div class="relative aspect-[2/3] mb-3 overflow-hidden rounded-sm
                  bg-bg-secondary shadow-book
                  group-hover:shadow-lg transition-shadow">
        <img :src="book.cover" :alt="book.title"
             class="w-full h-full object-cover
                    group-hover:scale-105 transition-transform duration-300" />

        <!-- Badge -->
        <div v-if="book.is_free"
             class="absolute top-2 right-2 px-2 py-1
                    bg-accent-forest text-white text-xs font-medium rounded">
          Bepul
        </div>
      </div>

      <!-- Info -->
      <h3 class="font-serif text-base font-medium leading-snug
                 text-text-primary line-clamp-2 group-hover:text-primary
                 transition-colors">
        {{ book.title }}
      </h3>

      <p class="mt-1 text-sm text-text-tertiary">
        {{ book.author_name }}
      </p>

      <!-- Price + Rating -->
      <div class="mt-2 flex items-center justify-between">
        <span class="font-semibold text-primary">
          {{ formatPrice(book.price) }}
        </span>
        <div class="flex items-center gap-1 text-sm text-text-tertiary">
          <Icon name="lucide:star" class="size-4 fill-accent-gold text-accent-gold" />
          {{ book.rating }}
        </div>
      </div>
    </NuxtLink>
  </article>
</template>
```

---

**Keyingi qadam:** [UI Guidelines](./02-ui-guidelines.md)
