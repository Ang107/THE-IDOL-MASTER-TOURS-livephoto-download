import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // ここで experimental 以下に serverActions の設定を追加
  experimental: {
    serverActions: {
      // ボディ上限を 25MB に設定（必要に応じて調整）
      bodySizeLimit: 250 * 1024 * 1024,
    },
  },
};

export default nextConfig;