# 03. Saytdagi Barcha Sahifalar Ro'yxati

> Saytning to'liq sahifalar strukturasi. URL'lar `/uz/` prefiks bilan keladi (i18n). Misol uchun bosh sahifa: `monografiya.com/uz/`.

---

## 🌐 Ommaviy sahifalar (Guest + barcha foydalanuvchilar)

| # | Nomi | URL | Tavsifi |
|---|------|-----|---------|
| 1 | Bosh sahifa | `/` | Hero, yangi kitoblar, kategoriyalar, top mualliflar |
| 2 | Katalog | `/books` | Barcha kitoblar (filtr, saralash, qidiruv) |
| 3 | Kitob tavsiloti | `/books/[slug]` | Yagona kitob sahifasi, sotib olish tugmasi |
| 4 | Kategoriya | `/category/[slug]` | Aniq kategoriya kitoblari |
| 5 | Mualliflar | `/authors` | Barcha mualliflar ro'yxati |
| 6 | Muallif profili | `/authors/[slug]` | Muallifning barcha kitoblari va biografiyasi |
| 7 | Qidiruv | `/search?q=...` | Qidiruv natijalari |
| 8 | Blog | `/blog` | Maqolalar (SEO uchun) |
| 9 | Blog maqolasi | `/blog/[slug]` | Yagona blog maqolasi |
| 10 | Biz haqimizda | `/about` | Saytning maqsadi va jamoasi |
| 11 | Aloqa | `/contact` | Kontakt formasi |
| 12 | FAQ | `/faq` | Tez-tez beriladigan savollar |
| 13 | Foydalanish shartlari | `/terms` | Terms of Service |
| 14 | Maxfiylik siyosati | `/privacy` | Privacy Policy |
| 15 | Muallif bo'lish | `/become-author` | Muallif bo'lish uchun ma'lumot |
| 16 | Sertifikat / Litsenziya | `/license` | Mualliflik shartnomasi haqida |
| 17 | 404 | `/404` | Topilmadi sahifasi |
| 18 | 500 | `/500` | Server xatosi |

---

## 🔐 Autentifikatsiya sahifalari

| # | Nomi | URL | Tavsifi |
|---|------|-----|---------|
| 19 | Kirish | `/auth/login` | Email + parol |
| 20 | Ro'yxatdan o'tish | `/auth/register` | Yangi hisob yaratish |
| 21 | Parolni unutdim | `/auth/forgot-password` | Email yuborish |
| 22 | Parolni tiklash | `/auth/reset-password?token=...` | Yangi parol kiritish |
| 23 | Emailni tasdiqlash | `/auth/verify-email?token=...` | Email tasdiqlash linkdan |
| 24 | Chiqish | `/auth/logout` | Sessiyani tugatish |

---

## 🔵 O'quvchi kabineti

URL prefiks: `/account/`

| # | Nomi | URL | Tavsifi |
|---|------|-----|---------|
| 25 | Dashboard | `/account` | Umumiy ko'rinish |
| 26 | Mening kutubxonam | `/account/library` | Sotib olingan kitoblar |
| 27 | Sevimlilarim | `/account/favorites` | Wishlist |
| 28 | Buyurtmalarim | `/account/orders` | Sotib olish tarixi |
| 29 | Buyurtma tafsiloti | `/account/orders/[id]` | Yagona buyurtma |
| 30 | Sharhlarim | `/account/reviews` | Yozgan sharhlarim |
| 31 | Profil | `/account/profile` | Shaxsiy ma'lumotlar |
| 32 | Sozlamalar | `/account/settings` | Parol, til, bildirishnomalar |
| 33 | Muallif bo'lish | `/account/become-author` | Muallif arizasi |

---

## 🟢 Muallif kabineti

URL prefiks: `/author/`

| # | Nomi | URL | Tavsifi |
|---|------|-----|---------|
| 34 | Dashboard | `/author` | Umumiy statistika |
| 35 | Mening kitoblarim | `/author/books` | Yuklangan kitoblar ro'yxati |
| 36 | Yangi kitob | `/author/books/new` | Kitob qo'shish formasi |
| 37 | Kitob tahrir | `/author/books/[id]/edit` | Kitobni tahrirlash |
| 38 | Sotuvlar | `/author/sales` | Sotuv statistikasi va grafiklar |
| 39 | Balans | `/author/balance` | Mening daromadlarim |
| 40 | Pul yechib olish | `/author/withdrawals` | Withdraw so'rovlari |
| 41 | Profil | `/author/profile` | Muallif profili |
| 42 | Shartnoma | `/author/contract` | Mualliflik shartnomasi |
| 43 | Xabarlar | `/author/messages` | O'quvchilar bilan xabar |

---

## 🟠 Admin paneli

URL prefiks: `/admin/`

| # | Nomi | URL | Tavsifi |
|---|------|-----|---------|
| 44 | Dashboard | `/admin` | Umumiy statistika |
| 45 | Moderatsiya | `/admin/moderation` | Tasdiqlashni kutayotgan kitoblar |
| 46 | Barcha kitoblar | `/admin/books` | Barcha kitoblar boshqaruvi |
| 47 | Kitob tafsilot | `/admin/books/[id]` | Kitobni ko'rish va tahrir |
| 48 | Foydalanuvchilar | `/admin/users` | Foydalanuvchilar ro'yxati |
| 49 | Foydalanuvchi profili | `/admin/users/[id]` | Yagona foydalanuvchi |
| 50 | Mualliflar | `/admin/authors` | Faqat mualliflar |
| 51 | Buyurtmalar | `/admin/orders` | Barcha buyurtmalar |
| 52 | To'lovlar | `/admin/payments` | To'lov tarixi |
| 53 | Shikoyatlar | `/admin/complaints` | O'quvchilarning shikoyatlari |
| 54 | Statistika | `/admin/analytics` | Batafsil hisobotlar |

---

## 🔴 SuperAdmin qo'shimcha sahifalari

Admin sahifalariga qo'shimcha:

| # | Nomi | URL | Tavsifi |
|---|------|-----|---------|
| 55 | Adminlar | `/admin/admins` | Adminlarni boshqarish |
| 56 | Pul yechishlar | `/admin/withdrawals` | Mualliflar so'rovlarini tasdiqlash |
| 57 | Komissiya sozlamalari | `/admin/settings/commission` | Foiz belgilash |
| 58 | Kategoriyalar | `/admin/categories` | CRUD kategoriya |
| 59 | Tarjimalar | `/admin/translations` | UI matnlari tarjimasi |
| 60 | Sayt sozlamalari | `/admin/settings/site` | Logo, banner, kontakt |
| 61 | Email shablonlari | `/admin/settings/emails` | Email matnlari |
| 62 | Tizim loglari | `/admin/logs` | Xavfsizlik loglari |
| 63 | Backup | `/admin/backup` | Backup va restore |

---

## 💳 To'lov sahifalari

| # | Nomi | URL | Tavsifi |
|---|------|-----|---------|
| 64 | Savatcha | `/cart` | Sotib olishdan oldin |
| 65 | To'lov | `/checkout` | Payme'ga yo'naltirish oldi |
| 66 | To'lov muvaffaqiyatli | `/payment/success` | Payme'dan qaytgan |
| 67 | To'lov muvaffaqiyatsiz | `/payment/failed` | Xatolik |
| 68 | To'lov bekor qilindi | `/payment/cancelled` | Foydalanuvchi bekor qildi |

---

## 📊 Sahifalar bo'yicha jami soni

| Bo'lim | Sahifalar soni |
|--------|----------------|
| Ommaviy | 18 |
| Autentifikatsiya | 6 |
| O'quvchi kabineti | 9 |
| Muallif kabineti | 10 |
| Admin paneli | 11 |
| SuperAdmin qo'shimcha | 9 |
| To'lov | 5 |
| **JAMI** | **68** |

---

## 🗺 Sahifa iyerarxiyasi (Sitemap)

```
monografiya.com/
├── / (bosh sahifa)
├── /books
│   ├── /books/[slug]
│   └── /books/new (muallif)
├── /category/[slug]
├── /authors
│   └── /authors/[slug]
├── /search
├── /blog
│   └── /blog/[slug]
├── /about
├── /contact
├── /faq
├── /terms
├── /privacy
│
├── /auth/
│   ├── login
│   ├── register
│   ├── forgot-password
│   ├── reset-password
│   ├── verify-email
│   └── logout
│
├── /account/ (o'quvchi)
│   ├── library
│   ├── favorites
│   ├── orders
│   ├── reviews
│   ├── profile
│   └── settings
│
├── /author/ (muallif)
│   ├── books
│   │   ├── new
│   │   └── [id]/edit
│   ├── sales
│   ├── balance
│   ├── withdrawals
│   ├── profile
│   └── messages
│
├── /admin/ (admin va superadmin)
│   ├── moderation
│   ├── books
│   ├── users
│   ├── authors
│   ├── orders
│   ├── payments
│   ├── complaints
│   ├── analytics
│   │
│   ├── admins (faqat SuperAdmin)
│   ├── withdrawals (faqat SuperAdmin)
│   ├── categories (faqat SuperAdmin)
│   ├── translations (faqat SuperAdmin)
│   └── settings/
│       ├── commission
│       ├── site
│       └── emails
│
├── /cart
├── /checkout
└── /payment/
    ├── success
    ├── failed
    └── cancelled
```

---

## 📝 Eslatmalar

1. **URL slug formati** — kitob va kategoriya nomi inglizcha translit qilingan, kichik harf, defis bilan ajratilgan:
   - Misol: `tibbiyot-asoslari-2024` (yaxshi)
   - Misol: `Tibbiyot_Asoslari` (yomon)

2. **i18n** — URL'lar `/uz/`, `/ru/`, `/en/` prefiks bilan keladi. Default sifatida `/uz/` (yoki Accept-Language header'ga qarab).

3. **Breadcrumbs** — har bir sahifada Bosh sahifa → Kategoriya → Kitob ko'rinishida ko'rsatiladi (SEO uchun ham foydali).

4. **Lazy loading** — Vue Router'da har bir sahifa alohida chunk sifatida yuklanadi.

5. **Protected routes** — `/account/`, `/author/`, `/admin/` middleware bilan himoyalangan.

---

**Keyingi qadam:** [`04-features.md`](./04-features.md) — Funksiyalar to'liq ro'yxati.
