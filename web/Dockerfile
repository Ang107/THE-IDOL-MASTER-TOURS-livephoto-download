# web/Dockerfile

FROM node:20-alpine

# 作業ディレクトリ
WORKDIR /app

# 依存だけ先にインストール
COPY package.json package-lock.json ./
RUN npm ci

# ソースをすべてコピー
COPY . .

# ポートを宣言（Render 側の $PORT へバインドされる）
EXPOSE 3000

# コンテナ起動時に環境変数を使ってビルド＆起動
CMD ["sh", "-c", "npm run build && npx next start -H 0.0.0.0 -p $PORT"]
