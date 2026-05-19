// Shape definitions mirroring backend Pydantic schemas under
// backend/app/schemas/auth.py. Keep in sync when the backend evolves.

export type UserRole = "reader" | "author" | "admin" | "superadmin";
export type UserStatus = "active" | "pending" | "blocked" | "deleted";
export type Locale = "uz" | "ru" | "en";

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
