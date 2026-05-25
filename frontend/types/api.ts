// Shape definitions mirroring backend Pydantic schemas. Keep in sync when
// the backend evolves — there's no codegen pipeline yet (Phase 6 candidate).
//
// JSONB / multilingual fields are typed as `LocalisedText` so callers can
// pick the active locale via `useLocaleText` rather than re-implementing
// the fallback chain inline.

export type UserRole = "reader" | "author" | "admin" | "superadmin";
export type UserStatus = "active" | "pending" | "blocked";
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

export type BookStatus =
  | "draft"
  | "pending"
  | "approved"
  | "rejected"
  | "archived";

export interface BookOwnerView extends BookPublic {
  status: BookStatus;
  rejection_reason: string | null;
  file_url: string | null;
  keywords: string[];
}

export interface BookOwnerList {
  items: BookOwnerView[];
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

export type ReviewStatus = "pending" | "approved" | "rejected";

export interface ReviewAdminView extends ReviewPublic {
  status: ReviewStatus;
}

export interface ReviewAdminList {
  items: ReviewAdminView[];
  total: number;
  page: number;
  page_size: number;
}

// ---------- Admin user list ----------

export interface UserList {
  items: UserPublic[];
  total: number;
  page: number;
  page_size: number;
}

// ---------- Audit log ----------

export type AuditAction =
  | "register"
  | "email_verified"
  | "resend_verification"
  | "login_success"
  | "login_failed"
  | "logout"
  | "logout_all"
  | "password_changed"
  | "password_reset_requested"
  | "password_reset_completed"
  | "profile_updated"
  | "avatar_uploaded"
  | "account_deleted";

export interface AuditLogPublic {
  id: string;
  user_id: string | null;
  action: AuditAction;
  ip_address: string | null;
  user_agent: string | null;
  meta: Record<string, unknown>;
  created_at: string;
}

export interface AuditLogList {
  items: AuditLogPublic[];
  total: number;
  page: number;
  page_size: number;
}

// ---------- Blog ----------

export type BlogPostStatus = "draft" | "published" | "archived";

export interface BlogPostPublic {
  id: string;
  slug: string;
  title: LocalisedText;
  excerpt: LocalisedText;
  body: LocalisedText;
  cover_url: string | null;
  published_at: string | null;
  created_at: string;
}

export interface BlogPostAdminView extends BlogPostPublic {
  status: BlogPostStatus;
}

export interface BlogPostList {
  items: BlogPostPublic[];
  total: number;
  page: number;
  page_size: number;
}

export interface BlogPostAdminList {
  items: BlogPostAdminView[];
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

// ---------- Orders ----------

export type OrderStatus =
  | "pending"
  | "paid"
  | "expired"
  | "cancelled"
  | "failed"
  | "refunded";

export interface OrderItemPublic {
  id: string;
  book: BookPublic;
  price: number;
  commission_rate: number;
  author_earning: number;
  platform_fee: number;
}

export interface OrderPublic {
  id: string;
  order_number: string;
  status: OrderStatus;
  subtotal: number;
  discount: number;
  total: number;
  currency: string;
  payment_method: string | null;
  paid_at: string | null;
  expires_at: string | null;
  created_at: string;
  items: OrderItemPublic[];
}

export interface OrderCheckout {
  order: OrderPublic;
  payment_url: string | null;
}

export interface OrderList {
  items: OrderPublic[];
  total: number;
  page: number;
  page_size: number;
}

// ---------- Library ----------

export interface UserLibraryItem {
  id: string;
  book: BookPublic;
  watermarked_url: string | null;
  downloaded_count: number;
  last_downloaded_at: string | null;
  acquired_at: string;
}

export interface UserLibraryList {
  items: UserLibraryItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface DownloadResponse {
  url: string;
  expires_in: number;
}

// ---------- Author balance + withdrawals ----------

export interface AuthorBalance {
  available_balance: number;
  pending_balance: number;
  total_revenue: number;
  total_sales: number;
  commission_rate: number;
  currency: string;
}

export type WithdrawalStatus =
  | "requested"
  | "approved"
  | "processing"
  | "completed"
  | "rejected"
  | "cancelled";

export interface WithdrawalPublic {
  id: string;
  amount: number;
  currency: string;
  status: WithdrawalStatus;
  bank_details: Record<string, unknown>;
  admin_notes: string | null;
  transaction_ref: string | null;
  processed_at: string | null;
  created_at: string;
}

export interface WithdrawalList {
  items: WithdrawalPublic[];
  total: number;
  page: number;
  page_size: number;
}
