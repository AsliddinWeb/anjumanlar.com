# UI Guidelines — Monografiya

Komponentlarni qanday joylashtirish, qachon qaysi pattern ishlatish va saytning umumiy his-tuyg'usini saqlash bo'yicha qoidalar.

## Umumiy printsiplar

1. **Kontent — qirol.** Bezak kontentni qoplamasligi kerak.
2. **Bir maqsad — bir CTA.** Har bir sahifada bitta asosiy harakat.
3. **Bo'sh joydan qo'rqmaslik.** Ko'p oq joy = professional ko'rinish.
4. **Konsistentlik takrorlanishdan muhim.** Bir xil tugma har joyda bir xil ishlaydi.
5. **Mobile-first.** Avval kichik ekran uchun loyihalash, keyin desktop.

## Sahifa tuzilishi

### Standart layout

```
┌─────────────────────────────────┐
│  Header (sticky, 64px)          │
├─────────────────────────────────┤
│                                 │
│  Breadcrumbs (ixtiyoriy)        │
│                                 │
│  Sahifa sarlavhasi              │
│                                 │
│  Asosiy kontent                 │
│                                 │
├─────────────────────────────────┤
│  Footer                         │
└─────────────────────────────────┘
```

### Container kengligi

| Sahifa turi | Max kenglik | Sabab |
|-------------|-------------|-------|
| Landing/Bosh | `max-w-7xl` (1280px) | Keng banner uchun |
| Katalog | `max-w-7xl` | Ko'p kartochka |
| Kitob batafsil | `max-w-6xl` | Markazlashtirilgan o'qish |
| Blog post | `max-w-3xl` (768px) | O'qish uchun qulay kenglik |
| Form (login, register) | `max-w-md` (448px) | Fokus |
| Admin panel | `max-w-full` | To'liq ekran tahlil |

## Header

### Tuzilish

```
[Logo]  [Katalog] [Mualliflar] [Blog]    [🔍 Qidiruv]  [🌐 Tili] [🌙] [Kirish] [Ro'yxat]
```

**Mobile (< 768px):**
```
[≡] [Logo]                                              [🔍] [👤]
```

### Qoidalar
- Sticky: `position: sticky; top: 0`
- Balandlik: 64px desktop, 56px mobile
- Background: `bg-bg-card/80 backdrop-blur-md` (yarim shaffof, blur)
- Border bottom: `border-b border-border`
- Z-index: 50

### Header pasayganda

Scroll qilganda header'ni yashirish (mobile UX):
- `scroll down` — header yashirinadi
- `scroll up` — header qaytadi

## Footer

### Tuzilish

```
┌──────────────────────────────────────────────────┐
│  [Logo]                                          │
│  Bilim baham ko'rish platformasi.                │
│                                                  │
│  Kompaniya       Foydalanuvchilar  Yordam        │
│  • Biz haqimizda • Mualliflar      • FAQ         │
│  • Bog'lanish    • O'quvchilar     • Yordam      │
│                                                  │
├──────────────────────────────────────────────────┤
│  © 2026 Monografiya  •  Foydalanish • Maxfiy │
└──────────────────────────────────────────────────┘
```

### Qoidalar
- Background: `bg-bg-secondary`
- Padding: `py-12 md:py-16`
- 4-5 ustun desktop, 1-2 ustun mobile
- Pastki copyright qatori alohida
- Til tanlovi va dark mode toggle footer'da ham (ixtiyoriy)

## Kitob kartochkasining variantlari

### 1. Grid card (asosiy, katalog uchun)
- Cover: 2:3 nisbat
- Sarlavha + muallif + narx + reyting
- O'lcham: ~180px kenglik mobile, ~220px desktop

### 2. List card (qidiruv natijalari uchun)
- Cover: 80x120px chap tomonda
- O'ng tomonda: sarlavha, muallif, qisqa tavsif, narx, tugma
- Vertikal joy ko'proq

### 3. Featured card (bosh sahifa "Tavsiya etiladi" uchun)
- Katta cover: 280x420px
- Yon tomonda batafsil ma'lumot
- "Tafsilotlar" tugmasi

### 4. Mini card (sidebar, "O'xshashlar" uchun)
- Kichik cover: 60x90px
- Faqat sarlavha + narx

## Form'lar

### Vertikal joylashish (default)

```html
<form class="space-y-6">
  <div>
    <label class="block text-sm font-medium mb-2">Email</label>
    <input class="input-style" type="email" />
    <p class="mt-1 text-xs text-text-tertiary">Email manzilingiz</p>
  </div>

  <div>
    <label class="block text-sm font-medium mb-2">Parol</label>
    <input class="input-style" type="password" />
  </div>

  <button class="btn-primary w-full">Kirish</button>
</form>
```

### Form qoidalari

- **Label har doim input'dan tepada** (placeholder label'ni almashtirmaydi)
- Required maydonlar: `*` belgisi
- Error matn input ostida, qizil rangda
- Helper matn input ostida, kulrang rangda
- Submit tugmasi formaning so'nggi elementi
- Tab tartib mantiqiy bo'lishi kerak
- Enter tugmasi formani submit qilishi kerak

### Loading holatlar

Submit qilinganda:
- Tugma `disabled` bo'ladi
- Tugma ichida spinner ko'rinadi
- Tugma matni o'zgaradi: "Kirish" → "Kirilmoqda..."

```vue
<button :disabled="loading" class="btn-primary">
  <Spinner v-if="loading" class="size-4 mr-2" />
  {{ loading ? 'Kirilmoqda...' : 'Kirish' }}
</button>
```

## Bildirishnomalar (Notifications / Toasts)

### Joylashuv
- Desktop: pastki o'ng burchak (`bottom-4 right-4`)
- Mobile: tepa, markazlashtirilgan (`top-4 left-1/2 -translate-x-1/2`)

### Turlari

```html
<!-- Success -->
<div class="bg-success/10 border-l-4 border-success text-success p-4 rounded">
  ✓ Muvaffaqiyatli saqlandi
</div>

<!-- Error -->
<div class="bg-error/10 border-l-4 border-error text-error p-4 rounded">
  ✕ Xato yuz berdi
</div>

<!-- Warning -->
<div class="bg-warning/10 border-l-4 border-warning text-warning p-4 rounded">
  ⚠ Diqqat: Bu amalni qaytarib bo'lmaydi
</div>

<!-- Info -->
<div class="bg-info/10 border-l-4 border-info text-info p-4 rounded">
  ℹ Profil yangilandi
</div>
```

### Qoidalar
- 3-5 sekund avtomatik yo'qoladi
- Foydalanuvchi qo'lda yopa olishi mumkin (✕)
- Bir vaqtda 3'dan ko'p toast bo'lmasligi kerak
- Ovozsiz (kerak bo'lsa, vibratsiya mobile)

## Modal va Dialog

### Qachon ishlatish kerak
- ✓ Tasdiqlash: "Rostdan ham o'chirilsinmi?"
- ✓ Tezkor form: parolni o'zgartirish
- ✓ Login/Register (sahifa o'rniga)
- ✗ Uzun forma — alohida sahifa qiling
- ✗ Asosiy navigatsiya — modal emas

### Tuzilish

```html
<div class="modal-overlay fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
  <div class="modal-content bg-bg-card rounded-lg shadow-lg max-w-md w-full p-6">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-semibold">Modal sarlavhasi</h2>
      <button @click="close" class="text-text-tertiary hover:text-text-primary">✕</button>
    </div>
    <div>Modal kontenti...</div>
    <div class="flex justify-end gap-3 mt-6">
      <button class="btn-ghost">Bekor qilish</button>
      <button class="btn-primary">Tasdiqlash</button>
    </div>
  </div>
</div>
```

### Qoidalar
- ESC tugmasi modal'ni yopadi
- Overlay'ga bosish ham yopadi (faqat ma'lumot uchun bo'lsa)
- Destructive modal'lar (o'chirish) overlay bosishni o'chirib qo'yishi mumkin
- Body scroll bloklash (`overflow: hidden` body'da)
- Focus trap: modal ichida tab ishlashi kerak
- Birinchi input avtomatik fokus

## Bo'sh holatlar (Empty states)

Foydalanuvchi hali kitob qo'shmagan, qidiruv natijasi yo'q, va hokazo.

```html
<div class="text-center py-16">
  <Icon name="lucide:book-open" class="size-16 mx-auto text-text-tertiary mb-4" />
  <h3 class="text-lg font-semibold mb-2">Hozircha kitoblar yo'q</h3>
  <p class="text-text-secondary mb-6">
    Birinchi monografiyangizni yuklang va sotuvni boshlang.
  </p>
  <NuxtLink to="/author/books/new" class="btn-primary">
    Kitob qo'shish
  </NuxtLink>
</div>
```

### Empty state komponentlari
- Icon (yumshoq, kulrang)
- Sarlavha (nima yo'qligi)
- Tavsif (nima qilish kerak)
- CTA tugma (yo'l ko'rsatish)

## Yuklanish holatlari (Loading states)

### 1. Skeleton (kontent shakli mavjud)

```html
<div class="animate-pulse">
  <div class="aspect-[2/3] bg-bg-secondary rounded-sm mb-3"></div>
  <div class="h-4 bg-bg-secondary rounded w-3/4 mb-2"></div>
  <div class="h-3 bg-bg-secondary rounded w-1/2"></div>
</div>
```

### 2. Spinner (kichik joy)

```html
<div class="flex justify-center py-8">
  <div class="size-8 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
</div>
```

### 3. Full-page loader (faqat boshlang'ich yuklashda)
- Logo + spinner
- 1 sekunddan ko'p emas

## Xato holatlari

### 404 sahifa
```html
<div class="min-h-[60vh] flex flex-col items-center justify-center text-center px-4">
  <h1 class="font-display text-8xl text-primary mb-4">404</h1>
  <h2 class="text-2xl font-semibold mb-3">Sahifa topilmadi</h2>
  <p class="text-text-secondary mb-8 max-w-md">
    Siz qidirayotgan sahifa mavjud emas yoki ko'chirilgan.
  </p>
  <div class="flex gap-3">
    <NuxtLink to="/" class="btn-primary">Bosh sahifa</NuxtLink>
    <NuxtLink to="/catalog" class="btn-ghost">Katalogga o'tish</NuxtLink>
  </div>
</div>
```

### 500 / Server xatosi
- Foydalanuvchini ayblamang
- "Yana urinib ko'rish" tugmasi
- Sentry'ga avtomatik xabar yuboriladi

## Accessibility (a11y)

### Majburiy talablar

- [ ] Har bir tugmaning aniq matni yoki `aria-label` mavjud
- [ ] Har bir input'da `label` (label maxfiy bo'lsa `sr-only`)
- [ ] Form xatolar `aria-describedby` orqali ulangan
- [ ] Modal'da `role="dialog"` va `aria-modal="true"`
- [ ] Tugma va link rolini aralashtirmaslik
- [ ] Klaviatura bilan barcha funksiyalarga kirish mumkin
- [ ] Focus indicator har doim ko'rinadi (`focus:ring-2`)
- [ ] Rang kontrasti WCAG AA: 4.5:1 matn uchun
- [ ] Alt matn rasmlarda

### Tab tartib

Mantiqiy ketma-ketlik: tepadan pastga, chapdan o'ngga.

### Sr-only matn

```html
<button>
  <Icon name="lucide:heart" />
  <span class="sr-only">Sevimlilarga qo'shish</span>
</button>
```

## Responsive xulq

### Breakpoint'lar bo'yicha o'zgarishlar

| Element | Mobile | Tablet | Desktop |
|---------|--------|--------|---------|
| Header navigatsiya | Hamburger menu | Inline | Inline |
| Kitob grid | 2 ustun | 3 ustun | 4-5 ustun |
| Sidebar (filter) | Drawer (slide-out) | Drawer | Inline |
| Footer ustunlari | 1-2 | 3 | 4-5 |
| Padding | `px-4 py-8` | `px-6 py-12` | `px-8 py-16` |
| Sarlavha | `text-3xl` | `text-4xl` | `text-5xl` |

### Mobile maxsus

- Tugma minimal o'lcham: 44x44px (touch target)
- Form input balandlik: 44px+
- Bottom sheet (mobile menu pastdan chiqadi)
- Swipe gesture (carousel uchun)

## Tasvir va rasm

### Cover'lar
- Optimal o'lcham: 600x900px (2:3)
- Format: WebP (fallback JPEG)
- Quality: 85
- Lazy load: `loading="lazy"` (birinchi 4 ta tashqari)
- Placeholder: blur yoki kulrang fon

### Banner / Hero
- Mobile: 800x600px
- Desktop: 1920x800px
- Format: WebP
- Optimallashtirilgan: 200KB dan kam

```html
<img
  src="cover.webp"
  srcset="cover-300.webp 300w, cover-600.webp 600w, cover-1200.webp 1200w"
  sizes="(max-width: 768px) 50vw, 25vw"
  loading="lazy"
  alt="Kitob nomi" />
```

## Microcopy — matn yo'riqlari

### Tugmalar
- ✓ "Sotib olish" (aniq, harakatga undaydi)
- ✗ "Yubor" (nima yuboriladi?)
- ✓ "Bepul yuklab olish"
- ✗ "OK"

### Tasdiqlash
- ✓ "Ha, o'chirish"
- ✗ "OK"

### Xatolar
- ✓ "Email manzili noto'g'ri formatda"
- ✗ "Xato"

### Bo'sh holat
- ✓ "Hali xaridingiz yo'q. Birinchi kitobingizni tanlang."
- ✗ "Hech narsa topilmadi"

### Til
- Hurmatli, lekin formal emas
- "Siz" emas, "siz" (kichik harf, kontekstga qarab)
- Texnik atamalardan qochish: "Server xatosi" emas, "Texnik nosozlik"

---

**Keyingi qadam:** [SEO Strategiyasi](../09-seo/01-seo-strategy.md)
