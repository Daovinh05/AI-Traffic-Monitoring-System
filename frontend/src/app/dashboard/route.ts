import type { NextRequest } from "next/server";

export const dynamic = "force-dynamic";

function backendUrl() {
  return (
    process.env.NEXT_BACKEND_INTERNAL_URL ||
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    "http://localhost:5001"
  ).replace(/\/$/, "");
}

export async function GET(request: NextRequest) {
  const target = new URL("/dashboard", backendUrl());
  target.search = request.nextUrl.search;

  try {
    const backendResponse = await fetch(target, {
      headers: {
        cookie: request.headers.get("cookie") || "",
        "user-agent": request.headers.get("user-agent") || "",
      },
      cache: "no-store",
      redirect: "manual",
    });

    const headers = new Headers(backendResponse.headers);
    headers.delete("content-encoding");
    headers.delete("content-length");
    headers.delete("transfer-encoding");

    return new Response(backendResponse.body, {
      status: backendResponse.status,
      headers,
    });
  } catch (error) {
    console.error("Dashboard backend proxy error:", error);
    return new Response("Backend is unavailable", { status: 502 });
  }
}
