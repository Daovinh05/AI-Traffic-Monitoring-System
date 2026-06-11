"use client";

import { useEffect, useState } from "react";
import "./LegacyFrame.css";

type LegacyFrameProps = {
  title: string;
  path: string;
};

export function LegacyFrame({ title, path }: LegacyFrameProps) {
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    let active = true;

    async function verifyUserRole() {
      try {
        const response = await fetch("/api/check-auth", {
          credentials: "include",
          cache: "no-store",
        });
        const data = await response.json();
        if (!active) return;

        if (!data.authenticated) {
          window.location.replace("/login");
          return;
        }
        if (data.user?.role === "admin") {
          window.location.replace("/dashboard");
          return;
        }
        setAuthorized(true);
      } catch {
        if (active) setAuthorized(false);
      }
    }

    verifyUserRole();
    const handleFocus = () => verifyUserRole();
    window.addEventListener("focus", handleFocus);
    return () => {
      active = false;
      window.removeEventListener("focus", handleFocus);
    };
  }, []);

  if (!authorized) {
    return (
      <main className="legacy-frame-page" aria-busy="true">
        <div>Đang kiểm tra phiên đăng nhập...</div>
      </main>
    );
  }

  return (
    <main className="legacy-frame-page">
      <iframe
        title={title}
        src={path}
        className="legacy-frame"
        allow="camera; microphone; autoplay; clipboard-read; clipboard-write"
      />
    </main>
  );
}
