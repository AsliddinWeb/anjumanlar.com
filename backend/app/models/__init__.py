"""Re-export every ORM class so Alembic autogenerate sees the full metadata.

Adding a new model? Import it here.
"""

from app.models.audit_log import AuditAction, AuditLog
from app.models.auth_token import AuthToken, AuthTokenPurpose
from app.models.author_profile import AuthorProfile
from app.models.book import Book, BookLanguage, BookStatus
from app.models.book_category import book_categories
from app.models.category import Category
from app.models.refresh_token import RefreshToken
from app.models.review import Review, ReviewStatus
from app.models.user import User, UserRole, UserStatus
from app.models.wishlist import Wishlist

__all__ = [
    "AuditAction",
    "AuditLog",
    "AuthToken",
    "AuthTokenPurpose",
    "AuthorProfile",
    "Book",
    "BookLanguage",
    "BookStatus",
    "Category",
    "RefreshToken",
    "Review",
    "ReviewStatus",
    "User",
    "UserRole",
    "UserStatus",
    "Wishlist",
    "book_categories",
]
