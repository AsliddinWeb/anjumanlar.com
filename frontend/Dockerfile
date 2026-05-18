# syntax=docker/dockerfile:1.7
# Development image for Nuxt 3. Source is mounted via docker-compose volume;
# node_modules is preserved in a named volume so the host doesn't shadow it.

FROM node:20-alpine AS base

ENV PNPM_HOME="/pnpm" \
    PATH="$PNPM_HOME:$PATH" \
    NODE_ENV=development \
    NUXT_TELEMETRY_DISABLED=1

RUN corepack enable && corepack prepare pnpm@9.15.0 --activate

WORKDIR /app

# Install deps in a separate layer so package.json changes invalidate cache appropriately.
COPY package.json ./
# pnpm-lock.yaml is generated on first build; copy it if present.
COPY pnpm-lock.yaml* ./
RUN pnpm install

COPY . .

EXPOSE 3000

CMD ["pnpm", "dev"]
