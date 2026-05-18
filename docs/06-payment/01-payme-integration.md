# Payme.uz Integratsiyasi

Payme — O'zbekistondagi eng keng tarqalgan to'lov tizimi. **Merchant API** (subscribe/checkout) orqali integratsiya qilamiz.

## Asosiy tushunchalar

Payme ikki yo'l bilan ishlaydi:
1. **Checkout API** — sayt foydalanuvchini Payme sahifasiga yo'naltiradi
2. **Subscribe API** — server-to-server, karta saqlash bilan

Bizning loyihada **Checkout API** ishlatamiz (sodda va MVP uchun yetarli).

## Hujjatlar

- Asosiy hujjat: https://developer.help.paycom.uz/
- Merchant API: https://developer.help.paycom.uz/protokol-merchant-api/

## Akkaunt va credentials

Payme business akkaunt ochib quyidagilarni olishingiz kerak:

- **MERCHANT_ID** — Payme tomonidan beriladi
- **MERCHANT_KEY** — webhook'larni tekshirish uchun (Basic Auth password)
- **TEST_KEY** — sandbox uchun alohida key
- **CHECKOUT_URL** — `https://checkout.paycom.uz/` (production) yoki `https://checkout.test.paycom.uz/` (sandbox)

## Oqim (Flow)

```
1. Foydalanuvchi "To'lash" tugmasini bosadi
   ↓
2. Backend: Order yaratiladi (status='pending')
   ↓
3. Backend: Payme Checkout URL generatsiya qilinadi
   ↓
4. Frontend: foydalanuvchi Payme sahifasiga yo'naltiriladi
   ↓
5. Foydalanuvchi karta ma'lumotini kiritib to'laydi
   ↓
6. Payme server bizga webhook (RPC) yuboradi:
   - CheckPerformTransaction → order mavjudligi/holatini tekshirish
   - CreateTransaction → transaction yozish (status='pending')
   - PerformTransaction → to'lov tasdiqlash (status='paid')
   - CancelTransaction → bekor qilish
   - GetStatement → tekshirish so'rovi
   ↓
7. Backend: Order status='paid', user_library'ga kitob qo'shiladi
   ↓
8. Foydalanuvchi /checkout/success sahifasiga qaytariladi
```

## Checkout URL generatsiya qilish

```python
# app/services/payme.py
import base64
import json
from app.core.config import settings


class PaymeService:
    @staticmethod
    def generate_checkout_url(
        order_id: str,
        amount: int,           # tiyin'da (1 so'm = 100 tiyin)
        return_url: str,
        language: str = "uz",
    ) -> str:
        """
        Payme checkout URL yaratadi.
        
        Hujjat: https://developer.help.paycom.uz/initsializatsiya-platezhey/
        """
        params = {
            "m": settings.PAYME_MERCHANT_ID,
            "ac.order_id": order_id,
            "a": amount,
            "l": language,
            "c": return_url,
            "ct": 10000,  # callback timeout (ms)
        }
        
        # Format: "m=XXX;ac.order_id=YYY;a=ZZZ;..."
        param_str = ";".join(f"{k}={v}" for k, v in params.items())
        encoded = base64.b64encode(param_str.encode()).decode()
        
        base_url = settings.PAYME_CHECKOUT_URL.rstrip("/")
        return f"{base_url}/{encoded}"
```

## Webhook handler (Merchant API)

Payme bizga JSON-RPC 2.0 so'rovlar yuboradi. Auth — Basic Auth (`Paycom:MERCHANT_KEY`).

### Error kodlari

```python
# app/services/payme_errors.py

PAYME_ERRORS = {
    -32700: "Parse error",
    -32600: "Invalid request",
    -32601: "Method not found",
    -32602: "Invalid params",
    -32603: "Internal error",
    -32504: "Authorization failed",
    -31001: "System error",
    -31050: "Order not found",
    -31051: "Order not available for payment",
    -31052: "Invalid amount",
    -31053: "Method not supported",
    -31054: "Order already paid",
    -31055: "Order cancelled",
    -31099: "Other error",
    -31008: "Unable to perform operation",
    -31003: "Transaction not found",
    -31007: "Unable to cancel",
}


class PaymeError(Exception):
    def __init__(self, code: int, message: str = None, data: dict = None):
        self.code = code
        self.message = message or PAYME_ERRORS.get(code, "Unknown error")
        self.data = data or {}
```

### Routes

```python
# app/api/v1/payme.py
import base64
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.config import settings
from app.services.payme_handler import PaymeMerchantHandler

router = APIRouter(prefix="/payments/payme", tags=["payme"])


def verify_payme_auth(request: Request):
    """Basic Auth tekshirish — Paycom:MERCHANT_KEY"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Basic "):
        raise HTTPException(401, "Auth required")
    
    try:
        decoded = base64.b64decode(auth_header[6:]).decode()
        username, password = decoded.split(":", 1)
    except Exception:
        raise HTTPException(401, "Invalid auth")
    
    if username != "Paycom" or password != settings.PAYME_MERCHANT_KEY:
        raise HTTPException(401, "Invalid credentials")


@router.post("/webhook", dependencies=[Depends(verify_payme_auth)])
async def payme_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Payme JSON-RPC webhook.
    
    Methods:
        - CheckPerformTransaction
        - CreateTransaction
        - PerformTransaction
        - CancelTransaction
        - CheckTransaction
        - GetStatement
    """
    payload = await request.json()
    handler = PaymeMerchantHandler(db)
    result = await handler.handle(payload)
    return result
```

### Merchant Handler

```python
# app/services/payme_handler.py
import time
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.models.user_library import UserLibrary
from app.services.payme_errors import PaymeError


class PaymeMerchantHandler:
    """Payme Merchant API JSON-RPC handler."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def handle(self, payload: dict) -> dict:
        method = payload.get("method")
        params = payload.get("params", {})
        req_id = payload.get("id")
        
        try:
            handler = getattr(self, f"_{method}", None)
            if not handler:
                raise PaymeError(-32601)
            result = await handler(params)
            return {"jsonrpc": "2.0", "id": req_id, "result": result}
        except PaymeError as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": e.code, "message": e.message, "data": e.data},
            }
    
    async def _get_order(self, account: dict) -> Order:
        order_id = account.get("order_id")
        if not order_id:
            raise PaymeError(-31050)
        try:
            order = await self.db.get(Order, UUID(order_id))
        except (ValueError, TypeError):
            raise PaymeError(-31050)
        if not order:
            raise PaymeError(-31050)
        return order
    
    def _check_amount(self, order: Order, amount: int):
        # amount tiyin'da keladi, order.total — UZS
        expected = int(order.total * 100)
        if expected != amount:
            raise PaymeError(-31001, "Invalid amount")
    
    # --- RPC Methods ---
    
    async def CheckPerformTransaction(self, params: dict):
        order = await self._get_order(params.get("account", {}))
        self._check_amount(order, params.get("amount"))
        
        if order.status == OrderStatus.paid:
            raise PaymeError(-31054)
        if order.status in (OrderStatus.cancelled, OrderStatus.refunded):
            raise PaymeError(-31055)
        if order.status != OrderStatus.pending:
            raise PaymeError(-31051)
        
        return {"allow": True}
    
    async def CreateTransaction(self, params: dict):
        transaction_id = params["id"]
        time_ms = params["time"]
        amount = params["amount"]
        account = params.get("account", {})
        
        # Mavjud transaction'ni qidiramiz
        existing = await self.db.scalar(
            select(Payment).where(
                Payment.provider == "payme",
                Payment.provider_id == transaction_id,
            )
        )
        
        if existing:
            if existing.state == 1:
                return {
                    "create_time": existing.create_time,
                    "transaction": str(existing.id),
                    "state": 1,
                }
            raise PaymeError(-31008)
        
        # Yangi tekshirish
        order = await self._get_order(account)
        self._check_amount(order, amount)
        
        if order.status != OrderStatus.pending:
            raise PaymeError(-31051)
        
        # Boshqa pending payment bormi
        other = await self.db.scalar(
            select(Payment).where(
                Payment.order_id == order.id,
                Payment.state == 1,
            )
        )
        if other:
            raise PaymeError(-31008)
        
        # Yangi payment yaratamiz
        payment = Payment(
            order_id=order.id,
            provider="payme",
            provider_id=transaction_id,
            amount=order.total,
            status=PaymentStatus.pending,
            state=1,
            create_time=time_ms,
        )
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)
        
        return {
            "create_time": time_ms,
            "transaction": str(payment.id),
            "state": 1,
        }
    
    async def PerformTransaction(self, params: dict):
        transaction_id = params["id"]
        payment = await self.db.scalar(
            select(Payment).where(
                Payment.provider == "payme",
                Payment.provider_id == transaction_id,
            )
        )
        if not payment:
            raise PaymeError(-31003)
        
        if payment.state == 2:
            # Allaqachon perform qilingan
            return {
                "transaction": str(payment.id),
                "perform_time": payment.perform_time,
                "state": 2,
            }
        
        if payment.state != 1:
            raise PaymeError(-31008)
        
        perform_time = int(time.time() * 1000)
        payment.state = 2
        payment.status = PaymentStatus.paid
        payment.perform_time = perform_time
        
        # Order'ni paid qilamiz
        order = await self.db.get(Order, payment.order_id)
        order.status = OrderStatus.paid
        order.paid_at = datetime.now(timezone.utc)
        
        # Kitoblarni user_library'ga qo'shamiz
        from app.models.order import OrderItem
        items = await self.db.scalars(
            select(OrderItem).where(OrderItem.order_id == order.id)
        )
        for item in items.all():
            db_entry = UserLibrary(
                user_id=order.user_id,
                book_id=item.book_id,
                order_id=order.id,
            )
            self.db.add(db_entry)
        
        await self.db.commit()
        
        # Background: PDF watermark, email, notification
        from app.tasks.book_tasks import watermark_purchased_books
        watermark_purchased_books.delay(str(order.id))
        
        return {
            "transaction": str(payment.id),
            "perform_time": perform_time,
            "state": 2,
        }
    
    async def CancelTransaction(self, params: dict):
        transaction_id = params["id"]
        reason = params.get("reason")
        
        payment = await self.db.scalar(
            select(Payment).where(
                Payment.provider == "payme",
                Payment.provider_id == transaction_id,
            )
        )
        if not payment:
            raise PaymeError(-31003)
        
        cancel_time = int(time.time() * 1000)
        
        if payment.state == 1:
            payment.state = -1
            payment.status = PaymentStatus.cancelled
        elif payment.state == 2:
            payment.state = -2
            payment.status = PaymentStatus.cancelled
            # TODO: order'ni refund, user_library'dan o'chirish
            order = await self.db.get(Order, payment.order_id)
            order.status = OrderStatus.refunded
        elif payment.state in (-1, -2):
            return {
                "transaction": str(payment.id),
                "cancel_time": payment.cancel_time,
                "state": payment.state,
            }
        else:
            raise PaymeError(-31007)
        
        payment.cancel_time = cancel_time
        payment.reason = reason
        await self.db.commit()
        
        return {
            "transaction": str(payment.id),
            "cancel_time": cancel_time,
            "state": payment.state,
        }
    
    async def CheckTransaction(self, params: dict):
        transaction_id = params["id"]
        payment = await self.db.scalar(
            select(Payment).where(
                Payment.provider == "payme",
                Payment.provider_id == transaction_id,
            )
        )
        if not payment:
            raise PaymeError(-31003)
        
        return {
            "create_time": payment.create_time or 0,
            "perform_time": payment.perform_time or 0,
            "cancel_time": payment.cancel_time or 0,
            "transaction": str(payment.id),
            "state": payment.state,
            "reason": payment.reason,
        }
    
    async def GetStatement(self, params: dict):
        from_time = params["from"]
        to_time = params["to"]
        
        from datetime import datetime as dt
        from_dt = dt.fromtimestamp(from_time / 1000, tz=timezone.utc)
        to_dt = dt.fromtimestamp(to_time / 1000, tz=timezone.utc)
        
        result = await self.db.scalars(
            select(Payment).where(
                Payment.provider == "payme",
                Payment.created_at >= from_dt,
                Payment.created_at <= to_dt,
            )
        )
        
        transactions = []
        for p in result.all():
            order = await self.db.get(Order, p.order_id)
            transactions.append({
                "id": p.provider_id,
                "time": p.create_time,
                "amount": int(p.amount * 100),
                "account": {"order_id": str(order.id)},
                "create_time": p.create_time or 0,
                "perform_time": p.perform_time or 0,
                "cancel_time": p.cancel_time or 0,
                "transaction": str(p.id),
                "state": p.state,
                "reason": p.reason,
            })
        
        return {"transactions": transactions}
```

## Frontend tomon

```vue
<!-- pages/checkout/index.vue -->
<script setup lang="ts">
const { $api } = useNuxtApp()
const cart = useCartStore()

async function pay() {
  // Order yaratamiz
  const order = await $api<{ id: string; total: number }>('/orders', {
    method: 'POST',
    body: { items: cart.items.map(i => ({ book_id: i.book_id })) },
  })
  
  // Payme checkout URL olamiz
  const { url } = await $api<{ url: string }>('/payments/payme/initiate', {
    method: 'POST',
    body: { order_id: order.id },
  })
  
  cart.clear()
  window.location.href = url
}
</script>

<template>
  <div>
    <CheckoutCart />
    <button @click="pay" class="btn-primary">{{ $t('checkout.pay') }}</button>
  </div>
</template>
```

## .env qo'shimcha

```env
PAYME_MERCHANT_ID=your-merchant-id
PAYME_MERCHANT_KEY=your-merchant-key
PAYME_CHECKOUT_URL=https://checkout.paycom.uz
# Sandbox uchun:
# PAYME_CHECKOUT_URL=https://checkout.test.paycom.uz
```

## Sandbox test

1. Payme'da test merchant oching
2. Webhook URL ko'rsating: `https://your-domain.com/api/v1/payments/payme/webhook`
3. Test karta: Payme hujjatida berilgan test ma'lumotlar

**Keyingi qadam:** `06-payment/02-payment-flow.md`
