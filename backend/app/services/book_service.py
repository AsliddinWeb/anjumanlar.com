"""Book lifecycle service.

State machine:

    draft ─── submit ──> pending ─── approve ──> approved
              ▲                  └── reject ──> rejected
              │                                    │
              └──── (author edits) ────────────────┘

- Authors create + edit in ``draft`` / ``rejected`` states only.
- ``submit`` moves draft → pending; admin then ``approve`` or ``reject``.
- ``delete_book`` removes the row outright (no soft-delete column). The
  FK from ``order_items.book_id`` defaults to RESTRICT, so a book that
  has been ordered will refuse to delete with a friendly error.

Public listings only ever surface ``approved`` rows.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from slugify import slugify
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.models import (
    AuthorProfile,
    Book,
    BookStatus,
    Category,
    User,
    UserRole,
)
from app.schemas.book import BookCreate, BookUpdate
from app.services import storage_service

# ---------- Helpers ----------


def _primary_title(title_map: dict[str, str]) -> str:
    """Pick the most "canonical" title across locales for slug generation."""
    for key in ("uz", "ru", "en"):
        if title_map.get(key):
            return title_map[key]
    # Fall back to the first non-empty value.
    for value in title_map.values():
        if isinstance(value, str) and value.strip():
            return value
    raise ValidationError("title must contain at least one non-empty locale")


async def _unique_slug(db: AsyncSession, base: str) -> str:
    candidate = slugify(base) or "book"
    n = 0
    while True:
        slug = f"{candidate}-{n}" if n else candidate
        slug = slug[:255]
        exists = await db.execute(select(Book.id).where(Book.slug == slug))
        if exists.scalar_one_or_none() is None:
            return slug
        n += 1


async def _load_categories(db: AsyncSession, category_ids: list[UUID]) -> list[Category]:
    if not category_ids:
        return []
    rows = (await db.execute(select(Category).where(Category.id.in_(category_ids)))).scalars().all()
    found = list(rows)
    if len(found) != len(set(category_ids)):
        raise ValidationError(
            "One or more category_ids do not exist",
            details={"code": "category_not_found"},
        )
    return found


def _book_load_options():
    """Eager-load relationships needed by the response models."""
    return (
        selectinload(Book.author),
        selectinload(Book.categories),
    )


async def _get_loaded(db: AsyncSession, book_id: UUID) -> Book:
    book = (
        await db.execute(select(Book).options(*_book_load_options()).where(Book.id == book_id))
    ).scalar_one_or_none()
    if book is None:
        raise NotFoundError("Book not found", details={"code": "book_not_found"})
    return book


def _assert_author_can_edit(book: Book, user: User) -> None:
    """Author can edit only their own books, only in draft/rejected status."""
    if user.role in {UserRole.admin, UserRole.superadmin}:
        return
    if book.uploaded_by != user.id:
        raise ForbiddenError("Not your book", details={"code": "not_owner"})
    if book.status not in {BookStatus.draft, BookStatus.rejected}:
        raise ConflictError(
            f"Cannot edit a book in status {book.status.value!r}",
            details={"code": "wrong_status", "status": book.status.value},
        )


# ---------- Author + admin actions ----------


async def create_book(
    db: AsyncSession, user: User, author_profile: AuthorProfile, data: BookCreate
) -> Book:
    if not any((v or "").strip() for v in data.title.values()):
        raise ValidationError(
            "title must contain at least one non-empty locale",
            details={"code": "empty_title"},
        )

    slug = await _unique_slug(db, _primary_title(data.title))
    categories = await _load_categories(db, data.category_ids)

    book = Book(
        author_id=author_profile.id,
        uploaded_by=user.id,
        slug=slug,
        title=data.title,
        subtitle=data.subtitle or {},
        description=data.description or {},
        language=data.language,
        isbn=data.isbn,
        publication_year=data.publication_year,
        publisher=data.publisher,
        price=data.price,
        discount_price=data.discount_price,
        keywords=data.keywords,
        status=BookStatus.draft,
    )
    book.categories = categories
    db.add(book)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise ConflictError("Slug collision creating book", details={"code": "slug_taken"}) from exc
    return await _get_loaded(db, book.id)


async def update_book(db: AsyncSession, user: User, book_id: UUID, data: BookUpdate) -> Book:
    book = await _get_loaded(db, book_id)
    _assert_author_can_edit(book, user)

    updates: dict[str, Any] = data.model_dump(exclude_unset=True, exclude={"category_ids"})
    for key, value in updates.items():
        setattr(book, key, value)

    if data.category_ids is not None:
        book.categories = await _load_categories(db, data.category_ids)

    await db.flush()
    return await _get_loaded(db, book.id)


async def admin_create_book(
    db: AsyncSession, admin: User, author_id: UUID, data: BookCreate
) -> Book:
    """Admin creates a book on behalf of any author profile.

    Unlike the author-self path the admin doesn't need to own an
    author_profile of their own — they just pick which author the book
    belongs to. ``uploaded_by`` still points at the admin so audit logs
    show who pushed the row in.
    """
    if not any((v or "").strip() for v in data.title.values()):
        raise ValidationError(
            "title must contain at least one non-empty locale",
            details={"code": "empty_title"},
        )

    profile = (
        await db.execute(select(AuthorProfile).where(AuthorProfile.id == author_id))
    ).scalar_one_or_none()
    if profile is None:
        raise ValidationError(
            "Author profile not found", details={"code": "author_not_found"}
        )

    slug = await _unique_slug(db, _primary_title(data.title))
    categories = await _load_categories(db, data.category_ids)

    book = Book(
        author_id=profile.id,
        uploaded_by=admin.id,
        slug=slug,
        title=data.title,
        subtitle=data.subtitle or {},
        description=data.description or {},
        language=data.language,
        isbn=data.isbn,
        publication_year=data.publication_year,
        publisher=data.publisher,
        price=data.price,
        discount_price=data.discount_price,
        keywords=data.keywords,
        status=BookStatus.draft,
    )
    book.categories = categories
    db.add(book)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise ConflictError("Slug collision creating book", details={"code": "slug_taken"}) from exc
    return await _get_loaded(db, book.id)


async def admin_update_book(
    db: AsyncSession, admin: User, book_id: UUID, data: BookUpdate
) -> Book:
    """Admin edit path — no status guard. Lets admins fix typos in
    already-approved books without having to bounce them through the
    full author/reject loop.
    """
    if admin.role not in {UserRole.admin, UserRole.superadmin}:
        raise ForbiddenError("Admin only", details={"code": "admin_required"})

    book = await _get_loaded(db, book_id)
    updates: dict[str, Any] = data.model_dump(exclude_unset=True, exclude={"category_ids"})
    for key, value in updates.items():
        setattr(book, key, value)
    if data.category_ids is not None:
        book.categories = await _load_categories(db, data.category_ids)

    await db.flush()
    # Re-index after admin tweaks so the search results catch up.
    if book.status == BookStatus.approved:
        from app.tasks.search_tasks import sync_book_to_meilisearch
        sync_book_to_meilisearch.delay(str(book.id))
    return await _get_loaded(db, book.id)


async def admin_publish_book(db: AsyncSession, admin: User, book_id: UUID) -> Book:
    """Admin shortcut — push a draft / rejected / pending book straight to
    approved without the explicit moderation round-trip. Useful when
    admin themselves authored the row (no point self-moderating)."""
    from app.tasks.search_tasks import sync_book_to_meilisearch

    if admin.role not in {UserRole.admin, UserRole.superadmin}:
        raise ForbiddenError("Admin only", details={"code": "admin_required"})

    book = await _get_loaded(db, book_id)
    if book.status == BookStatus.approved:
        raise ConflictError(
            "Already published", details={"code": "wrong_status", "status": book.status.value}
        )

    book.status = BookStatus.approved
    book.moderated_by = admin.id
    book.moderated_at = datetime.now(UTC)
    book.rejection_reason = None
    if book.published_at is None:
        book.published_at = book.moderated_at
    await db.flush()
    sync_book_to_meilisearch.delay(str(book.id))
    return await _get_loaded(db, book.id)


async def admin_unpublish_book(db: AsyncSession, admin: User, book_id: UUID) -> Book:
    """Admin shortcut — pull an approved book back to draft (hidden from
    the public catalogue and search index) without deleting it."""
    from app.tasks.search_tasks import remove_book_from_meilisearch

    if admin.role not in {UserRole.admin, UserRole.superadmin}:
        raise ForbiddenError("Admin only", details={"code": "admin_required"})

    book = await _get_loaded(db, book_id)
    if book.status != BookStatus.approved:
        raise ConflictError(
            "Only approved books can be unpublished",
            details={"code": "wrong_status", "status": book.status.value},
        )

    book.status = BookStatus.draft
    await db.flush()
    remove_book_from_meilisearch.delay(str(book.id))
    return await _get_loaded(db, book.id)


async def admin_list_all(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    status: BookStatus | None = None,
    search: str | None = None,
    author_id: UUID | None = None,
) -> tuple[list[Book], int]:
    """Full admin catalogue — every book regardless of status. Filters
    are AND-composed; missing values are ignored."""
    base = select(Book).options(*_book_load_options())
    if status is not None:
        base = base.where(Book.status == status)
    if author_id is not None:
        base = base.where(Book.author_id == author_id)
    if search:
        like = f"%{search}%"
        base = base.where(
            or_(
                func.cast(Book.title, sql_text_type()).ilike(like),
                Book.slug.ilike(like),
            )
        )
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    base = base.order_by(Book.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(base)).scalars().unique().all()
    return list(items), total


async def delete_book(db: AsyncSession, user: User, book_id: UUID) -> None:
    from app.tasks.search_tasks import remove_book_from_meilisearch

    book = await _get_loaded(db, book_id)
    if user.role not in {UserRole.admin, UserRole.superadmin} and book.uploaded_by != user.id:
        raise ForbiddenError("Not your book", details={"code": "not_owner"})

    book_id_str = str(book.id)
    await db.delete(book)
    try:
        await db.flush()
    except IntegrityError as exc:
        # order_items.book_id is RESTRICT — books that have been ordered
        # cannot be hard-deleted; refuse with a clear error rather than
        # exploding mid-transaction.
        await db.rollback()
        raise ConflictError(
            "Cannot delete a book that has orders. Archive it instead.",
            details={"code": "book_has_orders"},
        ) from exc

    remove_book_from_meilisearch.delay(book_id_str)


async def submit_for_moderation(db: AsyncSession, user: User, book_id: UUID) -> Book:
    book = await _get_loaded(db, book_id)
    if user.role not in {UserRole.admin, UserRole.superadmin} and book.uploaded_by != user.id:
        raise ForbiddenError("Not your book", details={"code": "not_owner"})
    if book.status not in {BookStatus.draft, BookStatus.rejected}:
        raise ConflictError(
            f"Cannot submit a book in status {book.status.value!r}",
            details={"code": "wrong_status", "status": book.status.value},
        )
    book.status = BookStatus.pending
    book.rejection_reason = None
    await db.flush()
    return await _get_loaded(db, book.id)


async def approve(db: AsyncSession, admin: User, book_id: UUID) -> Book:
    from app.tasks.search_tasks import sync_book_to_meilisearch

    book = await _get_loaded(db, book_id)
    if book.status != BookStatus.pending:
        raise ConflictError(
            f"Only pending books can be approved (got {book.status.value!r})",
            details={"code": "wrong_status", "status": book.status.value},
        )
    book.status = BookStatus.approved
    book.moderated_by = admin.id
    book.moderated_at = datetime.now(UTC)
    book.rejection_reason = None
    if book.published_at is None:
        book.published_at = book.moderated_at
    await db.flush()
    sync_book_to_meilisearch.delay(str(book.id))
    await _notify_book_moderation(db, book, template="book_approved")
    return await _get_loaded(db, book.id)


async def reject(db: AsyncSession, admin: User, book_id: UUID, reason: str) -> Book:
    from app.tasks.search_tasks import remove_book_from_meilisearch

    book = await _get_loaded(db, book_id)
    if book.status != BookStatus.pending:
        raise ConflictError(
            f"Only pending books can be rejected (got {book.status.value!r})",
            details={"code": "wrong_status", "status": book.status.value},
        )
    book.status = BookStatus.rejected
    book.rejection_reason = reason
    book.moderated_by = admin.id
    book.moderated_at = datetime.now(UTC)
    await db.flush()
    remove_book_from_meilisearch.delay(str(book.id))
    await _notify_book_moderation(db, book, template="book_rejected", reason=reason)
    return await _get_loaded(db, book.id)


async def _notify_book_moderation(
    db: AsyncSession,
    book: Book,
    *,
    template: str,
    reason: str | None = None,
) -> None:
    """Fire-and-forget moderation email to the uploader.

    Wrapped in a try/except: a Celery enqueue failure must not roll back
    the state transition the moderator just made.
    """
    try:
        from app.tasks.email_tasks import send_template_email

        uploader = (
            await db.execute(select(User).where(User.id == book.uploaded_by))
        ).scalar_one_or_none()
        if uploader is None:
            return
        title_map = book.title or {}
        primary_title = (
            title_map.get(uploader.preferred_locale)
            or title_map.get("uz")
            or title_map.get("en")
            or next(iter(title_map.values()), book.slug)
        )
        context = {
            "full_name": uploader.full_name,
            "email": uploader.email,
            "book_title": primary_title,
            "book_slug": book.slug,
        }
        if reason is not None:
            context["reason"] = reason
        send_template_email.delay(
            to=uploader.email,
            template_name=template,
            locale=uploader.preferred_locale or "uz",
            context=context,
        )
    except Exception:
        import logging

        logging.getLogger(__name__).exception(
            "book moderation email enqueue failed (book=%s)", book.id
        )


# ---------- Read paths ----------


async def get_public_by_slug(db: AsyncSession, slug: str) -> Book:
    book = (
        await db.execute(
            select(Book)
            .options(*_book_load_options())
            .where(
                Book.slug == slug,
                Book.status == BookStatus.approved,
            )
        )
    ).scalar_one_or_none()
    if book is None:
        raise NotFoundError("Book not found", details={"code": "book_not_found"})
    return book


async def get_for_owner(db: AsyncSession, user: User, book_id: UUID) -> Book:
    """Author's own view — bypasses the approved-only filter so the author
    sees drafts/rejected too."""
    book = await _get_loaded(db, book_id)
    if user.role not in {UserRole.admin, UserRole.superadmin} and book.uploaded_by != user.id:
        raise ForbiddenError("Not your book", details={"code": "not_owner"})
    return book


async def list_public(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    search: str | None = None,
    category_slug: str | None = None,
    author_slug: str | None = None,
    language: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    featured: bool | None = None,
    sort: str = "-published_at",
) -> tuple[list[Book], int]:
    base = (
        select(Book)
        .options(*_book_load_options())
        .where(Book.status == BookStatus.approved)
    )

    if search:
        like = f"%{search}%"
        # Postgres JSONB → text via ::text + ILIKE. Good enough until
        # Meilisearch comes online in Phase 2.5.
        base = base.where(
            or_(
                func.cast(Book.title, sql_text_type()).ilike(like),
                func.cast(Book.description, sql_text_type()).ilike(like),
            )
        )
    if category_slug:
        base = base.join(Book.categories).where(Category.slug == category_slug)
    if author_slug:
        base = base.join(Book.author).where(AuthorProfile.slug == author_slug)
    if language:
        base = base.where(Book.language == language)
    if min_price is not None:
        base = base.where(Book.price >= min_price)
    if max_price is not None:
        base = base.where(Book.price <= max_price)
    if featured is not None:
        base = base.where(Book.featured.is_(featured))

    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()

    base = _apply_sort(base, sort).offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(base)).scalars().unique().all()
    return list(items), total


async def list_my_books(
    db: AsyncSession,
    user: User,
    *,
    page: int,
    page_size: int,
    status: BookStatus | None = None,
) -> tuple[list[Book], int]:
    base = (
        select(Book)
        .options(*_book_load_options())
        .where(Book.uploaded_by == user.id)
    )
    if status is not None:
        base = base.where(Book.status == status)

    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    base = base.order_by(Book.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(base)).scalars().unique().all()
    return list(items), total


async def list_moderation_queue(
    db: AsyncSession, *, page: int, page_size: int
) -> tuple[list[Book], int]:
    base = (
        select(Book)
        .options(*_book_load_options())
        .where(Book.status == BookStatus.pending)
    )
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    items = (
        (
            await db.execute(
                base.order_by(Book.created_at.asc()).offset((page - 1) * page_size).limit(page_size)
            )
        )
        .scalars()
        .unique()
        .all()
    )
    return list(items), total


# ---------- File uploads ----------


def _assert_can_upload(book: Book, user: User) -> None:
    """Files can be (re)uploaded by the author while a book is in
    ``draft`` or ``rejected`` state. Admins can override anytime."""
    if user.role in {UserRole.admin, UserRole.superadmin}:
        return
    if book.uploaded_by != user.id:
        raise ForbiddenError("Not your book", details={"code": "not_owner"})
    if book.status not in {BookStatus.draft, BookStatus.rejected}:
        raise ConflictError(
            f"Cannot upload files for a book in status {book.status.value!r}",
            details={"code": "wrong_status", "status": book.status.value},
        )


async def set_cover(
    db: AsyncSession,
    user: User,
    book_id: UUID,
    raw: bytes,
    content_type: str,
) -> Book:
    """Push the new cover to MinIO and persist the URL."""
    book = await _get_loaded(db, book_id)
    _assert_can_upload(book, user)
    book.cover_url = storage_service.upload_book_cover(book.id, raw, content_type)
    await db.flush()
    return await _get_loaded(db, book.id)


async def set_file(
    db: AsyncSession,
    user: User,
    book_id: UUID,
    raw: bytes,
    content_type: str,
) -> Book:
    """Store the canonical PDF; update ``pages_count`` + ``file_size_mb``,
    then queue the demo-PDF generator on Celery so ``book.demo_url`` lands
    a few seconds later without blocking the upload response."""
    # Lazy import — avoids the auth_service ↔ email_tasks-style circular
    # import trap we hit in Phase 1.
    from app.tasks.pdf_tasks import generate_demo_pdf

    book = await _get_loaded(db, book_id)
    _assert_can_upload(book, user)
    result = storage_service.upload_book_file(book.id, raw, content_type)
    book.file_url = result.url
    book.pages_count = result.pages_count
    book.file_size_mb = result.file_size_mb
    await db.flush()

    # Fire-and-forget. If the broker is down the user still gets a 200 and
    # the demo materialises whenever the worker drains the queue.
    generate_demo_pdf.delay(str(book.id))

    return await _get_loaded(db, book.id)


# ---------- Sort helper ----------


_SORT_MAP = {
    "created_at": Book.created_at.asc(),
    "-created_at": Book.created_at.desc(),
    "price": Book.price.asc(),
    "-price": Book.price.desc(),
    "-average_rating": Book.average_rating.desc(),
    "-views_count": Book.views_count.desc(),
    "-sales_count": Book.sales_count.desc(),
    "published_at": Book.published_at.asc().nulls_last(),
    "-published_at": Book.published_at.desc().nulls_last(),
}


def _apply_sort(stmt, sort: str):
    clause = _SORT_MAP.get(sort, _SORT_MAP["-published_at"])
    return stmt.order_by(clause)


def sql_text_type():
    """Lazy import to keep top-level imports tidy."""
    from sqlalchemy import Text as _T

    return _T
