# 02. Foydalanuvchi Rollari va Huquqlari

## 👥 Tizimda 4 ta asosiy rol mavjud

| Rol | Tavsif | Soni (taxminiy) |
|-----|--------|-----------------|
| 🔴 **SuperAdmin** | Platforma egasi | 1-2 nafar |
| 🟠 **Admin** | Moderator | 3-10 nafar |
| 🟢 **Muallif** (Author) | Kitob yuklaydi va sotadi | 100+ |
| 🔵 **O'quvchi** (Reader) | Kitob sotib oladi | 10,000+ |

Qo'shimcha: **Guest** (ro'yxatdan o'tmagan) — faqat ko'rib chiqadi, sotib ololmaydi.

---

## 🔴 SuperAdmin

**Maqsad:** Platformaning to'liq egasi va texnik direktor.

### Huquqlari (Permissions):
- ✅ Barcha foydalanuvchilarni ko'rish/o'chirish/bloklash
- ✅ Adminlarni yaratish va o'chirish
- ✅ Komissiya foizini sozlash (masalan 15%)
- ✅ Saytning umumiy sozlamalarini boshqarish (logo, kontaktlar, banner)
- ✅ Moliyaviy hisobotlar (jami daromad, har bir muallif daromadi)
- ✅ Kategoriyalarni qo'shish/o'zgartirish/o'chirish
- ✅ Tarjimalarni boshqarish
- ✅ Tizim loglarini ko'rish
- ✅ Backup va restore
- ✅ Mualliflarning pul yechib olish so'rovlarini tasdiqlash
- ✅ Email shablonlarini tahrirlash
- ✅ Texnik xavfsizlik sozlamalari

### Admin paneldagi sahifalari:
- Dashboard (umumiy statistika)
- Foydalanuvchilar boshqaruvi
- Adminlar boshqaruvi
- Mualliflar va ularning daromadlari
- Kitoblar (barchasi)
- Buyurtmalar va to'lovlar
- Pul yechib olish so'rovlari
- Kategoriyalar
- Tarjimalar
- Sayt sozlamalari
- Xavfsizlik loglari

---

## 🟠 Admin

**Maqsad:** Kitoblarni moderatsiya qilish, foydalanuvchilar bilan ishlash.

### Huquqlari:
- ✅ Yangi yuklangan kitoblarni tasdiqlash/rad etish
- ✅ Kitoblarni tahrirlash (xatolarni tuzatish)
- ✅ Kitob yuklash (jurnal, akademiya nomidan)
- ✅ Mualliflar bilan xabar yozish
- ✅ O'quvchilar shikoyatlarini ko'rib chiqish
- ✅ Statistikalarni ko'rish
- ❌ Boshqa adminlarni yaratish/o'chirish (faqat SuperAdmin)
- ❌ Komissiya foizini o'zgartirish
- ❌ Pul o'tkazmalarini tasdiqlash (faqat SuperAdmin)

### Admin paneldagi sahifalari:
- Dashboard
- Moderatsiya navbati (kutilayotgan kitoblar)
- Kitoblar (faqat ko'rish va tahrir)
- Foydalanuvchilar (faqat ko'rish va bloklash)
- Shikoyatlar
- Xabar yozish

---

## 🟢 Muallif (Author)

**Maqsad:** O'z monografiyalarini yuklab, sotish yoki bepul tarqatish.

### Huquqlari:
- ✅ Yangi kitob yuklash (PDF, muqova, demo)
- ✅ O'z kitoblarini tahrirlash (faqat "draft" yoki "rejected" statusidagi)
- ✅ Narx belgilash (yoki bepul qilish)
- ✅ O'z sotuvlari statistikasini ko'rish
- ✅ O'z balansini ko'rish
- ✅ "Pul yechib olish" so'rovi yuborish
- ✅ Sotib oluvchilar bilan cheklangan xabar (savol-javob)
- ✅ Profil ma'lumotlarini tahrirlash (rasm, biografiya, lavozim)
- ❌ Boshqa mualliflarning kitoblarini ko'rish (statistik)
- ❌ Admin paneliga kirish

### Muallif kabinetidagi sahifalar:
- Mening kitoblarim (Dashboard)
- Yangi kitob qo'shish
- Sotuvlar statistikasi (grafik bilan)
- Balansim va daromadlar
- Pul yechib olish
- Mening profilim
- Xabarlar
- Mualliflik shartnomasi

### Muallif bo'lish jarayoni:
1. Foydalanuvchi sifatida ro'yxatdan o'tadi
2. "Muallif bo'lish" tugmasini bosadi
3. Forma to'ldiradi (ism-familiya, lavozimi, ish joyi, telefon, pasport seriyasi)
4. Admin tasdiqlaydi (yoki rad etadi)
5. Tasdiqlangach, muallif kabineti ochiladi

---

## 🔵 O'quvchi (Reader)

**Maqsad:** Kerakli kitoblarni topib sotib olish va o'qish.

### Huquqlari:
- ✅ Kitoblarni qidirish va filtrlash
- ✅ Demo (bepul qismni) yuklab olish
- ✅ Kitob sotib olish (Payme orqali)
- ✅ Sotib olgan kitobni cheksiz marta yuklab olish
- ✅ Kitobga sharh va reyting qoldirish
- ✅ "Sevimlilar" ro'yxatiga qo'shish
- ✅ Muallif bilan savol-javob (cheklangan)
- ✅ Profil ma'lumotlarini tahrirlash
- ✅ "Mening kutubxonam" — sotib olingan kitoblar
- ❌ Kitob yuklay olmaydi (oldin muallif bo'lishi kerak)

### O'quvchi kabinetidagi sahifalar:
- Mening kutubxonam (sotib olingan kitoblar)
- Sevimlilarim
- Buyurtmalar tarixi
- Sharhlarim
- Profil
- Sozlamalar (parol, til, rejim)

---

## 🚪 Guest (Mehmon)

Ro'yxatdan o'tmagan foydalanuvchi.

### Huquqlari:
- ✅ Bosh sahifa, katalog, qidiruv
- ✅ Kitob tavsilotini ko'rish
- ✅ Demo yuklab olish
- ✅ Sharhlarni o'qish
- ❌ Sotib olish (avval ro'yxatdan o'tish kerak)
- ❌ Sharh yozish
- ❌ Sevimliga qo'shish

---

## 🛡 Permissions matritsasi

| Amal | Guest | O'quvchi | Muallif | Admin | SuperAdmin |
|------|:-----:|:--------:|:-------:|:-----:|:----------:|
| Kitob ko'rish | ✅ | ✅ | ✅ | ✅ | ✅ |
| Demo yuklab olish | ✅ | ✅ | ✅ | ✅ | ✅ |
| Sotib olish | ❌ | ✅ | ✅ | ✅ | ✅ |
| Sharh qoldirish | ❌ | ✅ | ✅ | ✅ | ✅ |
| Kitob yuklash | ❌ | ❌ | ✅ | ✅ | ✅ |
| Boshqa muallif kitobini tahrirlash | ❌ | ❌ | ❌ | ✅ | ✅ |
| Foydalanuvchini bloklash | ❌ | ❌ | ❌ | ✅ | ✅ |
| Adminlarni boshqarish | ❌ | ❌ | ❌ | ❌ | ✅ |
| Komissiya o'zgartirish | ❌ | ❌ | ❌ | ❌ | ✅ |
| Tizim sozlamalari | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## 🗄 Bazada implementatsiya

`users` jadvalida `role` ustuni:

```sql
CREATE TYPE user_role AS ENUM ('reader', 'author', 'admin', 'superadmin');

ALTER TABLE users ADD COLUMN role user_role NOT NULL DEFAULT 'reader';
```

Backend'da har bir endpoint uchun dependency:

```python
from fastapi import Depends, HTTPException

def require_role(*allowed_roles: str):
    def checker(current_user = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Yetarli huquq yo'q")
        return current_user
    return checker

# Misol:
@router.post("/books")
def create_book(user = Depends(require_role("author", "admin", "superadmin"))):
    ...
```

Batafsil: [`03-backend/03-authentication.md`](../03-backend/03-authentication.md)

---

## 📝 Eslatmalar

1. **Default rol** — yangi ro'yxatdan o'tgan barcha foydalanuvchilar `reader` boladi
2. **Muallif bo'lish** — alohida ariza orqali
3. **Admin bo'lish** — faqat SuperAdmin qo'l bilan tayinlaydi
4. **Bir foydalanuvchi bir rolga ega** — agar Admin'ni Muallif qilishingiz kerak bo'lsa, alohida hisob ochishi kerak (yoki rolni almashtirish kerak)
5. **Bloklash** — har qanday rol bloklanishi mumkin (faqat SuperAdmin'dan boshqa)

---

**Keyingi qadam:** [`03-pages-list.md`](./03-pages-list.md) — Saytdagi barcha sahifalar ro'yxati.
