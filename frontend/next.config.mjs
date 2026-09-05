/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    let raw = (process.env.BACKEND_API_URL || "http://127.0.0.1:8000").trim().replace(/\/+$/, "");
    if (!raw.startsWith("http://") && !raw.startsWith("https://")) {
      raw = `https://${raw}`;
    }
    const backendUrl = raw;
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
      {
        source: "/merchants/:path*",
        destination: `${backendUrl}/merchants/:path*`,
      },
      {
        source: "/orders/:path*",
        destination: `${backendUrl}/orders/:path*`,
      },
    ];
  },

};

export default nextConfig;
