# To'lov oqimi (Payment Flow)

## To'liq oqim diagrammasi

```
┌─────────────┐                                              
│ Foydalanuvchi│                                              
└──────┬──────┘                                              
       │ 1. "Sotib olish" tugmasi                            
       ↓                                                      
┌─────────────┐                                              
│  Frontend   │  POST /orders                                
│   (Nuxt)    │  {items: [{book_id}]}                         
└──────┬──────┘                                              
       ↓                                                      
┌─────────────┐                                              
│  Backend    │  Order yaratiladi (status='pending')          
│  (FastAPI)  │  OrderItem'lar qo'shiladi                     
│             │  expires_at = now + 30min                     
└──────┬──────┘                                              
       │ return: {order_id, total}                           
       ↓                                                      
┌─────────────┐                                              
│  Frontend   │  POST /payments/payme/initiate                
│             │  {order_id}                                   
└──────┬──────┘                                              
       ↓                                                      
┌─────────────┐                                              
│  Backend    │  Checkout URL generatsiya                     
│             │  base64(m=X;ac.order_id=Y;a=Z;...)            
└──────┬──────┘                                              
       │ return: {url: "https://checkout.paycom.uz/..."}     
       ↓                                                      
┌─────────────┐                                              
│  Frontend   │  window.location.href = url                   
└──────┬──────┘                                              
       ↓                                                      
┌─────────────────────────────────────────────┐              
│            Payme Checkout sahifasi          │              
│  Foydalanuvchi karta ma'lumotini kiritadi   │              
└──────────────┬──────────────────────────────┘              
               ↓                                              
        ┌──────┴──────┐                                      
        │             │                                      
   PARALLEL OQIMLAR                                          
        │             │                                      
        ↓             ↓                                      
   ┌─────────┐   ┌─────────────────────────────┐             
   │ Browser │   │   Payme server → Backend     │             
   │ redirect│   │  (Server-to-server webhook)  │             
   │  /success│   │                              │             
   └─────────┘   │  POST /payments/payme/webhook│             
                 │  (Basic Auth)                 │             
                 │                               │             
                 │  Method ketma-ketligi:        │             
                 │  1. CheckPerformTransaction   │             
                 │  2. CreateTransaction         │             
                 │  3. PerformTransaction ←—muhim│             
                 └──────┬───────────────────────┘             
                        ↓                                     
                 ┌─────────────────────┐                      
                 │  Backend:           │                      
                 │  - Order='paid'     │                      
                 │  - Payment='paid'   │                      
                 │  - UserLibrary++   │                      
                 │  - Celery: PDF      │                      
                 │    watermark        │                      
                 │  - Celery: email    │                      
                 │  - Notification    │                      
                 └─────────────────────┘                      
```

## State diagram (Order)

```
                  ┌─────────┐
       create     │ PENDING │
   ───────────→   │         │
                  └────┬────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   payment ok    user cancel     expire (TTL)
        ↓              ↓              ↓
   ┌─────────┐    ┌─────────┐    ┌──────────┐
   │  PAID   │    │CANCELLED│    │  FAILED  │
   └────┬────┘    └─────────┘    └──────────┘
        │
    refund
        ↓
   ┌──────────┐
   │ REFUNDED │
   └──────────┘
```

## State diagram (Payme Payment)

Payme rasmiy 4 holat ishlatadi:

| State | Ma'no |
|---|---|
| 1 | Created (transaction yaratildi, lekin to'lov amalga oshmagan) |
| 2 | Performed (to'lov muvaffaqiyatli amalga oshdi) |
| -1 | Cancelled before perform (1 → -1) |
| -2 | Cancelled after perform (2 → -2, refund) |

```
         CreateTransaction
              ↓
    ┌─────────────────┐
    │   state = 1     │
    │   (created)     │
    └────┬─────────┬──┘
         │         │
   PerformTrans  CancelTrans
         ↓         ↓
    ┌────────┐ ┌────────┐
    │state=2 │ │state=-1│
    │ (paid) │ │(cancel)│
    └────┬───┘ └────────┘
         │
    CancelTrans
         ↓
    ┌────────┐
    │state=-2│
    │(refund)│
    └────────┘
```

## Order yaratish endpoint

```python
# app/api/v1/orders.py
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.models.order import Order, OrderItem, OrderStatus
from app.models.book import Book, BookStatus
from app.models.user_library import UserLibrary
from app.schemas.order import OrderCreate, OrderResponse


router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse)
async def create_order(
    data: OrderCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not data.items:
        raise HTTPException(400, "Cart is empty")
    
    # Order number
    today = datetime.now().strftime("%Y%m%d")
    count = await db.scalar(select(func.count(Order.id)).where(
        Order.created_at >= datetime.now().replace(hour=0, minute=0)
    ))
    order_number = f"ANJ-{today}-{count + 1:05d}"
    
    subtotal = Decimal("0")
    items_to_add = []
    
    for item in data.items:
        book = await db.get(Book, item.book_id)
        if not book or book.status != BookStatus.approved:
            raise HTTPException(404, f"Book not available: {item.book_id}")
        
        # Bepul kitob — birato user_library'ga
        if book.is_free:
            existing = await db.scalar(
                select(UserLibrary).where(
                    UserLibrary.user_id == user.id,
                    UserLibrary.book_id == book.id,
                )
            )
            if not existing:
                db.add(UserLibrary(user_id=user.id, book_id=book.id))
            continue
        
        # Allaqachon sotib olganmi
        owned = await db.scalar(
            select(UserLibrary).where(
                UserLibrary.user_id == user.id,
                UserLibrary.book_id == book.id,
            )
        )
        if owned:
            raise HTTPException(400, f"Already owned: {book.title}")
        
        price = book.discount_price or book.price
        subtotal += price
        
        commission_rate = book.author.commission_rate
        platform_fee = price * commission_rate / 100
        author_earning = price - platform_fee
        
        items_to_add.append(OrderItem(
            book_id=book.id,
            price=price,
            commission_rate=commission_rate,
            author_earning=author_earning,
            platform_fee=platform_fee,
        ))
    
    if subtotal == 0:
        # Hammasi bepul edi
        await db.commit()
        return {"message": "Books added to library", "free": True}
    
    order = Order(
        order_number=order_number,
        user_id=user.id,
        status=OrderStatus.pending,
        subtotal=subtotal,
        total=subtotal,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    db.add(order)
    await db.flush()
    
    for item in items_to_add:
        item.order_id = order.id
        db.add(item)
    
    await db.commit()
    await db.refresh(order)
    return order
```

## Payme initiate endpoint

```python
@router.post("/payme/initiate")
async def initiate_payme(
    body: PaymeInitiateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await db.get(Order, body.order_id)
    if not order or order.user_id != user.id:
        raise HTTPException(404, "Order not found")
    if order.status != OrderStatus.pending:
        raise HTTPException(400, "Order is not pending")
    
    return_url = f"{settings.SITE_URL}/checkout/success?order={order.id}"
    
    url = PaymeService.generate_checkout_url(
        order_id=str(order.id),
        amount=int(order.total * 100),  # tiyin'da
        return_url=return_url,
        language=user.preferred_locale,
    )
    
    return {"url": url}
```

## Pending orderlarni tozalash (cron)

```python
# app/tasks/order_tasks.py
from app.celery_app import celery_app
from datetime import datetime, timezone


@celery_app.task
def expire_pending_orders():
    """Har 5 daqiqada ishlaydi."""
    from app.db.session import SessionLocal
    
    with SessionLocal() as db:
        expired = db.scalars(
            select(Order).where(
                Order.status == OrderStatus.pending,
                Order.expires_at < datetime.now(timezone.utc),
            )
        ).all()
        
        for order in expired:
            order.status = OrderStatus.failed
        db.commit()
        return f"Expired {len(expired)} orders"


# celery_app.py beat schedule:
celery_app.conf.beat_schedule = {
    "expire-orders": {
        "task": "app.tasks.order_tasks.expire_pending_orders",
        "schedule": 300.0,  # har 5 minutda
    },
}
```

## Watermarked PDF generation (sotib olingandan keyin)

```python
# app/tasks/book_tasks.py
from app.celery_app import celery_app


@celery_app.task
def watermark_purchased_books(order_id: str):
    from app.db.session import SessionLocal
    from app.services.pdf_watermark import add_watermark
    from app.services.storage import storage
    
    with SessionLocal() as db:
        items = db.scalars(
            select(OrderItem).where(OrderItem.order_id == order_id)
        ).all()
        
        for item in items:
            book = db.get(Book, item.book_id)
            order = db.get(Order, order_id)
            user = db.get(User, order.user_id)
            
            # Original PDF olish
            original = storage.get_file(book.file_url)
            
            # Watermark text
            watermark_text = f"Sotib oluvchi: {user.email} | Buyurtma: {order.order_number}"
            
            # Watermark qo'shamiz
            watermarked = add_watermark(original, watermark_text)
            
            # MinIO'ga yuklaymiz
            key = f"books-watermarked/{user.id}/{book.id}.pdf"
            url = storage.upload_file(key, watermarked, "application/pdf")
            
            # user_library'ga link qo'shamiz
            entry = db.scalar(
                select(UserLibrary).where(
                    UserLibrary.user_id == user.id,
                    UserLibrary.book_id == book.id,
                )
            )
            entry.watermarked_url = url
            db.commit()
```

## Success/Failed sahifalar

```vue
<!-- pages/checkout/success.vue -->
<script setup lang="ts">
const route = useRoute()
const orderId = route.query.order
const localePath = useLocalePath()

definePageMeta({ middleware: 'auth' })
</script>

<template>
  <div class="container mx-auto px-4 py-16 text-center">
    <div class="max-w-md mx-auto">
      <Icon name="heroicons:check-circle" class="w-20 h-20 mx-auto text-green-500" />
      <h1 class="mt-6 text-3xl font-display font-bold">
        {{ $t('checkout.success_title') }}
      </h1>
      <p class="mt-4 text-ink/70 dark:text-ink-dark/70">
        {{ $t('checkout.success_message') }}
      </p>
      <div class="mt-8 flex gap-4 justify-center">
        <NuxtLink :to="localePath('/account/library')" class="btn-primary">
          {{ $t('book.in_library') }}
        </NuxtLink>
        <NuxtLink :to="localePath('/books')" class="btn-secondary">
          {{ $t('cart.continue_shopping') }}
        </NuxtLink>
      </div>
    </div>
  </div>
</template>
```

## Xavfsizlik

1. **Webhook auth** — Basic Auth bilan tasdiqlash majburiy
2. **Idempotency** — bir xil transaction ID 2 marta kelsa, ikkinchi safar to'g'ri javob qaytaring
3. **Amount tekshirish** — Payme'dan kelgan amount order summasiga mos kelishi shart
4. **Race condition** — DB transaction (SELECT ... FOR UPDATE) kerakli joylarda
5. **Logging** — har bir webhook so'rovini `audit_logs` ga yozing
6. **HTTPS only** — webhook URL faqat HTTPS

**Keyingi qadam:** `07-deployment/01-docker-setup.md`
