# web/Dockerfile

# 1) Build application with dev dependencies
FROM node:20-alpine AS builder
WORKDIR /app

# Copy package files and install all dependencies (dev + prod)
COPY package.json package-lock.json ./
RUN npm ci

# Copy source code and build
COPY . .
RUN npm run build && npm prune --production

# 2) Production image
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# Copy build output and production dependencies
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000
CMD ["sh", "-c", "npm run start -- -H 0.0.0.0 -p $PORT"]
