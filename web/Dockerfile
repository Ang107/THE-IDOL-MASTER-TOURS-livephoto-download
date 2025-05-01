# 1) Build stage
ARG NEXT_PUBLIC_API_BASE
FROM node:20-alpine AS builder
WORKDIR /app

# ビルド時に渡された NEXT_PUBLIC_API_BASE を環境変数にセット
# （npm run build 内で process.env.NEXT_PUBLIC_API_BASE として使われる）
ENV NEXT_PUBLIC_API_BASE=${NEXT_PUBLIC_API_BASE}

# 依存インストール
COPY package.json package-lock.json ./
RUN npm ci

# ソースコピー & ビルド
COPY . .
RUN npm run build && npm prune --production

# 2) Runtime stage
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# ビルド成果物をコピー
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

# デフォルトポートを設定（Render は $PORT を割り当てる）
EXPOSE 3000

# 起動時にランタイムPORTを使う（未設定時は3000）
CMD ["sh", "-c", "npx next start -H 0.0.0.0 -p ${PORT:-3000}"]
