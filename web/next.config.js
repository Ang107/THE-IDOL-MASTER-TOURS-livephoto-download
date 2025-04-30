/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    serverActions: {
      bodySizeLimit: 250 * 1024 * 1024, // 250 MiB
    },
  },
}

module.exports = nextConfig
