# 04. Saytning Funksiyalari (Features)

> Saytning to'liq funksional ro'yxati. MVP (1-bosqich) va kelajakdagi (2-bosqich) funksiyalarga bo'lingan.

---

## ✅ MVP Funksiyalar (1-bosqich, majburiy)

### 🔐 Autentifikatsiya va profil
- [x] Email + parol orqali ro'yxatdan o'tish
- [x] Email tasdiqlash (verification link)
- [x] Kirish (login)
- [x] Parolni unutdim → email orqali tiklash
- [x] Parolni o'zgartirish
- [x] JWT token (access + refresh)
- [x] Google OAuth (ixtiyoriy, qulaylik uchun)
- [x] Profil rasm yuklash
- [x] Profil tahrirlash

### 📚 Kitoblar (Monografiyalar)
- [x] Kitob yuklash (PDF, EPUB qo'llab-quvvatlanadi)
- [x] Muqova rasmi yuklash (avtomatik kropping)
- [x] Demo (bepul qism) yuklash
- [x] 3 tilda ma'lumot kiritish (sarlavha, annotatsiya)
- [x] Kategoriya tanlash (bir nechta)
- [x] Teglar (tags)
- [x] Narx belgilash (UZS) yoki bepul qilish
- [x] ISBN, nashr yili, sahifalar soni
- [x] Status: draft → pending → approved/rejected
- [x] PDF avtomatik watermark (sotib olganda foydalanuvchi ismi/email yoziladi)

### 🔍 Qidiruv va katalog
- [x] Tezkor qidiruv (Meilisearch)
- [x] Filtrlar: kategoriya, til, narx, yil, muallif
- [x] Saralash: yangi, mashhur, arzon, qimmat, reyting
- [x] Kategoriyalar daraxti (parent-child)
- [x] Pagination
- [x] "Sizga yoqishi mumkin" tavsiyalari

### 🛒 Sotib olish va to'lov
- [x] Savatcha (cart)
- [x] Bir kitobni ham bevosita sotib olish ("Hozir sotib ol")
- [x] Payme.uz integratsiyasi
- [x] Buyurtmalar tarixi
- [x] Sotib olingan PDF avtomatik yuklab olinadi (watermark bilan)
- [x] Email orqali chek yuborish

### ⭐ Sharhlar va reyting
- [x] 1-5 yulduz reyting
- [x] Matn sharh
- [x] Sharhga rahmat ("foydali" tugmasi)
- [x] Sharhni admin moderatsiyasi
- [x] Faqat sotib olganlar sharh qoldira oladi

### 👤 Muallif kabineti
- [x] Mening kitoblarim ro'yxati
- [x] Kitob qo'shish/tahrirlash
- [x] Sotuv statistikasi (grafiklar bilan)
- [x] Balans ko'rinishi
- [x] Pul yechib olish so'rovi
- [x] Sotib oluvchilar bilan xabar yozish

### 🔧 Admin paneli
- [x] Moderatsiya navbati (yangi kitoblar)
- [x] Foydalanuvchilarni boshqarish
- [x] Buyurtmalar va to'lovlar nazorati
- [x] Statistika (dashboard)
- [x] Shikoyatlar bilan ishlash

### 🌍 Ko'p tillilik
- [x] UI 3 tilda: uz, ru, en
- [x] Til almashtirish tugmasi
- [x] URL'larda til prefiksi (`/uz/`, `/ru/`, `/en/`)
- [x] Browser tiliga qarab default

### 🎨 Tema (rejim)
- [x] Kunduzgi rejim (Light)
- [x] Tungi rejim (Dark)
- [x] Avtomatik tizim rejimiga moslashish
- [x] LocalStorage'da saqlash

### 📱 Responsive dizayn
- [x] Mobile-first
- [x] Tablet, desktop versiyalar
- [x] Touch-friendly (tugmalar yetarli katta)
- [x] Hamburger menu mobile uchun

### 🔍 SEO
- [x] Server-side rendering (SSR) yoki SSG
- [x] Meta teglar (har bir sahifa)
- [x] Open Graph (Facebook, Telegram preview)
- [x] Twitter Card
- [x] JSON-LD schema (Book, Person, BreadcrumbList)
- [x] sitemap.xml
- [x] robots.txt
- [x] Canonical URLs
- [x] Hreflang teglar (uz/ru/en)

### 📧 Email bildirishnomalar
- [x] Ro'yxatdan o'tganda welcome
- [x] Email tasdiqlash
- [x] Parolni tiklash
- [x] Yangi buyurtma (o'quvchi va muallifga)
- [x] Kitob tasdiqlandi/rad etildi (muallifga)
- [x] Pul yechib olish bajarildi

### 🔒 Xavfsizlik
- [x] Parol hash (bcrypt)
- [x] Rate limiting (login, register, password reset)
- [x] CORS sozlamasi
- [x] CSRF himoya
- [x] XSS himoya (sanitize)
- [x] SQL injection — ORM ishlatish (SQLAlchemy)
- [x] HTTPS faqat (production'da)
- [x] PDF himoya — watermark + signed URLs

---

## 🚀 Kelajakdagi funksiyalar (2-bosqich)

### Mualliflarni reklama qilish
- [ ] Premium muallif obunasi
- [ ] Bosh sahifada "Tavsiya etilgan" bo'limi
- [ ] Email marketing (newsletter)

### Kengaytirilgan kontent
- [ ] Audiokitoblar (.mp3)
- [ ] Video kurslar
- [ ] Onlayn jurnal nashri (issue based)
- [ ] Multi-author (bir necha muallifli kitob)

### Sotsial funksiyalar
- [ ] Mualliflarga obuna bo'lish
- [ ] Yangiliklar lentasi (kuzatilayotgan mualliflar)
- [ ] Sharhlarga javob berish (treelar)
- [ ] Kitob to'plamlari (collections)

### To'lovlar
- [ ] Click.uz integratsiyasi
- [ ] Uzcard/Humo to'g'ridan-to'g'ri
- [ ] Xalqaro to'lovlar (Stripe — chet ellik foydalanuvchilar uchun)
- [ ] Promokod va chegirmalar
- [ ] Affiliate dasturi

### Mobile ilova
- [ ] iOS ilovasi (React Native yoki Flutter)
- [ ] Android ilovasi
- [ ] Offline o'qish (sotib olingan kitoblar)

### Analitika
- [ ] Mualliflar uchun batafsil statistika
- [ ] A/B testing
- [ ] Konversiya tahlili
- [ ] Heatmap (foydalanuvchi xatti-harakati)

### AI funksiyalari
- [ ] Avtomatik kategoriya tavsiyasi (AI orqali kitobni tahlil qilib)
- [ ] Annotatsiyani avtomatik yaratish (PDF dan)
- [ ] Smart qidiruv (semantic search)
- [ ] Tarjima yordamchi

### O'qish tajribasi
- [ ] Onlayn PDF reader (browser ichida o'qish)
- [ ] Bookmark va eslatmalar
- [ ] Yorqinlik, shrift sozlamalari
- [ ] Sahifalarni belgilash

### Mualliflar uchun
- [ ] Kitob yozish yordamchisi (markdown editor)
- [ ] Co-authoring (hamkorlikda yozish)
- [ ] Yangilanish versiyalari (kitobning yangi nashri)
- [ ] Print on demand (jismoniy kitob chiqarish)

---

## 🎯 Funksiyalar bo'yicha bosqichlar

### **Bosqich 1: MVP** (8-10 hafta)
Foydalanuvchi → kitob ko'rish → sotib olish → muallif → kitob yuklash → admin moderatsiya

### **Bosqich 2: Yaxshilash** (4-6 hafta)
SEO, performance, bug-fix, qo'shimcha sahifalar, batafsil statistika

### **Bosqich 3: Kengaytirish** (mavjud foydalanuvchilarga qarab)
Mobile ilova, audiokitob, premium

---

## ⚠️ Texnik talablar

| Talab | Qiymat |
|-------|--------|
| Maksimal kitob fayl hajmi | 100 MB |
| Demo fayl maksimal | 20 MB |
| Muqova rasm | 800x1200px, JPG/PNG, max 5MB |
| Bir vaqtning o'zida foydalanuvchilar | 1000+ |
| Sahifa yuklash tezligi | < 2 sekund |
| API javob vaqti | < 300ms |
| Uptime | 99.5%+ |
| Backup chastotasi | Har kuni 02:00 |

---

## 📝 Funksiyalar prioritetlari (MoSCoW)

### MUST have (majburiy)
- Autentifikatsiya
- Kitob yuklash va sotib olish
- Payme to'lov
- Admin moderatsiya
- 3 tillilik
- Mobil moslashuv

### SHOULD have (kerakli)
- Tungi rejim
- SEO optimallashtirish
- Email bildirishnomalar
- Sharhlar tizimi
- Sotuv statistikasi

### COULD have (yaxshi bo'lardi)
- Google OAuth
- Onlayn PDF reader
- Sevimlilar ro'yxati
- Tezkor qidiruv (Meilisearch)

### WON'T have (hozircha yo'q)
- Mobile native ilova
- Audiokitob
- AI funksiyalar
- Chet el to'lovlari

---

**Keyingi qadam:** [`02-architecture/01-system-architecture.md`](../02-architecture/01-system-architecture.md) — Tizim arxitekturasi.
