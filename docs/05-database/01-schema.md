# Database Schema (PostgreSQL 16)

Barcha jadvallar UUID primary key ishlatadi. Ko'p tilli maydonlar JSONB sifatida saqlanadi.

## ER diagrammasi (yuqori darajada)

```
users ──┬──< author_profiles
        ├──< books (uploaded_by)
        ├──< orders
        ├──< reviews
        ├──< wishlists
        ├──< user_libraries
        └──< withdrawals

books ──┬──< order_items
        ├──< reviews
        ├──< book_categories >── categories
        └──< wishlists

orders ──< order_items
       └──< payments
```

## SQL — Barcha jadvallar

### users

```sql
CREATE TYPE user_role AS ENUM ('superadmin', 'admin', 'author', 'reader');
CREATE TYPE user_status AS ENUM ('active', 'pending', 'blocked', 'deleted');

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    email_verified  BOOLEAN DEFAULT FALSE,
    phone           VARCHAR(20),
    phone_verified  BOOLEAN DEFAULT FALSE,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    avatar_url      VARCHAR(500),
    role            user_role NOT NULL DEFAULT 'reader',
    status          user_status NOT NULL DEFAULT 'pending',
    preferred_locale VARCHAR(5) DEFAULT 'uz',
    preferences     JSONB DEFAULT '{}',  -- {theme: 'dark', email_notifications: true, ...}
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_role ON users(role) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_status ON users(status);
```

### author_profiles

```sql
CREATE TABLE author_profiles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    slug            VARCHAR(150) UNIQUE NOT NULL,
    display_name    VARCHAR(255) NOT NULL,
    bio             JSONB DEFAULT '{}',     -- {uz, ru, en}
    academic_title  VARCHAR(255),           -- "Tarix fanlari doktori"
    institution     VARCHAR(255),
    website         VARCHAR(500),
    social_links    JSONB DEFAULT '{}',     -- {linkedin, telegram, ...}
    bank_details    JSONB DEFAULT '{}',     -- pul yechish uchun (encrypted)
    commission_rate NUMERIC(5,2) DEFAULT 15.00,  -- foiz
    total_sales     INTEGER DEFAULT 0,
    total_revenue   NUMERIC(15,2) DEFAULT 0,
    available_balance NUMERIC(15,2) DEFAULT 0,
    pending_balance NUMERIC(15,2) DEFAULT 0,
    verified        BOOLEAN DEFAULT FALSE,
    featured        BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_author_profiles_slug ON author_profiles(slug);
CREATE INDEX idx_author_profiles_featured ON author_profiles(featured) WHERE featured = TRUE;
```

### categories

```sql
CREATE TABLE categories (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id       UUID REFERENCES categories(id) ON DELETE SET NULL,
    slug            VARCHAR(150) UNIQUE NOT NULL,
    name            JSONB NOT NULL,         -- {uz, ru, en}
    description     JSONB DEFAULT '{}',
    icon            VARCHAR(100),
    image_url       VARCHAR(500),
    sort_order      INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    book_count      INTEGER DEFAULT 0,      -- denormalized
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_categories_parent ON categories(parent_id);
CREATE INDEX idx_categories_slug ON categories(slug);
```

### books

```sql
CREATE TYPE book_status AS ENUM ('draft', 'pending', 'approved', 'rejected', 'archived');
CREATE TYPE book_language AS ENUM ('uz', 'ru', 'en', 'mixed');

CREATE TABLE books (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    author_id       UUID NOT NULL REFERENCES author_profiles(id),
    uploaded_by     UUID NOT NULL REFERENCES users(id),  -- author yoki admin
    slug            VARCHAR(255) UNIQUE NOT NULL,
    title           JSONB NOT NULL,         -- {uz, ru, en}
    subtitle        JSONB DEFAULT '{}',
    description     JSONB DEFAULT '{}',     -- markdown
    isbn            VARCHAR(20),
    language        book_language DEFAULT 'uz',
    pages_count     INTEGER,
    file_size_mb    NUMERIC(8,2),
    cover_url       VARCHAR(500),
    file_url        VARCHAR(500),           -- original PDF (private, signed URL)
    demo_url        VARCHAR(500),           -- bepul preview PDF
    publication_year INTEGER,
    publisher       VARCHAR(255),
    
    price           NUMERIC(12,2) DEFAULT 0,
    discount_price  NUMERIC(12,2),
    is_free         BOOLEAN GENERATED ALWAYS AS (price = 0) STORED,
    
    status          book_status DEFAULT 'draft',
    rejection_reason TEXT,
    moderated_by    UUID REFERENCES users(id),
    moderated_at    TIMESTAMPTZ,
    
    views_count     INTEGER DEFAULT 0,
    downloads_count INTEGER DEFAULT 0,
    sales_count     INTEGER DEFAULT 0,
    average_rating  NUMERIC(3,2) DEFAULT 0,
    reviews_count   INTEGER DEFAULT 0,
    
    seo_title       JSONB DEFAULT '{}',
    seo_description JSONB DEFAULT '{}',
    keywords        TEXT[],
    
    featured        BOOLEAN DEFAULT FALSE,
    published_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX idx_books_author ON books(author_id);
CREATE INDEX idx_books_slug ON books(slug);
CREATE INDEX idx_books_status ON books(status);
CREATE INDEX idx_books_featured ON books(featured) WHERE featured = TRUE AND status = 'approved';
CREATE INDEX idx_books_published ON books(published_at DESC) WHERE status = 'approved';
CREATE INDEX idx_books_price ON books(price) WHERE status = 'approved';
CREATE INDEX idx_books_rating ON books(average_rating DESC) WHERE status = 'approved';
```

### book_categories (many-to-many)

```sql
CREATE TABLE book_categories (
    book_id         UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    category_id     UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (book_id, category_id)
);

CREATE INDEX idx_book_categories_category ON book_categories(category_id);
```

### orders

```sql
CREATE TYPE order_status AS ENUM ('pending', 'paid', 'failed', 'cancelled', 'refunded');

CREATE TABLE orders (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number    VARCHAR(20) UNIQUE NOT NULL,  -- ANJ-2025-00001
    user_id         UUID NOT NULL REFERENCES users(id),
    status          order_status DEFAULT 'pending',
    subtotal        NUMERIC(15,2) NOT NULL,
    discount        NUMERIC(15,2) DEFAULT 0,
    total           NUMERIC(15,2) NOT NULL,
    currency        VARCHAR(3) DEFAULT 'UZS',
    payment_method  VARCHAR(50),
    metadata        JSONB DEFAULT '{}',
    paid_at         TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ,             -- pending order TTL
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_number ON orders(order_number);
```

### order_items

```sql
CREATE TABLE order_items (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id        UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    book_id         UUID NOT NULL REFERENCES books(id),
    price           NUMERIC(12,2) NOT NULL,       -- buy paytidagi narx
    commission_rate NUMERIC(5,2) NOT NULL,
    author_earning  NUMERIC(12,2) NOT NULL,       -- price * (1 - commission/100)
    platform_fee    NUMERIC(12,2) NOT NULL,       -- price * commission/100
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_book ON order_items(book_id);
```

### payments (Payme integratsiyasi)

```sql
CREATE TYPE payment_status AS ENUM ('created', 'pending', 'paid', 'cancelled', 'failed');

CREATE TABLE payments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id        UUID NOT NULL REFERENCES orders(id),
    provider        VARCHAR(50) NOT NULL,         -- 'payme', 'click', ...
    provider_id     VARCHAR(255),                 -- Payme transaction id
    amount          NUMERIC(15,2) NOT NULL,
    currency        VARCHAR(3) DEFAULT 'UZS',
    status          payment_status DEFAULT 'created',
    state           INTEGER,                      -- Payme state (1, 2, -1, -2)
    create_time     BIGINT,
    perform_time    BIGINT,
    cancel_time     BIGINT,
    reason          INTEGER,                      -- cancellation reason
    raw_response    JSONB,                        -- saqlash uchun
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_payments_order ON payments(order_id);
CREATE INDEX idx_payments_provider_id ON payments(provider, provider_id);
CREATE INDEX idx_payments_status ON payments(status);
```

### user_libraries (sotib olingan kitoblar)

```sql
CREATE TABLE user_libraries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    book_id         UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    order_id        UUID REFERENCES orders(id),
    watermarked_url VARCHAR(500),                 -- shaxsiy watermarked PDF
    downloaded_count INTEGER DEFAULT 0,
    last_downloaded_at TIMESTAMPTZ,
    acquired_at     TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, book_id)
);

CREATE INDEX idx_libraries_user ON user_libraries(user_id);
```

### wishlists

```sql
CREATE TABLE wishlists (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    book_id         UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, book_id)
);

CREATE INDEX idx_wishlists_user ON wishlists(user_id);
```

### reviews

```sql
CREATE TYPE review_status AS ENUM ('pending', 'approved', 'rejected');

CREATE TABLE reviews (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id         UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating          SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title           VARCHAR(255),
    body            TEXT NOT NULL,
    status          review_status DEFAULT 'pending',
    helpful_count   INTEGER DEFAULT 0,
    moderated_by    UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (book_id, user_id)
);

CREATE INDEX idx_reviews_book ON reviews(book_id) WHERE status = 'approved';
CREATE INDEX idx_reviews_user ON reviews(user_id);
CREATE INDEX idx_reviews_status ON reviews(status);
```

### withdrawals (mualliflar pul yechishi)

```sql
CREATE TYPE withdrawal_status AS ENUM ('requested', 'approved', 'processing', 'completed', 'rejected', 'cancelled');

CREATE TABLE withdrawals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    author_id       UUID NOT NULL REFERENCES author_profiles(id),
    amount          NUMERIC(15,2) NOT NULL,
    currency        VARCHAR(3) DEFAULT 'UZS',
    bank_details    JSONB NOT NULL,               -- snapshot at request time
    status          withdrawal_status DEFAULT 'requested',
    admin_notes     TEXT,
    transaction_ref VARCHAR(255),
    processed_by    UUID REFERENCES users(id),
    processed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_withdrawals_author ON withdrawals(author_id);
CREATE INDEX idx_withdrawals_status ON withdrawals(status);
```

### blog_posts

```sql
CREATE TYPE post_status AS ENUM ('draft', 'published', 'archived');

CREATE TABLE blog_posts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    author_id       UUID NOT NULL REFERENCES users(id),
    slug            VARCHAR(255) UNIQUE NOT NULL,
    title           JSONB NOT NULL,
    excerpt         JSONB DEFAULT '{}',
    body            JSONB NOT NULL,
    cover_url       VARCHAR(500),
    status          post_status DEFAULT 'draft',
    views_count     INTEGER DEFAULT 0,
    seo_title       JSONB DEFAULT '{}',
    seo_description JSONB DEFAULT '{}',
    tags            TEXT[],
    published_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_blog_posts_slug ON blog_posts(slug);
CREATE INDEX idx_blog_posts_published ON blog_posts(published_at DESC) WHERE status = 'published';
```

### settings (global sozlamalar — superadmin uchun)

```sql
CREATE TABLE settings (
    key             VARCHAR(100) PRIMARY KEY,
    value           JSONB NOT NULL,
    description     TEXT,
    updated_by      UUID REFERENCES users(id),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Misol qiymatlar
INSERT INTO settings (key, value, description) VALUES
    ('default_commission_rate', '15', 'Platforma uchun standart komissiya foizi'),
    ('min_withdrawal_amount', '100000', 'Minimal pul yechish miqdori (UZS)'),
    ('max_book_size_mb', '100', 'Maksimal kitob fayl o''lchami (MB)'),
    ('payme_merchant_id', '""', 'Payme merchant identifikatori'),
    ('site_meta', '{"title": {"uz": "Anjumanlar"}, "description": {}}', 'Sayt SEO meta');
```

### notifications

```sql
CREATE TABLE notifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type            VARCHAR(50) NOT NULL,         -- 'book_approved', 'sale', 'review', ...
    title           VARCHAR(255) NOT NULL,
    body            TEXT,
    link            VARCHAR(500),
    metadata        JSONB DEFAULT '{}',
    read_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id, created_at DESC);
CREATE INDEX idx_notifications_unread ON notifications(user_id) WHERE read_at IS NULL;
```

### audit_logs

```sql
CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
    action          VARCHAR(100) NOT NULL,        -- 'book.approve', 'user.block', ...
    entity_type     VARCHAR(50),
    entity_id       UUID,
    changes         JSONB,
    ip_address      INET,
    user_agent      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
```

### refresh_tokens

```sql
CREATE TABLE refresh_tokens (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash      VARCHAR(255) UNIQUE NOT NULL,
    user_agent      TEXT,
    ip_address      INET,
    expires_at      TIMESTAMPTZ NOT NULL,
    revoked_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash);
```

## Trigger'lar

### updated_at avtomatik yangilash

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Har bir kerakli jadval uchun:
CREATE TRIGGER set_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_books_updated_at BEFORE UPDATE ON books
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
-- ... va boshqalar
```

### Kitob review qo'shilganda average_rating yangilash

```sql
CREATE OR REPLACE FUNCTION update_book_rating()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE books SET
        average_rating = COALESCE((
            SELECT AVG(rating)::NUMERIC(3,2)
            FROM reviews
            WHERE book_id = NEW.book_id AND status = 'approved'
        ), 0),
        reviews_count = (
            SELECT COUNT(*)
            FROM reviews
            WHERE book_id = NEW.book_id AND status = 'approved'
        )
    WHERE id = NEW.book_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER review_rating_update
AFTER INSERT OR UPDATE OR DELETE ON reviews
FOR EACH ROW EXECUTE FUNCTION update_book_rating();
```

## Performance maslahatlar

1. JSONB maydonlar uchun GIN indeks (full-text search kerak bo'lsa):
   ```sql
   CREATE INDEX idx_books_title_gin ON books USING GIN (title);
   ```

2. Trigram qidiruv (PostgreSQL `pg_trgm`):
   ```sql
   CREATE EXTENSION IF NOT EXISTS pg_trgm;
   CREATE INDEX idx_books_title_trgm ON books USING GIN ((title->>'uz') gin_trgm_ops);
   ```

3. Asosiy qidiruv esa Meilisearch'ga topshiriladi (alohida hujjatda).

**Keyingi qadam:** `05-database/02-migrations.md`
