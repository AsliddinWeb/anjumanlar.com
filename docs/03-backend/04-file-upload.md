# 04. Fayl Yuklash va PDF Watermark

> MinIO orqali fayl saqlash, PDF watermark qo'shish, signed URL'lar yaratish.

---

## 📂 Saqlash strukturasi (MinIO buckets)

### Bucket: `monografiya`

```
monografiya/
├── books/                          # Asl PDF/EPUB (XUSUSIY)
│   └── {book_id}/
│       ├── original.pdf
│       └── original.epub
│
├── books-watermarked/              # Watermarklangan, sotilgan
│   └── {user_id}/
│       └── {book_id}.pdf
│
├── covers/                         # OMMAVIY
│   └── {book_id}/
│       ├── original.jpg            # Asl muqova
│       ├── large.jpg               # 600x900
│       ├── medium.jpg              # 300x450
│       └── thumb.jpg               # 150x225
│
├── demos/                          # Bepul demo (OMMAVIY)
│   └── {book_id}/
│       └── demo.pdf
│
├── avatars/                        # OMMAVIY
│   └── {user_id}/
│       ├── original.jpg
│       └── thumb.jpg
│
└── blog/                           # OMMAVIY
    └── {post_id}/
        └── ...
```

---

## 🔐 Bucket policy

| Papka | Ommaviy | Sabab |
|-------|---------|-------|
| `books/` | ❌ Xususiy | Tugallangan kitob — sotiladi |
| `books-watermarked/` | ❌ Xususiy | Signed URL faqat egasi uchun |
| `covers/` | ✅ Ommaviy | Katalogda ko'rinadi |
| `demos/` | ✅ Ommaviy | Hammaga bepul yuklab olish |
| `avatars/` | ✅ Ommaviy | Profil ko'rinadi |
| `blog/` | ✅ Ommaviy | SEO uchun |

---

## 🔧 MinIO Client

### `app/services/storage_service.py`:

```python
from io import BytesIO
from datetime import timedelta
from minio import Minio
from minio.error import S3Error
from app.config import settings


class StorageService:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self.bucket = settings.MINIO_BUCKET
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """Bucket mavjudligini tekshirish, yo'q bo'lsa yaratish."""
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
    
    def upload_file(
        self,
        object_name: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Faylni yuklash."""
        self.client.put_object(
            bucket_name=self.bucket,
            object_name=object_name,
            data=BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        return object_name
    
    def upload_stream(
        self,
        object_name: str,
        stream,
        length: int,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Stream orqali yuklash (katta fayllar uchun)."""
        self.client.put_object(
            bucket_name=self.bucket,
            object_name=object_name,
            data=stream,
            length=length,
            content_type=content_type,
        )
        return object_name
    
    def get_public_url(self, object_name: str) -> str:
        """Ommaviy fayl uchun URL."""
        protocol = "https" if settings.MINIO_SECURE else "http"
        return f"{protocol}://{settings.MINIO_ENDPOINT}/{self.bucket}/{object_name}"
    
    def get_presigned_url(
        self,
        object_name: str,
        expires: timedelta = timedelta(hours=1),
    ) -> str:
        """Signed URL — vaqtincha access."""
        return self.client.presigned_get_object(
            bucket_name=self.bucket,
            object_name=object_name,
            expires=expires,
        )
    
    def delete_file(self, object_name: str) -> bool:
        """Faylni o'chirish."""
        try:
            self.client.remove_object(self.bucket, object_name)
            return True
        except S3Error:
            return False
    
    def file_exists(self, object_name: str) -> bool:
        """Fayl mavjudligini tekshirish."""
        try:
            self.client.stat_object(self.bucket, object_name)
            return True
        except S3Error:
            return False
    
    def download_file(self, object_name: str) -> bytes:
        """Faylni o'qish."""
        response = self.client.get_object(self.bucket, object_name)
        return response.read()


storage = StorageService()
```

---

## 📤 Fayl yuklash endpointlari

### `app/api/v1/endpoints/upload.py`:

```python
from typing import Annotated
from uuid import uuid4
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from app.services.storage_service import storage
from app.services.pdf_service import extract_pdf_metadata, generate_pdf_thumbnail
from app.services.image_service import process_image, generate_image_sizes
from app.dependencies import get_current_user, require_author
from app.models.user import User


router = APIRouter(prefix="/upload", tags=["Upload"])


# Konstantalar
MAX_PDF_SIZE = 100 * 1024 * 1024   # 100 MB
MAX_IMAGE_SIZE = 5 * 1024 * 1024   # 5 MB
MAX_DEMO_SIZE = 20 * 1024 * 1024   # 20 MB

ALLOWED_PDF_TYPES = ["application/pdf"]
ALLOWED_EPUB_TYPES = ["application/epub+zip"]
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]


def validate_file(file: UploadFile, max_size: int, allowed_types: list[str]):
    """Faylni tekshirish."""
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Bu fayl turi qo'llab-quvvatlanmaydi. Ruxsat etilgan: {allowed_types}"
        )
    # Hajmni tekshirish
    file.file.seek(0, 2)  # End
    size = file.file.tell()
    file.file.seek(0)
    if size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"Fayl hajmi {max_size / 1024 / 1024:.0f} MB dan oshmasligi kerak"
        )


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Avatar yoki muqova rasm yuklash."""
    validate_file(file, MAX_IMAGE_SIZE, ALLOWED_IMAGE_TYPES)
    
    content = await file.read()
    object_name = f"avatars/{current_user.id}/{uuid4().hex}.jpg"
    
    # Rasmni qayta ishlash (resize, optimize)
    processed = process_image(content, max_width=800, max_height=800)
    
    storage.upload_file(object_name, processed, "image/jpeg")
    
    return {
        "url": storage.get_public_url(object_name),
        "object_name": object_name,
        "size": len(processed),
    }


@router.post("/pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(require_author),
):
    """Asosiy kitob faylini yuklash."""
    validate_file(file, MAX_PDF_SIZE, ALLOWED_PDF_TYPES)
    
    content = await file.read()
    
    # PDF metadata olish
    metadata = extract_pdf_metadata(content)
    
    # Vaqtincha saqlash (kitob ID mavjud bo'lganda ko'chiriladi)
    temp_object = f"temp/{current_user.id}/{uuid4().hex}.pdf"
    storage.upload_file(temp_object, content, "application/pdf")
    
    return {
        "object_name": temp_object,
        "size": len(content),
        "pages": metadata["pages"],
        "title": metadata.get("title"),
    }


@router.post("/cover")
async def upload_cover(
    file: UploadFile = File(...),
    current_user: User = Depends(require_author),
):
    """Kitob muqovasini yuklash (bir necha o'lchamda saqlanadi)."""
    validate_file(file, MAX_IMAGE_SIZE, ALLOWED_IMAGE_TYPES)
    
    content = await file.read()
    base_id = uuid4().hex
    
    # 3 ta o'lcham yaratish
    sizes = generate_image_sizes(content, [
        ("large", 600, 900),
        ("medium", 300, 450),
        ("thumb", 150, 225),
    ])
    
    urls = {}
    for size_name, image_bytes in sizes.items():
        object_name = f"covers/temp/{current_user.id}/{base_id}/{size_name}.jpg"
        storage.upload_file(object_name, image_bytes, "image/jpeg")
        urls[size_name] = storage.get_public_url(object_name)
    
    return {
        "object_name_prefix": f"covers/temp/{current_user.id}/{base_id}",
        "urls": urls,
    }
```

---

## 📄 PDF Watermark

Sotib olganda foydalanuvchi ismi/emaili PDF'ga qo'shiladi.

### `app/services/pdf_service.py`:

```python
from io import BytesIO
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import Color


def extract_pdf_metadata(content: bytes) -> dict:
    """PDF dan metadata olish."""
    reader = PdfReader(BytesIO(content))
    info = reader.metadata or {}
    return {
        "pages": len(reader.pages),
        "title": info.get("/Title"),
        "author": info.get("/Author"),
        "subject": info.get("/Subject"),
    }


def create_watermark_pdf(text: str, page_width: float, page_height: float) -> bytes:
    """Watermark uchun shaffof PDF yaratish."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
    
    # Diagonal watermark (har bir sahifada)
    c.saveState()
    c.translate(page_width / 2, page_height / 2)
    c.rotate(45)
    c.setFillColor(Color(0.5, 0.5, 0.5, alpha=0.15))  # Yarim shaffof
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(0, 0, text)
    c.restoreState()
    
    # Pastki o'ng burchakda
    c.setFillColor(Color(0.3, 0.3, 0.3, alpha=0.5))
    c.setFont("Helvetica", 8)
    c.drawRightString(page_width - 20, 20, f"© Monografiya | {text}")
    
    c.save()
    return buffer.getvalue()


def add_watermark_to_pdf(pdf_bytes: bytes, watermark_text: str) -> bytes:
    """PDF'ning har bir sahifasiga watermark qo'shish."""
    reader = PdfReader(BytesIO(pdf_bytes))
    writer = PdfWriter()
    
    for page in reader.pages:
        page_width = float(page.mediabox.width)
        page_height = float(page.mediabox.height)
        
        # Watermark PDF yaratish
        watermark_bytes = create_watermark_pdf(watermark_text, page_width, page_height)
        watermark_reader = PdfReader(BytesIO(watermark_bytes))
        watermark_page = watermark_reader.pages[0]
        
        # Mergify
        page.merge_page(watermark_page)
        writer.add_page(page)
    
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def generate_pdf_thumbnail(pdf_bytes: bytes) -> bytes:
    """PDF'ning birinchi sahifasidan thumbnail yaratish.
    
    pdf2image va Pillow ishlatadi.
    """
    from pdf2image import convert_from_bytes
    from PIL import Image
    
    images = convert_from_bytes(pdf_bytes, first_page=1, last_page=1, dpi=150)
    if not images:
        return b""
    
    img = images[0]
    img.thumbnail((600, 900))
    
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=85, optimize=True)
    return buffer.getvalue()
```

---

## 🎨 Rasm bilan ishlash

### `app/services/image_service.py`:

```python
from io import BytesIO
from PIL import Image


def process_image(
    content: bytes,
    max_width: int = 1200,
    max_height: int = 1800,
    quality: int = 85,
) -> bytes:
    """Rasmni qayta ishlash: resize va optimize."""
    img = Image.open(BytesIO(content))
    
    # RGB ga o'tkazish (PNG transparency uchun ham)
    if img.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")
    
    # Resize
    img.thumbnail((max_width, max_height), Image.LANCZOS)
    
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=quality, optimize=True, progressive=True)
    return buffer.getvalue()


def generate_image_sizes(
    content: bytes,
    sizes: list[tuple[str, int, int]],
) -> dict[str, bytes]:
    """Bir nechta o'lchamda yaratish.
    
    sizes: [(name, width, height), ...]
    """
    result = {}
    for name, width, height in sizes:
        result[name] = process_image(content, max_width=width, max_height=height)
    return result
```

---

## 🎯 Celery task: Watermark qo'shish

### `app/tasks/pdf_tasks.py`:

```python
from app.tasks.celery_app import celery_app
from app.services.storage_service import storage
from app.services.pdf_service import add_watermark_to_pdf
from app.db.session import AsyncSessionLocal
from app.models.order import Order
from app.models.user import User
from app.models.book import Book
from sqlalchemy import select
import asyncio


@celery_app.task(name="add_watermark_to_book")
def add_watermark_to_book_task(order_id: str):
    """Buyurtma to'langandan keyin chaqiriladi."""
    asyncio.run(_add_watermark(order_id))


async def _add_watermark(order_id: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            return
        
        user = await db.get(User, order.user_id)
        
        for order_item in order.items:
            book = await db.get(Book, order_item.book_id)
            
            # Asl PDF'ni yuklab olish
            original_object = f"books/{book.id}/original.pdf"
            pdf_bytes = storage.download_file(original_object)
            
            # Watermark matnini tayyorlash
            watermark_text = f"{user.full_name} • {user.email}"
            
            # Watermark qo'shish
            watermarked = add_watermark_to_pdf(pdf_bytes, watermark_text)
            
            # Yangi joyga saqlash
            new_object = f"books-watermarked/{user.id}/{book.id}.pdf"
            storage.upload_file(new_object, watermarked, "application/pdf")
            
            # Order item'ga link qo'shish
            order_item.download_object_name = new_object
        
        await db.flush()
```

---

## 🔒 Yuklab olish endpoint (Signed URL)

```python
@router.get("/books/{book_id}/download")
async def download_book(
    book_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sotib olingan kitobni yuklab olish."""
    # Foydalanuvchi bu kitobni sotib olganmi tekshirish
    result = await db.execute(
        select(OrderItem)
        .join(Order)
        .where(
            Order.user_id == current_user.id,
            OrderItem.book_id == book_id,
            Order.status == "paid",
        )
    )
    order_item = result.scalar_one_or_none()
    
    if not order_item:
        raise HTTPException(status_code=403, detail="Bu kitob sotib olinmagan")
    
    if not order_item.download_object_name:
        raise HTTPException(status_code=425, detail="Fayl hali tayyor emas, biroz kuting")
    
    # Signed URL — 1 soat amal qiladi
    download_url = storage.get_presigned_url(
        order_item.download_object_name,
        expires=timedelta(hours=1),
    )
    
    return {"download_url": download_url}
```

---

## 📋 Eslatmalar

1. **Katta fayllar** — stream orqali yuklash, hammasi xotirada saqlamaslik
2. **Antivirus** — production'da yuklangan fayllarni ClamAV bilan tekshirish
3. **Kvota** — har bir muallif uchun saqlash hajmi cheklash
4. **Cleanup** — `temp/` papkasini har kuni tozalash (Celery beat)
5. **CDN** — production'da MinIO oldida CDN (Cloudflare)
6. **Backup** — har kuni `books/` ni boshqa serverga backup

---

**Keyingi qadam:** [`04-frontend/01-setup.md`](../04-frontend/01-setup.md) — Frontend setup.
