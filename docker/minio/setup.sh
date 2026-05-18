#!/bin/sh
# MinIO bucket bootstrap — idempotent.
# Creates the buckets used by the backend and sets sensible visibility.
set -e

echo "[minio-init] waiting for MinIO alias..."
until mc alias set local http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null 2>&1; do
  sleep 1
done

create_bucket() {
  bucket="$1"
  visibility="$2"   # "public" or "private"

  if mc ls "local/$bucket" >/dev/null 2>&1; then
    echo "[minio-init] bucket '$bucket' already exists"
  else
    echo "[minio-init] creating bucket '$bucket'"
    mc mb "local/$bucket"
  fi

  if [ "$visibility" = "public" ]; then
    mc anonymous set download "local/$bucket" >/dev/null
    echo "[minio-init] '$bucket' → public read"
  else
    mc anonymous set none "local/$bucket" >/dev/null
    echo "[minio-init] '$bucket' → private"
  fi
}

# Private — only signed URLs / backend access
create_bucket "$MINIO_BUCKET_BOOKS"        private
create_bucket "$MINIO_BUCKET_BOOKS_WM"     private

# Public — directly served (covers, avatars, demos, blog images)
create_bucket "$MINIO_BUCKET_COVERS"       public
create_bucket "$MINIO_BUCKET_AVATARS"      public
create_bucket "$MINIO_BUCKET_DEMOS"        public
create_bucket "$MINIO_BUCKET_BLOG"         public

echo "[minio-init] done."
