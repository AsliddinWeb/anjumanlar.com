# 01. Loyiha Xulosasi (Project Summary)

## 🎯 Loyihaning maqsadi

**Monografiya** — bu mualliflar (ilm-fan vakillari, o'qituvchilar, tadqiqotchilar) o'zlarining **monografiya**larini, **risola**larini va **ilmiy kitoblar**ini yuklab, sotish yoki bepul tarqatish imkonini beradigan **raqamli kitob do'koni**.

### Asosiy g'oya

> Hozirgi paytda O'zbekistonda mualliflar o'z monografiyalarini sotish uchun maxsus platforma yo'q. Ko'pchilik PDF orqali Telegram'da tarqatadi, hech qanday himoya va to'lov tizimi yo'q. **Monografiya** ana shu bo'shliqni to'ldiradi.

---

## 👥 Asosiy foydalanuvchi tiplari (User Personas)

### 1. Muallif (Aziz aka, 45 yosh, professor)
- O'zining yangi monografiyasini yuklab, sotishni xohlaydi
- Sotilgan kitoblar va daromad statistikasini kuzatadi
- Bir nechta kitob nashr qilgan va ularni boshqarishni xohlaydi

### 2. O'quvchi/Sotib oluvchi (Dilshod, 25 yosh, magistrant)
- Kerakli sohaviy monografiyani qidiradi
- PDF formatida sotib oladi
- Payme orqali to'lov qiladi
- Sotib olgan kitoblarini "Mening kutubxonam" da saqlaydi

### 3. Admin (Zilola opa, 30 yosh, kontent moderatori)
- Yangi yuklangan kitoblarni tekshiradi
- Plagiat va sifat nazoratini olib boradi
- Mualliflar va o'quvchilar bilan ishlaydi

### 4. SuperAdmin (Texnik direktor)
- Tizimning to'liq egasi
- Adminlarni yaratadi/o'chiradi
- Komissiya foizini boshqaradi
- Moliyaviy hisobotlarni ko'radi

---

## 📦 Asosiy mahsulot (Monografiya) nima?

**Monografiya** — bu ma'lum bir mavzu bo'yicha chuqur ilmiy tadqiqot natijasini yagona muallif (yoki mualliflar guruhi) tomonidan yozilgan kitob. Saytda u quyidagicha bo'ladi:

| Maydon | Tavsifi |
|--------|---------|
| Sarlavha | Kitob nomi (3 tilda) |
| Muallif(lar) | Bir yoki bir nechta muallif |
| Kategoriya | Soha (Tibbiyot, Iqtisod, Filologiya va h.k.) |
| ISBN | Xalqaro raqam (ixtiyoriy) |
| Yili | Nashr yili |
| Sahifalar soni | Avtomatik PDF dan olinadi |
| Tili | uz / ru / en / boshqa |
| Annotatsiya | Qisqacha mazmun (3 tilda) |
| Muqova | Kitob muqovasi rasmi (.jpg/.png) |
| Fayl | Asosiy fayl (.pdf, .epub) |
| Demo fayl | Bepul demo (birinchi 10-20 sahifa) |
| Narxi | UZS yoki bepul (0 so'm) |
| Status | draft / pending / approved / rejected |

---

## 💰 Biznes modeli

### Daromad manbalari:
1. **Komissiya** — har bir sotuvdan platforma 10-20% oladi (SuperAdmin sozlaydi)
2. **Premium muallif obunasi** (kelajakda) — yuqori ko'rinish, statistika
3. **Reklama** (kelajakda) — saytda banner reklamalari

### To'lov oqimi:
```
O'quvchi → Payme → Platforma hisobi
                        ↓
        Komissiya ushlab qolinadi (masalan 15%)
                        ↓
        Qolgan summa muallif balansiga o'tadi
                        ↓
        Muallif yetarli summa to'plagach,
        "Pul yechib olish" so'rovi yuboradi
                        ↓
        Admin tasdiqlaydi va o'tkazma qiladi
```

---

## 🌍 Til va lokalizatsiya

Sayt **3 tilda** ishlaydi:
- 🇺🇿 **O'zbek** (asosiy, default)
- 🇷🇺 **Rus**
- 🇬🇧 **Ingliz**

URL strukturasi: `monografiya.com/uz/`, `monografiya.com/ru/`, `monografiya.com/en/`

Tarjimalar:
- UI matnlari — i18n fayllarda
- Kitob ma'lumotlari — bazada JSONB ustun (`{"uz": "...", "ru": "...", "en": "..."}`)
- Muallif tomonidan har bir kitob uchun alohida kiritiladi

---

## 🎨 Dizayn falsafasi

- **Kitob do'koni** estetikasi — Amazon Kindle Store, Google Play Books'ga o'xshash
- **Issiq, kutubxona** tuyg'usi — qog'oz va siyoh ranglari
- **Minimalist** — ortiqcha narsa yo'q, mahsulotga e'tibor
- **Mobile-first** — telefon ekranida ham mukammal ishlaydi
- **Kunduzgi/Tungi rejim** — foydalanuvchi tanlovi

Batafsil: [`08-design/01-design-system.md`](../08-design/01-design-system.md)

---

## ⚖️ Huquqiy jihatlar (E'tiborga olish kerak)

1. **Mualliflik huquqi shartnomasi** — muallif kitob yuklaganda elektron shartnoma imzolaydi
2. **Foydalanish shartlari** (Terms of Service) — alohida sahifa
3. **Maxfiylik siyosati** (Privacy Policy) — GDPR/O'zbekiston qonunlariga muvofiq
4. **PDF himoyasi** — sotib olgan PDF'ga foydalanuvchi watermark qo'shiladi (email, ism)
5. **Daromad va soliq** — muallif daromadini olganda soliq hisobotini taqdim etish kerak

---

## 🚀 Loyihaning afzalliklari

1. ✅ **Yagona platforma** — O'zbekistondagi birinchi monografiya marketplace
2. ✅ **Mahalliy to'lov** — Payme orqali ishlash (Click qo'shilishi mumkin keyin)
3. ✅ **Ko'p tilli** — 3 tilda ishlaydi
4. ✅ **SEO optimallashtirilgan** — Google'da yuqori chiqadi
5. ✅ **Himoyalangan PDF** — watermark va DRM yengil himoya
6. ✅ **Mualliflarga foydali** — daromad statistikasi, hisobotlar
7. ✅ **Kengaytirib bo'ladigan** — kelajakda audiokitoblar, kurslar qo'shish mumkin

---

## 📊 Kutilayotgan natijalar (1-yil)

- 100+ ro'yxatdan o'tgan muallif
- 500+ monografiya
- 10,000+ ro'yxatdan o'tgan foydalanuvchi
- Oyiga 50-100 mln so'm aylanma

> Bu raqamlar taxminiy va marketing strategiyasiga bog'liq.

---

**Keyingi qadam:** [`02-user-roles.md`](./02-user-roles.md) — Foydalanuvchi rollari va huquqlarini ko'rib chiqing.
