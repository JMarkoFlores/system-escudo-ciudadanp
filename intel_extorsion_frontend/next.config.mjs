/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  images: {
    domains: ['localhost', 'ipfs.io', 'gateway.pinata.cloud'],
  },
  async rewrites() {
    return [
      {
        source: '/api/agents/:path*',
        destination: 'http://localhost:8000/v1/:path*',
      },
      {
        source: '/api/web3/:path*',
        destination: 'http://localhost:8001/v1/:path*',
      },
    ];
  },
};

export default nextConfig;
