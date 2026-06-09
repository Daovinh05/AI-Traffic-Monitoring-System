import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const backendUrl =
      process.env.NEXT_BACKEND_INTERNAL_URL ||
      process.env.NEXT_PUBLIC_BACKEND_URL ||
      "http://localhost:5001";
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
      {
        source: "/recordings/:path*",
        destination: `${backendUrl}/recordings/:path*`,
      },
      {
        source: "/sound/:path*",
        destination: `${backendUrl}/sound/:path*`,
      },
      {
        source: "/static/:path*",
        destination: "/legacy/:path*",
      },
      ...[
        "dashboard",
        "trang_chu",
        "lai_xe",
        "lai_xe_v2",
        "lich_su",
        "tu_van",
        "tu_van.html",
        "traffic_bus",
      ].map((path) => ({
        source: `/${path}`,
        destination: `${backendUrl}/${path}`,
      })),
      ...[
        "video_driver",
        "video_traffic",
        "video_sign",
        "video_vacham",
        "get_warnings",
        "get_latest_sign_image",
        "get_stats",
        "set_mode",
        "toggle_warning",
        "start_recording",
        "stop_recording",
        "stop_camera",
        "change_region_points",
      ].map((path) => ({
        source: `/${path}`,
        destination: `${backendUrl}/${path}`,
      })),
    ];
  },
};

export default nextConfig;
