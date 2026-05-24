# 02. API Endpointlar (REST API)

> Backend'ning to'liq REST API hujjati. Prefiks: `/api/v1/`

---

## 🔑 Autentifikatsiya (`/auth`)

| Method | URL | Auth | Tavsifi |
|--------|-----|------|---------|
| POST | `/auth/register` | ❌ | Yangi foydalanuvchi ro'yxatdan o'tish |
| POST | `/auth/login` | ❌ | Kirish (email + parol) |
| POST | `/auth/refresh` | Refresh token | Access token yangilash |
| POST | `/auth/logout` | ✅ | Chiqish (refresh token invalidate) |
| POST | `/auth/verify-email` | ❌ | Email tasdiqlash (token bilan) |
| POST | `/auth/resend-verification` | ❌ | Tasdiqlash emailini qayta yuborish |
| POST | `/auth/forgot-password` | ❌ | Parolni unutdim |
| POST | `/auth/reset-password` | ❌ | Yangi parol o'rnatish (token bilan) |
| GET | `/auth/me` | ✅ | Joriy foydalanuvchi ma'lumotlari |
| POST | `/auth/change-password` | ✅ | Parolni o'zgartirish |
| GET | `/auth/google` | ❌ | Google OAuth boshlash |
| GET | `/auth/google/callback` | ❌ | Google OAuth callback |

### Misol: Register

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "Ali Valiyev",
  "preferred_language": "uz"
}
```

Javob:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Ali Valiyev",
  "role": "reader",
  "is_verified": false,
  "message": "Verification email sent"
}
```

### Misol: Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

Javob:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "reader"
  }
}
```

---

## 👤 Foydalanuvchilar (`/users`)

| Method | URL | Auth | Tavsifi |
|--------|-----|------|---------|
| GET | `/users/me` | ✅ | Mening profilim |
| PUT | `/users/me` | ✅ | Profilni yangilash |
| POST | `/users/me/avatar` | ✅ | Avatar yuklash |
| DELETE | `/users/me/avatar` | ✅ | Avatarni o'chirish |
| GET | `/users/me/library` | ✅ Reader | Sotib olingan kitoblar |
| GET | `/users/me/favorites` | ✅ Reader | Sevimli kitoblar |
| POST | `/users/me/favorites/{book_id}` | ✅ Reader | Sevimliga qo'shish |
| DELETE | `/users/me/favorites/{book_id}` | ✅ Reader | Sevimlidan o'chirish |
| POST | `/users/me/become-author` | ✅ Reader | Muallif bo'lish arizasi |

---

## 📚 Kitoblar (`/books`)

| Method | URL | Auth | Tavsifi |
|--------|-----|------|---------|
| GET | `/books` | ❌ | Kitoblar ro'yxati (filter, paginate) |
| GET | `/books/{slug}` | ❌ | Yagona kitob tafsilot |
| GET | `/books/{id}/demo` | ❌ | Demo fayl URL |
| GET | `/books/{id}/download` | ✅ Reader | Sotib olgan kitobni yuklab olish |
| POST | `/books` | ✅ Author | Yangi kitob yaratish |
| PUT | `/books/{id}` | ✅ Author | Kitobni tahrirlash |
| DELETE | `/books/{id}` | ✅ Author | Kitobni o'chirish (faqat draft) |
| POST | `/books/{id}/submit` | ✅ Author | Moderatsiyaga yuborish |
| POST | `/books/{id}/cover` | ✅ Author | Muqovani yuklash |
| POST | `/books/{id}/file` | ✅ Author | Asosiy faylni yuklash |
| POST | `/books/{id}/demo-file` | ✅ Author | Demo faylni yuklash |
| GET | `/books/{id}/stats` | ✅ Author | Kitob statistikasi |
| GET | `/books/featured` | ❌ | Tavsiya etilgan kitoblar |
| GET | `/books/new-arrivals` | ❌ | Yangi qo'shilganlar |
| GET | `/books/bestsellers` | ❌ | Eng ko'p sotilganlar |

### Filter parametrlari (`GET /books`):

```
?category=tibbiyot
&language=uz
&min_price=0
&max_price=100000
&author=ali-valiyev
&year=2024
&sort=newest|popular|price_asc|price_desc|rating
&page=1
&per_page=20
&q=qidiruv-soz
```

### Misol: Kitob yaratish

```http
POST /api/v1/books
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": {
    "uz": "Tibbiyot asoslari",
    "ru": "Основы медицины",
    "en": "Basics of Medicine"
  },
  "description": {
    "uz": "Bu kitob...",
    "ru": "Эта книга...",
    "en": "This book..."
  },
  "category_ids": ["uuid1", "uuid2"],
  "language": "uz",
  "isbn": "978-9943-...",
  "publication_year": 2024,
  "price_uzs": 50000,
  "is_free": false
}
```

---

## 📁 Kategoriyalar (`/categories`)

| Method | URL | Auth | Tavsifi |
|--------|-----|------|---------|
| GET | `/categories` | ❌ | Barcha kategoriyalar (tree) |
| GET | `/categories/{slug}` | ❌ | Yagona kategoriya |
| GET | `/categories/{slug}/books` | ❌ | Kategoriyadagi kitoblar |
| POST | `/categories` | ✅ SuperAdmin | Yangi kategoriya |
| PUT | `/categories/{id}` | ✅ SuperAdmin | Tahrirlash |
| DELETE | `/categories/{id}` | ✅ SuperAdmin | O'chirish |

---

## 🛒 Buyurtmalar (`/orders`)

| Method | URL | Auth | Tavsifi |
|--------|-----|------|---------|
| POST | `/orders` | ✅ | Yangi buyurtma yaratish |
| GET | `/orders/my` | ✅ | Mening buyurtmalarim |
| GET | `/orders/{id}` | ✅ | Yagona buyurtma |

### Misol: Buyurtma yaratish

```http
POST /api/v1/orders
Authorization: Bearer <token>
Content-Type: application/json

{
  "book_ids": ["uuid1", "uuid2"]
}
```

Javob:
```json
{
  "order_id": "uuid",
  "total_amount": 100000,
  "currency": "UZS",
  "payment_url": "https://checkout.paycom.uz/...",
  "status": "pending"
}
```

---

## 💳 To'lovlar (`/payments`)

| Method | URL | Auth | Tavsifi |
|--------|-----|------|---------|
| POST | `/payments/payme/callback` | ❌ (signed) | Payme webhook |
| GET | `/payments/{order_id}/status` | ✅ | To'lov statusini tekshirish |
| POST | `/payments/{order_id}/retry` | ✅ | To'lovni qayta urinish |

> Webhook Payme tomonidan chaqiriladi. Detali: [`06-payment/01-payme-integration.md`](../06-payment/01-payme-integration.md)

---

## ⭐ Sharhlar (`/reviews`)

| Method | URL | Auth | Tavsifi |
|--------|-----|------|---------|
| GET | `/reviews/book/{book_id}` | ❌ | Kitobning sharhlari |
| POST | `/reviews` | ✅ Reader | Sharh yozish |
| PUT | `/reviews/{id}` | ✅ Author of review | Sharhni tahrirlash |
| DELETE | `/reviews/{id}` | ✅ Author of review | O'chirish |
| POST | `/reviews/{id}/helpful` | ✅ | "Foydali" tugmasi |
| POST | `/reviews/{id}/report` | ✅ | Shikoyat |

---

## 🔍 Qidiruv (`/search`)

| Method | URL | Auth | Tavsifi |
|--------|-----|------|---------|
| GET | `/search` | ❌ | Universal qidiruv |
| GET | `/search/books` | ❌ | Faqat kitoblar |
| GET | `/search/authors` | ❌ | Faqat mualliflar |
| GET | `/search/suggestions` | ❌ | Autocomplete |

### Parametrlari:
```
?q=qidiruv-soz
&lang=uz
&limit=10
```

---

## ✍️ Mualliflar (`/authors`)

| Method | URL | Auth | Tavsifi |
|--------|-----|------|---------|
| GET | `/authors` | ❌ | Barcha mualliflar |
| GET | `/authors/{slug}` | ❌ | Muallif profili |
| GET | `/authors/{slug}/books` | ❌ | Muallif kitoblari |
| GET | `/authors/top` | ❌ | Top mualliflar (sotuvlar bo'yicha) |
| GET | `/authors/me/dashboard` | ✅ Author | Muallif dashboard |
| GET | `/authors/me/sales` | ✅ Author | Sotuvlar statistikasi |
| GET | `/authors/me/balance` | ✅ Author | Balans |

---

## 💰 Pul yechib olish (`/withdrawals`)

| Method | URL | Auth | Tavsifi |
|--------|-----|------|---------|
| POST | `/withdrawals` | ✅ Author | Yangi so'rov |
| GET | `/withdrawals/my` | ✅ Author | Mening so'rovlarim |
| GET | `/withdrawals/{id}` | ✅ Author | Yagona so'rov |
| GET | `/withdrawals/all` | ✅ SuperAdmin | Barcha so'rovlar |
| POST | `/withdrawals/{id}/approve` | ✅ SuperAdmin | Tasdiqlash |
| POST | `/withdrawals/{id}/reject` | ✅ SuperAdmin | Rad etish |

---

## 🛠 Admin (`/admin`)

### Dashboard
| Method | URL | Tavsifi |
|--------|-----|---------|
| GET | `/admin/dashboard` | Umumiy statistika |

### Moderatsiya
| Method | URL | Tavsifi |
|--------|-----|---------|
| GET | `/admin/moderation/books` | Tasdiqlash kutayotgan kitoblar |
| POST | `/admin/books/{id}/approve` | Kitobni tasdiqlash |
| POST | `/admin/books/{id}/reject` | Rad etish (sabab bilan) |
| GET | `/admin/moderation/authors` | Muallif arizalari |
| POST | `/admin/authors/{id}/approve` | Muallifni tasdiqlash |

### Foydalanuvchilar
| Method | URL | Tavsifi |
|--------|-----|---------|
| GET | `/admin/users` | Barcha foydalanuvchilar |
| GET | `/admin/users/{id}` | Yagona foydalanuvchi |
| POST | `/admin/users/{id}/block` | Bloklash |
| POST | `/admin/users/{id}/unblock` | Blokdan chiqarish |
| DELETE | `/admin/users/{id}` | O'chirish (faqat SuperAdmin) |

### SuperAdmin
| Method | URL | Tavsifi |
|--------|-----|---------|
| POST | `/admin/admins` | Yangi admin yaratish |
| GET | `/admin/admins` | Adminlar ro'yxati |
| DELETE | `/admin/admins/{id}` | Adminni o'chirish |
| GET | `/admin/settings` | Sayt sozlamalari |
| PUT | `/admin/settings` | Sozlamalarni saqlash |
| GET | `/admin/analytics/revenue` | Daromad statistika |
| GET | `/admin/analytics/users` | Foydalanuvchilar statistika |

---

## 📤 Fayllar yuklash (`/upload`)

| Method | URL | Auth | Tavsifi |
|--------|-----|------|---------|
| POST | `/upload/image` | ✅ | Rasm yuklash (max 5MB) |
| POST | `/upload/pdf` | ✅ Author | PDF yuklash (max 100MB) |
| POST | `/upload/epub` | ✅ Author | EPUB yuklash |

### Misol:

```http
POST /api/v1/upload/pdf
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <binary>
```

Javob:
```json
{
  "file_url": "https://cdn.monografiya.com/books/xxx.pdf",
  "size": 5242880,
  "pages": 250
}
```

---

## 📊 Statistika (`/stats`)

| Method | URL | Auth | Tavsifi |
|--------|-----|------|---------|
| GET | `/stats/overview` | ❌ | Sayt umumiy statistika (kitoblar soni, mualliflar) |
| GET | `/stats/books/{id}/views` | ✅ Author | Kitob ko'rishlar |

---

## 📞 Aloqa (`/contact`)

| Method | URL | Auth | Tavsifi |
|--------|-----|------|---------|
| POST | `/contact` | ❌ | Aloqa formasi yuborish |

---

## 📰 Blog (`/blog`) — kelajakda

| Method | URL | Auth | Tavsifi |
|--------|-----|------|---------|
| GET | `/blog/posts` | ❌ | Postlar ro'yxati |
| GET | `/blog/posts/{slug}` | ❌ | Yagona post |
| POST | `/blog/posts` | ✅ Admin | Yangi post |

---

## 🌐 Til (`/i18n`)

| Method | URL | Auth | Tavsifi |
|--------|-----|------|---------|
| GET | `/i18n/translations/{lang}` | ❌ | Tarjima fayllari |
| GET | `/i18n/languages` | ❌ | Qo'llab-quvvatlanadigan tillar |

---

## 🚨 Status kodlar va xatoliklar

Barcha xatoliklar bir xil formatda:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email noto'g'ri",
    "details": {
      "field": "email"
    }
  }
}
```

Asosiy kodlar:
- `200` — muvaffaqiyatli
- `201` — yaratildi
- `204` — muvaffaqiyatli, javob yo'q (delete)
- `400` — noto'g'ri so'rov
- `401` — autentifikatsiya kerak
- `403` — ruxsat yo'q (rol)
- `404` — topilmadi
- `409` — konflikt (masalan, email mavjud)
- `422` — validation xatosi
- `429` — rate limit oshib ketdi
- `500` — server xatosi

---

## 🔐 Autentifikatsiya header

Barcha himoyalangan endpointlar:

```http
Authorization: Bearer eyJhbGc...
```

---

## 📄 Pagination format

```json
{
  "items": [...],
  "total": 250,
  "page": 1,
  "per_page": 20,
  "pages": 13,
  "has_next": true,
  "has_prev": false
}
```

---

## 🌐 OpenAPI / Swagger

Avtomatik hujjat: `http://localhost:8000/docs`

ReDoc: `http://localhost:8000/redoc`

OpenAPI JSON: `http://localhost:8000/api/v1/openapi.json`

---

**Keyingi qadam:** [`03-authentication.md`](./03-authentication.md) — JWT autentifikatsiya batafsil.
