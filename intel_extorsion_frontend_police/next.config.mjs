/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  basePath: '/policial',
  trailingSlash: true,
  images: {
    domains: ['localhost', 'ipfs.io', 'gateway.pinata.cloud'],
  },
  async rewrites() {
    return [
      {
        source: '/policial/api/agents/:path*',
        destination: 'http://agent-api:8000/v1/:path*',
      },
      {
        source: '/policial/api/web3/:path*',
        destination: 'http://web3-backend:8001/v1/:path*',
      },
    ];
  },
};

export default nextConfig;
