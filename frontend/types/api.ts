// Shape definitions mirroring backend Pydantic schemas. Keep in sync when
// the backend evolves — there's no codegen pipeline yet (Phase 6 candidate).
//
// JSONB / multilingual fields are typed as `LocalisedText` so callers can
// pick the active locale via `useLocaleText` rather than re-implementing
// the fallback chain inline.

export type UserRole = "reader" | "author" | "admin" | "superadmin";
export type UserStatus = "active" | "pending" | "blocked" | "deleted";
export type Locale = "uz" | "ru" | "en";

export type LocalisedText = Partial<Record<Locale | string, string>>;

// ---------- User / auth ----------

export interface UserPublic {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  status: UserStatus;
  email_verified: boolean;
  avatar_url: string | null;
  preferred_locale: string;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
}

export interface LoginResponse extends TokenPair {
  user: UserPublic;
}

export interface MessageResponse {
  message: string;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

// ---------- Author ----------

export interface AuthorPublic {
  id: string;
  slug: string;
  display_name: string;
  bio: LocalisedText;
  academic_title: string | null;
  institution: string | null;
  website: string | null;
  social_links: Record<string, string>;
  verified: boolean;
  featured: boolean;
  total_sales: number;
  created_at: string;
}

export interface AuthorList {
  items: AuthorPublic[];
  total: number;
  page: number;
  page_size: number;
}

// ---------- Category ----------

export interface CategoryPublic {
  id: string;
  parent_id: string | null;
  slug: string;
  name: LocalisedText;
  description: LocalisedText;
  icon: string | null;
  image_url: string | null;
  sort_order: number;
  is_active: boolean;
  book_count: number;
}

export interface CategoryTreeNode extends CategoryPublic {
  children: CategoryTreeNode[];
}

export interface CategoryList {
  items: CategoryPublic[];
  total: number;
}

// ---------- Book ----------

export type BookLanguage = "uz" | "ru" | "en" | "mixed";

export interface BookCategoryRef {
  id: string;
  slug: string;
  name: LocalisedText;
}

export interface BookAuthorRef {
  id: string;
  slug: string;
  display_name: string;
}

export interface BookPublic {
  id: string;
  slug: string;
  title: LocalisedText;
  subtitle: LocalisedText;
  description: LocalisedText;
  language: BookLanguage;
  isbn: string | null;
  pages_count: number | null;
  cover_url: string | null;
  demo_url: string | null;
  publication_year: number | null;
  publisher: string | null;
  price: number;
  discount_price: number | null;
  is_free: boolean;
  average_rating: number;
  reviews_count: number;
  views_count: number;
  sales_count: number;
  featured: boolean;
  published_at: string | null;
  created_at: string;
  author: BookAuthorRef;
  categories: BookCategoryRef[];
}

export interface BookList {
  items: BookPublic[];
  total: number;
  page: number;
  page_size: number;
}

// ---------- Review ----------

export interface ReviewAuthorRef {
  id: string;
  full_name: string;
  avatar_url: string | null;
}

export interface ReviewPublic {
  id: string;
  book_id: string;
  rating: number; // 1-5
  title: string | null;
  body: string;
  helpful_count: number;
  created_at: string;
  user: ReviewAuthorRef;
}

export interface ReviewList {
  items: ReviewPublic[];
  total: number;
  page: number;
  page_size: number;
}

// ---------- Wishlist ----------

export interface WishlistItem {
  id: string;
  created_at: string;
  book: BookPublic;
}

export interface WishlistList {
  items: WishlistItem[];
  total: number;
}
