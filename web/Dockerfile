# 1) Build stage
ARG NEXT_PUBLIC_API_BASE
FROM node:20-alpine AS builder
WORKDIR /app

# ビルド時の引数を ENV にセット（next build で使う）
ENV NEXT_PUBLIC_API_BASE=${NEXT_PUBLIC_API_BASE}

COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build && npm prune --production

# 2) Runtime stage
# → ここでも ARG を再宣言しないと、build 時の値が使えません
ARG NEXT_PUBLIC_API_BASE
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# （必要に応じて runtime でも ENV に落とし込む）
ENV NEXT_PUBLIC_API_BASE=${NEXT_PUBLIC_API_BASE}

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000
CMD ["sh", "-c", "npx next start -H 0.0.0.0 -p ${PORT:-3000}"]
