# Seed Data — Demo ma'lumotlar

Loyihani ishga tushirgandan keyin demo ma'lumotlar bilan to'ldirish uchun script.

## scripts/seed.py

```python
"""
Demo ma'lumotlar yaratish.
Foydalanish:
    python -m scripts.seed
    python -m scripts.seed --reset   # avval barcha jadvalni tozalash
"""
import asyncio
import sys
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.db.session import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole, UserStatus
from app.models.author_profile import AuthorProfile
from app.models.category import Category
from app.models.book import Book, BookStatus
from app.models.setting import Setting


async def seed_settings(db: AsyncSession):
    """Global sozlamalar."""
    defaults = [
        ("default_commission_rate", 15, "Standart komissiya foizi"),
        ("min_withdrawal_amount", 100000, "Minimal pul yechish (UZS)"),
        ("max_book_size_mb", 100, "Maksimal kitob hajmi (MB)"),
        ("payme_merchant_id", "", "Payme merchant ID"),
        ("site_name", {"uz": "Anjumanlar", "ru": "Anjumanlar", "en": "Anjumanlar"}, "Sayt nomi"),
    ]
    for key, value, desc in defaults:
        existing = await db.scalar(select(Setting).where(Setting.key == key))
        if not existing:
            db.add(Setting(key=key, value=value, description=desc))
    await db.commit()
    print("✓ Settings seed qilindi")


async def seed_users(db: AsyncSession) -> dict[str, User]:
    """Demo foydalanuvchilar."""
    users_data = [
        {
            "email": "superadmin@anjumanlar.com",
            "password": "SuperAdmin123!",
            "full_name": "Super Admin",
            "role": UserRole.superadmin,
            "status": UserStatus.active,
            "email_verified": True,
        },
        {
            "email": "admin@anjumanlar.com",
            "password": "Admin123!",
            "full_name": "Admin User",
            "role": UserRole.admin,
            "status": UserStatus.active,
            "email_verified": True,
        },
        {
            "email": "author1@anjumanlar.com",
            "password": "Author123!",
            "full_name": "Akmal Karimov",
            "role": UserRole.author,
            "status": UserStatus.active,
            "email_verified": True,
        },
        {
            "email": "author2@anjumanlar.com",
            "password": "Author123!",
            "full_name": "Dilnoza Rahimova",
            "role": UserRole.author,
            "status": UserStatus.active,
            "email_verified": True,
        },
        {
            "email": "reader@anjumanlar.com",
            "password": "Reader123!",
            "full_name": "Test O'quvchi",
            "role": UserRole.reader,
            "status": UserStatus.active,
            "email_verified": True,
        },
    ]
    
    created = {}
    for data in users_data:
        existing = await db.scalar(select(User).where(User.email == data["email"]))
        if existing:
            created[data["email"]] = existing
            continue
        
        password = data.pop("password")
        user = User(**data, password_hash=hash_password(password))
        db.add(user)
        await db.flush()
        created[data["email"]] = user
    
    await db.commit()
    print(f"✓ {len(users_data)} ta foydalanuvchi seed qilindi")
    return created


async def seed_author_profiles(db: AsyncSession, users: dict[str, User]):
    """Author profillari."""
    profiles_data = [
        {
            "email": "author1@anjumanlar.com",
            "slug": "akmal-karimov",
            "display_name": "Akmal Karimov",
            "academic_title": "Tarix fanlari doktori",
            "institution": "O'zbekiston Milliy Universiteti",
            "bio": {
                "uz": "20 yildan ortiq tarix tadqiqotlari bo'yicha tajribaga ega olim.",
                "ru": "Учёный с более чем 20-летним опытом исследований в области истории.",
                "en": "Scholar with over 20 years of experience in historical research.",
            },
            "verified": True,
        },
        {
            "email": "author2@anjumanlar.com",
            "slug": "dilnoza-rahimova",
            "display_name": "Dilnoza Rahimova",
            "academic_title": "Filologiya fanlari nomzodi",
            "institution": "O'zDJTU",
            "bio": {
                "uz": "O'zbek adabiyoti va tilshunoslik bo'yicha mutaxassis.",
                "ru": "Специалист по узбекской литературе и языкознанию.",
                "en": "Specialist in Uzbek literature and linguistics.",
            },
            "verified": True,
        },
    ]
    
    for data in profiles_data:
        email = data.pop("email")
        user = users[email]
        existing = await db.scalar(
            select(AuthorProfile).where(AuthorProfile.user_id == user.id)
        )
        if existing:
            continue
        profile = AuthorProfile(user_id=user.id, **data)
        db.add(profile)
    
    await db.commit()
    print("✓ Author profillari seed qilindi")


async def seed_categories(db: AsyncSession):
    """Kategoriyalar daraxti."""
    categories_data = [
        {
            "slug": "tarix",
            "name": {"uz": "Tarix", "ru": "История", "en": "History"},
            "icon": "book-open",
            "sort_order": 1,
        },
        {
            "slug": "adabiyot",
            "name": {"uz": "Adabiyot", "ru": "Литература", "en": "Literature"},
            "icon": "pen-tool",
            "sort_order": 2,
        },
        {
            "slug": "tilshunoslik",
            "name": {"uz": "Tilshunoslik", "ru": "Языкознание", "en": "Linguistics"},
            "icon": "message-circle",
            "sort_order": 3,
        },
        {
            "slug": "falsafa",
            "name": {"uz": "Falsafa", "ru": "Философия", "en": "Philosophy"},
            "icon": "compass",
            "sort_order": 4,
        },
        {
            "slug": "iqtisodiyot",
            "name": {"uz": "Iqtisodiyot", "ru": "Экономика", "en": "Economics"},
            "icon": "trending-up",
            "sort_order": 5,
        },
        {
            "slug": "huquq",
            "name": {"uz": "Huquq", "ru": "Право", "en": "Law"},
            "icon": "scale",
            "sort_order": 6,
        },
        {
            "slug": "pedagogika",
            "name": {"uz": "Pedagogika", "ru": "Педагогика", "en": "Pedagogy"},
            "icon": "graduation-cap",
            "sort_order": 7,
        },
        {
            "slug": "tibbiyot",
            "name": {"uz": "Tibbiyot", "ru": "Медицина", "en": "Medicine"},
            "icon": "heart",
            "sort_order": 8,
        },
        {
            "slug": "texnika",
            "name": {"uz": "Texnika", "ru": "Техника", "en": "Engineering"},
            "icon": "cpu",
            "sort_order": 9,
        },
        {
            "slug": "tabiiy-fanlar",
            "name": {"uz": "Tabiiy fanlar", "ru": "Естественные науки", "en": "Natural Sciences"},
            "icon": "flask",
            "sort_order": 10,
        },
    ]
    
    for data in categories_data:
        existing = await db.scalar(
            select(Category).where(Category.slug == data["slug"])
        )
        if existing:
            continue
        db.add(Category(**data))
    
    await db.commit()
    print(f"✓ {len(categories_data)} ta kategoriya seed qilindi")


async def seed_books(db: AsyncSession, users: dict[str, User]):
    """Demo kitoblar."""
    author1 = await db.scalar(
        select(AuthorProfile).where(AuthorProfile.slug == "akmal-karimov")
    )
    author2 = await db.scalar(
        select(AuthorProfile).where(AuthorProfile.slug == "dilnoza-rahimova")
    )
    
    if not author1 or not author2:
        print("⚠ Authorlar topilmadi, kitoblar seed qilinmadi")
        return
    
    books_data = [
        {
            "author_id": author1.id,
            "uploaded_by": users["author1@anjumanlar.com"].id,
            "slug": "ozbekiston-tarixi-metodologiyasi",
            "title": {
                "uz": "O'zbekiston tarixi metodologiyasi",
                "ru": "Методология истории Узбекистана",
                "en": "Methodology of Uzbekistan's History",
            },
            "description": {
                "uz": "Tarix fani metodlari va manbalari bilan ishlash bo'yicha qo'llanma.",
                "ru": "Руководство по методам исторической науки и работе с источниками.",
                "en": "Guide to methods of historical science and working with sources.",
            },
            "price": Decimal("75000"),
            "pages_count": 248,
            "publication_year": 2024,
            "status": BookStatus.approved,
            "featured": True,
        },
        {
            "author_id": author1.id,
            "uploaded_by": users["author1@anjumanlar.com"].id,
            "slug": "buyuk-ipak-yoli",
            "title": {
                "uz": "Buyuk ipak yo'li",
                "ru": "Великий шёлковый путь",
                "en": "The Great Silk Road",
            },
            "description": {
                "uz": "Buyuk ipak yo'li va uning Markaziy Osiyodagi roli.",
                "ru": "Великий шёлковый путь и его роль в Центральной Азии.",
                "en": "The Great Silk Road and its role in Central Asia.",
            },
            "price": Decimal("0"),  # bepul
            "pages_count": 156,
            "publication_year": 2023,
            "status": BookStatus.approved,
        },
        {
            "author_id": author2.id,
            "uploaded_by": users["author2@anjumanlar.com"].id,
            "slug": "ozbek-tili-stilistikasi",
            "title": {
                "uz": "O'zbek tili stilistikasi",
                "ru": "Стилистика узбекского языка",
                "en": "Stylistics of the Uzbek Language",
            },
            "description": {
                "uz": "Zamonaviy o'zbek tili stilistik xususiyatlari.",
                "ru": "Стилистические особенности современного узбекского языка.",
                "en": "Stylistic features of modern Uzbek language.",
            },
            "price": Decimal("65000"),
            "pages_count": 192,
            "publication_year": 2024,
            "status": BookStatus.approved,
        },
        {
            "author_id": author2.id,
            "uploaded_by": users["author2@anjumanlar.com"].id,
            "slug": "alisher-navoiy-ijodi",
            "title": {
                "uz": "Alisher Navoiy ijodi tahlili",
                "ru": "Анализ творчества Алишера Навои",
                "en": "Analysis of Alisher Navoi's Works",
            },
            "description": {
                "uz": "Buyuk shoir va davlat arbobi ijodining tadqiqi.",
                "ru": "Исследование творчества великого поэта и государственного деятеля.",
                "en": "Study of the works of the great poet and statesman.",
            },
            "price": Decimal("85000"),
            "pages_count": 320,
            "publication_year": 2024,
            "status": BookStatus.pending,  # moderatsiya kutmoqda
        },
    ]
    
    for data in books_data:
        existing = await db.scalar(select(Book).where(Book.slug == data["slug"]))
        if existing:
            continue
        db.add(Book(**data))
    
    await db.commit()
    print(f"✓ {len(books_data)} ta kitob seed qilindi")


async def reset_database(db: AsyncSession):
    """Barcha demo ma'lumotni o'chirish. Production'da ISHLATMA!"""
    print("⚠ Database tozalanmoqda...")
    tables_in_order = [
        "audit_logs", "notifications", "refresh_tokens",
        "wishlists", "user_libraries", "reviews",
        "order_items", "payments", "orders", "withdrawals",
        "book_categories", "books", "blog_posts",
        "categories", "author_profiles", "users", "settings",
    ]
    for table in tables_in_order:
        await db.execute(text(f"TRUNCATE {table} CASCADE"))
    await db.commit()


async def main():
    reset = "--reset" in sys.argv
    
    async with AsyncSessionLocal() as db:
        if reset:
            from sqlalchemy import text
            await reset_database(db)
        
        await seed_settings(db)
        users = await seed_users(db)
        await seed_author_profiles(db, users)
        await seed_categories(db)
        await seed_books(db, users)
    
    print("\n✅ Seed muvaffaqiyatli yakunlandi!")
    print("\n--- Demo akkauntlar ---")
    print("SuperAdmin: superadmin@anjumanlar.com / SuperAdmin123!")
    print("Admin:      admin@anjumanlar.com / Admin123!")
    print("Author 1:   author1@anjumanlar.com / Author123!")
    print("Author 2:   author2@anjumanlar.com / Author123!")
    print("Reader:     reader@anjumanlar.com / Reader123!")


if __name__ == "__main__":
    asyncio.run(main())
```

## Foydalanish

```bash
# Migratsiyalarni qo'llang
alembic upgrade head

# Seed ishga tushiring
python -m scripts.seed

# Yoki Docker ichida
docker compose exec backend python -m scripts.seed

# Hammasini tozalab qaytadan
docker compose exec backend python -m scripts.seed --reset
```

## Test ma'lumotlari (qo'shimcha)

Test fayllar yaratish uchun `factories.py` qo'shing (factory-boy):

```python
# tests/factories.py
import factory
from factory.alchemy import SQLAlchemyModelFactory
from app.models.user import User, UserRole, UserStatus


class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"
    
    email = factory.Sequence(lambda n: f"user{n}@test.com")
    full_name = factory.Faker("name")
    password_hash = factory.LazyFunction(lambda: hash_password("Test123!"))
    role = UserRole.reader
    status = UserStatus.active
    email_verified = True
```

**Keyingi qadam:** `06-payment/01-payme-integration.md`
