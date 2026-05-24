# 03. Autentifikatsiya va Avtorizatsiya (JWT)

> JWT-based autentifikatsiya tizimi va rol-based access control (RBAC) batafsil.

---

## 🔑 Autentifikatsiya strategiyasi

**Strategiya:** JWT (JSON Web Tokens) + Refresh Token pattern

### Tokenlar:
1. **Access Token** — qisqa muddatli (30 daqiqa), har bir so'rov uchun
2. **Refresh Token** — uzoq muddatli (7 kun), faqat access token yangilash uchun

### Saqlash:
- **Access Token** — frontend'da memory (Pinia state)
- **Refresh Token** — HttpOnly cookie (xavfsizroq) yoki localStorage (oddiy)

> Production'da HttpOnly cookie tavsiya etiladi — XSS hujumlardan himoyalanadi.

---

## 📝 To'liq oqim (Flow)

```
1. Foydalanuvchi → POST /auth/login {email, password}
2. Backend → email + parol tekshirish
3. Backend → access_token (30 daq) + refresh_token (7 kun) qaytaradi
4. Frontend → access_token'ni Pinia'ga saqlaydi
5. Frontend → refresh_token'ni HttpOnly cookie'ga saqlaydi
6. Har bir so'rov → "Authorization: Bearer <access_token>"
7. Access muddati tugadi → 401 keladi
8. Frontend → POST /auth/refresh (cookie avtomatik yuboriladi)
9. Backend → yangi access_token qaytaradi
10. Frontend → davom etadi
```

---

## 🔐 Parol siyosati

Minimal talablar:
- ✅ Kamida 8 belgi
- ✅ Kamida bitta katta harf
- ✅ Kamida bitta kichik harf
- ✅ Kamida bitta raqam
- ⚠️ Maxsus belgi (ixtiyoriy, lekin tavsiya etiladi)

Pydantic schema:

```python
from pydantic import BaseModel, EmailStr, field_validator
import re


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    preferred_language: str = "uz"

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Parol kamida 8 belgi bo'lishi kerak")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Parol katta harf saqlashi kerak")
        if not re.search(r"[a-z]", v):
            raise ValueError("Parol kichik harf saqlashi kerak")
        if not re.search(r"\d", v):
            raise ValueError("Parol raqam saqlashi kerak")
        return v
```

---

## 🔑 JWT yaratish va tekshirish

### `app/core/security.py`:

```python
from datetime import datetime, timedelta, timezone
from typing import Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(
    subject: str | Any,
    extra_claims: dict | None = None,
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
        "iat": datetime.now(timezone.utc),
    }
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str | Any) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None
```

---

## 🛡 Dependency: joriy foydalanuvchini olish

### `app/dependencies.py`:

```python
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.core.security import decode_token
from app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    if payload.get("type") != "access":
        raise credentials_exception
    
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Foydalanuvchi bloklangan")
    
    return user


async def get_current_verified_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Email tasdiqlanmagan. Pochtangizni tekshiring."
        )
    return current_user


def require_roles(*allowed_roles: str):
    """Rol-based access control dependency."""
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Bu amal uchun yetarli huquq yo'q. Kerakli rol: {allowed_roles}"
            )
        return current_user
    return role_checker


# Tez ishlatish uchun aliaslar
require_author = require_roles("author", "admin", "superadmin")
require_admin = require_roles("admin", "superadmin")
require_superadmin = require_roles("superadmin")
```

---

## 📋 Auth endpointlar implementatsiyasi

### `app/api/v1/endpoints/auth.py`:

```python
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    UserRegister, UserLogin, UserResponse, TokenResponse,
    PasswordResetRequest, PasswordReset
)
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token
)
from app.services.email_service import send_verification_email, send_password_reset_email
from app.core.limiter import limiter
from app.dependencies import get_current_user


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
@limiter.limit("5/minute")
async def register(
    data: UserRegister,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Email allaqachon mavjudligini tekshirish
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Bu email allaqachon ro'yxatdan o'tgan")
    
    # Yangi user yaratish
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        preferred_language=data.preferred_language,
        role="reader",
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    
    # Tasdiqlash emaili yuborish (Celery task)
    verification_token = create_access_token(
        user.id,
        extra_claims={"purpose": "email_verification"}
    )
    await send_verification_email.delay(user.email, verification_token)
    
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    data: UserLogin,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email yoki parol noto'g'ri")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Hisobingiz bloklangan")
    
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    # Refresh token HttpOnly cookie sifatida
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,  # production
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,  # frontend uchun ham qaytaramiz
        "token_type": "bearer",
        "user": user,
    }


@router.post("/refresh")
async def refresh_token(
    refresh_token: Annotated[str | None, Cookie()] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token yo'q")
    
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Noto'g'ri refresh token")
    
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Foydalanuvchi topilmadi")
    
    new_access_token = create_access_token(user.id)
    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("refresh_token")
    return {"message": "Muvaffaqiyatli chiqdingiz"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user


@router.post("/verify-email")
async def verify_email(
    token: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    payload = decode_token(token)
    if not payload or payload.get("purpose") != "email_verification":
        raise HTTPException(status_code=400, detail="Noto'g'ri token")
    
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    
    user.is_verified = True
    await db.flush()
    
    return {"message": "Email muvaffaqiyatli tasdiqlandi"}


@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(
    data: PasswordResetRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    
    # Xavfsizlik: foydalanuvchi mavjudligini oshkor qilmaymiz
    if user:
        reset_token = create_access_token(
            user.id,
            extra_claims={"purpose": "password_reset"}
        )
        await send_password_reset_email.delay(user.email, reset_token)
    
    return {"message": "Agar email mavjud bo'lsa, parol tiklash linki yuborildi"}


@router.post("/reset-password")
async def reset_password(
    data: PasswordReset,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    payload = decode_token(data.token)
    if not payload or payload.get("purpose") != "password_reset":
        raise HTTPException(status_code=400, detail="Noto'g'ri yoki muddati o'tgan token")
    
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    
    user.password_hash = hash_password(data.new_password)
    await db.flush()
    
    return {"message": "Parol muvaffaqiyatli o'zgartirildi"}
```

---

## 🎭 Endpoint'larda rollarni ishlatish

```python
from app.dependencies import require_author, require_admin, require_superadmin


@router.post("/books")
async def create_book(
    data: BookCreate,
    current_user: Annotated[User, Depends(require_author)],  # Faqat author+
    db: Annotated[AsyncSession, Depends(get_db)],
):
    book = Book(**data.dict(), author_id=current_user.id)
    db.add(book)
    await db.flush()
    return book


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: Annotated[User, Depends(require_superadmin)],  # Faqat SuperAdmin
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Logika
    ...


@router.post("/books/{book_id}/approve")
async def approve_book(
    book_id: str,
    current_user: Annotated[User, Depends(require_admin)],  # Admin yoki SuperAdmin
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Logika
    ...
```

---

## 🚦 Rate Limiting

### `app/core/limiter.py`:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address


limiter = Limiter(key_func=get_remote_address)
```

Ishlatish:

```python
@router.post("/login")
@limiter.limit("10/minute")  # Bir IP'dan daqiqada max 10
async def login(...):
    ...


@router.post("/register")
@limiter.limit("5/minute")  # Daqiqada max 5
async def register(...):
    ...


@router.post("/forgot-password")
@limiter.limit("3/minute")  # Daqiqada max 3
async def forgot_password(...):
    ...
```

---

## 🌐 Google OAuth (ixtiyoriy)

### Sozlash:

1. Google Cloud Console'da OAuth client yarating
2. `.env`'ga qo'shing:
```
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=https://monografiya.com/api/v1/auth/google/callback
```

3. `authlib` o'rnating: `pip install authlib`

```python
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@router.get("/google")
async def google_login(request: Request):
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")
    
    # Foydalanuvchi mavjudmi tekshirish, yo'q bo'lsa yaratish
    # ...
    
    # JWT qaytarish
    return {"access_token": create_access_token(user.id)}
```

---

## 🔒 Xavfsizlik bo'yicha eslatmalar

1. ✅ **JWT_SECRET_KEY** strong va `.env`'da
2. ✅ Production'da `secure=True` cookie
3. ✅ HTTPS faqat
4. ✅ Rate limit har bir auth endpoint
5. ✅ Email tasdiqlash majburiy (kritik amallar uchun)
6. ✅ Parol bcrypt bilan
7. ✅ CSRF token (cookie ishlatilsa)
8. ✅ Lockout — 5 noto'g'ri urinishdan keyin akkaunt vaqtincha bloklash (kelajak versiya)

---

**Keyingi qadam:** [`04-file-upload.md`](./04-file-upload.md) — Fayl yuklash logikasi.
