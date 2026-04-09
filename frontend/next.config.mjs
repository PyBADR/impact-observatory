/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  eslint: { ignoreDuringBuilds: true },
  typescript: { ignoreBuildErrors: false },
  images: { unoptimized: true },
  async rewrites() {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    return [
      {
        source: "/api/health",
        destination: "${apiBase}/health",  // eslint-disable-line no-template-curly-in-string
      },
      {
        source: "/api/:path*",
        destination: "${apiBase}/api/:path*",
      },
      {
        source: "/health",
        destination: "${apiBase}/health",
      },
    ];
  },
};

export default nextConfig;
