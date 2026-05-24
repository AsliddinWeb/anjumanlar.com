-- Monografiya — PostgreSQL initial setup
-- Runs once on first container start (empty data dir).

-- UUID generation used as primary key default across all tables.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Case-insensitive text (used for email uniqueness).
CREATE EXTENSION IF NOT EXISTS citext;

-- Trigram index — helps search-by-slug fallback when Meilisearch is down.
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Useful for full-text search dictionaries (if we ever use Postgres FTS).
CREATE EXTENSION IF NOT EXISTS unaccent;
